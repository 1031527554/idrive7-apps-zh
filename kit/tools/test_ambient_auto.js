'use strict';
// Ambient config's automatic animations (apps/ambient_config/scenes.js): the colour cycle through a
// palette, the beat, and Follow driving - rev, speed or g - including with no car data at all.
//   node kit/tools/test_ambient_auto.js
const path = require('path');
const S = require(path.join(__dirname, '..', '..', 'apps', 'ambient_config', 'scenes'));

let fails = 0, checks = 0;
const ok = (c, msg) => { checks++; if (!c) { fails++; console.log('FAIL ' + msg); } };

const upper = { rgb: [120, 60, 255], bright: 80 }, lower = { rgb: [120, 60, 255], bright: 60 };
const scene = (o) => Object.assign({ kind: 'solid', upper: upper, lower: lower, speed: 2 }, o);
const at = (sc, t, part, y) => S.lightAt(sc, { part: part || 'upper', y: y == null ? 0.5 : y }, t);
const hue = (c) => S.hueOf(c.rgb);
const near = (a, b, d) => Math.abs(((a - b + 540) % 360) - 180) <= (d || 2);
const between = (h, from, to) => (to <= 360 ? h >= from - 2 && h <= to + 2 : h >= from - 2 || h <= to - 360 + 2);

ok(S.KINDS.indexOf('cycle') >= 0 && S.KINDS.indexOf('beat') >= 0 && S.KINDS.indexOf('drive') >= 0, 'the three automatic animations are kinds');
ok(S.moves(scene({ kind: 'cycle' })) && S.moves(scene({ kind: 'beat' })) && S.moves(scene({ kind: 'drive' })), 'all three keep the lights being written');
ok(S.lasts(scene({ kind: 'cycle' })) === 0 && S.lasts(scene({ kind: 'beat' })) === 0 && S.lasts(scene({ kind: 'drive' })) === 0, 'none of them is a once-only scene');

/* ---- Colour cycle ---- */
const cyc = scene({ kind: 'cycle' });
const h0 = hue(at(cyc, 0)), hMid = hue(at(cyc, S.CYCLE_MS / 4));
ok(!near(h0, hMid, 5), 'the cycle walks the hue (' + h0.toFixed(0) + ' -> ' + hMid.toFixed(0) + ')');
ok(near(hue(at(cyc, S.CYCLE_MS)), h0, 3), 'one turn takes CYCLE_MS at speed 2');
ok(near(hue(at(scene({ kind: 'cycle', speed: 1 }), S.CYCLE_MS)), h0, 3) === false, 'speed 1 takes longer than CYCLE_MS');
ok(at(cyc, 0, 'lower').bright === lower.bright, 'the cycle keeps each part its own brightness');
['cool', 'warm', 'm'].forEach((p) => {
    const band = S.PALETTES[p];
    let inBand = true;
    for (let i = 0; i < 24; i++) {
        const h = hue(at(scene({ kind: 'cycle', palette: p }), S.CYCLE_MS * i / 24));
        if (!between(h, band[0], band[1])) inBand = false;
    }
    ok(inBand, 'the ' + p + ' palette stays inside ' + band[0] + '-' + band[1]);
});
ok(S.PALETTES.warm[1] > 360, 'the warm palette wraps around (red at both ends)');

/* ---- Beat ---- */
const beat = scene({ kind: 'beat', bpm: 60 });
const b0 = at(beat, 0).bright, bHalf = at(beat, 500).bright, bLate = at(beat, 950).bright;
ok(b0 > bHalf && bHalf > bLate, 'the beat goes down between two beats (' + b0 + ' > ' + bHalf + ' > ' + bLate + ')');
ok(at(beat, 1000).bright === b0, 'the next beat comes at 60000 / bpm ms');
ok(bLate >= Math.round(upper.bright * S.BEAT_FLOOR) - 1, 'it never goes below the floor');
ok(at(scene({ kind: 'beat', bpm: 180 }), 100).bright < at(scene({ kind: 'beat', bpm: 60 }), 100).bright, 'more beats a minute is dimmer again sooner');
ok(at(scene({ kind: 'beat' }), 0).bright === upper.bright, 'no beats a minute set: the default is used');
ok(at(beat, 0).rgb.join() === upper.rgb.join(), 'the beat keeps the colour that is set');

/* ---- Follow driving ---- */
const rev = (rpm) => at(scene({ kind: 'drive', source: 'rev', car: { rpm: rpm } }), 0);
const spd = (kmh) => at(scene({ kind: 'drive', source: 'speed', car: { speed: kmh } }), 0);
ok(near(hue(rev(800)), 210, 3) && near(hue(rev(6500)), 0, 3), 'idle is blue, flat out is red');
ok(between(hue(rev(3650)), 80, 130), 'half the revs is halfway round');
ok(rev(6500).bright > rev(800).bright, 'more revs is brighter');
ok(near(hue(spd(0)), 210, 3) && near(hue(spd(160)), 0, 3), 'standing still is blue, 160 km/h is red');
const glow = (g) => at(scene({ kind: 'drive', source: 'g', car: { gLat: g } }), 0);
ok(glow(0.6).bright === upper.bright && glow(0).bright === Math.round(upper.bright * 0.35), 'g takes the brightness from a third to all of it');
ok(glow(0.6).rgb.join() === upper.rgb.join(), 'g leaves the colour that is set');
ok(at(scene({ kind: 'drive', source: 'g', car: { gLong: -1, gLat: 1 } }), 0).bright === upper.bright, 'both directions count, and the sign does not');
ok(rev(0).bright > 0 && near(hue(rev(0)), 210, 3), 'a car that sends nothing: the idle look, not a crash');
ok(near(hue(at(scene({ kind: 'drive' }), 0)), 210, 3), 'no source set: the revs');
ok(at(scene({ kind: 'drive', car: { rpm: 'x', speed: null } }), 0).bright > 0, 'values that are not numbers are taken as none');

console.log('ambient auto: ' + checks + ' checks, ' + fails + ' failed');
process.exit(fails ? 1 : 0);
