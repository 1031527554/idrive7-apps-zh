#!/usr/bin/env python3
"""Glyph coverage: which characters of the fork's Chinese are NOT in the atlas.

The committed atlas kit/runtime/fonts/cjk.json is baked from
kit/runtime/locales/zh-CN.json only (kit/tools/bake_cjk.py), so anything this
fork translated outside that file - fork-tools/zh-CN-supplement.json - has no
glyph and kit/runtime/fonts.js draws it as "?".

    python fork-tools/check_glyphs.py [--atlas PATH] [--fork DIR]

--atlas defaults to <fork>/kit/runtime/fonts/cjk.json (independent of the current
directory); a relative --atlas is taken from the current directory first, then from
the fork root:
    python fork-tools/check_glyphs.py --atlas fork-tools/out/cjk.json
Exit status is 0 when nothing is missing, 1 when a character is missing, 2 when
the atlas cannot be read. ASCII is checked as well: a truncated atlas must not pass.
"""
import argparse
import json
from pathlib import Path
import sys

FORK = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--atlas', default=None,
                        help='atlas to check (default: <fork>/kit/runtime/fonts/cjk.json)')
    parser.add_argument('--fork', default=str(FORK), help='fork root (default: this script\'s repo)')
    args = parser.parse_args()

    fork = Path(args.fork).resolve()
    if args.atlas is None:
        atlas_path = fork / 'kit/runtime/fonts/cjk.json'
    else:
        atlas_path = Path(args.atlas)
        if not atlas_path.is_absolute():
            atlas_path = Path.cwd() / atlas_path
            if not atlas_path.exists() and (fork / args.atlas).exists():
                atlas_path = fork / args.atlas
    atlas_path = atlas_path.resolve()
    if not atlas_path.exists():
        print(f'atlas not found: {atlas_path}', file=sys.stderr)
        return 2
    atlas = json.loads(atlas_path.read_text(encoding='utf-8'))
    sizes = atlas.get('sizes') or []
    covered = set()
    for s in sizes:
        covered |= {int(cp) for cp in s.get('glyphs', {})}
    shown = atlas_path
    try:
        shown = atlas_path.relative_to(Path.cwd())
    except ValueError:
        pass
    print(f'atlas: {shown}')
    real = set(covered)                      # what the atlas really has, before ASCII is assumed
    ascii_missing = [c for c in range(0x20, 0x7f) if c not in real]
    if sizes:
        print(f'       {len(sizes)} size(s) {[s.get("size") for s in sizes]}, {len(covered)} glyphs, '
              f'{sizes[0].get("atlasW")}x{sizes[0].get("atlasH")} px, source {atlas.get("source")}')
    else:
        print('       no sizes - nothing is covered')
    print(f'       family {atlas.get("family")}, cacheKey {atlas.get("cacheKey")}')
    if ascii_missing:
        print(f'       ASCII glyphs missing: {len(ascii_missing)} '
              f'({"".join(chr(c) for c in ascii_missing[:24])}) - the atlas is truncated')

    # ASCII is expected (baker.TEXT) but not assumed: a truncated atlas must not pass
    covered |= set(range(0x20, 0x7f))

    def missing(text):
        return sorted({ch for ch in text if ord(ch) > 0x7f and ord(ch) not in covered})

    catalog = json.loads((fork / 'kit/runtime/locales/zh-CN.json').read_text(encoding='utf-8'))
    supplement = json.loads((fork / 'fork-tools/zh-CN-supplement.json').read_text(encoding='utf-8'))
    sup_items = {k: v for k, v in supplement.items() if not k.startswith('_')}

    cat_missing = {k: missing(_text(v)) for k, v in catalog.items()}
    cat_missing = {k: m for k, m in cat_missing.items() if m}
    sup_missing = {k: missing(_text(v)) for k, v in sup_items.items()}
    sup_missing = {k: m for k, m in sup_missing.items() if m}

    print(f'\nupstream catalog kit/runtime/locales/zh-CN.json: {len(catalog)} entries, '
          f'{len(cat_missing)} with a glyph missing')
    for k, m in list(cat_missing.items())[:10]:
        print(f'   {k[:44]:<46} missing {len(m)}: {"".join(m[:20])}')

    print(f'\nfork supplement fork-tools/zh-CN-supplement.json: {len(sup_items)} entries, '
          f'{len(sup_missing)} with a glyph missing')
    all_missing = set()
    for k, m in sup_missing.items():
        all_missing |= set(m)
        print(f'   {k[:40]:<42} "{_text(sup_items[k])[:18]}"  missing {len(m)}: {"".join(m[:24])}')
    print(f'\nunion of characters this fork needs and the atlas lacks: {len(all_missing)}')
    print(''.join(sorted(all_missing)))

    if cat_missing or sup_missing or ascii_missing:
        print('\nFAIL: the atlas does not cover all the text that is drawn '
              f'({len(all_missing)} Chinese character(s) and {len(ascii_missing)} ASCII glyph(s) missing; '
              'a missing glyph draws as "?"). Re-bake with fork-tools/bake_cjk_fork.py.')
        return 1
    print('\nOK: the atlas covers every Chinese character of the upstream catalog and the fork supplement.')
    return 0


def _text(value):
    """Every string inside a catalog value, joined (values may be nested)."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ''.join(_text(v) for v in value)
    if isinstance(value, dict):
        return ''.join(_text(v) for v in value.values())
    return ''


if __name__ == '__main__':
    raise SystemExit(main())
