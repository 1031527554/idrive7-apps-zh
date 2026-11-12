#!/usr/bin/env python3
"""Temp analysis: are any fork-supplement strings drawn by dtc_scanner (which uses
the separate diagnostic atlas instead of the shared cjk.json)?"""
import json, pathlib, sys

f = pathlib.Path(sys.argv[1])
sup = json.loads((f / 'fork-tools/zh-CN-supplement.json').read_text(encoding='utf-8'))
items = {k: v for k, v in sup.items() if not k.startswith('_')}
diag_path = f / 'kit/localization/fonts/diagnostic-zh-CN.json'
diag = json.loads(diag_path.read_text(encoding='utf-8'))
d = diag['sizes'][0]
covered = {int(k) for k in d['glyphs']} | set(range(0x20, 0x7f))
print(f'diagnostic atlas: {len(covered)} glyphs, {d["atlasW"]}x{d["atlasH"]} px, size {d["size"]}')

blob = '\n'.join(p.read_text(encoding='utf-8', errors='replace')
                 for p in sorted((f / 'apps/dtc_scanner').rglob('*')) if p.is_file() and p.suffix in ('.js', '.json'))
hits = {k: v for k, v in items.items() if k in blob}
print(f'supplement entries whose English key appears in apps/dtc_scanner/**: {len(hits)}')
missing = {}
for k, v in hits.items():
    m = sorted({c for c in str(v) if ord(c) > 0x7f and ord(c) not in covered})
    if m:
        missing[k] = m
print(f'of those, entries with a character missing from the diagnostic atlas: {len(missing)}')
for k, m in list(missing.items())[:20]:
    print(f'   {k[:44]:<46} "{str(hits[k])[:20]}"  missing {len(m)}: {"".join(m[:24])}')
union = set().union(*missing.values()) if missing else set()
print(f'union: {len(union)} {"" if not union else "".join(sorted(union))}')
