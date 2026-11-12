#!/usr/bin/env python3
"""Bake the fork's Chinese glyph atlas: upstream corpus + this fork's supplement.

kit/tools/bake_cjk.py bakes only kit/runtime/locales/zh-CN.json, but this fork's
extra Chinese lives in fork-tools/zh-CN-supplement.json. Those characters have no
glyph in the committed atlas and kit/runtime/fonts.js then falls back to
glyphs[63], i.e. they draw as "?" on the head unit. This script is the same bake
(same font, same SHA-256 check, same 48/44/40/36/32 fallback, same <=2048 px
budget, same output structure) with the supplement's strings added to the corpus.
kit/tools/bake_cjk.py is deliberately left untouched so the fork stays mergeable.

    python fork-tools/bake_cjk_fork.py [--out PATH] [--font PATH] [<font.ttf>]

The default output is fork-tools/out/cjk.json: the committed
kit/runtime/fonts/cjk.json is NOT touched unless you pass --out explicitly.
The upstream diagnostic atlas (kit/localization/fonts/diagnostic-zh-CN.json) is
not built here; use kit/tools/bake_cjk.py --diagnostic for that one.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import urllib.request

FORK = Path(__file__).resolve().parent.parent
KIT_TOOLS = FORK / 'kit/tools'
LOCALES = FORK / 'kit/runtime/locales/zh-CN.json'
SUPPLEMENT = FORK / 'fork-tools/zh-CN-supplement.json'
CREDIT = FORK / 'kit/localization/credit.zh-CN.json'
COMMITTED = FORK / 'kit/runtime/fonts/cjk.json'
DEFAULT_OUT = FORK / 'fork-tools/out/cjk.json'
DEFAULT_FONT = KIT_TOOLS / '.font-cache/NotoSansSC.ttf'
URL = 'https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf'
SHA256 = 'a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da'
SIZES = (48, 44, 40, 36, 32)
BUDGET_H = 2048


def strings(value):
    """Every string inside a catalog value (str, or list/dict of them)."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def font_path(argument):
    font = Path(argument).resolve() if argument else DEFAULT_FONT
    if not font.exists():
        font.parent.mkdir(parents=True, exist_ok=True)
        print(f'downloading {URL} -> {font}')
        with urllib.request.urlopen(URL, timeout=120) as response:
            font.write_bytes(response.read())
    digest = hashlib.sha256(font.read_bytes()).hexdigest()
    if digest != SHA256:
        raise SystemExit('Noto Sans SC SHA-256 mismatch; refusing to bake a different font')
    return font


def atlas_summary(path):
    """(glyph count, [sizes], 'WxH') of an atlas file, or None when absent."""
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding='utf-8'))
    sizes = data.get('sizes') or []
    if not sizes:
        return (0, [], '-')
    first = sizes[0]
    return (len(first.get('glyphs', {})), [s.get('size') for s in sizes],
            f'{first.get("atlasW")}x{first.get("atlasH")}')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('font_pos', nargs='?', metavar='font',
                        help=f'NotoSansSC.ttf path (default: {DEFAULT_FONT})')
    parser.add_argument('--font', dest='font_opt', metavar='PATH',
                        help=f'the same, as an option (default: {DEFAULT_FONT})')
    parser.add_argument('--out', default=str(DEFAULT_OUT),
                        help=f'atlas to write (default: {DEFAULT_OUT})')
    args = parser.parse_args()

    font = font_path(args.font_opt or args.font_pos)
    spec = importlib.util.spec_from_file_location('bake_fonts', KIT_TOOLS / 'bake_fonts.py')
    baker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baker)
    baker.FONTDIR = str(font.parent)

    catalog = json.loads(LOCALES.read_text(encoding='utf-8'))
    supplement_doc = json.loads(SUPPLEMENT.read_text(encoding='utf-8'))
    supplement = {k: v for k, v in supplement_doc.items() if not k.startswith('_')}
    credit_source = CREDIT.read_text(encoding='utf-8')

    # exactly the upstream corpus, plus every non-underscore supplement value
    upstream_text = ''.join(strings(catalog))
    supplement_text = ''.join(strings(supplement))
    upstream_chars = ''.join(sorted(set(baker.TEXT + upstream_text + credit_source)))
    chars = ''.join(sorted(set(baker.TEXT + upstream_text + supplement_text + credit_source)))

    print(f'corpus: {LOCALES.name} {len(catalog)} entries, {SUPPLEMENT.name} '
          f'{len(supplement)} entries, {CREDIT.name} {len(credit_source)} chars')
    print(f'        upstream-only corpus {len(upstream_chars)} glyphs; with the fork supplement '
          f'{len(chars)} glyphs (+{len(chars) - len(upstream_chars)})')

    attempts = []
    atlas = None
    for size in SIZES:
        atlas = baker.bake(font.name, (500,), size, chars)
        attempts.append((size, atlas['atlasH']))
        if atlas['atlasH'] <= BUDGET_H:
            break
    if atlas['atlasH'] > BUDGET_H:
        raise SystemExit('Chinese atlas exceeds its reserved GPU budget; subset it before publishing')
    tried = '; '.join(f'{s} -> {h} px' + (' (fits)' if h <= BUDGET_H else ' (over budget)')
                      for s, h in attempts)
    print(f'bake:   {tried}')

    cache_key = hashlib.sha256(json.dumps(atlas, separators=(',', ':')).encode()).hexdigest()[:16]
    data = {'family': 'cjk', 'source': 'Noto Sans SC (OFL-1.1)', 'cacheKey': cache_key,
            'sizes': [atlas]}

    out = Path(args.out)
    out = (out if out.is_absolute() else Path.cwd() / out).resolve()
    publishing = out == COMMITTED.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')

    print(f'wrote {out} ({out.stat().st_size} bytes)'
          + ('   *** this IS the committed atlas: publish only when the translations are final ***'
             if publishing else ''))
    print(f'atlas:  {len(atlas["glyphs"])} glyphs, size {atlas["size"]}, '
          f'{atlas["atlasW"]} x {atlas["atlasH"]} px '
          f'(budget {BUDGET_H}, {BUDGET_H - atlas["atlasH"]} px spare)')

    was = atlas_summary(COMMITTED)
    if was:
        was_sizes = '/'.join(str(s) for s in was[1]) or '-'
        was_h = was[2].split('x')[-1]
        print(f'was:    {COMMITTED.relative_to(FORK)} {was[0]} glyphs, size {was_sizes}, {was[2]} px')
        print(f'change: {len(atlas["glyphs"]) - was[0]:+d} glyphs, size {was_sizes} -> {atlas["size"]}, '
              f'{was_h} -> {atlas["atlasH"]} px')
        if atlas['size'] < max(was[1]):
            print(f'DOWNGRADE: the atlas had to move to a smaller font size '
                  f'({max(was[1])} -> {atlas["size"]}): every app\'s Chinese text gets smaller. '
                  f'Trim the longest supplement strings or subset unused glyphs before publishing.')
        else:
            print(f'size check: no downgrade (still {atlas["size"]})')
    if not publishing and COMMITTED.exists():
        print(f'note:   {COMMITTED.relative_to(FORK)} was not modified; '
              f'publish with --out {COMMITTED.relative_to(FORK)}')


if __name__ == '__main__':
    main()
