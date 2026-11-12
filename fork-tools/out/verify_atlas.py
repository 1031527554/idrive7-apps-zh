#!/usr/bin/env python3
"""Temporary structural check of fork-tools/out/cjk.json vs the committed atlas."""
import base64, json, pathlib, sys, zlib

f = pathlib.Path(sys.argv[1])
old = json.loads((f / 'kit/runtime/fonts/cjk.json').read_text(encoding='utf-8'))
new = json.loads((f / 'fork-tools/out/cjk.json').read_text(encoding='utf-8'))
print('top-level keys equal      :', sorted(old) == sorted(new), sorted(new))
print('family/source/cacheKey    :', new['family'], '|', new['source'], '|', new['cacheKey'])
for tag, d in (('old', old), ('new', new)):
    s = d['sizes'][0]
    print(f'{tag}: sizes={len(d["sizes"])} size={s["size"]} ascent={s["ascent"]} descent={s["descent"]} '
          f'atlas={s["atlasW"]}x{s["atlasH"]} glyphs={len(s["glyphs"])} '
          f'alpha_unwrapped={len(zlib.decompress(base64.b64decode(s["alpha"])))}')
for tag, d in (('old', old), ('new', new)):
    s = d['sizes'][0]
    print(f'{tag}: raw alpha == W*H    :', len(zlib.decompress(base64.b64decode(s['alpha']))) == s['atlasW'] * s['atlasH'],
          '| same keys as first size:', sorted(s) == sorted(old['sizes'][0]))
    print(f'{tag}: ASCII 0x20-0x7e all present:', all(str(c) in s['glyphs'] for c in range(0x20, 0x7f)))
    print(f'{tag}: glyph tuple length     :', {len(v) for v in list(s['glyphs'].values())[:50]})
need = '「」临仿优体千去寸导居年廓弧彩拍晰暗案欢泡洁着矢签箭翼联胶荧落街裂观赛越迎遥青'
old_keys = {int(k) for k in old['sizes'][0]['glyphs']}
new_keys = {int(k) for k in new['sizes'][0]['glyphs']}
print('the 39 needed chars       :', len(need), 'chars; missing from committed:', len([c for c in need if ord(c) not in old_keys]),
      '; missing from new:', len([c for c in need if ord(c) not in new_keys]))
print('sample glyph (临)          :', new['sizes'][0]['glyphs'][str(ord('临'))])
print('new adds, never removes   :', old_keys <= new_keys, f'(old {len(old_keys)} -> new {len(new_keys)})')
print('out/cjk.json bytes        :', (f / 'fork-tools/out/cjk.json').stat().st_size,
      '| committed:', (f / 'kit/runtime/fonts/cjk.json').stat().st_size)
