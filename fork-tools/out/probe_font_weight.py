#!/usr/bin/env python3
"""Temp probe: is the committed atlas from the wght=500 instance of the pinned
variable font (what kit/tools/bake_cjk.py asks for) or from the default one?"""
import importlib.util, json, pathlib, sys

f = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(f / 'fork-tools'))
bake_cjk_fork = importlib.util.spec_from_file_location('bake_cjk_fork', f / 'fork-tools/bake_cjk_fork.py')
mod = importlib.util.module_from_spec(bake_cjk_fork)          # constants + strings() only
bake_cjk_fork.loader.exec_module(mod)

spec = importlib.util.spec_from_file_location('bake_fonts', f / 'kit/tools/bake_fonts.py')
baker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baker)
font = f / 'kit/tools/.font-cache/NotoSansSC.ttf'
baker.FONTDIR = str(font.parent)

catalog = json.loads((f / 'kit/runtime/locales/zh-CN.json').read_text(encoding='utf-8'))
sup = {k: v for k, v in json.loads((f / 'fork-tools/zh-CN-supplement.json').read_text(encoding='utf-8')).items()
       if not k.startswith('_')}
credit = (f / 'kit/localization/credit.zh-CN.json').read_text(encoding='utf-8')
chars = ''.join(sorted(set(baker.TEXT + ''.join(mod.strings(catalog)) + ''.join(mod.strings(sup)) + credit)))

old = json.loads((f / 'kit/runtime/fonts/cjk.json').read_text(encoding='utf-8'))['sizes'][0]['glyphs']
for var in ((500,), None):
    atlas = baker.bake(font.name, var, 44, chars)
    print(f'var={var}: glyphs={len(atlas["glyphs"])} H={atlas["atlasH"]}')
    for ch in 'A0?中位温':
        g = atlas['glyphs'].get(ord(ch))
        o = old.get(str(ord(ch)))
        print(f'   {ch!r} new {g}   committed {o}')
