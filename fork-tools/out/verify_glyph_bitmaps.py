#!/usr/bin/env python3
"""Temp check: for characters in both atlases, is the rendered bitmap identical?
Positions differ (the shelf packing moves) but the pixels and metrics must not."""
import base64, json, pathlib, sys, zlib
import numpy as np

f = pathlib.Path(sys.argv[1])
old = json.loads((f / 'kit/runtime/fonts/cjk.json').read_text(encoding='utf-8'))['sizes'][0]
new = json.loads((f / 'fork-tools/out/cjk.json').read_text(encoding='utf-8'))['sizes'][0]
ao = np.frombuffer(zlib.decompress(base64.b64decode(old['alpha'])), dtype=np.uint8).reshape(old['atlasH'], old['atlasW'])
an = np.frombuffer(zlib.decompress(base64.b64decode(new['alpha'])), dtype=np.uint8).reshape(new['atlasH'], new['atlasW'])
print(f'metrics: ascent/descent old {old["ascent"]}/{old["descent"]} new {new["ascent"]}/{new["descent"]}')
bad = 0
sample = '中转向挡位0A?红油温度'
for ch in sample:
    g_o, g_n = old['glyphs'].get(str(ord(ch))), new['glyphs'].get(str(ord(ch)))
    if not g_o or not g_n:
        print(f'  {ch!r}: present old={bool(g_o)} new={bool(g_n)}')
        continue
    co = ao[g_o[1]:g_o[1] + g_o[3], g_o[0]:g_o[0] + g_o[2]]
    cn = an[g_n[1]:g_n[1] + g_n[3], g_n[0]:g_n[0] + g_n[2]]
    same_px, same_metrics = co.shape == cn.shape and np.array_equal(co, cn), g_o[4:] == g_n[4:]
    if not (same_px and same_metrics):
        bad += 1
    print(f'  {ch!r}: bitmap identical={same_px} (shape {co.shape} vs {cn.shape}), metrics identical={same_metrics} {g_o[4:]} vs {g_n[4:]}')
print(f'sample of {len(sample)} shared glyphs: {bad} differ')
