'use strict';
// Ambient config's pages, drawn for real: boots the built app (dist/) on the head-unit stub, opens
// every page and drives its tab and tap handlers. A scope or API error inside a drawing function
// only shows when that page is drawn - the logic tests never render, so a merge that drops a
// declaration passes them all. (2026-11-16: a dropped `let picked = ''` made drawAnimations throw
// "picked is not defined", which froze the whole app the moment a tab was pressed.)
//
//   python kit/tools/build.py --language zh-CN --preview-only ambient_config
//   node kit/tools/test_ambient_pages.js [stage]
const path = require('path');
const fs = require('fs');
const os = require('os');
const { headUnit } = require(path.join(__dirname, 'hu-stub.js'));

const STAGE = path.resolve(process.argv[2] || path.join(__dirname, '..', '..', 'dist', 'ambient_config'));
let fails = 0, checks = 0;
const ok = (c, msg) => { checks++; if (!c) { fails++; console.log('FAIL ' + msg); } };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

if (!fs.existsSync(path.join(STAGE, 'source', 'javascript', 'app.js'))) {
    console.log('no built app at ' + STAGE);
    console.log('build it first: python kit/tools/build.py --language zh-CN --preview-only ambient_config');
    process.exit(2);
}

const errors = [], images = [];
const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ambient-pages-'));
const hu = headUnit(STAGE, {
    dataDir, fresh: true, image: (name) => { images.push(name); },
    log: { info: () => {}, warn: (m) => errors.push(String(m)), error: (m) => errors.push(String(m)), debug: () => {} },
});
process.on('unhandledRejection', (e) => errors.push('unhandled: ' + (e && e.message || e)));
process.on('uncaughtException', (e) => errors.push('uncaught: ' + (e && e.message || e)));

const tabs = [], taps = [], touches = [];
const ctx = hu.ctx, onTab0 = ctx.onTab, onTap0 = ctx.onTap, onTouch0 = ctx.onTouch;
ctx.onTab = (fn) => { tabs.push(fn); return onTab0.call(ctx, fn); };
ctx.onTap = (fn) => { taps.push(fn); return onTap0.call(ctx, fn); };
// upstream 11-20 draws the ring and the dial from phased touches where the kit offers them, and only
// falls back to a plain tap otherwise: capture both and drive whichever the app took
ctx.onTouch = (fn) => { touches.push(fn); return onTouch0 ? onTouch0.call(ctx, fn) : undefined; };

const draw = (what, fn) => {
    try { fn(); checks++; } catch (e) { checks++; fails++; console.log('FAIL ' + what + ': ' + (e && e.message || e)); }
};

(async () => {
    try { hu.start(); } catch (e) { ok(false, 'the app loads: ' + e.message); }
    await sleep(1500);                                 // the app's own async start()
    // the app takes the tabs at once (a temporary handler while its background comes up) and registers
    // the real one when it is ready: the kit's onTab replaces, so the last one is the live handler
    ok(tabs.length >= 1, 'the app registered a tab handler');
    ok(taps.length + touches.length >= 1, 'the app registered a tap or touch handler');
    ok(images.length >= 2, 'a frame before the background (the loading screen) and the pages after');
    const tabFn = tabs[tabs.length - 1];
    const tapFn = taps.length ? taps[taps.length - 1] : null;
    const touchFn = touches.length ? touches[touches.length - 1] : null;
    const press = (x, y) => {
        if (touchFn) { touchFn(1, x, y); touchFn(3, x, y); }     // down then up, as the kit sends them
        else if (tapFn) tapFn(x, y);
    };

    for (let page = 0; page <= 4; page++) {
        draw('page ' + page + ' draws', () => { tabFn(page); hu.loopFn(); });
        await sleep(80);
    }
    for (const [x, y, what] of [[800, 260, 'the colour ring'], [1300, 200, 'a swatch'], [200, 400, 'the dial'],
                                [300, 100, 'the animation buttons'], [1000, 300, 'the page']]) {
        draw('tap ' + what, () => { press(x, y); hu.loopFn(); });
        await sleep(60);
    }
    await sleep(400);                                  // let the async renders finish
    const bad = errors.filter((e) => /is not defined|is not a function|Cannot read/.test(e));
    ok(!bad.length, 'no scope or API error while drawing' + (bad.length ? ': ' + bad.slice(0, 3).join(' | ') : ''));
    console.log('ambient pages: ' + checks + ' checks, ' + fails + ' failed');
    process.exit(fails ? 1 : 0);
})();
