#!/usr/bin/env python3
"""Merge fork-tools/zh-CN-supplement.json into kit/runtime/locales/zh-CN.json.

The build reads the catalog, so the translations must BE in it: a fork-only file elsewhere in the
repo is not something the unit's build can be relied on to have (2026-11-19: the app arrived with
upstream's catalog only - the tabs showed COLOUR / ANIMATIONS / 行驶 MODES, i.e. 'Driving' from the
catalog was translated while every key that only the supplement carries was not).

  fork-tools/zh-CN-upstream.json  upstream's catalog, verbatim (the sync refreshes it)
  fork-tools/zh-CN-supplement.json  this fork's entries (upstream always wins)
  kit/runtime/locales/zh-CN.json    the merged file this script writes, in upstream's own style

    python fork-tools/merge_supplement.py [<fork-dir>]
"""
import json
import pathlib
import sys

fork = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
up_path = fork / 'fork-tools/zh-CN-upstream.json'
sup_path = fork / 'fork-tools/zh-CN-supplement.json'
out_path = fork / 'kit/runtime/locales/zh-CN.json'

upstream = json.loads(up_path.read_text(encoding='utf-8'))
supplement = json.loads(sup_path.read_text(encoding='utf-8'))
entries = {k: v for k, v in supplement.items() if not k.startswith('_')}

lines = up_path.read_text(encoding='utf-8').rstrip('\n').split('\n')
close = len(lines) - 1
while not lines[close].strip():
    close -= 1
if lines[close].strip() not in ('}', '},'):
    raise SystemExit(f'{up_path}: the last line is not a closing brace: {lines[close]!r}')
body = [l for l in lines[:close]]
while body and not body[-1].strip():
    body.pop()
if not body[-1].rstrip().endswith(','):
    body[-1] = body[-1].rstrip() + ','

added = [k for k in entries if k not in upstream]
for k in added:
    body.append('    ' + json.dumps(k, ensure_ascii=False) + ': ' + json.dumps(entries[k], ensure_ascii=False) + ',')
body[-1] = body[-1].rstrip(',')                       # no trailing comma before the brace
text = '\n'.join(body + [lines[close]]) + '\n'

merged = json.loads(text)                             # must parse
for k, v in entries.items():
    if merged.get(k) != v:
        raise SystemExit(f'merge lost {k!r}: {merged.get(k)!r} != {v!r}')
for k, v in upstream.items():
    if merged.get(k) != v:
        raise SystemExit(f'merge changed upstream {k!r}: {merged.get(k)!r} != {v!r}')
out_path.write_text(text, encoding='utf-8', newline='\n')
print(f'  upstream {len(upstream)} + fork {len(added)} = {len(merged)} entries -> {out_path.relative_to(fork)}')
print(f'  (upstream entries unchanged, {len(entries) - len(added)} supplement entries were already there)')
