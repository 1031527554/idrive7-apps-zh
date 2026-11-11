'use strict';
/**
 * scenes.js - what each light shows at a moment. Pure: a scene and a light in, { rgb, bright } out.
 *
 * A scene: { kind, upper: { rgb, bright }, lower: { rgb, bright }, speed }
 *   solid      upper and lower lights each their own colour (the same colour for both: one colour)
 *   breathing  the colour slowly brighter and dimmer
 *   rainbow    the whole cabin through every colour
 *   fade       slowly from the upper colour to the lower one and back
 *   wave       a band of colour moving from the dash to the rear
 *   welcome    a sweep of the colour from the dash to the rear, once (then solid)
 *   pulse      red for 1.5 s, then the colour (Sport)
 *   cycle      the whole cabin walks through a palette, on and on (scene.palette: which one)
 *   beat       a beat at scene.bpm: quickly on, then down to the next one
 *   drive      the car drives it: rev, speed or g (scene.source), from scene.car's live values
 * speed: 1 slow, 2 normal, 3 fast.
 */
const KINDS = ['solid', 'breathing', 'rainbow', 'fade', 'wave', 'cycle', 'beat', 'drive'];
const ONCE = { welcome: 2600, pulse: 2000 };
const NAMES = { solid: 'Solid', breathing: 'Breathing', rainbow: 'Rainbow', fade: 'Smooth fade', wave: 'Colour wave', welcome: 'Welcome sweep',
    pulse: 'Sport pulse', cycle: 'Colour cycle', beat: 'Beat', drive: 'Follow driving' };
const PERIOD = { 1: 1.6, 2: 1, 3: 0.55 };      // x the base time of each animation

/* The palettes the colour cycle walks through: hue degrees, wrap-around allowed (warm goes
 * 300 -> 420, so red comes up between the two ends rather than jumping back). */
const PALETTES = { full: [0, 360], cool: [160, 300], warm: [300, 420], m: [240, 380] };
const PALETTE_NAMES = { full: 'Every colour', cool: 'Cool', warm: 'Warm', m: 'M colours' };
const CYCLE_MS = 24000;         // one turn through the palette, at speed 2
const DEFAULT_BPM = 100;        // the beat's beats per minute when none is set
const BEAT_FLOOR = 0.15;        // how dim a beat's light goes between two beats
const REV = { idle: 800, max: 6500 };   // revs that read as idle and as flat out
const FAST = 160;               // km/h that reads as flat out
const PULL = 0.6;               // g that reads as all of it
const clamp01 = (x) => Math.max(0, Math.min(1, x));
const num = (x) => (typeof x === 'number' && isFinite(x) ? x : 0);

function hsv(h, s, v) {
    const f = (n) => { const k = (n + h / 60) % 6; return v - v * s * Math.max(0, Math.min(k, 4 - k, 1)); };
    return [Math.round(f(5) * 255), Math.round(f(3) * 255), Math.round(f(1) * 255)];
}
function hueOf(rgb) {
    const [r, g, b] = rgb.map((x) => x / 255), mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
    if (!d) return 0;
    const h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
    return (h * 60 + 360) % 360;
}
/** A hue picked on the ring: within 5 degrees of red, yellow, green, cyan, blue or magenta, exactly that one (a
 * finger is not that precise, and a little green in a red shows orange on the car's LEDs); others as they are. */
function snapHue(h) {
    const s = (Math.round(h / 60) * 60) % 360;
    return Math.abs(((h - s + 540) % 360) - 180) <= 5 ? s : (h + 360) % 360;
}
/** The < / > buttons: the next multiple of 15 degrees (d +-15), so red, green and blue come up exactly. */
const stepHue = (h, d) => ((Math.round((h + d) / 15) * 15) % 360 + 360) % 360;
const mix = (a, b, f) => a.map((x, i) => Math.round(x + (b[i] - x) * f));
const hex = (rgb) => '#' + rgb.map((x) => ('0' + Math.max(0, Math.min(255, x | 0)).toString(16)).slice(-2)).join('');

/** The time a once-only scene lasts (ms), 0 for one that runs on. */
const lasts = (scene) => ONCE[scene && scene.kind] || 0;
/** Whether a scene moves (the lights are written over and over). */
const moves = (scene) => !!scene && scene.kind !== 'solid';

/** What a light shows: the scene, the light ({ part, y }), t ms since the scene started. */
function lightAt(scene, light, t) {
    const own = scene[light.part === 'upper' ? 'upper' : 'lower'] || scene.upper;
    const base = scene.upper, k = PERIOD[scene.speed] || 1;
    switch (scene.kind) {
    case 'breathing': {
        const f = 0.5 - 0.5 * Math.cos(2 * Math.PI * t / (4000 * k));
        return { rgb: own.rgb, bright: Math.round(own.bright * (0.12 + 0.88 * f)) };
    }
    case 'rainbow':
        return { rgb: hsv((t / (12000 * k) * 360) % 360, 1, 1), bright: base.bright };
    case 'fade': {
        const f = 0.5 - 0.5 * Math.cos(2 * Math.PI * t / (8000 * k));
        return { rgb: mix(scene.upper.rgb, scene.lower.rgb, f), bright: Math.round(scene.upper.bright + (scene.lower.bright - scene.upper.bright) * f) };
    }
    case 'wave': {
        // the base colour's hue, a band 120 degrees wide travelling to the rear
        const h = hueOf(base.rgb) + 60 * Math.sin(2 * Math.PI * (t / (5000 * k) - light.y));
        return { rgb: hsv((h + 360) % 360, 1, 1), bright: base.bright };
    }
    case 'welcome': {
        // the lights come on from the dash to the rear
        const front = t / ONCE.welcome * 1.4 - 0.2, f = Math.max(0, Math.min(1, (front - light.y) / 0.2));
        return { rgb: own.rgb, bright: Math.round(own.bright * f) };
    }
    case 'pulse': {
        // one long red: the lights are written one after the other, quick flashes would never reach them all
        return t < 1500 ? { rgb: [255, 0, 0], bright: 100 } : own;
    }
    case 'cycle': {
        // the palette walked once every CYCLE_MS x speed, the whole cabin the same hue at a time and
        // each part its own brightness
        const p = PALETTES[scene.palette] || PALETTES.full, f = (t / (CYCLE_MS * k)) % 1;
        return { rgb: hsv(p[0] + (p[1] - p[0]) * f, 1, 1), bright: own.bright };
    }
    case 'beat': {
        // a beat: on at once, then down until the next one. Quick flashes would never reach every
        // light (one write each ~200 ms through the gateway), so the beat is the brightness itself
        const period = 60000 / Math.max(30, Math.min(240, scene.bpm || DEFAULT_BPM)), x = (t % period) / period;
        return { rgb: own.rgb, bright: Math.round(own.bright * (BEAT_FLOOR + (1 - BEAT_FLOOR) * Math.pow(1 - x, 2.2))) };
    }
    case 'drive': {
        const c = scene.car || {}, src = scene.source || 'rev';
        const rev = clamp01((num(c.rpm) - REV.idle) / (REV.max - REV.idle));
        const fast = clamp01(num(c.speed) / FAST);
        const pull = clamp01((Math.abs(num(c.gLat)) + Math.abs(num(c.gLong))) / PULL);
        // g only brightens the look that is set; rev and speed walk blue (idle) to red (flat out)
        if (src === 'g') return { rgb: own.rgb, bright: Math.round(own.bright * (0.35 + 0.65 * pull)) };
        const f = src === 'speed' ? fast : rev;
        return { rgb: hsv(210 * (1 - f), 1, 1), bright: Math.round(own.bright * (0.55 + 0.45 * f)) };
    }
    default:
        return own;
    }
}

module.exports = { KINDS, NAMES, lightAt, lasts, moves, hsv, hueOf, snapHue, stepHue, hex, mix,
    PALETTES, PALETTE_NAMES, CYCLE_MS, DEFAULT_BPM, BEAT_FLOOR };
