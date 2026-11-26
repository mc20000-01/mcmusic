#!/usr/bin/env node
// Generate every client's Lucide icons from the installed lucide-static package.
//
//   node scripts/gen-lucide.mjs           # write generated files
//   node scripts/gen-lucide.mjs --check   # fail if a generated file is stale
//
// design/tokens.json chooses which glyphs ship and which legacy names point at
// them. No glyph is hand-copied: the SVG files in ui/node_modules/lucide-static
// are the only source of path geometry. This intentionally complements (and
// never writes) gen-tokens.mjs; both use the same marker convention.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CHECK = process.argv.includes("--check");
const tokens = JSON.parse(fs.readFileSync(path.join(ROOT, "design/tokens.json"), "utf8"));
const ICONS_DIR = path.join(ROOT, "ui/node_modules/lucide-static/icons");
const DRAWABLE_DIR = path.join(ROOT, "gui/android/app/src/main/res/drawable");
const DRAWABLE_PREFIX = "ic_lucide_";
const outputs = new Map();

// Qt keeps the transport buttons solid even when the rest of the set is an
// outline. The preference toggle only fills circles/rects, so these need an
// explicit per-primitive fill. Everything else stays generated outline art.
const FILLED_ICONS = new Set(["play", "pause", "skip-forward", "skip-back"]);

// Legacy names that never became Lucide file names. tokens.json owns all the
// other aliases (home, user, music-note, more-horizontal, trash, circle_help).
const LEGACY_ICONS = {
    "x-circle": "circle-x",
    album: "disc-3",
    text: "type",
};

// Kotlin vals were consumed before this generator existed; keep the exact set
// of names that current Compose call sites reference.
const KT_LEGACY_NAMES = `
    Check ChevronLeft Compass Ellipsis EyeOff Film Link ChevronRight Clock
    Download GripVertical HardDrive Heart House Image Info Library ListMusic
    LoaderCircle Lock LogIn LogOut Mail MessageCircle Palette Pause Pencil
    Play ListPlus Plus RefreshCw Radio Repeat Search Server Settings Shuffle
    SkipBack SkipForward Trash User Wifi
`.trim().split(/\s+/);

// ── naming ───────────────────────────────────────────────────────────────────
const kebab = name => name
    .replace(/([A-Za-z])([0-9])/g, "$1-$2")
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/([A-Z])([A-Z][a-z])/g, "$1-$2")
    .replace(/[_\s]+/g, "-")
    .toLowerCase();

const pascal = name => name
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map(part => part[0].toUpperCase() + part.slice(1))
    .join("");

const iconFile = name => path.join(ICONS_DIR, `${name}.svg`);
const hasIcon = name => fs.existsSync(iconFile(name));

/** Resolve any web/Kotlin/Swift/Qt name to one canonical lucide-static icon. */
function canonical(name) {
    let key = kebab(name);
    const seen = new Set();
    while (!seen.has(key)) {
        seen.add(key);
        if (tokens.icons.includes(key)) return key;
        if (Object.prototype.hasOwnProperty.call(tokens.iconAliases, key)) {
            key = kebab(tokens.iconAliases[key]);
            continue;
        }
        if (Object.prototype.hasOwnProperty.call(LEGACY_ICONS, key)) {
            key = LEGACY_ICONS[key];
            continue;
        }
        if (hasIcon(key)) return key;
        throw new Error(`gen-lucide: no lucide-static icon for "${name}" (tried ${key})`);
    }
    throw new Error(`gen-lucide: alias cycle for "${name}"`);
}

const sorted = names => [...new Set(names)].sort((a, b) => a.localeCompare(b, "en"));
const snake = name => kebab(name).replace(/-/g, "_");

// Names already present in each target; parsed before replacement so a second
// run sees exactly the same set (generated names stay inside the markers).
const tsSource = fs.readFileSync(path.join(ROOT, "ui/src/common/lucide.tsx"), "utf8");
const tsLegacy = [...tsSource.matchAll(/^export const ([A-Za-z][A-Za-z0-9]*) = styled\(/gm)]
    .map(match => match[1]);
const swiftSource = fs.readFileSync(path.join(ROOT, "app/ios/McMusic/Lucide.swift"), "utf8");
const swiftLegacy = [...swiftSource.matchAll(/^        "([^"]+)": \[/gm)]
    .map(match => match[1]);
const pySource = fs.readFileSync(path.join(ROOT, "app/linux/mcmusic_linux/icons.py"), "utf8");
const pyLegacy = [...pySource.matchAll(/^    "([^"]+)": /gm)]
    .map(match => match[1]);

const aliasNames = Object.keys(tokens.iconAliases);
const tsNames = sorted([
    ...tokens.icons.map(pascal), ...aliasNames.map(pascal), ...tsLegacy,
]);
const ktNames = sorted([
    ...tokens.icons.map(pascal), ...aliasNames.map(pascal), ...KT_LEGACY_NAMES,
]);
const swiftNames = sorted([...tokens.icons, ...aliasNames, ...swiftLegacy]);
const pyNames = sorted([...tokens.icons, ...aliasNames, ...pyLegacy]);
const drawableNames = sorted([
    ...tsNames, ...ktNames, ...swiftNames, ...pyNames,
].map(canonical));

// ── SVG reading ──────────────────────────────────────────────────────────────
const SHAPE_RE = /<(path|circle|rect|line|polyline|polygon)\b([^>]*)>/g;
const ATTR_RE = /([A-Za-z][A-Za-z0-9-]*)\s*=\s*"([^"]*)"/g;

function primitives(icon) {
    const svg = fs.readFileSync(iconFile(icon), "utf8").replace(/<!--[\s\S]*?-->/g, "");
    const out = [];
    for (const match of svg.matchAll(SHAPE_RE)) {
        const attrs = {};
        for (const attr of match[2].matchAll(ATTR_RE)) attrs[attr[1]] = attr[2];
        out.push({ tag: match[1], attrs });
    }
    if (!out.length) throw new Error(`gen-lucide: ${icon}.svg has no drawable primitives`);
    return out;
}

/** Fixed-decimal formatting without trailing zeroes or negative zero. */
function fmt(value) {
    const n = Number(value);
    if (!Number.isFinite(n)) throw new Error(`gen-lucide: bad SVG number ${value}`);
    let out = n.toFixed(6).replace(/\.?0+$/, "");
    if (out === "-0" || out === "") out = "0";
    return out;
}

/** SVG path data -> absolute Android pathData (M/L/C/Q/A/Z only). */
function androidPath(d) {
    const tokensInPath = d.match(/[a-zA-Z]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?/g) || [];
    const out = [];
    let i = 0;
    let command = null;
    let cx = 0, cy = 0, sx = 0, sy = 0;
    let cubicControl = null, quadControl = null;

    const number = () => {
        if (i >= tokensInPath.length || /[a-zA-Z]/.test(tokensInPath[i])) {
            throw new Error(`gen-lucide: missing operand in "${d}"`);
        }
        return Number(tokensInPath[i++]);
    };
    const point = relative => {
        const x = number(), y = number();
        return [relative ? cx + x : x, relative ? cy + y : y];
    };
    // SVG allows arc flags to be glued to the next number ("0022" = 0, 0, 22).
    const flag = () => {
        const token = tokensInPath[i];
        if (token === undefined || (token[0] !== "0" && token[0] !== "1")) {
            throw new Error(`gen-lucide: bad arc flags in "${d}"`);
        }
        const value = Number(token[0]);
        if (token.length > 1) tokensInPath[i] = token.slice(1);
        else i++;
        return value;
    };
    const emit = (letter, ...values) => {
        out.push([letter, ...values.map(fmt)].join(" "));
    };

    while (i < tokensInPath.length) {
        if (/[a-zA-Z]/.test(tokensInPath[i])) command = tokensInPath[i++];
        if (!command) throw new Error(`gen-lucide: path starts without a command: "${d}"`);
        const letter = command.toLowerCase();
        const relative = command === letter;
        if (letter !== "c" && letter !== "s") cubicControl = null;
        if (letter !== "q" && letter !== "t") quadControl = null;

        switch (letter) {
            case "m": {
                const [x, y] = point(relative);
                emit("M", x, y);
                sx = cx = x;
                sy = cy = y;
                // Extra coordinate pairs after M/m are implicit L/l.
                command = relative ? "l" : "L";
                break;
            }
            case "l": {
                const [x, y] = point(relative);
                emit("L", x, y);
                cx = x; cy = y;
                break;
            }
            case "h": {
                const value = number();
                cx = relative ? cx + value : value;
                emit("L", cx, cy);
                break;
            }
            case "v": {
                const value = number();
                cy = relative ? cy + value : value;
                emit("L", cx, cy);
                break;
            }
            case "c": {
                const c1 = point(relative), c2 = point(relative), end = point(relative);
                emit("C", ...c1, ...c2, ...end);
                cubicControl = c2;
                cx = end[0]; cy = end[1];
                break;
            }
            case "s": {
                const c2 = point(relative), end = point(relative);
                const c1 = cubicControl
                    ? [2 * cx - cubicControl[0], 2 * cy - cubicControl[1]]
                    : [cx, cy];
                emit("C", ...c1, ...c2, ...end);
                cubicControl = c2;
                cx = end[0]; cy = end[1];
                break;
            }
            case "q": {
                const control = point(relative), end = point(relative);
                emit("Q", ...control, ...end);
                quadControl = control;
                cx = end[0]; cy = end[1];
                break;
            }
            case "t": {
                const end = point(relative);
                const control = quadControl
                    ? [2 * cx - quadControl[0], 2 * cy - quadControl[1]]
                    : [cx, cy];
                emit("Q", ...control, ...end);
                quadControl = control;
                cx = end[0]; cy = end[1];
                break;
            }
            case "a": {
                const rx = number(), ry = number(), rotation = number();
                const largeArc = flag(), sweep = flag();
                const end = point(relative);
                emit("A", rx, ry, rotation, largeArc, sweep, ...end);
                cx = end[0]; cy = end[1];
                break;
            }
            case "z": {
                emit("Z");
                cx = sx; cy = sy;
                command = null;
                break;
            }
            default:
                throw new Error(`gen-lucide: unsupported path command "${command}" in "${d}"`);
        }
    }
    return out.join("");
}

/** Turn a non-path SVG primitive into equivalent path data. */
function primitivePath(primitive) {
    const a = primitive.attrs;
    if (primitive.tag === "path") return a.d;
    if (primitive.tag === "circle") {
        const x = Number(a.cx), y = Number(a.cy), r = Number(a.r);
        return `M${fmt(x - r)} ${fmt(y)}a${fmt(r)} ${fmt(r)} 0 1 0 ${fmt(2 * r)} 0`
            + `a${fmt(r)} ${fmt(r)} 0 1 0 ${fmt(-2 * r)} 0Z`;
    }
    if (primitive.tag === "rect") {
        const x = Number(a.x), y = Number(a.y);
        const w = Number(a.width), h = Number(a.height), r = Number(a.rx || a.ry || 0);
        if (!r) return `M${fmt(x)} ${fmt(y)}h${fmt(w)}v${fmt(h)}h${fmt(-w)}Z`;
        return `M${fmt(x + r)} ${fmt(y)}h${fmt(w - 2 * r)}a${fmt(r)} ${fmt(r)} 0 0 1 ${fmt(r)} ${fmt(r)}`
            + `v${fmt(h - 2 * r)}a${fmt(r)} ${fmt(r)} 0 0 1 ${fmt(-r)} ${fmt(r)}`
            + `h${fmt(-w + 2 * r)}a${fmt(r)} ${fmt(r)} 0 0 1 ${fmt(-r)} ${fmt(-r)}`
            + `v${fmt(-h + 2 * r)}a${fmt(r)} ${fmt(r)} 0 0 1 ${fmt(r)} ${fmt(-r)}Z`;
    }
    if (primitive.tag === "line") {
        return `M${fmt(a.x1)} ${fmt(a.y1)}L${fmt(a.x2)} ${fmt(a.y2)}`;
    }
    const points = (a.points || "").trim().split(/[\s,]+/).map(Number);
    if (points.length < 4 || points.length % 2) {
        throw new Error("gen-lucide: malformed polyline/polygon points");
    }
    let d = `M${fmt(points[0])} ${fmt(points[1])}`;
    for (let n = 2; n < points.length; n += 2) d += `L${fmt(points[n])} ${fmt(points[n + 1])}`;
    return primitive.tag === "polygon" ? `${d}Z` : d;
}

const xmlEscape = value => value.replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");

// ── outputs ──────────────────────────────────────────────────────────────────
function put(relative, content) {
    outputs.set(path.join(ROOT, relative), content);
}

function replaceMarkers(relative, begin, end, generated) {
    const file = path.join(ROOT, relative);
    const content = fs.readFileSync(file, "utf8");
    const start = content.indexOf(begin);
    const stop = content.indexOf(end, start + begin.length);
    if (start < 0 || stop < 0) throw new Error(`${relative}: missing generation markers`);
    const body = generated.replace(/^\n+|\n+$/g, "");
    put(relative, content.slice(0, start + begin.length) + "\n" + body + "\n" + content.slice(stop));
}

// Web: named aliases keep the old import surface working while every glyph
// resolves through the shared styled() wrapper.
const tsBase = name => {
    const key = kebab(name);
    if (aliasNames.includes(key)) return pascal(canonical(key));
    return pascal(name);
};
replaceMarkers("ui/src/common/lucide.tsx", "// BEGIN GENERATED ICONS", "// END GENERATED ICONS",
    tsNames.map(name => `export const ${name} = styled("${tsBase(name)}");`).join("\n"));

// Kotlin: one vector drawable per canonical icon, plus val aliases for the old
// names. The composable below the END marker is deliberately untouched.
replaceMarkers("gui/android/app/src/main/java/dev/mcmusic/app/ui/Lucide.kt",
    "    // BEGIN GENERATED ICONS", "    // END GENERATED ICONS",
    ktNames.map(name => `    @DrawableRes val ${name} = R.drawable.ic_lucide_${snake(canonical(name))}`).join("\n"));

// iOS: SwiftUI primitives read straight from the SVG elements.
function swiftPrimitives(icon) {
    return primitives(icon).map(primitive => {
        const a = primitive.attrs;
        if (primitive.tag === "circle") {
            return `.circle(${fmt(a.cx)}, ${fmt(a.cy)}, ${fmt(a.r)})`;
        }
        if (primitive.tag === "rect") {
            return `.rect(${fmt(a.x)}, ${fmt(a.y)}, ${fmt(a.width)}, ${fmt(a.height)}, `
                + `${fmt(a.rx || a.ry || 0)})`;
        }
        const d = primitive.tag === "path" ? a.d : primitivePath(primitive);
        return `.path(${JSON.stringify(d)})`;
    });
}
replaceMarkers("app/ios/McMusic/Lucide.swift",
    "    // BEGIN GENERATED ICONS", "    // END GENERATED ICONS",
    "    static let paths: [String: [Primitive]] = [\n"
    + swiftNames.map(name => `        ${JSON.stringify(name)}: [${swiftPrimitives(canonical(name)).join(", ")}],`).join("\n")
    + "\n    ]");

// Qt: keep circle/rect elements intact so the fill preference can still turn
// only those primitives solid; paths remain outline geometry.
function pythonBody(icon) {
    const fill = FILLED_ICONS.has(icon) ? ' fill="currentColor" stroke="none"' : "";
    return primitives(icon).map(primitive => {
        const a = primitive.attrs;
        if (primitive.tag === "circle") {
            return `<circle cx="${fmt(a.cx)}" cy="${fmt(a.cy)}" r="${fmt(a.r)}"${fill}/>`;
        }
        if (primitive.tag === "rect") {
            const radius = a.rx || a.ry;
            const rx = radius ? ` rx="${fmt(radius)}"` : "";
            return `<rect x="${fmt(a.x)}" y="${fmt(a.y)}" width="${fmt(a.width)}" `
                + `height="${fmt(a.height)}"${rx}${fill}/>`;
        }
        const d = primitive.tag === "path" ? a.d : primitivePath(primitive);
        return `<path d="${d}"${fill}/>`;
    }).join("");
}
replaceMarkers("app/linux/mcmusic_linux/icons.py",
    "# BEGIN GENERATED ICONS", "# END GENERATED ICONS",
    "PATHS = {\n"
    + pyNames.map(name => `    ${JSON.stringify(name)}: ${JSON.stringify(pythonBody(canonical(name)))},`).join("\n")
    + "\n}");

// Android vector drawables: outline stroke on a 24x24 grid, transparent fill.
for (const icon of drawableNames) {
    const elements = primitives(icon)
        .map(primitive => androidPath(primitivePath(primitive)))
        .map(d => `    <path\n        android:fillColor="#00000000"\n`
            + `        android:pathData="${xmlEscape(d)}"\n`
            + `        android:strokeColor="#FF000000"\n`
            + `        android:strokeLineCap="round"\n`
            + `        android:strokeLineJoin="round"\n`
            + `        android:strokeWidth="2" />`);
    const body = [
        '<?xml version="1.0" encoding="utf-8"?>',
        `<!-- Generated by scripts/gen-lucide.mjs from lucide-static ${icon}.svg (ISC). -->`,
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"',
        '    android:width="24dp"',
        '    android:height="24dp"',
        '    android:viewportWidth="24"',
        '    android:viewportHeight="24">',
        ...elements,
        '</vector>',
        '',
    ].join("\n");
    put(`gui/android/app/src/main/res/drawable/${DRAWABLE_PREFIX}${snake(icon)}.xml`, body);
}

// ── write or verify ──────────────────────────────────────────────────────────
let stale = 0;
for (const [file, content] of outputs) {
    const current = fs.existsSync(file) ? fs.readFileSync(file, "utf8") : null;
    if (current === content) continue;
    stale++;
    if (CHECK) {
        console.error(`stale generated file: ${path.relative(ROOT, file)}`);
    } else {
        fs.mkdirSync(path.dirname(file), { recursive: true });
        fs.writeFileSync(file, content);
        console.log(`generated ${path.relative(ROOT, file)}`);
    }
}

// A renamed/removed icon must not leave an obsolete drawable behind.
for (const name of fs.readdirSync(DRAWABLE_DIR)) {
    if (!name.startsWith(DRAWABLE_PREFIX) || !name.endsWith(".xml")) continue;
    const file = path.join(DRAWABLE_DIR, name);
    if (outputs.has(file)) continue;
    stale++;
    if (CHECK) {
        console.error(`stale generated file: ${path.relative(ROOT, file)} (no longer needed)`);
    } else {
        fs.unlinkSync(file);
        console.log(`removed ${path.relative(ROOT, file)}`);
    }
}

if (CHECK && stale) {
    console.error(`${stale} generated file(s) are stale; run node scripts/gen-lucide.mjs`);
    process.exit(1);
}
if (!CHECK) console.log(`gen-lucide: ${outputs.size} files up to date`);
