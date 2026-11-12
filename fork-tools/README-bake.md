# Baking the Chinese atlas in this fork

`kit/runtime/fonts/cjk.json` is the pre-baked glyph atlas the kit draws canvas text
with. On the head unit there is no font rasteriser, so **every character must be in
that atlas**; `kit/runtime/fonts.js` falls back to `glyphs[63]` when a character is
missing, which draws as **`?`**.

Upstream's `kit/tools/bake_cjk.py` builds its character set from
`kit/runtime/locales/zh-CN.json` only. This fork's extra Chinese lives in
`fork-tools/zh-CN-supplement.json` (a fork-only file), so those strings had no
glyphs and showed up as `?` in the car. `fork-tools/bake_cjk_fork.py` is the same
bake (same Noto Sans SC build + SHA-256 check, same 48/44/40/36/32 fallback, same
<=2048 px budget, same JSON structure) with the supplement's values added to the
corpus. `kit/tools/bake_cjk.py` itself is intentionally left untouched, so the
fork keeps syncing cleanly with upstream.

## Commands (run from the fork root)

```bash
# bake into fork-tools/out/cjk.json (the committed atlas is NOT touched)
python fork-tools/bake_cjk_fork.py

# is the committed atlas complete?
python fork-tools/check_glyphs.py                 # exit 1 while characters are missing

# bake and check the result in one go
python fork-tools/bake_cjk_fork.py --out fork-tools/out/cjk.json
python fork-tools/check_glyphs.py --atlas fork-tools/out/cjk.json   # exit 0 = nothing missing

# publish (only once the translations are final - this overwrites the committed atlas)
python fork-tools/bake_cjk_fork.py --out kit/runtime/fonts/cjk.json
```

`--font <path>` (or a positional `.ttf` path) uses an existing font file instead of
downloading it. The default cache is `kit/tools/.font-cache/NotoSansSC.ttf`, shared
with `kit/tools/bake_cjk.py` and gitignored.

## When to re-run

* after a sync brought a new `kit/runtime/locales/zh-CN.json` (`fork-tools/sync_upstream.py`),
* after **any** edit to `fork-tools/zh-CN-supplement.json` (new or changed Chinese),
* before publishing a release whose Chinese is expected to be complete.

`check_glyphs.py` returning 0 is the gate: while it returns 1, some on-screen Chinese
draws as `?`.

## Budget: the atlas may fall back to a smaller font size

The atlas is packed 1024 px wide and must stay **<= 2048 px high** (the renderer packs
1024-wide atlases into two 4096-high columns). `bake_cjk_fork.py` therefore tries
48 px, then 44, 40, 36, 32 px, and stops at the first size that fits. Whatever size
wins applies to **all** apps' Chinese text:

* normal result today: 48 px does not fit, **44 px** is used;
* if the corpus grows enough that 44 px no longer fits, the bake silently drops to
  40 px (then 36) and **every app's Chinese gets visibly smaller**;
* the script prints exactly which sizes were tried and their heights, plus
  `DOWNGRADE:` when the new size is smaller than the committed atlas's size.

Before accepting a downgrade, trim the longest supplement strings or drop characters
that are not drawn on screen; a lower font size is a whole-product change, not a
local one. Above 32 px the script refuses to publish rather than exceed the budget.

## Notes

* `fork-tools/out/` holds generated atlases and is not committed; only
  `kit/runtime/fonts/cjk.json` is the published atlas.
* The separate Fault Scanner atlas (`kit/localization/fonts/diagnostic-zh-CN.json`)
  is still baked by upstream's `python kit/tools/bake_cjk.py --diagnostic`. Its
  32 px atlas currently covers the few supplement strings that app draws; if you
  add strings for `dtc_scanner`, re-bake that one too (and it has no fork version
  yet).
* **A fresh bake regenerates every glyph, not only the new ones.** The committed
  `cjk.json` does not reproduce byte-for-byte on this machine with the currently
  pinned font (for the upstream-only corpus a fresh bake picks 48 px / 2046 px,
  while the committed file is 44 px / 1732 px; per-glyph advances differ by
  <0.4 px). Publishing therefore changes the atlas globally - check one app in the
  car after publishing. The font *size* stays 44 px as long as the corpus fits the
  budget, so text does not get smaller.
* Pillow is needed to bake (this machine has it); normal app builds do not.
