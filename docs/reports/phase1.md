# mcmusic 4.2.0 — Phase 1 report

Branch: `design-4.2.0`. Parent commit: `b5ae6a2` (Phase 0). This phase is the web client only; no version bump or release action is included.

## What changed

- Rebuilt the web shell as flat Material 3 tonal containers: 64px top bar, 264px/64px sidebar, pill navigation, 28px cards, 36px hero and sheet corners, a 4px spacing rhythm, Lexend type-scale variables, and a 48px minimum touch target on icon buttons, transport controls, rows, search fields and lyric controls.
- Added a cover-derived HCT colour path. `dynamic-colour.ts` loads the same same-origin cover the player already displays, samples a dominant colour on a 24px canvas, and feeds `setCoverSeed()` into the existing `rolesFromSeed()`/`paletteVars()` helpers. Missing art, disabled covers, failed extraction and placeholder sentinels restore the selected family palette. `currentPaletteValue()` and palette subscribers now see the effective cover-seeded palette, so canvas visualisers follow the same colour as CSS.
- Replaced the text-initial SVG fallback with a real flat tonal tile. `CoverArt.tsx` renders `placeholder:` results as a DOM surface with a deterministic Lucide glyph chosen from circle, squircle, cookie, flower and pentagon; real artwork is still rendered as-is. All cover call sites (library, search, profile, playlists and player) now use it.
- Added the five placeholder glyphs to `design/tokens.json` and regenerated the web/Kotlin/Swift/Qt icon maps and four Android vector drawables. No glyph geometry was hand-copied and generated marker blocks were not hand-edited.
- Added playful web motion from the committed tokens: medium-spring hover/press easing, 0.96 press scale, play/pause pill-to-squircle morph with icon rotation, and a wavy seek line only while playing. A local `mcmusic:playfulMotion` switch defaults on; `prefers-reduced-motion` and the switch both disable the wave, springs and slide/bob animations.
- Reworked Home around real data: the first `/api/home` shelf is a flat tonal hero, remaining shelves are playable chips and track lists, and the album grid keeps real filtering/sorting/paging. No Mix, Radio destination or global Chart is invented; `Made for you` is never hard-coded.
- Softened Search, Likes, Artists, Playlists, Lyrics and Up next with tonal surfaces, pill controls and readable two-line cards; Sing along is shown only when the lyrics are genuinely LRC time-synced, and plain lyrics stay a read-only sheet.
- Fixed `scripts/strip-font-cdn.mjs` to catch Vite’s minified `@import"..."` form. The built CSS now contains no Google Fonts CDN import; local Lexend/Inter/JetBrains Mono remain the only font sources and no tracker or extra network call was added.
- Kept all feature-truth boundaries intact: no Dolby Atmos/Spatial Audio/Spatial Mix labels, no fake lossless or explicit badges, no curated radio backend, and no invented recommendation copy.

## What was run

- `node scripts/gen-tokens.mjs && node scripts/gen-lucide.mjs` — pass; generated outputs refreshed.
- `node scripts/gen-tokens.mjs --check && node scripts/gen-lucide.mjs --check` — pass; committed generated files are current.
- `./scripts/build_ui.sh` — pass; `tsc --noEmit -p tsconfig.app.json`, Vite build and CDN stripping succeeded (`web/ui/` is generated and gitignored).
- Post-build CDN scan over `web/ui/**/*.css` and `web/ui/**/*.html` — no `fonts.googleapis.com` or `fonts.gstatic.com` references.
- `python -m pytest tests/test_no_gradients.py tests/test_contrast.py tests/test_generated_fresh.py -q` — 3 passed using `.venv/bin/python`.
- Full non-Qt suite with the CI Qt ignores — 95 passed, 1 skipped, 2 subtests passed.
- Qt offscreen suite (`QT_QPA_PLATFORM=offscreen`, audio stub) — 35 passed.
- `node --check web/sw.js`, `node --check web/embed/widgets.js`, `python -m py_compile app/linux/mcmusic_linux/theme.py app/linux/mcmusic_linux/icons.py` — pass.
- `./scripts/check-versions.sh`, `./tests/test_check_versions.sh`, `./tests/test_publish_release.sh` — pass; all version carriers still agree at 4.1.0.
- `git diff --check` — pass.
- CI is triggered by pushing this separate phase commit to `design-4.2.0`; no CI result is claimed in this pre-push report.

## What was not done and why

- No version bump or release publication: Phase 5 owns that, after Phases 1–4 are CI-green.
- No Android, iOS or Qt visual redesign yet: those are Phases 2–4. This phase only regenerates their committed Lucide assets from the shared token icon list; their authored UI sources are untouched here.
- No mockup-driven visual parity check: no mockup images were supplied, so the written M3 Expressive contract is the only specification.
- No device rendering verification locally: no browser/device farm is available here; CI covers builds, and real visual review must happen on devices later.
- No server `playfulMotion` setting: `src/mcmusic.py::_sanitize_settings()` drops keys outside `DEFAULT_SETTINGS`, and adding one would exceed this phase's `ui/` scope. The switch is stored on this device only and never presented as a server preference.
- No curated Radio, Mixes tab, Mix chip, global Chart, Dolby/Spatial label, fake lossless badge or fake explicit badge: the backend and feature-truth audit do not support them.
- No new external fonts, trackers, analytics or network endpoints: the only image load is the same same-origin cover already shown in the player.
- No live database changes, branch sync, redeploy or secret rotation: those require explicit permission and are outside this design phase.
- Generated artifacts are committed but not duplicated below: `ui/src/env.css`, `ui/src/common/lucide.tsx`, `gui/android/.../Lucide.kt`, `app/ios/McMusic/Lucide.swift`, `app/linux/mcmusic_linux/icons.py`, the four new Android drawables and the gitignored `web/ui/` build are all reproducible from their sources and generators.

## Full authored file contents

The files below are reproduced in full. No generated marker block was hand-edited; `ui/src/common/theme.ts` is included in full because its hand-authored helpers were changed outside the generated block.

### `design/tokens.json`

```json
{
  "schema": 1,
  "note": "Single source of truth for 4.2.0. Legacy swatches are kept verbatim so stored palette ids still resolve to the same bytes; `seed` is the Material 3 HCT seed used to generate the full tonal role set. Change a value here and run node scripts/gen-tokens.mjs + node scripts/gen-lucide.mjs.",
  "shape": {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 28,
    "xxl": 36,
    "pill": 999,
    "coverMin": 20,
    "coverMax": 28,
    "card": 28,
    "hero": 36,
    "touchTarget": 48
  },
  "spacing": { "unit": 4 },
  "motion": {
    "spring": { "stiffness": "medium", "damping": 0.7 },
    "pressScale": 0.96,
    "morphMs": 320,
    "progressWaveHz": 0.55,
    "progressWavePx": 3,
    "settingsKey": "playfulMotion",
    "defaultEnabled": true,
    "reducedMotion": "honour platform setting and disable springs, morphs and waves"
  },
  "type": {
    "display": { "size": 36, "weight": 700, "line": 44 },
    "headline": { "size": 28, "weight": 700, "line": 36 },
    "title": { "size": 22, "weight": 700, "line": 28 },
    "body": { "size": 16, "weight": 400, "line": 24 },
    "label": { "size": 14, "weight": 600, "line": 20 }
  },
  "aliases": {
    "": "violet",
    "auto": "violet",
    "system": "violet",
    "flufi": "violet-dark",
    "dark": "violet-dark",
    "dusk": "violet-dark",
    "paper": "violet-light",
    "light": "violet-light",
    "ink": "indigo-dark",
    "amoled": "indigo-dark",
    "midnight": "sky-dark",
    "tide": "aqua-dark",
    "forest": "mint-dark",
    "rose": "violet-dark",
    "copper": "violet-dark",
    "mocha": "violet-dark"
  },
  "families": [
    {
      "id": "violet",
      "name": "Violet",
      "seed": "#9F7EFF",
      "legacy": {
        "light": {
          "bg": "#F5F2FF", "bg2": "#EDE7FF", "surface": "#FFFFFF", "surface2": "#F7F4FF",
          "fg": "#08060D", "dim": "#473872", "dim2": "#6A54AA", "line": "#DACDFF", "line2": "#CAB8FF", "accent": "#9F7EFF", "accentText": "#5B3F9E"
        },
        "dark": {
          "bg": "#171721", "bg2": "#222130", "surface": "#2A293C", "surface2": "#444361",
          "fg": "#FFFFFF", "dim": "#AAAAB7", "dim2": "#8B8A9D", "line": "#35344B", "line2": "#605F78", "accent": "#9F7EFF", "accentText": "#C6B2FF"
        }
      }
    },
    {
      "id": "indigo",
      "name": "Indigo",
      "seed": "#8293FF",
      "legacy": {
        "light": {
          "bg": "#F2F4FF", "bg2": "#E8EBFF", "surface": "#FFFFFF", "surface2": "#F5F6FF",
          "fg": "#08060D", "dim": "#3B4172", "dim2": "#5761AA", "line": "#CFD5FF", "line2": "#BAC3FF", "accent": "#8293FF", "accentText": "#4A56A8"
        },
        "dark": {
          "bg": "#12171F", "bg2": "#1B212D", "surface": "#212838", "surface2": "#36425B",
          "fg": "#FFFFFF", "dim": "#A4A9B5", "dim2": "#828999", "line": "#2A3346", "line2": "#545E73", "accent": "#8293FF", "accentText": "#B4BEFF"
        }
      }
    },
    {
      "id": "sky",
      "name": "Sky",
      "seed": "#7BBDFE",
      "legacy": {
        "light": {
          "bg": "#F1F8FE", "bg2": "#E7F3FE", "surface": "#FFFFFF", "surface2": "#F4F9FE",
          "fg": "#08060D", "dim": "#385272", "dim2": "#527CA9", "line": "#CCE5FE", "line2": "#B6DAFE", "accent": "#7BBDFE", "accentText": "#235F93"
        },
        "dark": {
          "bg": "#182127", "bg2": "#222F39", "surface": "#2A3A46", "surface2": "#455F72",
          "fg": "#FFFFFF", "dim": "#ABB7BF", "dim2": "#8B9BA7", "line": "#354A58", "line2": "#607787", "accent": "#7BBDFE", "accentText": "#A9D5FF"
        }
      }
    },
    {
      "id": "aqua",
      "name": "Aqua",
      "seed": "#7CE0E6",
      "legacy": {
        "light": {
          "bg": "#F1FBFC", "bg2": "#E7F9FA", "surface": "#FFFFFF", "surface2": "#F4FCFD",
          "fg": "#08060D", "dim": "#386168", "dim2": "#53939A", "line": "#CDF3F5", "line2": "#B6EDF1", "accent": "#7CE0E6", "accentText": "#126F77"
        },
        "dark": {
          "bg": "#15241C", "bg2": "#1F3328", "surface": "#263F32", "surface2": "#3E6751",
          "fg": "#FFFFFF", "dim": "#A8BAB0", "dim2": "#87A093", "line": "#30503F", "line2": "#5A7D6B", "accent": "#7CE0E6", "accentText": "#A6EFF3"
        }
      }
    },
    {
      "id": "mint",
      "name": "Mint",
      "seed": "#7BFFA4",
      "legacy": {
        "light": {
          "bg": "#F1FFF5", "bg2": "#E7FFEE", "surface": "#FFFFFF", "surface2": "#F4FFF7",
          "fg": "#08060D", "dim": "#386E4C", "dim2": "#52A76F", "line": "#CCFFDC", "line2": "#B6FFCC", "accent": "#7BFFA4", "accentText": "#216A43"
        },
        "dark": {
          "bg": "#15241A", "bg2": "#1F3425", "surface": "#26412E", "surface2": "#3E694B",
          "fg": "#FFFFFF", "dim": "#A8BBAE", "dim2": "#87A28F", "line": "#30513A", "line2": "#5A7F66", "accent": "#7BFFA4", "accentText": "#A9FFC2"
        }
      }
    }
  ],
  "icons": [
    "audio-lines", "cast", "check", "chevron-down", "chevron-left", "chevron-right", "chevron-up",
    "circle", "circle-alert", "circle-check", "circle-help", "circle-x", "clock", "cookie", "coffee", "compass",
    "disc-3", "download", "dumbbell", "ellipsis", "eye-off", "flame", "flower", "film", "folder-plus",
    "grip-vertical", "hard-drive", "headphones", "heart", "house", "image", "inbox", "info",
    "key", "library", "link", "list", "list-music", "list-plus", "loader-circle", "lock",
    "log-in", "log-out", "mail", "message-circle", "mic-vocal", "monitor", "moon", "music",
    "palette", "pause", "pencil", "pentagon", "picture-in-picture-2", "play", "plus", "radio", "refresh-cw",
    "repeat", "repeat-1", "search", "server", "settings", "shield", "shield-alert", "shield-check",
    "shuffle", "skip-back", "skip-forward", "smartphone", "sparkles", "squircle", "star", "trash-2",
    "user-round", "volume-1", "volume-2", "volume-x", "wifi", "wifi-off", "x", "zap"
  ],
  "iconAliases": {
    "home": "house",
    "user": "user-round",
    "music-note": "music",
    "more-horizontal": "ellipsis",
    "trash": "trash-2",
    "circle_help": "circle-help"
  }
}
```

### `scripts/gen-tokens.mjs`

```js
#!/usr/bin/env node
// Generate every client's design tokens from design/tokens.json.
//
//   node scripts/gen-tokens.mjs           # write generated files
//   node scripts/gen-tokens.mjs --check   # fail if a generated file is stale
//
// The five family accents are Material 3 HCT seeds. The generated tonal roles
// come from @material/material-color-utilities. Legacy swatches stay verbatim in
// tokens.json so saved palette ids keep resolving to the same bytes.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  Hct,
  SchemeTonalSpot,
  TonalPalette,
  argbFromHex,
  hexFromArgb,
} from "../ui/node_modules/@material/material-color-utilities/index.js";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CHECK = process.argv.includes("--check");
const tokens = JSON.parse(fs.readFileSync(path.join(ROOT, "design/tokens.json"), "utf8"));
const outputs = new Map();

// `surface` exists in every legacy token set already, so the generated M3
// surface role reuses that field rather than duplicating a constructor arg.
const ROLES = [
  "primary", "onPrimary", "primaryContainer", "onPrimaryContainer",
  "secondary", "onSecondary", "secondaryContainer", "onSecondaryContainer",
  "tertiary", "onTertiary", "tertiaryContainer", "onTertiaryContainer",
  "error", "onError", "errorContainer", "onErrorContainer",
  "background", "onBackground", "onSurface",
  "surfaceVariant", "onSurfaceVariant",
  "surfaceContainerLowest", "surfaceContainerLow", "surfaceContainer",
  "surfaceContainerHigh", "surfaceContainerHighest",
  "outline", "outlineVariant", "inverseSurface", "inverseOnSurface",
  "inversePrimary", "scrim", "shadow",
];

/** Legacy accents are deliberately bright brand swatches. Text painted on them
 *  needs the higher-contrast of ink/white, not the M3 onPrimary role (which is
 *  paired with the generated darker `primary` role instead). */
function readableOn(hex) {
  const channel = value => {
    const v = value / 255;
    return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  };
  const luminance = color => {
    const r = channel(parseInt(color.slice(1, 3), 16));
    const g = channel(parseInt(color.slice(3, 5), 16));
    const b = channel(parseInt(color.slice(5, 7), 16));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const accent = luminance(hex.toUpperCase());
  const ink = luminance("#08060D");
  const white = luminance("#FFFFFF");
  const contrast = (a, b) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  return contrast(ink, accent) >= contrast(white, accent) ? "#08060D" : "#FFFFFF";
}

function rolesFor(family, mode) {
  const dark = mode === "dark";
  const source = Hct.fromInt(argbFromHex(family.seed));
  const scheme = new SchemeTonalSpot(source, dark, 0);
  // Low-chroma surfaces in the seed's own hue stay tonal without translucency.
  const surface = TonalPalette.fromHueAndChroma(
    source.hue, Math.min(20, Math.max(8, source.chroma / 5)),
  );
  const tone = (palette, t) => hexFromArgb(palette.tone(t)).toUpperCase();
  const fixed = {
    primary: scheme.primary,
    onPrimary: scheme.onPrimary,
    primaryContainer: scheme.primaryContainer,
    onPrimaryContainer: scheme.onPrimaryContainer,
    secondary: scheme.secondary,
    onSecondary: scheme.onSecondary,
    secondaryContainer: scheme.secondaryContainer,
    onSecondaryContainer: scheme.onSecondaryContainer,
    tertiary: scheme.tertiary,
    onTertiary: scheme.onTertiary,
    tertiaryContainer: scheme.tertiaryContainer,
    onTertiaryContainer: scheme.onTertiaryContainer,
    error: scheme.error,
    onError: scheme.onError,
    errorContainer: scheme.errorContainer,
    onErrorContainer: scheme.onErrorContainer,
    outline: scheme.outline,
    // M3's default outlineVariant is decorative (1.7:1 on light surfaces).
    // Boundaries in this app carry meaning, so use tone 55 (>=3.5:1).
    outlineVariant: surface.tone(55),
    inversePrimary: scheme.inversePrimary,
  };
  const legacy = family.legacy[mode];
  const roles = {
    ...Object.fromEntries(Object.entries(fixed)
      .map(([key, value]) => [key, hexFromArgb(value).toUpperCase()])),
    background: tone(surface, dark ? 6 : 99),
    onBackground: tone(surface, dark ? 95 : 10),
    surface: legacy.surface.toUpperCase(),
    onSurface: tone(surface, dark ? 95 : 10),
    surfaceVariant: tone(surface, dark ? 24 : 90),
    onSurfaceVariant: tone(surface, dark ? 80 : 30),
    surfaceContainerLowest: tone(surface, dark ? 4 : 99),
    surfaceContainerLow: tone(surface, dark ? 10 : 96),
    surfaceContainer: tone(surface, dark ? 12 : 94),
    surfaceContainerHigh: tone(surface, dark ? 17 : 92),
    surfaceContainerHighest: tone(surface, dark ? 22 : 90),
    inverseSurface: tone(surface, dark ? 95 : 20),
    inverseOnSurface: tone(surface, dark ? 20 : 95),
    scrim: "#000000",
    shadow: "#000000",
  };
  return {
    legacy,
    roles: {
      ...roles,
      accentFg: readableOn(legacy.accent),
    },
  };
}

const variants = Object.fromEntries(tokens.families.map(family => [
  family.id,
  Object.fromEntries(["light", "dark"].map(mode => [mode, rolesFor(family, mode)])),
]));

function put(relative, content) {
  outputs.set(path.join(ROOT, relative), content);
}

function replaceMarkers(relative, begin, end, generated) {
  const file = path.join(ROOT, relative);
  const content = fs.readFileSync(file, "utf8");
  const start = content.indexOf(begin);
  const stop = content.indexOf(end);
  if (start < 0 || stop < 0 || stop <= start) {
    throw new Error(`${relative}: missing generation markers`);
  }
  const body = generated.replace(/^\n+|\n+$/g, "");
  put(relative, content.slice(0, start + begin.length) + "\n" + body + "\n" + content.slice(stop));
}

const kebab = s => s.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
const snake = s => (s === "scrim" ? "scrim_color" : s === "shadow" ? "shadow_color"
  : s.replace(/([a-z0-9])([A-Z])/g, "$1_$2").toLowerCase());

// ── machine-readable export used by the contrast test ───────────────────────
put("design/tokens.generated.json", JSON.stringify({
  schema: tokens.schema,
  families: Object.fromEntries(Object.entries(variants).map(([id, modes]) => [
    id,
    Object.fromEntries(Object.entries(modes).map(([mode, value]) => [mode, {
      seed: tokens.families.find(f => f.id === id).seed,
      legacy: value.legacy,
      roles: value.roles,
    }])),
  ])),
  shape: tokens.shape,
  spacing: tokens.spacing,
  motion: tokens.motion,
  type: tokens.type,
  aliases: tokens.aliases,
}, null, 2) + "\n");

// ── CSS ─────────────────────────────────────────────────────────────────────
function cssVars(variant) {
  const l = variant.legacy;
  const r = variant.roles;
  const lines = [
    ["--back", l.bg], ["--back-raised", l.bg2], ["--flat-hover", l.line],
    ["--prim", l.surface], ["--prim-brighter", l.surface2], ["--seco", l.bg2],
    ["--tert", l.line], ["--tert-hover", l.line2],
    ["--text", l.fg], ["--text-bright", l.fg], ["--text-dim", l.dim], ["--text-dark", l.dim2],
    ["--accent", l.accent], ["--accent-hover", l.accentText],
    ["--text-on-light", r.accentFg], ["--accent-soft", r.primaryContainer],
    ["--accent-faint", r.surfaceContainerLow], ["--surface-lift", r.surfaceContainerHigh],
    ["--layer-rim", r.outlineVariant], ["--layer-highlight", r.outline],
    ["--elevation-1", "none"], ["--elevation-2", "none"],
    ["--back-border", l.line], ["--prim-border", l.line2],
    ["--shadow", r.scrim], ["--shadow-raised", "none"], ["--backdrop", r.scrim],
    ["--success", "#1DB954"], ["--warning", "#FFBF69"], ["--equaliser", "var(--accent)"],
    ["--radius", `${tokens.shape.card}px`], ["--radius-lg", `${tokens.shape.xl}px`],
    ["--radius-xl", `${tokens.shape.hero}px`], ["--radius-pill", `${tokens.shape.pill}px`],
    ["--shape-xs", `${tokens.shape.xs}px`], ["--shape-sm", `${tokens.shape.sm}px`],
    ["--shape-md", `${tokens.shape.md}px`], ["--shape-lg", `${tokens.shape.lg}px`],
    ["--shape-xl", `${tokens.shape.xl}px`], ["--shape-xxl", `${tokens.shape.xxl}px`],
    ["--touch-target", `${tokens.shape.touchTarget}px`],
    ["--topbar-h", "50px"], ["--player-h", "84px"],
    ["--spring-damping", String(tokens.motion.spring.damping)],
    ["--press-scale", String(tokens.motion.pressScale)],
    ["--morph-ms", `${tokens.motion.morphMs}ms`],
    ["--progress-wave-hz", String(tokens.motion.progressWaveHz)],
    ["--progress-wave-px", `${tokens.motion.progressWavePx}px`],
  ];
  for (const [name, style] of Object.entries(tokens.type)) {
    lines.push(["--type-" + name + "-size", `${style.size}px`]);
    lines.push(["--type-" + name + "-weight", String(style.weight)]);
    lines.push(["--type-" + name + "-line", `${style.line}px`]);
  }
  for (const role of ROLES) lines.push([`--md-${kebab(role)}`, r[role]]);
  return lines.map(([key, value]) => `    ${key}: ${value};`).join("\n");
}
put("ui/src/env.css", `/* GENERATED by scripts/gen-tokens.mjs — edit design/tokens.json instead.
   Flat Material 3 tones only. Do not hand-edit this file. */
:root {
${cssVars(variants.violet.dark)}
}

${tokens.families.flatMap(f => ["light", "dark"].map(mode =>
  `[data-palette="${f.id}-${mode}"] {\n${cssVars(variants[f.id][mode])}\n}`,
)).join("\n\n")}

/* Only Lucide's rect/circle primitives are fillable; paths stay outlined. */
svg.icon-filled > rect,
svg.icon-filled > circle {
    fill: currentColor;
    stroke: none;
}
`);

// ── TypeScript ──────────────────────────────────────────────────────────────
const tsRoles = ROLES.map(role => `    ${role}: string;`).join("\n");
const tsFamilies = tokens.families.map(f => {
  const modes = ["light", "dark"].map(mode => {
    const v = variants[f.id][mode];
    const body = [
      ...Object.entries(v.legacy).map(([k, value]) => `            ${k}: "${value}",`),
      `            accentFg: "${v.roles.accentFg}",`,
      ...ROLES.map(role => `            ${role}: "${v.roles[role]}",`),
    ].join("\n");
    return `        ${mode}: {\n${body}\n        },`;
  }).join("\n");
  return `    {\n        id: "${f.id}",\n        name: "${f.name}",\n${modes}\n    },`;
}).join("\n");
replaceMarkers("ui/src/common/theme.ts", "// BEGIN GENERATED PALETTE DATA", "// END GENERATED PALETTE DATA",
  `export type PaletteMode = "light" | "dark";
export type FamilyId = ${tokens.families.map(f => `"${f.id}"`).join(" | ")};

export const DESIGN_SHAPE = ${JSON.stringify(tokens.shape)} as const;
export const DESIGN_SPACING = ${JSON.stringify(tokens.spacing)} as const;
export const DESIGN_MOTION = ${JSON.stringify(tokens.motion)} as const;
export const DESIGN_TYPE = ${JSON.stringify(tokens.type)} as const;

export interface PaletteTokens {
    // Legacy swatches: unchanged bytes for stored palette ids.
    bg: string; bg2: string; surface: string; surface2: string;
    fg: string; dim: string; dim2: string; line: string; line2: string;
    accent: string; accentText: string; accentFg: string;
    // Generated Material 3 tonal roles (HCT from this family's accent seed).
${tsRoles}
}

export interface Palette extends PaletteTokens {
    /** Concrete id, e.g. \`violet-dark\`. */
    id: string;
    family: FamilyId;
    mode: PaletteMode;
}

export interface PaletteFamily {
    id: FamilyId;
    name: string;
    light: PaletteTokens;
    dark: PaletteTokens;
}

/** Generated Material 3 role names, exported for CSS variable mirroring. */
export const M3_ROLE_NAMES = ${JSON.stringify(ROLES)} as const;

/** CSS custom property for each generated Material 3 role. */
export const M3_CSS_VARS: Record<string, keyof PaletteTokens> = {
${ROLES.map(role => `    "--md-${kebab(role)}": "${role}",`).join("\n")}
};

export const PALETTE_FAMILIES: readonly PaletteFamily[] = [
${tsFamilies}
];

function concrete(family: PaletteFamily, mode: PaletteMode): Palette {
    const tokens = family[mode];
    return {
        ...tokens,
        id: family.id + "-" + mode,
        family: family.id,
        mode,
    };
}

/** Every pinned half of every family, keyed by its concrete id. */
export const PALETTE_VARIANTS: Record<string, Palette> = Object.fromEntries(
    PALETTE_FAMILIES.flatMap(f => ([
        [f.id + "-light", concrete(f, "light")] as [string, Palette],
        [f.id + "-dark", concrete(f, "dark")] as [string, Palette],
    ])),
);

/** Legacy settings/embed ids. Aliases resolve to a concrete variant where the
 *  old name already implied light or dark; bare family names stay adaptive. */
export const PALETTE_ALIASES: Record<string, string> = {
${Object.entries(tokens.aliases).map(([k, v]) => `    ${JSON.stringify(k)}: "${v}",`).join("\n")}
};`);

// ── Kotlin ──────────────────────────────────────────────────────────────────
const ktRoles = ROLES.map(role => `    val ${role}: Color,`).join("\n");
const ktArgs = ROLES.map(role => `    ${role}: String,`).join("\n");
const ktAssign = ROLES.map(role => `        ${role} = color(${role}),`).join("\n");
const ktFamilies = tokens.families.map(f => {
  const modes = ["light", "dark"].map(mode => {
    const v = variants[f.id][mode];
    const args = [
      ...Object.entries(v.legacy).map(([k, value]) => `${k} = "${value.slice(1)}"`),
      `accentFg = "${v.roles.accentFg.slice(1)}"`,
      ...ROLES.map(role => `${role} = "${v.roles[role].slice(1)}"`),
    ].join(", ");
    return `        ${mode} = variant("${f.id}", "${f.name}", ${mode === "dark"}, ${args}),`;
  }).join("\n");
  return `    val ${f.id} = PaletteFamily(\n        id = "${f.id}",\n        label = "${f.name}",\n${modes}\n    )`;
}).join("\n\n");
replaceMarkers("gui/android/app/src/main/java/dev/mcmusic/app/ui/design/Design.kt",
  "// BEGIN GENERATED PALETTES", "// END GENERATED PALETTES",
  `object Palettes {
    private fun color(hex: String) = Color(android.graphics.Color.parseColor("#$hex"))

    private fun variant(
        family: String, label: String, dark: Boolean,
        bg: String, bg2: String, surface: String, surface2: String,
        fg: String, dim: String, dim2: String, line: String, line2: String,
        accent: String, accentText: String, accentFg: String,
${ktArgs}
    ) = McPalette(
        id = "$family-" + (if (dark) "dark" else "light"),
        label = label, dark = dark,
        bg = color(bg), bg2 = color(bg2), surface = color(surface), surface2 = color(surface2),
        fg = color(fg), dim = color(dim), dim2 = color(dim2), line = color(line), line2 = color(line2),
        accent = color(accent), accentText = color(accentText), accentFg = color(accentFg),
${ktAssign}
    )

${ktFamilies}

    /** Exactly five chooser entries; each adapts to system light/dark. */
    val families = listOf(violet, indigo, sky, aqua, mint)

    private val byConcreteId: Map<String, McPalette> = families.flatMap { listOf(it.light, it.dark) }
        .associateBy { it.id }

    private val byFamilyId: Map<String, PaletteFamily> = families.associateBy { it.id }

    const val AUTO = "auto"

    /** Legacy ids keep the light/dark half they used to imply. */
    private val aliases = mapOf(
${Object.entries(tokens.aliases).filter(([k]) => k)
    .map(([k, v]) => `        "${k}" to ${v === "violet" ? "AUTO" : `"${v}"`},`).join("\n")}
    )

    private fun canonicalID(id: String?): String {
        val key = (id ?: AUTO).lowercase().trim()
        return aliases[key] ?: key
    }

    /** \`auto\`, \`system\`, empty and bare family ids follow system appearance. */
    fun resolve(id: String?, systemDark: Boolean): McPalette {
        val key = canonicalID(id)
        return byConcreteId[key]
            ?: byFamilyId[key]?.resolve(systemDark)
            ?: violet.resolve(systemDark)
    }
}`);

// ── Swift ───────────────────────────────────────────────────────────────────
const swiftFamilies = tokens.families.map(f => {
  const modes = ["light", "dark"].map(mode => {
    const v = variants[f.id][mode];
    const args = [
      ...Object.entries(v.legacy).map(([k, value]) => `${k}: Color(hex: "${value.slice(1)}")`),
      `accentFg: Color(hex: "${v.roles.accentFg.slice(1)}")`,
      ...ROLES.map(role => `${role}: Color(hex: "${v.roles[role].slice(1)}")`),
      `success: Color(hex: "1DB954")`,
      `isDark: ${mode === "dark"}`,
    ].join(", ");
    return `        ${mode}: PaletteTokens(${args})`;
  }).join(",\n");
  return `    static let ${f.id} = PaletteFamily(\n        id: .${f.id},\n${modes}\n    )`;
}).join("\n\n");
replaceMarkers("app/ios/McMusic/Theme.swift", "// BEGIN GENERATED PALETTES", "// END GENERATED PALETTES",
  `${swiftFamilies}\n\n    static let families: [PaletteFamily] = [${tokens.families.map(f => f.id).join(", ")}]`);

// ── Python / Qt ─────────────────────────────────────────────────────────────
const pyParams = ROLES.map(role => `${snake(role)}`).join(", ");
const pyAssign = ROLES.map(role => `        ${snake(role)}=${snake(role)},`).join("\n");
const pyFamilies = tokens.families.map(f => ["light", "dark"].map(mode => {
  const v = variants[f.id][mode];
  const args = [
    ...Object.entries(v.legacy).map(([k, value]) => `${k}=${JSON.stringify(value.toLowerCase())}`),
    `accent_fg=${JSON.stringify(v.roles.accentFg.toLowerCase())}`,
    ...ROLES.map(role => `${snake(role)}=${JSON.stringify(v.roles[role].toLowerCase())}`),
    `dark=${mode === "dark" ? "True" : "False"}`,
    `label=${JSON.stringify(f.name)}`,
  ].join(", ");
  return `${f.id}_${mode} = _variant(${args})`;
}).join("\n")).join("\n\n");
replaceMarkers("app/linux/mcmusic_linux/theme.py", "# BEGIN GENERATED PALETTES", "# END GENERATED PALETTES",
  `def _variant(bg, bg2, surface, surface2, fg, dim, dim2, line, line2, accent, accentText, accent_fg,
             ${pyParams}, dark, label):
    name = "%s-%s" % (label.lower(), "dark" if dark else "light")
    return Palette(
        name=name, bg=bg, bg2=bg2, surface=surface, surface2=surface2,
        fg=fg, dim=dim, dim2=dim2, line=line, line2=line2,
        accent=accent, accent_text=accentText, accent_fg=accent_fg, warn="#ffbf69",
        err="#ff6b72" if dark else "#b3261e",
        scrim="rgba(23, 23, 33, 0.78)", ink=bg2,
${pyAssign}
    )


${pyFamilies}

# Public uppercase aliases used by the runtime appearance state.
VIOLET_LIGHT = violet_light
VIOLET_DARK = violet_dark

FAMILIES = {
${tokens.families.map(f => `    ${JSON.stringify(f.id)}: (${JSON.stringify(f.name)}, ${f.id}_light, ${f.id}_dark),`).join("\n")}
}

PALETTES: dict[str, Palette] = {}
for _family, (_label, _light, _dark) in FAMILIES.items():
    PALETTES[_light.name] = _light
    PALETTES[_dark.name] = _dark

# Legacy saved values resolve to the nearest family.
ALIASES = {
${Object.entries(tokens.aliases).map(([k, v]) => `    ${JSON.stringify(k)}: ${JSON.stringify(v)},`).join("\n")}
}`);

// ── embed widgets ───────────────────────────────────────────────────────────
const widgetThemes = tokens.families.flatMap(f => ["light", "dark"].map(mode => {
  const v = variants[f.id][mode];
  const body = Object.entries(v.legacy).map(([k, value]) => `${k}:'${value}'`).join(", ");
  return `    '${f.id}-${mode}': { ${body} },`;
}));
replaceMarkers("web/embed/widgets.js", "// BEGIN GENERATED THEMES", "// END GENERATED THEMES",
  `const THEMES = {
${widgetThemes.join("\n")}
${tokens.families.map(f => `    ${f.id}: 'system',`).join("\n")}
${Object.entries(tokens.aliases).map(([k, v]) => `    ${JSON.stringify(k)}: ${v === "violet" ? "'system'" : JSON.stringify(v)},`).join("\n")}
  };`);

// ── write or verify ─────────────────────────────────────────────────────────
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
if (CHECK && stale) {
  console.error(`${stale} generated file(s) are stale; run node scripts/gen-tokens.mjs`);
  process.exit(1);
}
if (!CHECK) console.log(`gen-tokens: ${outputs.size} files up to date`);
```

### `scripts/strip-font-cdn.mjs`

```js
#!/usr/bin/env node
// Remove third-party font CDN imports from built CSS.
//
// Fonts are bundled locally from @fontsource-variable packages. flufi-ui's
// stylesheet still carries a fonts.googleapis.com @import, so the built CSS is
// sanitised here instead of patching node_modules. This script intentionally
// fails on any remote @import it cannot account for, rather than silently
// shipping a CDN dependency.
import fs from "node:fs";
import path from "node:path";

const ROOT = process.argv[2] || process.cwd();
const allowedFontHosts = /(?:fonts\.googleapis\.com|fonts\.gstatic\.com)/i;
// Vite minifies `@import "..."` to `@import"..."`; allow zero whitespace so a
// bundled CDN import cannot slip through in either form.
const remoteImport = /@import\s*(?:url\(\s*)?["']?https?:\/\/[^"')]+["']?\s*\)?\s*;/gi;

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) return walk(full);
    return entry.isFile() && full.endsWith(".css") ? [full] : [];
  });
}

const files = walk(path.join(ROOT, "web/ui"));
let removed = 0;
for (const file of files) {
  const before = fs.readFileSync(file, "utf8");
  const matches = before.match(remoteImport) || [];
  const unexpected = matches.filter(match => !allowedFontHosts.test(match));
  if (unexpected.length) {
    console.error(`${path.relative(ROOT, file)}: unexpected remote @import: ${unexpected.join(" ")}`);
    process.exit(1);
  }
  const after = before.replace(remoteImport, "");
  if (after !== before) {
    fs.writeFileSync(file, after);
    removed += matches.length;
    console.log(`stripped ${matches.length} font CDN import(s) from ${path.relative(ROOT, file)}`);
  }
}
console.log(`strip-font-cdn: checked ${files.length} CSS file(s), removed ${removed} import(s)`);
```

### `ui/src/app.css`

```css

:root {
    /* Medium spring: quick lift, small overshoot, no decorative shadows. */
    --spring-ease: cubic-bezier(0.2, 0.9, 0.2, 1.2);
    --topbar-h: 64px;
}

html, body, #app {
    height: 100dvh;
    overflow: hidden;
}

#app > div {
    position: fixed;
    inset: 0;
    height: 100dvh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    max-height: 100dvh;

    /* flufi's .container is a column; the shell's middle row is a row. */
    > main {
        flex-direction: row;
        flex: 1;
        min-height: 0;
        overflow: hidden;
    }
}

/* Every page's Content renders <main class="content-*"> with no padding of
   its own; the v3 shell expects the gutter here. The bottom padding leaves
   room for the pinned player bar. */
main[class^="content-"] {
    flex: 1;
    min-width: 0;
    overflow-y: auto;
    padding: 24px 28px calc(var(--player-h) + 24px);
    display: flex;
    flex-direction: column;
    gap: 20px;

    background: var(--back);
}

/* Material 3 type scale, sourced from design/tokens.json. */
main[class^="content-"] h2 {
    font-family: 'Lexend', sans-serif;
    font-size: var(--type-headline-size);
    line-height: var(--type-headline-line);
    font-weight: var(--type-headline-weight);
}

main[class^="content-"] h3 {
    font-family: 'Lexend', sans-serif;
    font-size: var(--type-title-size);
    line-height: var(--type-title-line);
    font-weight: var(--type-title-weight);
}

/* ── Soft Material 3 layer polish ─────────────────────────────────────────
   Shared across flufi controls so the app reads like a set of calm, rounded
   flat surfaces. The tokens are palette-derived, so every family gets its own
   ink, accent wash and rim. */
:where(button, a).button {
    border-radius: var(--radius-pill);
    min-height: var(--touch-target);
    transition: background var(--transition-fast),
                transform var(--transition-fast) var(--spring-ease),
                color var(--transition-fast);
}

:where(button, a).button:not(.track):not(.drawer-link):not(.queue-row):not(:disabled):hover {
    transform: translateY(-2px);
}

:where(button, a).button:not(:disabled):active {
    transform: scale(var(--press-scale));
}

:where(button, a).button.variant-accent {
    background: var(--accent);
    color: var(--text-on-light);
    border: 1px solid var(--accent-hover);
}

:where(button, a).button.variant-panel,
:where(button, a).button.variant-secondary {
    background: var(--surface-lift);
    border: 1px solid var(--layer-rim);
}

:where(input, textarea, select).input,
.select-box,
.search-bar {
    background: var(--surface-lift);
    border: 1px solid var(--layer-rim);
}

:where(input, textarea, select).input:focus-within,
.select-box:focus-within,
.search-bar:focus-within {
    border-color: var(--accent);
    outline: 2px solid var(--accent);
    outline-offset: 1px;
}

.palette-card,
.icon-choice,
.icon-toggle,
.popout {
    background: var(--surface-lift);
    border: 1px solid var(--layer-rim);
}

/* Page actions should hug their label, not stretch across the pane. */
main[class^="content-"] .button {
    width: fit-content;
}

/* Library cards keep the v3 tile size instead of growing with the pane; the
   grid overrides the width so columns share the row evenly. */
.library-card {
    width: 150px;
    flex: none;
    min-width: 0;
}

.library-card .library-img {
    width: 100%;
    height: auto;
    aspect-ratio: 1 / 1;
}

@media (max-width: 800px) {
    main[class^="content-"] {
        padding: 16px 16px calc(var(--player-h) + 24px);
    }
    .library-card {
        width: 122px;
    }
}

.logo {
    font-family: 'Lexend';
    font-size: var(--type-title-size);
    line-height: var(--type-title-line);
    font-weight: var(--type-title-weight);
    text-decoration: none;
}

/* Visible keyboard focus everywhere, in the active tonal accent. */
:where(a, button, input, textarea, select, [tabindex]):focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
    border-radius: var(--radius-lg);
}

/* Icon-only controls stay comfortably tappable on phones. */
@media (max-width: 800px) {
    #topbar .button,
    #left-sidebar .button {
        min-width: var(--touch-target);
        min-height: var(--touch-target);
    }
}

/* Playful motion is opt-out and always yields to the platform setting. */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
    }
}

html[data-playful="false"] :where(button, a).button:hover {
    transform: none;
}

/* Shared helpers for the few places where flufi-ui has no equivalent. */
.error {
    color: var(--danger);
}

.status-line {
    display: block;
    font-size: var(--font-size-small);
    line-height: 1.45;
}

.status,
.status-ok {
    color: var(--success);
}

.status-idle {
    color: var(--text-dim);
}

.warning {
    color: var(--warning);
}

.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

.icon-tip {
    display: inline-flex;
    align-items: center;
}

.grow {
    flex: 1;
    min-width: 0;
}

/* Shared ellipsis helper: rows stay single-line and the full value is only
   shown in a context menu or a detail dialog. */
.clip {
    min-width: 0;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Menus are detail surfaces: never truncate their labels. */
:where(.flufi-context-menu, .context-menu, [role="menu"]) :where(.label, .menu-label, span) {
    overflow: visible;
    text-overflow: clip;
    white-space: normal;
    overflow-wrap: anywhere;
}

/* Narrow screens: keep every page inside the viewport and stop cards, admin
   tables and form rows from pushing controls off the edge. */
@media (max-width: 800px) {
    main[class^="content-"] {
        padding: 12px 12px calc(var(--player-h) + 18px);
        gap: 12px;
    }

    main[class^="content-"] :where(.container, .wrap-list, .settings-card, .admin-card) {
        min-width: 0;
        max-width: 100%;
    }

    main[class^="content-"] :where(.row, .build-row, .download-row, .admin-row) {
        min-width: 0;
        flex-wrap: wrap;
    }

    main[class^="content-"] h2,
    main[class^="content-"] h3 {
        overflow-wrap: anywhere;
    }
}

/* System banners sit above the topbar and never push the shell out of view. */
.system-banners {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 60;
    display: flex;
    flex-direction: column;
    gap: 4px;
    pointer-events: none;
}

.system-banner {
    pointer-events: auto;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: var(--prim);
    border-bottom: 1px solid var(--back-border);
    font-size: var(--font-size-small);
}

.system-banner a {
    color: var(--accent);
}

.system-banner > span {
    flex: 1;
}
```

### `ui/src/common/net/api.ts`

```ts
import { signal } from "@preact/signals";
import type { Option } from "flufi-ui/types";
import type {
    Artist, HomePayload, PlaybackResponse, PublicListening, PublicNow, RoturStatus,
    SearchItem, Set as SetEntity, Track, User,
} from "./types";
import * as idb from "../idb";

const BASE = "/api";

export type ApiJson = Record<string, any>;

function emit(name: string, detail?: unknown) {
    try {
        window.dispatchEvent(new CustomEvent(name, { detail }));
    } catch { /* no window during tests */ }
}

function offline(e: unknown): boolean {
    const message = e instanceof Error ? e.message : String(e);
    return (typeof navigator !== "undefined" && navigator.onLine === false) ||
        e instanceof TypeError ||
        // The service worker answers cacheable GETs with a 503 JSON body while
        // offline; that error must use the same CacheStorage fallback as a
        // genuine network failure.
        message === "offline" || /HTTP 503$/.test(message);
}

async function once(path: string, method: string, body?: unknown): Promise<ApiJson> {
    const res = await fetch(`${BASE}/${path}`, {
        method,
        credentials: "same-origin",
        headers: body === undefined ? undefined : { "content-type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `${method} ${path} -> HTTP ${res.status}`);
    return data;
}

async function get(path: string): Promise<ApiJson> {
    try {
        return await once(path, "GET");
    } catch (e) {
        // The service worker caches the same read-only GETs the legacy client
        // used; serve that body when the network is gone instead of an error.
        if (!offline(e) || typeof caches === "undefined") throw e;
        const url = new URL(`${BASE}/${path}`, location.origin).toString();
        const hit = await caches.match(url).catch(() => undefined);
        if (hit) {
            emit("mc:cachehit", { path });
            return hit.json();
        }
        emit("mc:offline", { path });
        throw e;
    }
}

/**
 * Only replay-safe writes are queued. Likes are toggles, so every tap is kept;
 * playlist adds/removes and renames converge when replayed. Others fail loudly.
 */
type OutboxEntry = { path: string; method: string; body?: unknown; at: number };
const REPLAYABLE: { method: string; path: RegExp; toggle?: boolean }[] = [
    { method: "POST", path: /^like\/\d+$/, toggle: true },
    { method: "POST", path: /^playlists\/\d+\/tracks$/ },
    { method: "PATCH", path: /^playlists\/\d+$/ },
    { method: "DELETE", path: /^playlists\/\d+$/ },
    { method: "DELETE", path: /^playlists\/\d+\/tracks\/\d+$/ },
];
function replayRule(method: string, path: string) {
    return REPLAYABLE.find(r => r.method === method && r.path.test(path));
}

const OUTBOX_KEY = "outbox";
const OUTBOX_STORE = "session";
async function queued(): Promise<OutboxEntry[]> {
    try {
        const v = await idb.get<OutboxEntry[]>(OUTBOX_KEY, OUTBOX_STORE);
        return Array.isArray(v) ? v : [];
    } catch { return []; }
}
export async function pendingWrites(): Promise<number> {
    return (await queued()).length;
}
async function enqueue(path: string, method: string, body?: unknown) {
    const same = (a: unknown, b: unknown) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
    const keepAll = !!replayRule(method, path)?.toggle;
    const items = (await queued()).filter(e =>
        keepAll || !(e.method === method && e.path === path && same(e.body, body)));
    items.push({ path, method, ...(body === undefined ? {} : { body }), at: Date.now() });
    const kept = items.slice(-100);
    await idb.set(OUTBOX_KEY, kept, OUTBOX_STORE);
    emit("mc:queued", { path, method, pending: kept.length });
}

async function send(path: string, method: string, body?: unknown): Promise<ApiJson> {
    try {
        return await once(path, method, body);
    } catch (e) {
        if (!offline(e) || !replayRule(method, path)) throw e;
        await enqueue(path, method, body);
        return { queued: true, offline: true };
    }
}

let flushInFlight: Promise<number> | null = null;
/** Replay queued writes oldest-first; a network error stops the run. */
export function flushOutbox(): Promise<number> {
    if (flushInFlight) return flushInFlight;
    flushInFlight = (async () => {
        if (typeof navigator !== "undefined" && navigator.onLine === false) return 0;
        let list = await queued();
        let sent = 0;
        while (list.length) {
            const item = list[0];
            try {
                await once(item.path, item.method, item.body);
                sent += 1;
            } catch (e) {
                const gone = item.method === "DELETE" && /HTTP (404|410)$/.test(String(e));
                const permanent = /HTTP 4\d\d$/.test(String(e)) && !/HTTP 429$/.test(String(e));
                if (!gone && !permanent) break;
                if (!gone) emit("mc:syncfail", { path: item.path, error: String(e) });
            }
            list = list.slice(1);
            await idb.set(OUTBOX_KEY, list, OUTBOX_STORE);
        }
        if (sent) emit("mc:synced", { count: sent, pending: (await queued()).length });
        return sent;
    })().finally(() => { flushInFlight = null; });
    return flushInFlight;
}

if (typeof window !== "undefined") {
    window.addEventListener("online", () => { void flushOutbox().catch(() => {}); });
    window.addEventListener("load", () => { void flushOutbox().catch(() => {}); });
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") void flushOutbox().catch(() => {});
    });
}

// ---------------------------------------------------------------- ids
// mcmusic keys albums by name and artists by name, so the client's uuids are
// "album:<cover id>:<name>" / "artist:<cover id>:<name>" with the name
// URI-encoded (so a slash in an album name is safe in a path segment).
export function artistUuid(name: string, coverId?: number | null): string {
    return `artist:${coverId ?? ""}:${encodeURIComponent(name || "Unknown Artist")}`;
}

export function parseArtistUuid(uuid: string): { coverId: number | null; name: string } {
    const [, cover, ...rest] = String(uuid).split(":");
    return {
        coverId: cover ? Number(cover) || null : null,
        name: decodeURIComponent(rest.join(":")) || "Unknown Artist",
    };
}

export function albumUuid(album: string, coverId?: number | null): string {
    return `album:${coverId ?? ""}:${encodeURIComponent(album || "Unknown Album")}`;
}

export function parseAlbumUuid(uuid: string): { coverId: number | null; name: string } {
    const [, cover, ...rest] = String(uuid).split(":");
    return {
        coverId: cover ? Number(cover) || null : null,
        name: decodeURIComponent(rest.join(":")) || "Unknown Album",
    };
}

export function coverUrl(id?: number | null): string {
    return id ? `${BASE}/tracks/${id}/cover` : "";
}

/** Missing artwork is rendered by `CoverArt` as a flat tonal Lucide tile. */
export function fallbackCover(name: string, kind: "track" | "artist" | "album" = "album"): string {
    return `placeholder:${kind}:${encodeURIComponent((name || "?").trim() || "?")}`;
}

// ---------------------------------------------------------------- json -> model
export function userFromJson(d: ApiJson): User {
    return {
        uuid: String(d.id ?? d.uid ?? ""),
        username: String(d.username ?? ""),
        display_name: d.display_name ?? null,
        email: d.email ?? null,
        is_admin: !!d.is_admin,
        avatar_url: d.avatar_url,
        provider: d.provider,
        rotur_id: d.rotur_id ?? null,
        rotur_linked: d.rotur_linked ?? (d.rotur_id != null),
        playing: null,
    };
}

export function trackFromJson(d: ApiJson, setUuid: string | null): Track {
    const names: string[] = (Array.isArray(d.artists) && d.artists.length
        ? d.artists
        : d.artist ? [d.artist] : []) as string[];
    return {
        uuid: String(d.id),
        name: signal(String(d.title ?? "")),
        artists: signal(names.map((n) => artistUuid(n))),
        set: setUuid,
        duration: signal(Number(d.duration ?? 0) || 0),
        year: signal(d.year ?? null),
        trackNo: signal(Number(d.track_no ?? 0) || 0),
        liked: d.liked == null ? undefined : !!d.liked,
    };
}

/** Raw track row for the track-info dialog and the admin explicit flag. */
export async function getTrackInfo(uuid: string): Promise<ApiJson> {
    const t = (await libraryIndex()).get(String(uuid));
    if (!t) throw new Error(`no track ${uuid}`);
    return t;
}

function setFromJson(album: string, tracks: ApiJson[], coverId: number | null, artist?: string): SetEntity {
    const artistName = artist || tracks[0]?.artist || "Unknown Artist";
    const uuid = albumUuid(album, coverId);
    return {
        uuid,
        kind: signal("album"),
        name: signal(album),
        release: signal(null),
        genres: signal([]),
        artist: artistUuid(artistName),
        artistName,
        tracks: signal(tracks.map((t) => trackFromJson(t, uuid))),
    };
}

function artistFromJson(name: string, coverId: number | null, tracks: ApiJson[] = []): Artist {
    const byAlbum = new Map<string, ApiJson[]>();
    for (const t of tracks) {
        const album = t.album || "Unknown Album";
        if (!byAlbum.has(album)) byAlbum.set(album, []);
        byAlbum.get(album)!.push(t);
    }
    return {
        uuid: artistUuid(name, coverId),
        name: signal(name),
        bio: signal(""),
        genres: signal([]),
        sets: signal([...byAlbum.entries()].map(([album, list]) =>
            setFromJson(album, list, list[0]?.id ?? null, name))),
    };
}

function artistStub(name: string): Artist {
    return artistFromJson(name || "Unknown Artist", null);
}

// ---------------------------------------------------------------- library cache
let indexPromise: Promise<Map<string, ApiJson>> | null = null;

function libraryIndex(): Promise<Map<string, ApiJson>> {
    if (!indexPromise) {
        indexPromise = get("tracks?limit=2000")
            .then((d) => new Map<string, ApiJson>((d.tracks ?? []).map((t: ApiJson) => [String(t.id), t])))
            .catch((e) => { indexPromise = null; throw e; });
    }
    return indexPromise;
}

export function refreshLibrary() {
    indexPromise = null;
}

// ---------------------------------------------------------------- api
export const API = {
    me: () => get("me"),
    login: (username: string, password: string) =>
        send("login", "POST", { username, password }),
    register: (data: { username: string; password: string; invite?: string; email?: string }) =>
        send("register", "POST", data),
    logout: () => send("logout", "POST"),

    // ------------------------------------------------------------- password resets
    requestReset: (email: string) => send("auth/reset/request", "POST", { email }),
    checkReset: (token: string) => send("auth/reset/check", "POST", { token }),
    confirmReset: (token: string, password: string) =>
        send("auth/reset/confirm", "POST", { token, password }),

    async listAlbums(opts: {
        limit?: number, offset?: number, q?: string, sort?: string, minTracks?: number
    } = {}): Promise<{ albums: SetEntity[], total: number }> {
        const params = new URLSearchParams({
            limit: String(opts.limit ?? 60),
            offset: String(opts.offset ?? 0),
            min_tracks: String(opts.minTracks ?? 1),
        });
        if (opts.q) params.set("q", opts.q);
        if (opts.sort) params.set("sort", opts.sort);

        const d = await get(`albums?${params}`);
        // Tracks with no album of their own list under their song name, which
        // would turn the grid into 1,000 one-song "albums". The server keeps
        // those out unless the Singles filter asks for them.
        return {
            total: d.total ?? 0,
            albums: (d.albums ?? []).map((a: ApiJson) =>
                setFromJson(a.album, [], a.cover_id ?? null, a.artist)),
        };
    },

    async listTracks(limit = 50): Promise<Track[]> {
        const d = await get(`tracks?limit=${limit}`);
        return (d.tracks ?? []).map((t: ApiJson) => trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null));
    },

    async listArtists(): Promise<Artist[]> {
        const d = await get("artists");
        return (d.artists ?? []).map((a: ApiJson) => artistFromJson(a.artist, a.cover_id ?? null));
    },

    async getArtist(uuidOrName: string): Promise<Artist> {
        const { name, coverId } = uuidOrName.startsWith("artist:")
            ? parseArtistUuid(uuidOrName)
            : { name: uuidOrName, coverId: null };
        const d = await get(`artist?name=${encodeURIComponent(name)}`);
        return artistFromJson(name, coverId, d.tracks ?? []);
    },

    getArtistPfpUrl(uuid: string): string {
        const { coverId, name } = parseArtistUuid(uuid);
        return coverUrl(coverId) || fallbackCover(name, "artist");
    },

    async getArtistPfp(uuid: string): Promise<Blob> {
        return (await fetch(this.getArtistPfpUrl(uuid), { credentials: "same-origin" })).blob();
    },

    async getSet(uuid: string): Promise<SetEntity> {
        const { name } = parseAlbumUuid(uuid);
        const d = await get(`album?name=${encodeURIComponent(name)}`);
        const tracks: ApiJson[] = d.tracks ?? [];
        return setFromJson(name, tracks, tracks[0]?.id ?? null, tracks[0]?.artist);
    },

    getSetCoverUrl(uuid: string): string {
        const { coverId, name } = parseAlbumUuid(uuid);
        return coverUrl(coverId) || fallbackCover(name, "album");
    },

    async getSetCover(uuid: string): Promise<Blob> {
        return (await fetch(this.getSetCoverUrl(uuid), { credentials: "same-origin" })).blob();
    },

    async getTrack(uuid: string): Promise<Track> {
        const t = (await libraryIndex()).get(String(uuid));
        if (!t) throw new Error(`no track ${uuid}`);
        return trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null);
    },

    streamUrl: (uuid: string) => `${BASE}/tracks/${uuid}/stream`,
    getTrackCoverUrl: (uuid: string) => coverUrl(Number(uuid)) || fallbackCover(uuid, "track"),
    lyrics: (uuid: string) => get(`tracks/${uuid}/lyrics`),
    trackSources: (uuid: string): Promise<{ sources: ApiJson[] }> =>
        get(`tracks/${uuid}/sources`) as Promise<{ sources: ApiJson[] }>,
    patchTrack: (uuid: string, patch: { explicit?: boolean | null }) =>
        send(`tracks/${uuid}`, "PATCH", patch),

    // ------------------------------------------------------ home / likes / radio
    async home(): Promise<HomePayload> {
        const d = await get("home");
        const sections: HomePayload["sections"] = (d.sections ?? []).map((s: ApiJson) => ({
            title: String(s.title ?? ""),
            tracks: (s.tracks ?? []).map((t: ApiJson) =>
                trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null)),
        }));
        return { sections, albums: d.albums ?? [] };
    },

    async likes(): Promise<Track[]> {
        const d = await get("likes");
        return (d.tracks ?? []).map((t: ApiJson) =>
            trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null));
    },
    like: (uuid: string): Promise<{ liked?: boolean; queued?: boolean }> =>
        send(`like/${uuid}`, "POST"),

    async radio(uuid: string): Promise<Track[]> {
        const d = await get(`radio/${uuid}`);
        return (d.tracks ?? []).map((t: ApiJson) =>
            trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null));
    },

    /**
     * MDL ordering for the current queue. Empty until the server's 76%
     * work-rate gate opens; callers keep the existing order when it is empty.
     */
    async modelRank(current: string, ids: string[]): Promise<string[]> {
        const d = await send("model/rank", "POST", {
            current: Number(current) || 0,
            ids: ids.map(Number).filter(n => Number.isInteger(n) && n > 0).slice(0, 500),
        });
        if (!d.active || !Array.isArray(d.ids)) return [];
        return d.ids.map(String);
    },

    // ---------------------------------------------------------- public / social
    publicListening: (): Promise<PublicListening> => get("public/listening") as Promise<PublicListening>,
    publicNow: (username: string): Promise<PublicNow> =>
        get(`public/now/${encodeURIComponent(username)}`) as Promise<PublicNow>,

    // --------------------------------------------------------------- playback
    playback: (device?: string): Promise<PlaybackResponse> =>
        get(device ? `playback?device=${encodeURIComponent(device)}` : "playback") as Promise<PlaybackResponse>,
    playbackPush: (body: ApiJson) => send("playback", "POST", body),
    deviceHeartbeat: (body: ApiJson) => send("devices/heartbeat", "POST", body),
    version: () => get("version"),
    ping: () => get("ping"),

    // --------------------------------------------------------------- builds
    builds: () => get("builds"),
    emailBuild: (email: string, kind: string) =>
        send("builds/email", "POST", { email, build: kind }),
    setEmail: (email: string) => send("auth/email", "POST", { email }),

    async getTrackAudio(uuid: string): Promise<Blob> {
        const res = await fetch(API.streamUrl(uuid), { credentials: "same-origin" });
        if (!res.ok) throw new Error(`audio ${uuid} -> HTTP ${res.status}`);
        return res.blob();
    },

    async getTrackCover(uuid: string): Promise<Blob> {
        return (await fetch(this.getTrackCoverUrl(uuid), { credentials: "same-origin" })).blob();
    },

    async search(q: string, filter?: string[]): Promise<SearchItem[]> {
        const d = await get(`search?q=${encodeURIComponent(q)}`);
        const out: SearchItem[] = [];
        const want = (t: string) => !filter || filter.includes(t);
        if (want("artist")) {
            for (const a of d.artists ?? []) {
                out.push({
                    type: "artist",
                    uuid: artistUuid(a.artist, a.cover_id),
                    artist: artistFromJson(a.artist, a.cover_id ?? null),
                });
            }
        }
        if (want("set")) {
            for (const a of d.albums ?? []) {
                out.push({
                    type: "set",
                    uuid: albumUuid(a.album, a.cover_id),
                    set: setFromJson(a.album, [], a.cover_id ?? null, a.artist),
                    artist: artistStub(a.artist),
                });
            }
        }
        if (want("track")) {
            for (const t of d.tracks ?? []) {
                out.push({
                    type: "track",
                    uuid: String(t.id),
                    track: trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null),
                    set: t.album ? setFromJson(t.album, [], t.id, t.artist) : null,
                    artist: artistStub(t.artist),
                });
            }
        }
        return out;
    },

    requestDownload: (url: string) => send("requests", "POST", { url }),
    requests: () => get("requests"),

    // ------------------------------------------------------------ playlists
    listPlaylists: () => get("playlists"),

    async playlistTracks(id: number | string): Promise<{ id: number; name: string; tracks: Track[] }> {
        const d = await get(`playlists/${id}`);
        return {
            id: d.id,
            name: d.name ?? "",
            tracks: (d.tracks ?? []).map((t: ApiJson) =>
                trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null)),
        };
    },

    createPlaylist: (name: string) => send("playlists", "POST", { name }),
    renamePlaylist: (id: number | string, name: string) => send(`playlists/${id}`, "PATCH", { name }),
    deletePlaylist: (id: number | string) => send(`playlists/${id}`, "DELETE"),
    addToPlaylist: (id: number | string, trackId: number | string) =>
        send(`playlists/${id}/tracks`, "POST", { track_id: Number(trackId) }),
    removeFromPlaylist: (id: number | string, trackId: number | string) =>
        send(`playlists/${id}/tracks/${trackId}`, "DELETE"),

    // ------------------------------------------------------------- settings
    getSettings: () => get("settings"),
    saveSettings: (patch: Record<string, unknown>) => send("settings", "PUT", patch),
    changePassword: (oldPw: string, newPw: string) =>
        send("password", "POST", { old: oldPw, new: newPw }),

    // ---------------------------------------------------------- linked accounts
    roturStatus: async (): Promise<RoturStatus> => (await get("auth/rotur/status")) as RoturStatus,
    roturUnlink: () => send("auth/rotur/unlink", "POST"),
    roturAuthorizeUrl: (next = "/settings") =>
        `${BASE}/auth/rotur/authorize?next=${encodeURIComponent(next)}`,
    roturActivity: (body: { track_id: number | string | null; playing: boolean; position?: number }) =>
        send("auth/rotur/activity", "POST", body),

    discordStatus: () => get("auth/discord/status"),
    discordUnlink: () => send("auth/discord/unlink", "POST"),
    discordAuthorizeUrl: (next = "/settings") =>
        `${BASE}/auth/discord/authorize?next=${encodeURIComponent(next)}`,
    discordActivity: (body: { track_id: number | string | null; playing: boolean; position?: number }) =>
        send("auth/discord/activity", "POST", body),

    // -------------------------------------------------------- control channels
    channels: (state = false) => get(`channels${state ? "?state=1" : ""}`),
    bindChannel: (body: { platform: string; channel_id: string; mode?: string; guild_id?: string }) =>
        send("channels", "POST", body),
    unbindChannel: (id: number) => send(`channels/${id}`, "DELETE"),
    channelState: (id: number) => get(`channels/${id}/state`),

    // -------------------------------------------------------------- devices
    deviceCode: () => send("devices/code", "POST"),
    devices: () => get("devices"),
    activateDevice: (id: number) => send(`devices/${id}/activate`, "POST"),
    renameDevice: (id: number, name: string) => send(`devices/${id}`, "PATCH", { name }),
    forgetDevice: (id: number) => send(`devices/${id}`, "DELETE"),
    clearDevices: () => send("devices/clear", "POST"),
    cleanupDevices: () => send("devices/cleanup", "POST"),
    deviceTokens: () => get("devices/tokens"),
    revokeDeviceToken: (id: number) => send(`devices/tokens/${id}/revoke`, "POST"),

    // ---------------------------------------------------------------- admin
    adminStats: () => get("admin/stats"),
    adminMetrics: () => get("admin/metrics"),
    adminHistory: (id: number, limit = 100) => get(`admin/history/${id}?limit=${limit}`),
    adminDevices: () => get("admin/devices"),
    adminEnrich: () => get("admin/enrich"),
    startEnrich: (force = false) => send("admin/enrich", "POST", { force }),
    adminLyrics: () => get("admin/lyrics"),
    startLyrics: () => send("admin/lyrics", "POST"),
    adminRooms: () => get("admin/rooms"),
    adminCloseRoom: (code: string) => send(`admin/rooms/${encodeURIComponent(code)}`, "DELETE"),
    adminRequests: () => get("admin/requests"),
    adminRequestLog: (id: number) => get(`admin/requests/${id}/log?tail=20000`),
    adminReqAction: (id: number, action: "approve" | "reject") => send(`requests/${id}/${action}`, "POST"),
    adminReqCancel: (id: number) => send(`admin/requests/${id}/cancel`, "POST"),
    adminReqRetry: (id: number) => send(`admin/requests/${id}/retry`, "POST"),
    adminReqDelete: (id: number) => send(`admin/requests/${id}`, "DELETE"),
    adminUsers: () => get("admin/users"),
    adminSetAdmin: (id: number, isAdmin: boolean) =>
        send(`admin/users/${id}/admin`, "POST", { is_admin: isAdmin }),
    adminDeleteUser: (id: number) => send(`admin/users/${id}`, "DELETE"),
    adminInviteCodes: () => get("admin/invite-codes"),
    adminCreateInvite: (data: { uses?: number; hours?: number; note?: string; for_user?: string }) =>
        send("admin/invite-codes", "POST", data),
    adminRevokeInvite: (id: number) => send(`admin/invite-codes/${id}`, "DELETE"),
    adminScan: () => send("admin/scan", "POST"),

    // The library is server-side; this UI has no upload/delete endpoints.
    uploadTrack: (): Promise<string> => Promise.reject(new Error("uploads are not supported")),
    uploadSet: (): Promise<string> => Promise.reject(new Error("uploads are not supported")),
    uploadArtist: (): Promise<string> => Promise.reject(new Error("uploads are not supported")),
    deleteTrack: (): Promise<void> => Promise.reject(new Error("deletes are not supported")),
    deleteSet: (): Promise<void> => Promise.reject(new Error("deletes are not supported")),
    deleteArtist: (): Promise<void> => Promise.reject(new Error("deletes are not supported")),
};

export type { Option };
```

### `ui/src/common/prefs.ts`

```ts
import { signal } from "@preact/signals";
import { API } from "./net/api";
import {
    applyIconStyle, applyPalette, DEFAULT_ACCENT, DEFAULT_ICON_FILLED,
    DEFAULT_ICON_STROKE, DEFAULT_PALETTE, DESIGN_MOTION, normalizeIconStroke,
    type IconStroke,
} from "./theme";

// Server-stored preferences. The v3 client honours the ones that change what
// it renders/plays; the rest are kept for the Android/Qt/legacy clients.
export const volume = signal(0.8);

/** Appearance is applied as soon as its signal changes; `applyPalette` writes
 *  inline vars on <html> so it beats flufi-ui's later `:root` block. */
export const palette = signal<string>(DEFAULT_PALETTE);
export const accentOverride = signal<string>(DEFAULT_ACCENT);
palette.subscribe(id => applyPalette(id, accentOverride.peek()));
accentOverride.subscribe(accent => applyPalette(palette.peek(), accent));

export function setPalettePreference(id: string) {
    palette.value = String(id ?? "").trim() || DEFAULT_PALETTE;
}

/** An empty accent means "use the palette's own accent". */
export function setAccentPreference(accent: string) {
    accentOverride.value = String(accent ?? "").trim();
}

/** Icon width/fill follow the same immediate-apply pattern as palette. */
export const iconStroke = signal<IconStroke>(DEFAULT_ICON_STROKE);
export const iconFilled = signal<boolean>(DEFAULT_ICON_FILLED);
iconStroke.subscribe(scale => applyIconStyle(scale, iconFilled.peek()));
iconFilled.subscribe(filled => applyIconStyle(iconStroke.peek(), filled));

export function setIconStrokePreference(value: unknown) {
    iconStroke.value = normalizeIconStroke(value);
}

export function setIconFilledPreference(value: unknown) {
    iconFilled.value = !!value;
}

export const covers = signal(true);
export const hideExplicit = signal(false);
/** Keep played tracks in the browser's browse cache for offline playback. */
export const offlineAudio = signal(false);
/** Mirrors the server flags the player needs to publish listening activity. */
export const roturActivity = signal(false);
export const discordActivity = signal(false);
/** Autoplay is on by default; a local choice (queue toggle/repeat) wins over
 *  the server default so a reload doesn't silently turn it back on. */
function localAutoplayValue(): string | null {
    try { return localStorage.getItem("mcmusic:autoplay"); } catch { return null; }
}
function localAutoplay(): boolean {
    const v = localAutoplayValue();
    return v == null ? true : v === "true";
}
export const autoplay = signal(localAutoplay());
export function setAutoplayPreference(on: boolean) {
    autoplay.value = on;
    try { localStorage.setItem("mcmusic:autoplay", on ? "true" : "false"); } catch { /* noop */ }
}

/** Playful motion is local to this device: the server's settings whitelist does
 *  not carry it yet, so it never becomes a phantom server preference. */
const PLAYFUL_KEY = `mcmusic:${DESIGN_MOTION.settingsKey}`;
function localPlayfulMotion(): boolean {
    try {
        const value = localStorage.getItem(PLAYFUL_KEY);
        return value == null ? DESIGN_MOTION.defaultEnabled : value === "true";
    } catch {
        return DESIGN_MOTION.defaultEnabled;
    }
}
export const playfulMotion = signal(localPlayfulMotion());
export function setPlayfulMotionPreference(on: boolean) {
    playfulMotion.value = on;
    try { localStorage.setItem(PLAYFUL_KEY, on ? "true" : "false"); } catch { /* noop */ }
}
function applyPlayfulMotion(on: boolean) {
    if (typeof document === "undefined") return;
    document.documentElement.dataset.playful = on ? "true" : "false";
}
playfulMotion.subscribe(applyPlayfulMotion);
applyPlayfulMotion(playfulMotion.peek());

export function prefersReducedMotion(): boolean {
    return typeof window !== "undefined" && typeof window.matchMedia === "function"
        && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export type Settings = Record<string, any>;

export async function loadPrefs(): Promise<Settings | null> {
    try {
        const s = await API.getSettings();
        volume.value = Math.min(1, Math.max(0, Number(s.volume ?? 0.8)));
        covers.value = s.covers !== false;
        hideExplicit.value = !!s.hide_explicit;
        offlineAudio.value = s.offline_audio === true;
        roturActivity.value = !!s.rotur_activity;
        discordActivity.value = !!s.discord_activity;
        setPalettePreference(typeof s.theme === "string" ? s.theme : DEFAULT_PALETTE);
        setAccentPreference(typeof s.accent === "string" ? s.accent : DEFAULT_ACCENT);
        setIconStrokePreference(s.iconStroke);
        setIconFilledPreference(s.iconFilled);
        if (s.autoplay != null && localAutoplayValue() == null)
            autoplay.value = s.autoplay !== false;
        return s;
    } catch {
        return null;
    }
}

export function applyPrefs(s: Settings) {
    if (s.volume != null) volume.value = Math.min(1, Math.max(0, Number(s.volume)));
    if (s.covers != null) covers.value = !!s.covers;
    if (s.hide_explicit != null) hideExplicit.value = !!s.hide_explicit;
    if (s.offline_audio != null) offlineAudio.value = !!s.offline_audio;
    if (s.rotur_activity != null) roturActivity.value = !!s.rotur_activity;
    if (s.discord_activity != null) discordActivity.value = !!s.discord_activity;
    if (s.theme != null) setPalettePreference(String(s.theme));
    if (s.accent != null) setAccentPreference(String(s.accent));
    if (s.iconStroke != null) setIconStrokePreference(s.iconStroke);
    if (s.iconFilled != null) setIconFilledPreference(s.iconFilled);
    if (s.autoplay != null && localAutoplayValue() == null) autoplay.value = s.autoplay !== false;
}
```

### `ui/src/common/theme.ts`

```ts
/** The five palette families shared by the v3 SPA and the embed widgets.
 *
 * A bare family id (violet, indigo, ...) follows the visitor's
 * prefers-color-scheme; `*-light` / `*-dark` pin one half of the sheet. Legacy
 * ids stay as aliases so old server settings and embed tags keep working.
 *
 * flufi-ui declares its own `:root` tokens after the client stylesheet, so a
 * client `:root` rule loses at equal specificity. `applyPalette()` therefore
 * writes inline custom properties on <html>, which always win, and mirrors the
 * resolved half into `data-palette`, `color-scheme` and the theme-color meta.
 */

import {
  Hct,
  SchemeTonalSpot,
  TonalPalette,
  argbFromHex,
  hexFromArgb,
} from "@material/material-color-utilities";

// BEGIN GENERATED PALETTE DATA
export type PaletteMode = "light" | "dark";
export type FamilyId = "violet" | "indigo" | "sky" | "aqua" | "mint";

export const DESIGN_SHAPE = {"xs":4,"sm":8,"md":12,"lg":16,"xl":28,"xxl":36,"pill":999,"coverMin":20,"coverMax":28,"card":28,"hero":36,"touchTarget":48} as const;
export const DESIGN_SPACING = {"unit":4} as const;
export const DESIGN_MOTION = {"spring":{"stiffness":"medium","damping":0.7},"pressScale":0.96,"morphMs":320,"progressWaveHz":0.55,"progressWavePx":3,"settingsKey":"playfulMotion","defaultEnabled":true,"reducedMotion":"honour platform setting and disable springs, morphs and waves"} as const;
export const DESIGN_TYPE = {"display":{"size":36,"weight":700,"line":44},"headline":{"size":28,"weight":700,"line":36},"title":{"size":22,"weight":700,"line":28},"body":{"size":16,"weight":400,"line":24},"label":{"size":14,"weight":600,"line":20}} as const;

export interface PaletteTokens {
    // Legacy swatches: unchanged bytes for stored palette ids.
    bg: string; bg2: string; surface: string; surface2: string;
    fg: string; dim: string; dim2: string; line: string; line2: string;
    accent: string; accentText: string; accentFg: string;
    // Generated Material 3 tonal roles (HCT from this family's accent seed).
    primary: string;
    onPrimary: string;
    primaryContainer: string;
    onPrimaryContainer: string;
    secondary: string;
    onSecondary: string;
    secondaryContainer: string;
    onSecondaryContainer: string;
    tertiary: string;
    onTertiary: string;
    tertiaryContainer: string;
    onTertiaryContainer: string;
    error: string;
    onError: string;
    errorContainer: string;
    onErrorContainer: string;
    background: string;
    onBackground: string;
    onSurface: string;
    surfaceVariant: string;
    onSurfaceVariant: string;
    surfaceContainerLowest: string;
    surfaceContainerLow: string;
    surfaceContainer: string;
    surfaceContainerHigh: string;
    surfaceContainerHighest: string;
    outline: string;
    outlineVariant: string;
    inverseSurface: string;
    inverseOnSurface: string;
    inversePrimary: string;
    scrim: string;
    shadow: string;
}

export interface Palette extends PaletteTokens {
    /** Concrete id, e.g. `violet-dark`. */
    id: string;
    family: FamilyId;
    mode: PaletteMode;
}

export interface PaletteFamily {
    id: FamilyId;
    name: string;
    light: PaletteTokens;
    dark: PaletteTokens;
}

/** Generated Material 3 role names, exported for CSS variable mirroring. */
export const M3_ROLE_NAMES = ["primary","onPrimary","primaryContainer","onPrimaryContainer","secondary","onSecondary","secondaryContainer","onSecondaryContainer","tertiary","onTertiary","tertiaryContainer","onTertiaryContainer","error","onError","errorContainer","onErrorContainer","background","onBackground","onSurface","surfaceVariant","onSurfaceVariant","surfaceContainerLowest","surfaceContainerLow","surfaceContainer","surfaceContainerHigh","surfaceContainerHighest","outline","outlineVariant","inverseSurface","inverseOnSurface","inversePrimary","scrim","shadow"] as const;

/** CSS custom property for each generated Material 3 role. */
export const M3_CSS_VARS: Record<string, keyof PaletteTokens> = {
    "--md-primary": "primary",
    "--md-on-primary": "onPrimary",
    "--md-primary-container": "primaryContainer",
    "--md-on-primary-container": "onPrimaryContainer",
    "--md-secondary": "secondary",
    "--md-on-secondary": "onSecondary",
    "--md-secondary-container": "secondaryContainer",
    "--md-on-secondary-container": "onSecondaryContainer",
    "--md-tertiary": "tertiary",
    "--md-on-tertiary": "onTertiary",
    "--md-tertiary-container": "tertiaryContainer",
    "--md-on-tertiary-container": "onTertiaryContainer",
    "--md-error": "error",
    "--md-on-error": "onError",
    "--md-error-container": "errorContainer",
    "--md-on-error-container": "onErrorContainer",
    "--md-background": "background",
    "--md-on-background": "onBackground",
    "--md-on-surface": "onSurface",
    "--md-surface-variant": "surfaceVariant",
    "--md-on-surface-variant": "onSurfaceVariant",
    "--md-surface-container-lowest": "surfaceContainerLowest",
    "--md-surface-container-low": "surfaceContainerLow",
    "--md-surface-container": "surfaceContainer",
    "--md-surface-container-high": "surfaceContainerHigh",
    "--md-surface-container-highest": "surfaceContainerHighest",
    "--md-outline": "outline",
    "--md-outline-variant": "outlineVariant",
    "--md-inverse-surface": "inverseSurface",
    "--md-inverse-on-surface": "inverseOnSurface",
    "--md-inverse-primary": "inversePrimary",
    "--md-scrim": "scrim",
    "--md-shadow": "shadow",
};

export const PALETTE_FAMILIES: readonly PaletteFamily[] = [
    {
        id: "violet",
        name: "Violet",
        light: {
            bg: "#F5F2FF",
            bg2: "#EDE7FF",
            surface: "#FFFFFF",
            surface2: "#F7F4FF",
            fg: "#08060D",
            dim: "#473872",
            dim2: "#6A54AA",
            line: "#DACDFF",
            line2: "#CAB8FF",
            accent: "#9F7EFF",
            accentText: "#5B3F9E",
            accentFg: "#08060D",
            primary: "#64558F",
            onPrimary: "#FFFFFF",
            primaryContainer: "#E8DDFF",
            onPrimaryContainer: "#4C3E76",
            secondary: "#615B71",
            onSecondary: "#FFFFFF",
            secondaryContainer: "#E8DEF8",
            onSecondaryContainer: "#494458",
            tertiary: "#7D5261",
            onTertiary: "#FFFFFF",
            tertiaryContainer: "#FFD9E3",
            onTertiaryContainer: "#633B49",
            error: "#BA1A1A",
            onError: "#FFFFFF",
            errorContainer: "#FFDAD6",
            onErrorContainer: "#93000A",
            background: "#FFFBFF",
            onBackground: "#1D1927",
            onSurface: "#1D1927",
            surfaceVariant: "#E7DFF3",
            onSurfaceVariant: "#494454",
            surfaceContainerLowest: "#FFFBFF",
            surfaceContainerLow: "#F8F1FF",
            surfaceContainer: "#F3EAFE",
            surfaceContainerHigh: "#EDE5F9",
            surfaceContainerHighest: "#E7DFF3",
            outline: "#79757F",
            outlineVariant: "#878192",
            inverseSurface: "#322E3D",
            inverseOnSurface: "#F5EEFF",
            inversePrimary: "#CEBDFE",
            scrim: "#000000",
            shadow: "#000000",
        },
        dark: {
            bg: "#171721",
            bg2: "#222130",
            surface: "#2A293C",
            surface2: "#444361",
            fg: "#FFFFFF",
            dim: "#AAAAB7",
            dim2: "#8B8A9D",
            line: "#35344B",
            line2: "#605F78",
            accent: "#9F7EFF",
            accentText: "#C6B2FF",
            accentFg: "#08060D",
            primary: "#CEBDFE",
            onPrimary: "#35275D",
            primaryContainer: "#4C3E76",
            onPrimaryContainer: "#E8DDFF",
            secondary: "#CBC3DC",
            onSecondary: "#332E41",
            secondaryContainer: "#494458",
            onSecondaryContainer: "#E8DEF8",
            tertiary: "#EFB8C9",
            onTertiary: "#492533",
            tertiaryContainer: "#633B49",
            onTertiaryContainer: "#FFD9E3",
            error: "#FFB4AB",
            onError: "#690005",
            errorContainer: "#93000A",
            onErrorContainer: "#FFDAD6",
            background: "#15111F",
            onBackground: "#F5EEFF",
            onSurface: "#F5EEFF",
            surfaceVariant: "#3B3746",
            onSurfaceVariant: "#CBC3D6",
            surfaceContainerLowest: "#0F0C19",
            surfaceContainerLow: "#1D1927",
            surfaceContainer: "#211E2B",
            surfaceContainerHigh: "#2C2836",
            surfaceContainerHighest: "#373341",
            outline: "#938F99",
            outlineVariant: "#878192",
            inverseSurface: "#F5EEFF",
            inverseOnSurface: "#322E3D",
            inversePrimary: "#64558F",
            scrim: "#000000",
            shadow: "#000000",
        },
    },
    {
        id: "indigo",
        name: "Indigo",
        light: {
            bg: "#F2F4FF",
            bg2: "#E8EBFF",
            surface: "#FFFFFF",
            surface2: "#F5F6FF",
            fg: "#08060D",
            dim: "#3B4172",
            dim2: "#5761AA",
            line: "#CFD5FF",
            line2: "#BAC3FF",
            accent: "#8293FF",
            accentText: "#4A56A8",
            accentFg: "#08060D",
            primary: "#525A92",
            onPrimary: "#FFFFFF",
            primaryContainer: "#DEE0FF",
            onPrimaryContainer: "#3A4379",
            secondary: "#5B5D72",
            onSecondary: "#FFFFFF",
            secondaryContainer: "#E0E1F9",
            onSecondaryContainer: "#434559",
            tertiary: "#77536D",
            onTertiary: "#FFFFFF",
            tertiaryContainer: "#FFD7F1",
            onTertiaryContainer: "#5D3C54",
            error: "#BA1A1A",
            onError: "#FFFFFF",
            errorContainer: "#FFDAD6",
            onErrorContainer: "#93000A",
            background: "#FFFBFF",
            onBackground: "#191B26",
            onSurface: "#191B26",
            surfaceVariant: "#E2E1F2",
            onSurfaceVariant: "#454653",
            surfaceContainerLowest: "#FFFBFF",
            surfaceContainerLow: "#F4F2FF",
            surfaceContainer: "#EDECFD",
            surfaceContainerHigh: "#E7E7F7",
            surfaceContainerHighest: "#E2E1F2",
            outline: "#767680",
            outlineVariant: "#828391",
            inverseSurface: "#2E303C",
            inverseOnSurface: "#F0EFFF",
            inversePrimary: "#BBC3FF",
            scrim: "#000000",
            shadow: "#000000",
        },
        dark: {
            bg: "#12171F",
            bg2: "#1B212D",
            surface: "#212838",
            surface2: "#36425B",
            fg: "#FFFFFF",
            dim: "#A4A9B5",
            dim2: "#828999",
            line: "#2A3346",
            line2: "#545E73",
            accent: "#8293FF",
            accentText: "#B4BEFF",
            accentFg: "#08060D",
            primary: "#BBC3FF",
            onPrimary: "#232C61",
            primaryContainer: "#3A4379",
            onPrimaryContainer: "#DEE0FF",
            secondary: "#C4C5DD",
            onSecondary: "#2D2F42",
            secondaryContainer: "#434559",
            onSecondaryContainer: "#E0E1F9",
            tertiary: "#E6BAD7",
            onTertiary: "#45263D",
            tertiaryContainer: "#5D3C54",
            onTertiaryContainer: "#FFD7F1",
            error: "#FFB4AB",
            onError: "#690005",
            errorContainer: "#93000A",
            onErrorContainer: "#FFDAD6",
            background: "#11131E",
            onBackground: "#F0EFFF",
            onSurface: "#F0EFFF",
            surfaceVariant: "#373845",
            onSurfaceVariant: "#C5C5D5",
            surfaceContainerLowest: "#0C0D18",
            surfaceContainerLow: "#191B26",
            surfaceContainer: "#1D1F2B",
            surfaceContainerHigh: "#282935",
            surfaceContainerHighest: "#333440",
            outline: "#90909A",
            outlineVariant: "#828391",
            inverseSurface: "#F0EFFF",
            inverseOnSurface: "#2E303C",
            inversePrimary: "#525A92",
            scrim: "#000000",
            shadow: "#000000",
        },
    },
    {
        id: "sky",
        name: "Sky",
        light: {
            bg: "#F1F8FE",
            bg2: "#E7F3FE",
            surface: "#FFFFFF",
            surface2: "#F4F9FE",
            fg: "#08060D",
            dim: "#385272",
            dim2: "#527CA9",
            line: "#CCE5FE",
            line2: "#B6DAFE",
            accent: "#7BBDFE",
            accentText: "#235F93",
            accentFg: "#08060D",
            primary: "#32628D",
            onPrimary: "#FFFFFF",
            primaryContainer: "#CFE5FF",
            onPrimaryContainer: "#134A74",
            secondary: "#526070",
            onSecondary: "#FFFFFF",
            secondaryContainer: "#D6E4F7",
            onSecondaryContainer: "#3A4857",
            tertiary: "#695779",
            onTertiary: "#FFFFFF",
            tertiaryContainer: "#F0DBFF",
            onTertiaryContainer: "#514060",
            error: "#BA1A1A",
            onError: "#FFFFFF",
            errorContainer: "#FFDAD6",
            onErrorContainer: "#93000A",
            background: "#FCFCFF",
            onBackground: "#161C23",
            onSurface: "#161C23",
            surfaceVariant: "#DDE3ED",
            onSurfaceVariant: "#41474F",
            surfaceContainerLowest: "#FCFCFF",
            surfaceContainerLow: "#EEF4FE",
            surfaceContainer: "#E9EEF8",
            surfaceContainerHigh: "#E3E8F2",
            surfaceContainerHighest: "#DDE3ED",
            outline: "#73777F",
            outlineVariant: "#7E848D",
            inverseSurface: "#2B3138",
            inverseOnSurface: "#ECF1FB",
            inversePrimary: "#9DCBFC",
            scrim: "#000000",
            shadow: "#000000",
        },
        dark: {
            bg: "#182127",
            bg2: "#222F39",
            surface: "#2A3A46",
            surface2: "#455F72",
            fg: "#FFFFFF",
            dim: "#ABB7BF",
            dim2: "#8B9BA7",
            line: "#354A58",
            line2: "#607787",
            accent: "#7BBDFE",
            accentText: "#A9D5FF",
            accentFg: "#08060D",
            primary: "#9DCBFC",
            onPrimary: "#003355",
            primaryContainer: "#134A74",
            onPrimaryContainer: "#CFE5FF",
            secondary: "#BAC8DA",
            onSecondary: "#243240",
            secondaryContainer: "#3A4857",
            onSecondaryContainer: "#D6E4F7",
            tertiary: "#D4BEE6",
            onTertiary: "#392A49",
            tertiaryContainer: "#514060",
            onTertiaryContainer: "#F0DBFF",
            error: "#FFB4AB",
            onError: "#690005",
            errorContainer: "#93000A",
            onErrorContainer: "#FFDAD6",
            background: "#0E141B",
            onBackground: "#ECF1FB",
            onSurface: "#ECF1FB",
            surfaceVariant: "#343A41",
            onSurfaceVariant: "#C1C7D0",
            surfaceContainerLowest: "#090F15",
            surfaceContainerLow: "#161C23",
            surfaceContainer: "#1A2027",
            surfaceContainerHigh: "#242A32",
            surfaceContainerHighest: "#2F353D",
            outline: "#8C9199",
            outlineVariant: "#7E848D",
            inverseSurface: "#ECF1FB",
            inverseOnSurface: "#2B3138",
            inversePrimary: "#32628D",
            scrim: "#000000",
            shadow: "#000000",
        },
    },
    {
        id: "aqua",
        name: "Aqua",
        light: {
            bg: "#F1FBFC",
            bg2: "#E7F9FA",
            surface: "#FFFFFF",
            surface2: "#F4FCFD",
            fg: "#08060D",
            dim: "#386168",
            dim2: "#53939A",
            line: "#CDF3F5",
            line2: "#B6EDF1",
            accent: "#7CE0E6",
            accentText: "#126F77",
            accentFg: "#08060D",
            primary: "#00696E",
            onPrimary: "#FFFFFF",
            primaryContainer: "#9CF0F6",
            onPrimaryContainer: "#004F53",
            secondary: "#4A6364",
            onSecondary: "#FFFFFF",
            secondaryContainer: "#CCE8E9",
            onSecondaryContainer: "#324B4C",
            tertiary: "#4E5F7D",
            onTertiary: "#FFFFFF",
            tertiaryContainer: "#D6E3FF",
            onTertiaryContainer: "#364764",
            error: "#BA1A1A",
            onError: "#FFFFFF",
            errorContainer: "#FFDAD6",
            onErrorContainer: "#93000A",
            background: "#F4FEFE",
            onBackground: "#141D1E",
            onSurface: "#141D1E",
            surfaceVariant: "#DAE4E5",
            onSurfaceVariant: "#3F4949",
            surfaceContainerLowest: "#F4FEFE",
            surfaceContainerLow: "#EBF6F6",
            surfaceContainer: "#E6F0F0",
            surfaceContainerHigh: "#E0EAEA",
            surfaceContainerHighest: "#DAE4E5",
            outline: "#6F7979",
            outlineVariant: "#7C8686",
            inverseSurface: "#293233",
            inverseOnSurface: "#E9F3F3",
            inversePrimary: "#80D4D9",
            scrim: "#000000",
            shadow: "#000000",
        },
        dark: {
            bg: "#15241C",
            bg2: "#1F3328",
            surface: "#263F32",
            surface2: "#3E6751",
            fg: "#FFFFFF",
            dim: "#A8BAB0",
            dim2: "#87A093",
            line: "#30503F",
            line2: "#5A7D6B",
            accent: "#7CE0E6",
            accentText: "#A6EFF3",
            accentFg: "#08060D",
            primary: "#80D4D9",
            onPrimary: "#003739",
            primaryContainer: "#004F53",
            onPrimaryContainer: "#9CF0F6",
            secondary: "#B1CCCD",
            onSecondary: "#1B3436",
            secondaryContainer: "#324B4C",
            onSecondaryContainer: "#CCE8E9",
            tertiary: "#B6C7E9",
            onTertiary: "#1F314C",
            tertiaryContainer: "#364764",
            onTertiaryContainer: "#D6E3FF",
            error: "#FFB4AB",
            onError: "#690005",
            errorContainer: "#93000A",
            onErrorContainer: "#FFDAD6",
            background: "#0C1516",
            onBackground: "#E9F3F3",
            onSurface: "#E9F3F3",
            surfaceVariant: "#313B3B",
            onSurfaceVariant: "#BEC8C9",
            surfaceContainerLowest: "#071010",
            surfaceContainerLow: "#141D1E",
            surfaceContainer: "#182122",
            surfaceContainerHigh: "#222C2C",
            surfaceContainerHighest: "#2D3637",
            outline: "#899393",
            outlineVariant: "#7C8686",
            inverseSurface: "#E9F3F3",
            inverseOnSurface: "#293233",
            inversePrimary: "#00696E",
            scrim: "#000000",
            shadow: "#000000",
        },
    },
    {
        id: "mint",
        name: "Mint",
        light: {
            bg: "#F1FFF5",
            bg2: "#E7FFEE",
            surface: "#FFFFFF",
            surface2: "#F4FFF7",
            fg: "#08060D",
            dim: "#386E4C",
            dim2: "#52A76F",
            line: "#CCFFDC",
            line2: "#B6FFCC",
            accent: "#7BFFA4",
            accentText: "#216A43",
            accentFg: "#08060D",
            primary: "#316A42",
            onPrimary: "#FFFFFF",
            primaryContainer: "#B3F1BF",
            onPrimaryContainer: "#16512C",
            secondary: "#506352",
            onSecondary: "#FFFFFF",
            secondaryContainer: "#D2E8D3",
            onSecondaryContainer: "#394B3C",
            tertiary: "#3A656E",
            onTertiary: "#FFFFFF",
            tertiaryContainer: "#BDEAF5",
            onTertiaryContainer: "#204D56",
            error: "#BA1A1A",
            onError: "#FFFFFF",
            errorContainer: "#FFDAD6",
            onErrorContainer: "#93000A",
            background: "#F5FFF3",
            onBackground: "#121E14",
            onSurface: "#121E14",
            surfaceVariant: "#D7E7D6",
            onSurfaceVariant: "#3C4A3E",
            surfaceContainerLowest: "#F5FFF3",
            surfaceContainerLow: "#E8F8E7",
            surfaceContainer: "#E3F2E1",
            surfaceContainerHigh: "#DDECDC",
            surfaceContainerHighest: "#D7E7D6",
            outline: "#717971",
            outlineVariant: "#798879",
            inverseSurface: "#263428",
            inverseOnSurface: "#E5F5E4",
            inversePrimary: "#98D5A4",
            scrim: "#000000",
            shadow: "#000000",
        },
        dark: {
            bg: "#15241A",
            bg2: "#1F3425",
            surface: "#26412E",
            surface2: "#3E694B",
            fg: "#FFFFFF",
            dim: "#A8BBAE",
            dim2: "#87A28F",
            line: "#30513A",
            line2: "#5A7F66",
            accent: "#7BFFA4",
            accentText: "#A9FFC2",
            accentFg: "#08060D",
            primary: "#98D5A4",
            onPrimary: "#00391A",
            primaryContainer: "#16512C",
            onPrimaryContainer: "#B3F1BF",
            secondary: "#B7CCB7",
            onSecondary: "#223526",
            secondaryContainer: "#394B3C",
            onSecondaryContainer: "#D2E8D3",
            tertiary: "#A2CED9",
            onTertiary: "#01363F",
            tertiaryContainer: "#204D56",
            onTertiaryContainer: "#BDEAF5",
            error: "#FFB4AB",
            onError: "#690005",
            errorContainer: "#93000A",
            onErrorContainer: "#FFDAD6",
            background: "#0A160D",
            onBackground: "#E5F5E4",
            onSurface: "#E5F5E4",
            surfaceVariant: "#2F3C31",
            onSurfaceVariant: "#BBCBBB",
            surfaceContainerLowest: "#051108",
            surfaceContainerLow: "#121E14",
            surfaceContainer: "#162218",
            surfaceContainerHigh: "#202D22",
            surfaceContainerHighest: "#2B382D",
            outline: "#8B938A",
            outlineVariant: "#798879",
            inverseSurface: "#E5F5E4",
            inverseOnSurface: "#263428",
            inversePrimary: "#316A42",
            scrim: "#000000",
            shadow: "#000000",
        },
    },
];

function concrete(family: PaletteFamily, mode: PaletteMode): Palette {
    const tokens = family[mode];
    return {
        ...tokens,
        id: family.id + "-" + mode,
        family: family.id,
        mode,
    };
}

/** Every pinned half of every family, keyed by its concrete id. */
export const PALETTE_VARIANTS: Record<string, Palette> = Object.fromEntries(
    PALETTE_FAMILIES.flatMap(f => ([
        [f.id + "-light", concrete(f, "light")] as [string, Palette],
        [f.id + "-dark", concrete(f, "dark")] as [string, Palette],
    ])),
);

/** Legacy settings/embed ids. Aliases resolve to a concrete variant where the
 *  old name already implied light or dark; bare family names stay adaptive. */
export const PALETTE_ALIASES: Record<string, string> = {
    "": "violet",
    "auto": "violet",
    "system": "violet",
    "flufi": "violet-dark",
    "dark": "violet-dark",
    "dusk": "violet-dark",
    "paper": "violet-light",
    "light": "violet-light",
    "ink": "indigo-dark",
    "amoled": "indigo-dark",
    "midnight": "sky-dark",
    "tide": "aqua-dark",
    "forest": "mint-dark",
    "rose": "violet-dark",
    "copper": "violet-dark",
    "mocha": "violet-dark",
};
// END GENERATED PALETTE DATA

export const DEFAULT_PALETTE = "violet";
export const DEFAULT_ACCENT = "";

/** Lucide width choices, shared by web/iOS/Qt and the server schema. */
export const ICON_STROKE_CHOICES = [1, 1.5, 2] as const;
export type IconStroke = (typeof ICON_STROKE_CHOICES)[number];
export const DEFAULT_ICON_STROKE: IconStroke = 1;
export const DEFAULT_ICON_FILLED = false;

/** Snap stored or hand-edited values onto the three allowed widths. */
export function normalizeIconStroke(value: unknown): IconStroke {
    const requested = Number(value);
    if (!Number.isFinite(requested)) return DEFAULT_ICON_STROKE;
    return ICON_STROKE_CHOICES.reduce<IconStroke>(
        (best, choice) =>
            Math.abs(choice - requested) < Math.abs(best - requested) ? choice : best,
        DEFAULT_ICON_STROKE,
    );
}

/** Rendered pixels for a Lucide glyph at `size` px and `scale` multiplier.
 *  1x is Lucide's default 2-unit stroke, so the rendered width is
 *  `size * scale / 12`. The `size / 6` ceiling keeps 2x from crowding tiny
 *  icons; there is no pixel floor, so small icons still change visibly. */
export function iconStrokeWidth(scale: number, size: number): number {
    const requested = Number(size);
    const logical = Number.isFinite(requested) && requested > 0 ? requested : 24;
    return Math.min(logical * Number(scale) / 12, logical / 6);
}

/** lucide-preact's strokeWidth prop is in viewBox units, not pixels. */
export function lucideStrokeWidth(scale: number, size: number): number {
    const requested = Number(size);
    const logical = Number.isFinite(requested) && requested > 0 ? requested : 24;
    return iconStrokeWidth(scale, logical) * 24 / logical;
}

/** Expose the preference for CSS and non-React surfaces. */
export function applyIconStyle(scale: IconStroke, filled: boolean): void {
    if (typeof document === "undefined") return;
    const root = document.documentElement;
    root.style.setProperty("--icon-stroke-scale", String(scale));
    root.dataset.iconFilled = filled ? "true" : "false";
}

/** Shared status colours, kept here so UI code never hardcodes a hex. */
const SUCCESS = "#1DB954";
const WARNING = "#FFBF69";

/** Fallbacks for canvas code, which cannot consume CSS custom properties. */
export const DEFAULT_ACCENT_RGB = "159, 126, 255";
export const DEFAULT_BACK_RGB = "23, 23, 33";

function darkPreferred(): boolean {
    return typeof window !== "undefined" && typeof window.matchMedia === "function"
        && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

/** Map a stored id/alias to a concrete token set. Bare families resolve with
 *  the current system preference. */
export function resolvePalette(id: string | null | undefined): Palette {
    const key = String(id ?? "").trim().toLowerCase();
    const resolved = PALETTE_ALIASES[key] ?? key;
    const pinned = PALETTE_VARIANTS[resolved];
    if (pinned) return pinned;
    const family = PALETTE_FAMILIES.find(f => f.id === resolved);
    if (family) return concrete(family, darkPreferred() ? "dark" : "light");
    return resolvePalette(DEFAULT_PALETTE);
}

/** Ink or white, whichever reads better on an arbitrary accent fill. */
function readableOn(hex: string): string {
    const channel = (value: number) => {
        const v = value / 255;
        return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    };
    const luminance = (color: string) => {
        const r = channel(parseInt(color.slice(1, 3), 16));
        const g = channel(parseInt(color.slice(3, 5), 16));
        const b = channel(parseInt(color.slice(5, 7), 16));
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    const fill = luminance(hex);
    const ink = luminance("#08060D");
    const white = luminance("#FFFFFF");
    const ratio = (a: number, b: number) =>
        (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    return ratio(ink, fill) >= ratio(white, fill) ? "#08060D" : "#FFFFFF";
}

/** Derive flat M3 roles from an arbitrary seed. Used by accent overrides and
 *  by the cover-dominant-colour pass in Phase 1. Invalid seeds keep the
 *  family's generated roles. */
export function rolesFromSeed(seed: string, mode: PaletteMode): Partial<PaletteTokens> {
    const match = /^#?([0-9a-f]{6})$/i.exec(seed.trim());
    if (!match) return {};
    const source = Hct.fromInt(argbFromHex(`#${match[1]}`));
    const dark = mode === "dark";
    const scheme = new SchemeTonalSpot(source, dark, 0);
    const surface = TonalPalette.fromHueAndChroma(
      source.hue, Math.min(20, Math.max(8, source.chroma / 5)),
    );
    const hex = (argb: number) => hexFromArgb(argb).toUpperCase();
    const tone = (palette: TonalPalette, value: number) => hex(palette.tone(value));
    const primary = hex(scheme.primary);
    return {
        primary,
        onPrimary: hex(scheme.onPrimary),
        primaryContainer: hex(scheme.primaryContainer),
        onPrimaryContainer: hex(scheme.onPrimaryContainer),
        secondary: hex(scheme.secondary),
        onSecondary: hex(scheme.onSecondary),
        secondaryContainer: hex(scheme.secondaryContainer),
        onSecondaryContainer: hex(scheme.onSecondaryContainer),
        tertiary: hex(scheme.tertiary),
        onTertiary: hex(scheme.onTertiary),
        tertiaryContainer: hex(scheme.tertiaryContainer),
        onTertiaryContainer: hex(scheme.onTertiaryContainer),
        error: hex(scheme.error),
        onError: hex(scheme.onError),
        errorContainer: hex(scheme.errorContainer),
        onErrorContainer: hex(scheme.onErrorContainer),
        background: tone(surface, dark ? 6 : 99),
        onBackground: tone(surface, dark ? 95 : 10),
        surface: tone(surface, dark ? 6 : 98),
        onSurface: tone(surface, dark ? 95 : 10),
        surfaceVariant: tone(surface, dark ? 24 : 90),
        onSurfaceVariant: tone(surface, dark ? 80 : 30),
        surfaceContainerLowest: tone(surface, dark ? 4 : 99),
        surfaceContainerLow: tone(surface, dark ? 10 : 96),
        surfaceContainer: tone(surface, dark ? 12 : 94),
        surfaceContainerHigh: tone(surface, dark ? 17 : 92),
        surfaceContainerHighest: tone(surface, dark ? 22 : 90),
        outline: hex(scheme.outline),
        outlineVariant: tone(surface, 55),
        inverseSurface: tone(surface, dark ? 95 : 20),
        inverseOnSurface: tone(surface, dark ? 20 : 95),
        inversePrimary: hex(scheme.inversePrimary),
        scrim: "#000000",
        shadow: "#000000",
        accentFg: readableOn(`#${match[1].toUpperCase()}`),
    };
}

/** Translate the sheet's tokens into flat CSS custom properties. No gradients,
 *  blur, glass or decorative shadows are emitted anywhere in this map. */
export function paletteVars(p: Palette, accentOverride = ""): Record<string, string> {
    const override = accentOverride.trim();
    const derived = override ? rolesFromSeed(override, p.mode) : {};
    const t: PaletteTokens = { ...p, ...derived };
    const accent = override || p.accent;
    const vars: Record<string, string> = {
        "--back": t.bg,
        "--back-raised": t.bg2,
        "--flat-hover": t.line,
        "--prim": t.surface,
        "--prim-brighter": t.surface2,
        "--seco": t.bg2,
        "--tert": t.line,
        "--tert-hover": t.line2,
        "--text": t.fg,
        "--text-bright": t.fg,
        "--text-dim": t.dim,
        "--text-dark": t.dim2,
        "--accent": accent,
        "--accent-hover": t.accentText,
        "--text-on-light": t.accentFg,
        "--back-border": t.line,
        "--prim-border": t.line2,
        "--shadow": t.scrim,
        "--shadow-raised": "none",
        "--backdrop": t.scrim,
        "--success": SUCCESS,
        "--warning": WARNING,
        "--equaliser": "var(--accent)",
        "--accent-soft": t.primaryContainer,
        "--accent-faint": t.surfaceContainerLow,
        "--surface-lift": t.surfaceContainerHigh,
        "--layer-rim": t.outlineVariant,
        "--layer-highlight": t.outline,
        "--elevation-1": "none",
        "--elevation-2": "none",
        "--radius": `${DESIGN_SHAPE.card}px`,
        "--radius-lg": `${DESIGN_SHAPE.xl}px`,
        "--radius-xl": `${DESIGN_SHAPE.hero}px`,
        "--radius-pill": `${DESIGN_SHAPE.pill}px`,
        "--shape-xs": `${DESIGN_SHAPE.xs}px`,
        "--shape-sm": `${DESIGN_SHAPE.sm}px`,
        "--shape-md": `${DESIGN_SHAPE.md}px`,
        "--shape-lg": `${DESIGN_SHAPE.lg}px`,
        "--shape-xl": `${DESIGN_SHAPE.xl}px`,
        "--shape-xxl": `${DESIGN_SHAPE.xxl}px`,
        "--touch-target": `${DESIGN_SHAPE.touchTarget}px`,
        "--progress-wave-hz": String(DESIGN_MOTION.progressWaveHz),
        "--progress-wave-px": `${DESIGN_MOTION.progressWavePx}px`,
    };
    for (const [name, style] of Object.entries(DESIGN_TYPE)) {
        vars[`--type-${name}-size`] = `${style.size}px`;
        vars[`--type-${name}-weight`] = String(style.weight);
        vars[`--type-${name}-line`] = `${style.line}px`;
    }
    for (const [cssName, role] of Object.entries(M3_CSS_VARS))
        vars[cssName] = String(t[role]);
    return vars;
}

/** Layer a cover-derived HCT seed over the active family without changing the
 *  stored palette id or alias. The seed only supplies tonal role values. */
function effectivePalette(p: Palette, accentOverride = "", seed = ""): Palette {
    const roles = seed ? rolesFromSeed(seed, p.mode) : {};
    return {
        ...p,
        ...roles,
        bg: roles.background ?? p.bg,
        bg2: roles.surfaceContainerLow ?? p.bg2,
        surface: roles.surfaceContainerLow ?? p.surface,
        surface2: roles.surfaceContainerHigh ?? p.surface2,
        fg: roles.onSurface ?? p.fg,
        dim: roles.onSurfaceVariant ?? p.dim,
        dim2: roles.onSurfaceVariant ?? p.dim2,
        line: roles.outlineVariant ?? p.line,
        line2: roles.outline ?? p.line2,
        accent: accentOverride.trim() || roles.primary || p.accent,
        accentText: roles.onPrimary ?? p.accentText,
        accentFg: roles.accentFg ?? p.accentFg,
    };
}

function paletteVarsWithSeed(p: Palette, accentOverride = "", seed = ""): Record<string, string> {
    return paletteVars(effectivePalette(p, accentOverride, seed), accentOverride);
}

/** Replace the active cover seed. An empty/invalid seed restores the family. */
export function setCoverSeed(seed: string | null | undefined): void {
    const value = /^#?[0-9a-f]{6}$/i.test(String(seed ?? "").trim())
        ? String(seed).trim().replace(/^#/, "").toUpperCase()
        : "";
    if (value === coverSeed) return;
    coverSeed = value;
    if (typeof document !== "undefined") {
        const root = document.documentElement;
        for (const [name, css] of Object.entries(
            paletteVarsWithSeed(currentPalette, currentAccent, coverSeed),
        )) root.style.setProperty(name, css);
        root.dataset.coverColour = value ? "true" : "false";
    }
    // Canvases (e.g. the lyric visualizer) read tokens through this subscription.
    for (const listener of listeners) listener();
}

export function currentCoverSeed(): string {
    return coverSeed;
}

/** Hex/rgb(a) -> "r, g, b" for canvas gradients; falls back for named colours. */
export function rgbTriplet(color: string, fallback: string): string {
    const value = String(color ?? "").trim();
    const hex = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(value);
    if (hex) {
        const digits = hex[1].length === 3
            ? hex[1].split("").map(c => c + c).join("")
            : hex[1];
        return [0, 2, 4]
            .map(i => String(parseInt(digits.slice(i, i + 2), 16)))
            .join(", ");
    }
    const rgb = /^rgba?\(\s*(\d+)\s*[,\s]\s*(\d+)\s*[,\s]\s*(\d+)/i.exec(value);
    if (rgb) return `${Number(rgb[1])}, ${Number(rgb[2])}, ${Number(rgb[3])}`;
    return fallback;
}

let currentPalette: Palette = resolvePalette(DEFAULT_PALETTE);
let currentAccent = DEFAULT_ACCENT;
let coverSeed = "";
let watchedFamily = "";
let mediaQuery: MediaQueryList | null = null;
let mediaListener: (() => void) | null = null;
const listeners = new Set<() => void>();

/** Notification for consumers that cannot just read a CSS var, e.g. canvases. */
export function subscribePalette(listener: () => void): () => void {
    listeners.add(listener);
    return () => { listeners.delete(listener); };
}

export function currentPaletteValue(): Palette {
    return effectivePalette(currentPalette, currentAccent, coverSeed);
}

export function currentAccentOverride(): string {
    return currentAccent;
}

function watchFamily(id: string) {
    const isFamily = PALETTE_FAMILIES.some(f => f.id === id);
    if (!isFamily || typeof window === "undefined" || typeof window.matchMedia !== "function") {
        if (mediaQuery && mediaListener) {
            if (typeof mediaQuery.removeEventListener === "function")
                mediaQuery.removeEventListener("change", mediaListener);
            else mediaQuery.removeListener(mediaListener);
        }
        mediaQuery = null;
        mediaListener = null;
        watchedFamily = "";
        return;
    }
    if (watchedFamily === id && mediaListener) return;
    if (mediaQuery && mediaListener) {
        if (typeof mediaQuery.removeEventListener === "function")
            mediaQuery.removeEventListener("change", mediaListener);
        else mediaQuery.removeListener(mediaListener);
    }
    watchedFamily = id;
    mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaListener = () => applyPalette(id, currentAccent);
    if (typeof mediaQuery.addEventListener === "function")
        mediaQuery.addEventListener("change", mediaListener);
    else mediaQuery.addListener(mediaListener);
}

/** Apply a palette id/alias now, following system appearance for bare family
 *  ids and re-applying when that appearance changes. */
export function applyPalette(id: string | null | undefined = DEFAULT_PALETTE, accentOverride: string | null | undefined = ""): Palette {
    const requested = String(id ?? "").trim().toLowerCase() || DEFAULT_PALETTE;
    const palette = resolvePalette(requested);
    const accent = String(accentOverride ?? "").trim();
    currentPalette = palette;
    currentAccent = accent;

    if (typeof document !== "undefined") {
        const root = document.documentElement;
        for (const [name, value] of Object.entries(paletteVarsWithSeed(palette, accent, coverSeed)))
            root.style.setProperty(name, value);
        root.dataset.palette = palette.id;
        root.style.colorScheme = palette.mode;
        const meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
        if (meta) meta.setAttribute("content", palette.bg);
    }
    watchFamily(requested);
    for (const listener of listeners) listener();
    return palette;
}

// Establish an inline palette and icon preference before components mount:
// later equal-specificity flufi-ui :root rules cannot beat inline properties.
applyPalette(DEFAULT_PALETTE, DEFAULT_ACCENT);
applyIconStyle(DEFAULT_ICON_STROKE, DEFAULT_ICON_FILLED);
```

### `ui/src/common/dynamic-colour.ts`

```ts
/** Cover-derived tonal colour for the web player.
 *
 * Loads the same cover the UI already displays, samples its dominant flat
 * colour on a tiny canvas and seeds a Material 3 tonal scheme through HCT in
 * `theme.ts`. Missing artwork, disabled covers and failed extraction clear the
 * seed so the chosen family palette stays in charge. No external requests are
 * made and no decorative effects are introduced.
 */
import { useEffect } from "preact/hooks";
import { covers } from "./prefs";
import { setCoverSeed } from "./theme";

const cache = new Map<string, string>();
let requestId = 0;

function hex(r: number, g: number, b: number): string {
    return "#" + [r, g, b].map(v => Math.max(0, Math.min(255, Math.round(v)))
        .toString(16).padStart(2, "0")).join("");
}

function loadImage(src: string): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
        const image = new Image();
        image.decoding = "async";
        image.onload = () => resolve(image);
        image.onerror = () => reject(new Error(`cover image failed: ${src}`));
        image.src = src;
    });
}

/** Quantise to 16-level buckets and weight saturated tones over grey ones. */
function dominantColour(image: HTMLImageElement): string | null {
    if (typeof document === "undefined") return null;
    const size = 24;
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) return null;
    context.drawImage(image, 0, 0, size, size);
    let data: Uint8ClampedArray;
    try {
        data = context.getImageData(0, 0, size, size).data;
    } catch {
        return null;
    }
    const buckets = new Map<string, { score: number; weight: number; r: number; g: number; b: number }>();
    for (let i = 0; i < data.length; i += 4) {
        const a = data[i + 3];
        if (a < 128) continue;
        const r = data[i], g = data[i + 1], b = data[i + 2];
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        if (max < 24 || max > 248) continue;
        const saturation = max === 0 ? 0 : (max - min) / max;
        const weight = 1 + saturation * 4;
        const key = `${r >> 4}-${g >> 4}-${b >> 4}`;
        const bucket = buckets.get(key) ?? { score: 0, weight: 0, r: 0, g: 0, b: 0 };
        bucket.score += weight;
        bucket.weight += 1;
        bucket.r += r;
        bucket.g += g;
        bucket.b += b;
        buckets.set(key, bucket);
    }
    let best: { score: number; weight: number; r: number; g: number; b: number } | null = null;
    for (const bucket of buckets.values())
        if (!best || bucket.score > best.score) best = bucket;
    if (!best) return null;
    return hex(best.r / best.weight, best.g / best.weight, best.b / best.weight);
}

async function apply(src: string): Promise<void> {
    const id = ++requestId;
    const usable = !!src && !src.startsWith("placeholder:") && covers.value;
    if (!usable) {
        setCoverSeed(null);
        return;
    }
    let seed = cache.get(src) ?? null;
    if (seed == null) {
        try {
            seed = dominantColour(await loadImage(src));
        } catch {
            seed = null;
        }
        if (seed) cache.set(src, seed);
    }
    if (id !== requestId) return;
    setCoverSeed(seed);
}

/** Apply the current track's cover colour, falling back to the family palette. */
export function useCoverColour(src: string | null | undefined): void {
    const value = src ?? "";
    useEffect(() => {
        void apply(value);
        return () => {
            requestId++;
            setCoverSeed(null);
        };
    }, [value, covers.value]);
}
```

### `ui/src/components/LeftSidebar/style.css`

```css

#left-sidebar {
    display: flex;
    flex-direction: column;

    width: 264px;

    border-right: 1px solid var(--layer-rim);
    background: var(--md-surface-container-low);

    overflow: hidden;

    transition: width var(--transition-fast) var(--spring-ease);

    > div.desktop {
        position: relative;
        flex: 1;

        > .openclose {
            position: absolute;
            z-index: 100;
            top: 8px;
            right: 8px;
            min-width: var(--touch-target);
            min-height: var(--touch-target);
            border-radius: var(--radius-pill);
            background: var(--md-surface-container-high);
        }

        > .opened,
        > .closed {
            position: absolute;
            inset: 0;

            transition: opacity var(--transition-fast);
        }

        > .closed {
            margin-top: 64px;
        }

        &.open {
            > .opened { opacity: 100%; z-index: 1; }
            > .closed { opacity: 0%; z-index: 0; }
        }
        &:not(.open) {
            > .opened { opacity: 0%; z-index: 0; }
            > .closed { opacity: 100%; z-index: 1; }
        }

        .mini-header {
            margin: 12px 16px 8px;
            font-family: 'Lexend', sans-serif;
            font-size: var(--type-label-size);
            font-weight: var(--type-label-weight);
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: var(--text-dim);
        }

        .button {
            justify-content: flex-start;
            gap: 12px;
            min-height: var(--touch-target);
            margin: 2px 12px;
            padding-inline: 16px;
            border-radius: var(--radius-pill);
        }

        .button[href="/"],
        .button.current {
            background: var(--md-secondary-container);
            color: var(--md-on-secondary-container);
        }
    }

    &.desktop:not(.open) {
        width: 64px;
    }
}

.mobile {
    #left-sidebar {
        width: min(max(calc(100vw - 88px), 280px), 360px);

        position: absolute;
        inset: 0 auto 0 0;
        left: -100%;

        z-index: 50;

        transition: left var(--transition-fast) var(--spring-ease);

        &.open {
            left: 0%;
        }
    }
}

#left-sidebar > .mobile-drawer {
    height: 100%;
    padding: 12px 16px 24px;
    gap: 4px;
    overflow-y: auto;
    overscroll-behavior: contain;
    background: var(--md-surface-container-low);
}

#left-sidebar .mobile-drawer .drawer-head {
    justify-content: space-between;
    margin-bottom: 8px;
}

#left-sidebar .mobile-drawer .mini-header {
    margin: 16px 8px 4px;
}

#left-sidebar .mobile-drawer .drawer-link {
    width: 100%;
    justify-content: flex-start;
    gap: 14px;
    min-height: var(--touch-target);
    padding: 10px 16px;
    border-radius: var(--radius-pill);
    background: var(--md-surface-container-high);
    border: 0;
}

.mobile-sidebar-scrim {
    position: absolute;
    inset: 0;
    z-index: 45;
    background: var(--md-scrim);
    opacity: 0.32;
}
```

### `ui/src/components/Library/Image.tsx`

```tsx
import { addClass } from "flufi-ui";
import {
    API, parseAlbumUuid, parseArtistUuid,
} from "../../common/net/api";
import type { Artist, SearchItem, Set, Track, Uuid } from "../../common/net/types";
import { covers } from "../../common/prefs";
import { CoverArt } from "./CoverArt";

import "./style.css";

// "Covers" off (Settings) hides artwork without removing the layout box.
function artwork(src: string, name: string, kind: "artist" | "album" | "track",
                 size: number | undefined, cls: string | undefined, lazy?: boolean) {
    if (!covers.value)
        return <div class={addClass("library-img", "no-art", cls)} style={{ width: size, height: size }} aria-hidden="true" />;
    return (
        <CoverArt
            src={src}
            name={name}
            kind={kind}
            size={size}
            class={addClass("library-img", cls)}
            lazy={lazy}
        />
    );
}

export type SharedImageProps = {
    size?: number,
    class?: string,
    lazy?: boolean
};

export type ArtistImageProps = { uuid: Uuid }
    | { artist: Artist }
    | Extract<SearchItem, { type: "artist" }>;
export function ArtistPfp(props: SharedImageProps & ArtistImageProps) {
    const uuid = "uuid" in props ? props.uuid : props.artist.uuid;
    const name = "artist" in props ? props.artist.name.value : parseArtistUuid(uuid).name;
    return artwork(API.getArtistPfpUrl(uuid), name, "artist", props.size,
        addClass("artist-pfp", props.class), props.lazy)
}

export type SetImageProps = { uuid: Uuid }
    | { set: Set }
    | Extract<SearchItem, { type: "set" }>;
export function SetCover(props: SharedImageProps & SetImageProps) {
    const uuid = "uuid" in props ? props.uuid : props.set.uuid;
    const name = "set" in props ? props.set.name.value : parseAlbumUuid(uuid).name;
    return artwork(API.getSetCoverUrl(uuid), name, "album", props.size,
        addClass("set-cover", props.class), props.lazy)
}

export type TrackImageProps = { uuid: Uuid }
    | { track: Track }
    | Extract<SearchItem, { type: "track" }>;
export function TrackCover(props: SharedImageProps & TrackImageProps) {
    const uuid = "uuid" in props ? props.uuid : props.track.uuid;
    const name = "track" in props && "name" in props.track ? props.track.name.value : uuid;
    return artwork(API.getTrackCoverUrl(uuid), name, "track", props.size,
        addClass("track-cover", props.class), props.lazy)
}
```

### `ui/src/components/Library/CoverArt.tsx`

```tsx
/** Cover image with a flat tonal Lucide placeholder.
 *
 * `fallbackCover()` returns a `placeholder:` sentinel instead of a text-initial
 * SVG. This component renders that sentinel as a real DOM surface so it picks
 * up the active palette's CSS variables; real artwork is shown untouched.
 */
import { Circle, Cookie, Flower, Pentagon, Squircle } from "lucide-preact";
import { addClass } from "flufi-ui";

import "./style.css";

export type CoverKind = "track" | "artist" | "album";

const PLACEHOLDER_GLYPHS = [Circle, Squircle, Cookie, Flower, Pentagon] as const;

function glyphIndex(name: string, kind: CoverKind): number {
    let hash = kind.length * 17;
    for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
    return hash % PLACEHOLDER_GLYPHS.length;
}

function parsePlaceholder(src: string): { name: string; kind: CoverKind } | null {
    if (!src.startsWith("placeholder:")) return null;
    const [, rawKind, encoded = ""] = src.split(":");
    const kind = (rawKind === "artist" || rawKind === "track" ? rawKind : "album") as CoverKind;
    let name = "?";
    try { name = decodeURIComponent(encoded) || "?"; } catch { /* keep ? */ }
    return { name, kind };
}

export function CoverArt(props: {
    src?: string | null;
    name: string;
    kind?: CoverKind;
    size?: number;
    class?: string;
    lazy?: boolean;
    alt?: string;
    onClick?: () => void;
}) {
    const classes = addClass("cover-art", props.class, props.onClick && "cover-clickable");
    const style = props.size != null ? { width: props.size, height: props.size } : undefined;
    const placeholder = parsePlaceholder(props.src ?? "");
    if (placeholder) {
        const index = glyphIndex(placeholder.name, placeholder.kind);
        const Glyph = PLACEHOLDER_GLYPHS[index];
        return (
            <div
                class={addClass(classes, "cover-placeholder")}
                data-shape={String(index)}
                data-kind={placeholder.kind}
                style={style}
                role="img"
                aria-label={`${placeholder.name} artwork placeholder`}
                onClick={props.onClick}
            >
                <Glyph size={Math.max(20, Math.min(56, (props.size ?? 64) * 0.42))} aria-hidden="true" />
            </div>
        );
    }
    if (!props.src) {
        return <div class={addClass(classes, "cover-placeholder", "cover-empty")} style={style} aria-hidden="true" />;
    }
    return (
        <img
            class={classes}
            src={props.src}
            alt={props.alt ?? ""}
            loading={props.lazy ? "lazy" : "eager"}
            draggable={false}
            style={style}
            onClick={props.onClick}
        />
    );
}
```

### `ui/src/components/Library/style.css`

```css

.library-img,
.cover-art {
    border-radius: var(--radius-xl);
    transition: transform var(--transition-fast) var(--spring-ease);
}

.library-card:hover .library-img {
    transform: translateY(-2px);
}

.library-card {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.library-link {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 4px;
    padding: 8px 4px 0 !important;
    width: 100%;
    min-width: 0;
}

.cover-wrap {
    position: relative;
    width: 100%;
    aspect-ratio: 1 / 1;
}

.cover-wrap .cover-link {
    display: block;
    width: 100%;
    height: 100%;
    padding: 0 !important;
}

.cover-wrap .library-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    background: var(--md-surface-container-high);
}

/* Flat tonal placeholder: the Lucide glyph is generated from lucide-static and
   one of five shapes is chosen deterministically from the item's name. */
.cover-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--md-on-primary-container);
    background: var(--md-primary-container);
    border-radius: var(--radius-lg);
    overflow: hidden;
}

.cover-placeholder[data-shape="0"] { border-radius: 50%; }
.cover-placeholder[data-shape="1"] { border-radius: var(--radius-xl); }
.cover-placeholder[data-shape="2"] { border-radius: var(--radius-pill); }
.cover-placeholder[data-shape="3"] { border-radius: 24% 48% 24% 48%; }
.cover-placeholder[data-shape="4"] { border-radius: 28% 28% 20% 20%; }

.cover-placeholder.cover-empty {
    background: var(--md-surface-container-high);
}

.cover-clickable {
    cursor: pointer;
}

/* Two lines are always reserved, so a long album name cannot change the row
   height or push the next row of covers out of line. */
.library-card .card-title {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    line-height: var(--type-body-line);
    height: calc(var(--type-body-line) * 2);
    overflow-wrap: anywhere;
}

.library-card .card-sub {
    font-size: var(--type-label-size);
    line-height: var(--type-label-line);
    color: var(--text-dim);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Play button floats over the cover, revealed on hover or keyboard focus. */
.library-card .card-play {
    position: absolute;
    right: 8px;
    bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: var(--touch-target);
    height: var(--touch-target);
    padding: 0;
    border: 0;
    border-radius: var(--radius-pill);
    background: var(--accent);
    color: var(--text-on-light);
    cursor: pointer;
    opacity: 0;
    transform: translateY(4px);
    transition: opacity var(--transition-fast), transform var(--transition-fast) var(--spring-ease);
}

.library-card:hover .card-play,
.library-card:focus-within .card-play {
    opacity: 1;
    transform: translateY(0);
}

@media (pointer: coarse) {
    .library-card .card-play {
        opacity: 1;
    }
}
```

### `ui/src/components/Lyrics/LyricsPanel.tsx`

```tsx
/** Synced lyrics panel.
 *
 * Fetches (cached server-side) lyrics for a track, parses LRC into
 * {time, text} lines and highlights the current line as the track plays.
 * Renders a right-side drawer above the player bar (full screen on mobile)
 * with a slide animation, text-size control and per-track open/closed state.
 */
import { useEffect, useRef, useState, useCallback } from "preact/hooks";
import { Button, Container, Header3, Text, TextIconButton } from "flufi-ui/components";
import {
    AArrowDown,
    AArrowUp,
    AudioLines,
    AudioWaveform,
    LocateFixed,
    MicVocal,
    Sparkles,
    X,
} from "lucide-preact";
import { EmptyState } from "../EmptyState/EmptyState";
import {
    LyricVisualizer,
    VISUALIZER_LABELS,
    VISUALIZER_MODES,
    readVisualizerMode,
    saveVisualizerMode,
    type VisualizerMode,
} from "./LyricVisualizer";
import { API } from "../../common/net/api";
import { position, seekTo } from "../../common/player";

import "./style.css";

type LrcLine = { time: number; text: string };

const SIZE_KEY = "mcmusic:lyricsSize";

const VISUALIZER_ICONS = {
    bars: AudioLines,
    wave: AudioWaveform,
    glow: Sparkles,
};

function parseLrc(text: string): LrcLine[] {
    const lines = text.split(/\r?\n/);
    const out: LrcLine[] = [];
    const tagRe = /\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]/g;

    for (const raw of lines) {
        const times: number[] = [];
        let lastIndex = 0;
        let m: RegExpExecArray | null = null;
        tagRe.lastIndex = 0;
        while ((m = tagRe.exec(raw)) !== null) {
            const min = parseInt(m[1], 10);
            const sec = parseInt(m[2], 10);
            const ms = m[3] ? parseInt(String(m[3]).padEnd(3, "0"), 10) : 0;
            times.push(min * 60 + sec + ms / 1000);
            lastIndex = tagRe.lastIndex;
        }
        const lyric = raw.slice(lastIndex).trim();

        // Skip metadata lines like [ar:], [ti:], [al:], [by:], [offset:]
        if (/^\[(ar|ti|al|by|offset|re|ue):/i.test(raw)) continue;

        if (times.length && lyric) {
            for (const t of times) out.push({ time: t, text: lyric });
        } else if (!times.length && lyric) {
            out.push({ time: -1, text: lyric });
        }
    }

    out.sort((a, b) => a.time - b.time);
    return out;
}

function sourceLabel(source: string, synced: boolean): string {
    const s = (source || "").toLowerCase();
    const via = s.includes("lrclib") ? "via LRCLIB" : s.includes("stored") ? "stored" : "";
    return synced ? `Synced${via ? ` · ${via}` : ""}` : `Plain${via ? ` · ${via}` : ""}`;
}

export function LyricsPanel(props: {
    trackId: string;
    open: boolean;
    onOpen: () => void;
    onClose: () => void;
}) {
    const { trackId, open, onOpen, onClose } = props;
    const [lines, setLines] = useState<LrcLine[]>([]);
    const [synced, setSynced] = useState(false);
    const [source, setSource] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [size, setSize] = useState(() => {
        const v = localStorage.getItem(SIZE_KEY);
        return v ? parseFloat(v) : 1;
    });
    const [manualScroll, setManualScroll] = useState(false);
    const [activeIndex, setActiveIndex] = useState(-1);
    const [visualizerMode, setVisualizerMode] = useState<VisualizerMode>(readVisualizerMode);
    const [singMode, setSingMode] = useState(false);

    const containerRef = useRef<HTMLDivElement>(null);
    const scrollTimeoutRef = useRef<number>(0);
    const programmaticScrollRef = useRef(false);
    const sizeRef = useRef(size);
    sizeRef.current = size;
    const prevOpenRef = useRef(open);
    useEffect(() => {
        if (!prevOpenRef.current && open) onOpen();
        prevOpenRef.current = open;
    }, [open, onOpen]);

    useEffect(() => {
        localStorage.setItem(SIZE_KEY, String(size));
    }, [size]);

    useEffect(() => {
        saveVisualizerMode(visualizerMode);
    }, [visualizerMode]);

    // Sing Mode is a display mode only, and only real LRC timestamps earn it.
    useEffect(() => {
        if (!synced) setSingMode(false);
    }, [synced]);

    const changeSize = useCallback((delta: number) => {
        setSize((s) => {
            return Math.min(1.8, Math.max(0.6, s + delta));
        });
    }, []);

    const jumpToCurrent = useCallback(() => {
        setManualScroll(false);
        scrollToActive();
    }, []);

    const scrollToActive = useCallback(() => {
        const el = containerRef.current;
        if (!el || activeIndex < 0) return;
        const node = el.querySelector(`[data-line="${activeIndex}"]`);
        if (!node) return;
        const elRect = el.getBoundingClientRect();
        const nodeRect = node.getBoundingClientRect();
        const offset =
            nodeRect.top - elRect.top + el.scrollTop - elRect.height / 2 + nodeRect.height / 2;
        programmaticScrollRef.current = true;
        el.scrollTo({ top: offset, behavior: "smooth" });
        window.clearTimeout(scrollTimeoutRef.current);
        scrollTimeoutRef.current = window.setTimeout(() => {
            programmaticScrollRef.current = false;
        }, 600);
    }, [activeIndex]);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setError(null);
        API.lyrics(trackId)
            .then((d) => {
                if (cancelled) return;
                const text = d.lyrics || "";
                const parsed = parseLrc(text);
                setLines(parsed);
                setSynced(parsed.some((l) => l.time >= 0));
                setSource(d.source || "");
                setLoading(false);
            })
            .catch((e) => {
                if (cancelled) return;
                setError(e instanceof Error ? e.message : String(e));
                setLoading(false);
            });
        return () => { cancelled = true; };
    }, [trackId]);

    useEffect(() => {
        if (!open) return;
        let scheduled = false;
        function onTime() {
            if (manualScroll) return;
            if (scheduled) return;
            scheduled = true;
            requestAnimationFrame(() => {
                scheduled = false;
                const now = position.value;
                let idx = -1;
                for (let i = lines.length - 1; i >= 0; i--) {
                    if (lines[i].time >= 0 && lines[i].time <= now) {
                        idx = i;
                        break;
                    }
                }
                setActiveIndex(idx);
                if (idx >= 0) scrollToActive();
            });
        }
        const unsub = position.subscribe(onTime);
        onTime();
        return () => {
            unsub();
            window.clearTimeout(scrollTimeoutRef.current);
        };
    }, [open, lines, manualScroll, scrollToActive]);

    function onContainerScroll() {
        if (programmaticScrollRef.current) return;
        setManualScroll(true);
        window.clearTimeout(scrollTimeoutRef.current);
        scrollTimeoutRef.current = window.setTimeout(() => setManualScroll(false), 400);
    }

    if (!open) return null;

    const missing = loading === false && lines.length === 0 && !error;
    const showLyrics = lines.length > 0 && !error && !loading;

    return (
        <Container
            class="lyrics-panel"
            other={{
                role: "dialog",
                "aria-modal": "true",
                "aria-label": "Lyrics",
                onScroll: onContainerScroll,
                ref: containerRef,
            }}
        >
            <Container horizontal centered_y class="head">
                <TextIconButton
                    variant="always-transparent"
                    title="Close lyrics"
                    onClick={onClose}
                >
                    <X size={15} />
                </TextIconButton>
                <Header3 class="title">Lyrics</Header3>
                <Container horizontal class="controls">
                    <div class="visualizer-modes" role="group" aria-label="Lyric visualizer mode">
                        {VISUALIZER_MODES.map((mode) => {
                            const Icon = VISUALIZER_ICONS[mode];
                            const active = visualizerMode === mode;
                            return (
                                <button
                                    key={mode}
                                    type="button"
                                    class={`visualizer-mode${active ? " visualizer-mode-active" : ""}`}
                                    title={`${VISUALIZER_LABELS[mode]} visualizer`}
                                    aria-label={`${VISUALIZER_LABELS[mode]} visualizer mode`}
                                    aria-pressed={active}
                                    onClick={() => setVisualizerMode(mode)}
                                >
                                    <Icon size={14} aria-hidden="true" />
                                </button>
                            );
                        })}
                    </div>
                    {source && (
                        <Text dim class="source" content={sourceLabel(source, synced)} />
                    )}
                    {synced && (
                        <Button
                            class="sing-toggle"
                            variant={singMode ? "accent-subtle" : "panel"}
                            title="Larger karaoke-style lines. This does not record your voice."
                            onClick={() => setSingMode(v => !v)}
                        >
                            <MicVocal size={14} /> {singMode ? "Reading" : "Sing along"}
                        </Button>
                    )}
                    <TextIconButton
                        variant="always-transparent"
                        title="Smaller text"
                        onClick={() => changeSize(-0.15)}
                        disabled={size <= 0.6}
                    >
                        <AArrowDown size={14} />
                    </TextIconButton>
                    <TextIconButton
                        variant="always-transparent"
                        title="Larger text"
                        onClick={() => changeSize(0.15)}
                        disabled={size >= 1.8}
                    >
                        <AArrowUp size={14} />
                    </TextIconButton>
                    {manualScroll && synced && (
                        <TextIconButton
                            variant="accent-subtle"
                            title="Jump to current line"
                            onClick={jumpToCurrent}
                        >
                            <LocateFixed size={14} /> Jump to current
                        </TextIconButton>
                    )}
                </Container>
            </Container>

            {error && (
                <Container class="lyrics-state">
                    <Text class="error" content={error} />
                    <button
                        type="button"
                        class="retry"
                        onClick={() => {
                            setLoading(true);
                            setError(null);
                            void API.lyrics(trackId)
                                .then((d) => {
                                    const parsed = parseLrc(d.lyrics || "");
                                    setLines(parsed);
                                    setSynced(parsed.some((l) => l.time >= 0));
                                    setSource(d.source || "");
                                    setLoading(false);
                                })
                                .catch((e) => {
                                    setError(e instanceof Error ? e.message : String(e));
                                    setLoading(false);
                                });
                        }}
                    >
                        Try again
                    </button>
                </Container>
            )}
            {loading && !error && (
                <Container class="lyrics-state">
                    <Text dim content="Loading lyrics…" />
                </Container>
            )}
            {missing && !error && !loading && (
                <EmptyState
                    class="lyrics-empty"
                    icon={<MicVocal size={22} />}
                    title="No lyrics found"
                    body="This track does not have a synced or plain lyrics file yet."
                />
            )}
            {showLyrics && (
                <LyricVisualizer mode={visualizerMode} activeIndex={activeIndex} />
            )}
            {showLyrics && (
                <div
                    class={`lyrics-text${singMode && synced ? " sing-along" : ""}`}
                    style={{ fontSize: `${sizeRef.current}rem` }}
                >
                    {lines.map((line, i) => {
                        const active = i === activeIndex;
                        return (
                            <div
                                key={i}
                                data-line={i}
                                class={`lyrics-line${active ? " lyrics-line-active" : ""}${synced ? "" : " lyrics-line-static"}`}
                                onClick={() => {
                                    if (line.time >= 0) {
                                        setManualScroll(false);
                                        seekTo(line.time);
                                        setActiveIndex(i);
                                        scrollToActive();
                                    }
                                }}
                            >
                                {line.text}
                            </div>
                        );
                    })}
                    {synced && activeIndex < 0 && position.value > 0 && (
                        <Container class="lyrics-state" centered_x>
                            <Text dim content="Waiting for the track to start…" />
                        </Container>
                    )}
                </div>
            )}
        </Container>
    );
}
```

### `ui/src/components/Lyrics/style.css`

```css
/* Lyrics and Up next are peer sheets above the player bar: flat tonal panels,
   generous pill controls, and motion that yields to reduced-motion settings. */
.lyrics-panel {
    position: fixed;
    right: 0;
    top: var(--topbar-h);
    bottom: max(var(--player-h), 78px);
    z-index: 45;
    width: min(460px, calc(100vw - 24px));
    max-height: none;
    overflow: auto;
    overscroll-behavior: contain;
    background: var(--md-surface-container-high);
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius-xl) 0 0 var(--radius-xl);
    display: flex;
    flex-direction: column;
    animation: lyrics-slide-in 0.28s cubic-bezier(0.2, 0.9, 0.2, 1.2);
}

@keyframes lyrics-slide-in {
    from {
        opacity: 0;
        transform: translateX(120%);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.lyrics-panel .head {
    position: sticky;
    top: 0;
    z-index: 1;
    gap: 10px;
    padding: 12px 16px;
    background: var(--md-surface-container-high);
    border-bottom: 1px solid var(--layer-rim);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
}

.lyrics-panel .title {
    margin: 0;
    flex: 1;
    min-width: 0;
}

.lyrics-panel .controls {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    margin-left: 10px;
}

.lyrics-panel .visualizer-modes {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 3px;
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius-pill);
    background: var(--md-surface-container-low);
}

.lyrics-panel .visualizer-mode {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: var(--touch-target);
    height: var(--touch-target);
    padding: 0;
    border: 0;
    border-radius: var(--radius-pill);
    background: transparent;
    color: var(--text-dim);
    cursor: pointer;
    transition: background var(--transition-fast), color var(--transition-fast);
}

.lyrics-panel .visualizer-mode:hover {
    background: var(--flat-hover);
    color: var(--text-bright);
}

.lyrics-panel .visualizer-mode[aria-pressed="true"] {
    background: var(--md-secondary-container);
    color: var(--md-on-secondary-container);
}

.lyrics-panel .visualizer-mode:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 1px;
}

.lyrics-panel .source {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: var(--type-label-size);
}

.lyrics-panel .sing-toggle {
    min-height: var(--touch-target);
    border-radius: var(--radius-pill);
}

.lyrics-panel .head > button,
.lyrics-panel .head > .button {
    margin-left: auto;
    flex: none;
}

.lyrics-panel .lyrics-empty {
    min-height: 110px;
    margin: 12px;
    border-style: solid;
}

.lyrics-panel .lyrics-state {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    padding: 12px;
}

.lyrics-panel .retry {
    min-height: var(--touch-target);
    padding: 6px 16px;
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius-pill);
    background: transparent;
    color: inherit;
    cursor: pointer;
    font-size: var(--type-label-size);
}

.lyrics-panel .retry:hover {
    background: var(--flat-hover);
}

.lyrics-panel .lyrics-visualizer {
    display: block;
    flex: none;
    width: calc(100% - 24px);
    height: 56px;
    margin: 12px 12px 0;
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius-lg);
    background: var(--back);
}

.lyrics-text {
    margin: 0;
    padding: 16px 12px 24px;
    overflow-wrap: anywhere;
    font-family: inherit;
    line-height: 1.7;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.lyrics-line {
    padding: 8px 14px;
    border-radius: var(--radius-lg);
    cursor: pointer;
    overflow-wrap: anywhere;
    transition: background var(--transition-fast), transform var(--transition-fast) var(--spring-ease);
}

.lyrics-line:hover {
    background: var(--flat-hover);
}

.lyrics-line-static {
    cursor: default;
}

.lyrics-line.lyrics-line-active {
    color: var(--md-on-primary-container);
    font-weight: 700;
    background: var(--md-primary-container);
    transform: scale(1.02);
}

.lyrics-text.sing-along .lyrics-line {
    padding: 12px 16px;
    font-weight: 600;
}

.lyrics-text.sing-along .lyrics-line-active {
    font-size: 1.18em;
}

.lyrics-panel .lyrics-state.centered_x {
    justify-content: center;
    align-items: center;
}

@media (max-width: 800px) {
    .lyrics-panel {
        right: 0;
        left: 0;
        top: var(--topbar-h);
        bottom: var(--player-h);
        width: auto;
        border-radius: var(--radius-xl) var(--radius-xl) 0 0;
    }
}

@media (prefers-reduced-motion: reduce) {
    .lyrics-panel {
        animation: none;
    }

    .lyrics-line.lyrics-line-active {
        transform: none;
    }
}
```

### `ui/src/components/PlayerBar/PlayerBar.tsx`

```tsx
/** Bottom player bar: artwork, transport (prev / play-pause / next / shuffle /
 * repeat / volume / queue), a seek bar with filled progress, the track title
 * and artist as links, and the lyrics toggle. Also installs Media Session and
 * the full set of legacy keyboard shortcuts.
 */
import { useEffect, useRef, useState } from "preact/hooks";
import { Container, FooterContainer, IconButton, Text } from "flufi-ui/components";
import {
    Heart,
    ListMusic,
    MicVocal,
    Pause,
    Play,
    Radio,
    Repeat,
    Shuffle,
    SkipBack,
    SkipForward,
    Volume2,
    VolumeX,
    X,
} from "lucide-preact";
import {
    autoplay,
    currentId,
    currentLiked,
    duration,
    formatTime,
    isPlaying,
    nowPlaying,
    playError,
    playNext,
    playPrev,
    playQueueIndex,
    queue,
    queueIndex,
    queueOpen,
    repeatMode,
    seekTo,
    setAutoplay,
    setShuffle,
    setVolume,
    shuffleEnabled,
    cycleRepeat,
    toggleCurrentLike,
    togglePlay,
    toggleMute,
    position,
} from "../../common/player";
import { API } from "../../common/net/api";
import { playfulMotion, prefersReducedMotion, volume } from "../../common/prefs";
import { useCoverColour } from "../../common/dynamic-colour";
import { CoverArt } from "../Library/CoverArt";
import { LyricsPanel } from "../Lyrics/LyricsPanel";

import "./style.css";

function setLinkHref(uuid: string): string {
    return `/set/${uuid}`;
}

export function PlayerBar() {
    const track = nowPlaying.value;
    const coverSrc = track ? API.getTrackCoverUrl(String(currentId.value ?? track.id)) : "";
    useCoverColour(coverSrc);
    const [showLyrics, setShowLyrics] = useState(() => {
        const v = localStorage.getItem("mcmusic:lyricsOpen");
        return v === "true";
    });
    const [muted, setMuted] = useState(false);
    const showQueue = queueOpen;
    const [seekHover, setSeekHover] = useState<number | null>(null);
    const [seekDragging, setSeekDragging] = useState(false);
    const [volumeHover, setVolumeHover] = useState<number | null>(null);
    const [volumeDragging, setVolumeDragging] = useState(false);
    const seekRef = useRef<HTMLDivElement>(null);
    const volRef = useRef<HTMLDivElement>(null);

    if (!track) return null;

    const setUuid = (track as any).setUuid ?? null;
    const artistUuid = (track as any).artistUuid ?? null;
    const album = (track as any).album ?? "";

    // Persist lyrics open/closed.
    useEffect(() => {
        localStorage.setItem("mcmusic:lyricsOpen", showLyrics ? "true" : "false");
    }, [showLyrics]);

    // A drag can end outside the thin slider tracks; always release it.
    useEffect(() => {
        if (!seekDragging && !volumeDragging) return;
        const stop = () => {
            setSeekDragging(false);
            setVolumeDragging(false);
        };
        window.addEventListener("mouseup", stop);
        return () => window.removeEventListener("mouseup", stop);
    }, [seekDragging, volumeDragging]);

    // Media Session API (lock screen, media keys, artwork).
    useEffect(() => {
        if (!("mediaSession" in navigator)) return;
        const cover = `/api/tracks/${currentId.value ?? track.id}/cover`;
        navigator.mediaSession.metadata = new MediaMetadata({
            title: track.title,
            artist: track.artist,
            album,
            artwork: [{ src: cover, sizes: "512x512", type: "image/jpeg" }],
        });
        const setHandler = (action: string) => {
            switch (action) {
                case "play":
                case "pause":
                    togglePlay();
                    break;
                case "previoustrack":
                    playPrev();
                    break;
                case "nexttrack":
                    playNext();
                    break;
            }
        };
        for (const action of ["play", "pause", "previoustrack", "nexttrack"]) {
            try { (navigator.mediaSession as any).setActionHandler(action, setHandler); } catch { /* noop */ }
        }
        return () => {
            for (const action of ["play", "pause", "previoustrack", "nexttrack"]) {
                try { (navigator.mediaSession as any).setActionHandler(action, null); } catch { /* noop */ }
            }
        };
    }, [track.id, track.title, track.artist, album]);

    // Global keyboard controls — the full legacy shortcut set.
    useEffect(() => {
        function onKey(e: KeyboardEvent) {
            const target = e.target as HTMLElement | null;
            const editing = target instanceof HTMLInputElement ||
                target instanceof HTMLTextAreaElement ||
                target instanceof HTMLSelectElement ||
                !!target?.isContentEditable;

            if (e.key === "Escape") {
                if (editing) target?.blur?.();
                queueOpen.value = false;
                setShowLyrics(false);
                return;
            }
            if (editing) return;

            if (e.key === " ") { e.preventDefault(); togglePlay(); return; }
            if (e.key === "ArrowLeft") {
                e.preventDefault();
                if (e.shiftKey) playPrev();
                else seekTo(Math.max(0, position.value - 5));
                return;
            }
            if (e.key === "ArrowRight") {
                e.preventDefault();
                if (e.shiftKey) playNext();
                else seekTo(Math.min(duration.value, position.value + 5));
                return;
            }
            if (e.shiftKey && e.key === "ArrowUp") {
                e.preventDefault(); setVolume(Math.min(1, volume.value + 0.05)); return;
            }
            if (e.shiftKey && e.key === "ArrowDown") {
                e.preventDefault(); setVolume(Math.max(0, volume.value - 0.05)); return;
            }
            if (e.key === "/") {
                e.preventDefault();
                document.getElementById("global-search")?.focus();
                return;
            }
            const k = e.key.toLowerCase();
            if (k === "m") { toggleMute(); return; }
            if (k === "l") { void toggleCurrentLike(); return; }
            if (k === "q") { queueOpen.value = !queueOpen.value; return; }
        }
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [position.value, duration.value]);

    const playedPct = duration.value > 0 ? (position.value / duration.value) * 100 : 0;
    const isMutedEffective = muted || volume.value <= 0;
    const wavePlaying = isPlaying.value && playfulMotion.value && !prefersReducedMotion();

    function seekAt(clientX: number): number | null {
        const rect = seekRef.current?.getBoundingClientRect();
        if (!rect || rect.width <= 0) return null;
        const frac = (clientX - rect.left) / rect.width;
        return Math.max(0, Math.min(duration.value, frac * duration.value));
    }

    function volumeAt(clientX: number): number | null {
        const rect = volRef.current?.getBoundingClientRect();
        if (!rect || rect.width <= 0) return null;
        const frac = (clientX - rect.left) / rect.width;
        return Math.max(0, Math.min(1, frac));
    }

    function onSeekMove(clientX: number) {
        const t = seekAt(clientX);
        if (t == null) return;
        setSeekHover(t);
        if (seekDragging) seekTo(t);
    }

    function onVolumeMove(clientX: number) {
        const v = volumeAt(clientX);
        if (v == null) return;
        setVolumeHover(v);
        if (volumeDragging) setVolume(v);
    }

    function toggleMuteButton() {
        // A zero volume is silent even when audio.muted is false.
        if (volume.value <= 0) {
            setVolume(0.8);
            if (muted) { toggleMute(); setMuted(false); }
            return;
        }
        setMuted(!muted);
        toggleMute();
    }

    const queueTracks = queue.value;

    return (
        <>
            <LyricsPanel
                trackId={track.id}
                open={showLyrics}
                onOpen={() => setShowLyrics(true)}
                onClose={() => setShowLyrics(false)}
            />
            <FooterContainer other={{ id: "player-bar" }}>
                <Container horizontal centered_y class="player">
                    {/* Cover art — 56px, opens the album. */}
                    <div class="art-wrap">
                        <CoverArt
                            class="art"
                            src={coverSrc}
                            name={track.title}
                            kind="track"
                            alt=""
                            onClick={() => { if (setUuid) window.location.href = setLinkHref(setUuid); }}
                        />
                    </div>

                    {/* Transport controls. */}
                    <Container horizontal centered_y class="transport">
                        <IconButton
                            title="Previous"
                            onClick={playPrev}
                        >
                            <SkipBack size={17} />
                        </IconButton>
                        <IconButton
                            title={isPlaying.value ? "Pause" : "Play"}
                            onClick={togglePlay}
                            class={isPlaying.value ? "play-pause playing" : "play-pause"}
                        >
                            {isPlaying.value ? <Pause size={19} /> : <Play size={19} />}
                        </IconButton>
                        <IconButton
                            title="Next"
                            onClick={() => playNext()}
                        >
                            <SkipForward size={17} />
                        </IconButton>
                        <IconButton
                            title={shuffleEnabled.value ? "Shuffle on" : "Shuffle off"}
                            class="control-shuffle"
                            variant={shuffleEnabled.value ? "accent-subtle" : "always-transparent"}
                            onClick={() => setShuffle(!shuffleEnabled.value)}
                        >
                            <Shuffle size={16} />
                        </IconButton>
                        <IconButton
                            title={repeatMode.value === "one" ? "Repeat one" : repeatMode.value === "all" ? "Repeat all" : "Repeat off"}
                            class="control-repeat"
                            variant={repeatMode.value !== "off" ? "accent-subtle" : "always-transparent"}
                            onClick={() => cycleRepeat()}
                        >
                            <Repeat size={16} />
                        </IconButton>
                    </Container>

                    {/* Title / artist links. */}
                    <Container vertical class="meta">
                        <div class="title-row">
                            <a
                                href={setUuid ? setLinkHref(setUuid) : "/"}
                                class="title-link"
                                title={track.title}
                                onClick={(e) => {
                                    if (setUuid) { e.preventDefault(); window.location.href = setLinkHref(setUuid); }
                                }}
                            >
                                {track.title}
                            </a>
                        </div>
                        <div class="artist-row">
                            {artistUuid ? (
                                <a
                                    href={`/artist/${artistUuid}`}
                                    class="artist-link"
                                    title={track.artist}
                                    onClick={(e) => { e.preventDefault(); window.location.href = `/artist/${artistUuid}`; }}
                                >
                                    {track.artist}
                                </a>
                            ) : (
                                <span class="artist-link">{track.artist}</span>
                            )}
                        </div>
                        {playError.value && (
                            <span class="play-error" role="status">{playError.value}</span>
                        )}
                    </Container>

                    {/* Seek bar with filled progress. */}
                    <div class="seek-wrap">
                        <div
                            class="seek-track"
                            ref={seekRef}
                            onMouseMove={(e) => onSeekMove(e.clientX)}
                            onMouseLeave={() => { setSeekHover(null); setSeekDragging(false); }}
                            onMouseDown={(e) => {
                                const t = seekAt(e.clientX);
                                if (t == null) return;
                                seekTo(t);
                                setSeekHover(t);
                                setSeekDragging(true);
                            }}
                            onMouseUp={() => setSeekDragging(false)}
                            role="slider"
                            aria-label="Seek"
                            aria-valuenow={position.value}
                            aria-valuemin={0}
                            aria-valuemax={duration.value}
                            tabIndex={-1}
                        >
                            <div class="seek-fill" style={{ width: `${playedPct}%` }}>
                                {wavePlaying && (
                                    <svg class="seek-wave" viewBox="0 0 24 12" preserveAspectRatio="none" aria-hidden="true">
                                        <path d="M0 6 Q6 1 12 6 T24 6" />
                                    </svg>
                                )}
                            </div>
                            {seekHover != null && !seekDragging && duration.value > 0 && (
                                <div class="seek-preview" style={{ left: `${(seekHover / duration.value) * 100}%` }}>
                                    {formatTime(seekHover)}
                                </div>
                            )}
                            <div class="seek-thumb" style={{ left: `${playedPct}%` }} />
                        </div>
                        <div class="seek-times">
                            <Text dim content={formatTime(position.value)} />
                            <Text dim content={formatTime(duration.value)} />
                        </div>
                    </div>

                    {/* Volume with mute. */}
                    <Container horizontal centered_y class="volume-wrap">
                        <IconButton
                            title={isMutedEffective ? "Unmute" : "Mute"}
                            onClick={toggleMuteButton}
                        >
                            {isMutedEffective ? <VolumeX size={16} /> : <Volume2 size={16} />}
                        </IconButton>
                        <div
                            class="volume-track"
                            ref={volRef}
                            onMouseMove={(e) => onVolumeMove(e.clientX)}
                            onMouseLeave={() => setVolumeHover(null)}
                            onMouseDown={(e) => {
                                const v = volumeAt(e.clientX);
                                if (v == null) return;
                                setVolume(v);
                                setVolumeHover(v);
                                setVolumeDragging(true);
                            }}
                            onMouseUp={() => setVolumeDragging(false)}
                        >
                            <div class="volume-fill" style={{ width: `${Math.max(0, volume.value) * 100}%` }} />
                            <div class="volume-thumb" style={{ left: `${Math.max(0, volume.value) * 100}%` }} />
                        </div>
                        {volumeHover != null && (
                            <Text dim class="volume-preview" content={`${Math.round(volumeHover * 100)}%`} />
                        )}
                    </Container>

                    {/* Like / queue / lyrics. */}
                    <Container horizontal centered_y class="player-actions">
                        <IconButton
                            title={currentLiked.value ? "Unlike" : "Like"}
                            variant={currentLiked.value ? "accent-subtle" : "always-transparent"}
                            onClick={() => void toggleCurrentLike()}
                        >
                            <Heart size={16} fill={currentLiked.value ? "currentColor" : "none"} />
                        </IconButton>
                        <IconButton
                            title={showQueue.value ? "Hide up next" : "Up next"}
                            variant={showQueue.value ? "accent-subtle" : "always-transparent"}
                            onClick={() => { queueOpen.value = !queueOpen.value; }}
                        >
                            <ListMusic size={16} />
                        </IconButton>
                        <IconButton
                            title={showLyrics ? "Hide lyrics" : "Lyrics"}
                            variant={showLyrics ? "accent-subtle" : "always-transparent"}
                            onClick={() => setShowLyrics(!showLyrics)}
                        >
                            <MicVocal size={16} />
                        </IconButton>
                    </Container>
                </Container>

                {showQueue.value && (
                    <Container class="queue-drawer">
                        <Container horizontal centered_y class="queue-head">
                            <Text class="queue-title" content="Up next" />
                            <Text dim content={` · ${queueTracks.length} track${queueTracks.length == 1 ? "" : "s"}`} />
                            <IconButton title="Close queue" onClick={() => { queueOpen.value = false; }}>
                                <X size={14} />
                            </IconButton>
                        </Container>
                        {queueTracks.length === 0 && (
                            <div class="queue-empty">Nothing queued — play an album to fill this up.</div>
                        )}
                        <div class="queue-list">
                            {queueTracks.map((t, i) => (
                                <button
                                    type="button"
                                    key={`${t.id}-${i}`}
                                    class={`queue-row${i === queueIndex.value ? " queue-row-active" : ""}`}
                                    onClick={() => playQueueIndex(i)}
                                >
                                    <Text dim content={i + 1} class="queue-num" />
                                    <span class="queue-info">
                                        <span class="queue-title-text">{t.title}</span>
                                        <span class="queue-artist-text">{t.artist}</span>
                                    </span>
                                    {i === queueIndex.value && <Text dim content={formatTime(position.value)} />}
                                </button>
                            ))}
                            <button
                                type="button"
                                class={`queue-row queue-autoplay${autoplay.value ? " queue-row-active" : ""}`}
                                title={autoplay.value ? "Autoplay on — similar tracks are added at the end" : "Autoplay off"}
                                onClick={() => setAutoplay(!autoplay.value)}
                            >
                                <Radio size={15} />
                                <span class="queue-info">
                                    <span class="queue-title-text">Autoplay</span>
                                    <span class="queue-artist-text">
                                        {autoplay.value ? "On — keep the music going" : "Off"}
                                    </span>
                                </span>
                            </button>
                        </div>
                    </Container>
                )}
            </FooterContainer>
        </>
    );
}
```

### `ui/src/components/PlayerBar/style.css`

```css
#player-bar {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 40;
    padding: 10px 16px;
    padding-bottom: max(10px, env(safe-area-inset-bottom));
    /* One flat tonal container; no translucency, blur or elevation. */
    background: var(--md-surface-container);
    border-top: 1px solid var(--layer-rim);
    border-radius: var(--radius-xl) var(--radius-xl) 0 0;
    display: flex;
    align-items: center;
}

#player-bar .player {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    max-width: 100%;
    flex-wrap: nowrap;
}

#player-bar .art-wrap {
    position: relative;
    flex: none;
    cursor: pointer;
    border-radius: var(--radius-lg);
    overflow: hidden;
    background: var(--surface-lift);
}

#player-bar .art,
#player-bar .art-wrap .cover-art {
    width: 56px;
    height: 56px;
    border-radius: var(--radius-xl);
    object-fit: cover;
    background: var(--surface-lift);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--accent);
}

#player-bar .transport {
    gap: 4px;
    flex: none;
}

#player-bar .button:active {
    transform: scale(var(--press-scale));
}

#player-bar .play-pause {
    min-width: var(--touch-target);
    min-height: var(--touch-target);
    justify-content: center;
    background: var(--accent);
    color: var(--text-on-light);
    border-radius: var(--radius-pill);
    transition: border-radius var(--morph-ms) cubic-bezier(0.2, 0.9, 0.2, 1.2),
                transform var(--transition-fast), background var(--transition-fast);
}

#player-bar .play-pause.playing {
    border-radius: 18px;
    background: var(--accent-hover);
}

#player-bar .play-pause svg {
    transition: transform var(--morph-ms) cubic-bezier(0.2, 0.9, 0.2, 1.2);
}

#player-bar .play-pause.playing svg {
    transform: rotate(90deg);
}

#player-bar .meta {
    min-width: 0;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
}

#player-bar .title-row {
    display: flex;
}

#player-bar .title-link {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--text-bright);
    text-decoration: none;
    font-weight: 600;
}

#player-bar .title-link:hover {
    text-decoration: underline;
}

#player-bar .artist-row {
    display: flex;
}

#player-bar .artist-link {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--text-dim);
    text-decoration: none;
    font-size: var(--font-size-medium);
}

#player-bar .artist-link:hover {
    text-decoration: underline;
}

#player-bar .play-error {
    display: block;
    color: var(--danger);
    font-size: var(--font-size-small);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Seek bar: filled progress in the accent color. */
#player-bar .seek-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 120px;
    flex: 2;
}

#player-bar .seek-track {
    position: relative;
    flex: 1;
    min-width: 0;
    height: 32px;
    display: flex;
    align-items: center;
    cursor: pointer;
}

#player-bar .seek-track::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    height: 8px;
    border-radius: var(--radius-pill);
    background: var(--md-surface-container-highest);
}

#player-bar .seek-fill {
    position: relative;
    height: 8px;
    border-radius: var(--radius-pill);
    background: var(--accent);
    width: 0%;
    transition: width 0.1s linear;
}

/* The wave only exists while playing and playful motion is on; CSS media and
   the root dataset disable it for reduced motion / the local setting. */
#player-bar .seek-wave {
    position: absolute;
    right: -6px;
    top: -2px;
    width: 20px;
    height: 12px;
    color: var(--accent);
    overflow: visible;
}

#player-bar .seek-wave path {
    fill: none;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    animation: seek-wave-bob calc(1s / var(--progress-wave-hz)) ease-in-out infinite alternate;
}

@keyframes seek-wave-bob {
    from { transform: translateY(-2px); }
    to { transform: translateY(2px); }
}

html[data-playful="false"] #player-bar .seek-wave { display: none; }

@media (prefers-reduced-motion: reduce) {
    #player-bar .seek-wave { display: none; }
    #player-bar .seek-wave path { animation: none; }
}

#player-bar .seek-thumb {
    position: absolute;
    left: 0%;
    top: 50%;
    width: 14px;
    height: 14px;
    margin-top: -7px;
    margin-left: -7px;
    border-radius: 50%;
    background: var(--text-bright);
    transition: left 0.1s linear, width 0.1s, height 0.1s, margin-top 0.1s, margin-left 0.1s;
}

#player-bar .seek-track:hover .seek-thumb {
    width: 18px;
    height: 18px;
    margin-top: -9px;
    margin-left: -9px;
    background: var(--accent-hover);
}

#player-bar .seek-preview {
    position: absolute;
    top: -20px;
    transform: translateX(-50%);
    padding: 2px 6px;
    border-radius: 6px;
    background: var(--prim);
    border: 1px solid var(--back-border);
    color: var(--text-bright);
    font-size: var(--font-size-small);
    font-variant-numeric: tabular-nums;
    pointer-events: none;
    white-space: nowrap;
}

#player-bar .seek-times {
    display: flex;
    gap: 10px;
    flex-shrink: 0;
}

#player-bar .seek-times > * {
    font-size: var(--font-size-small);
    color: var(--text-dim);
    font-variant-numeric: tabular-nums;
}

/* Volume bar. */
#player-bar .volume-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    flex: none;
    min-width: 110px;
}

#player-bar .volume-track {
    position: relative;
    flex: 1;
    min-width: 0;
    height: 32px;
    display: flex;
    align-items: center;
    cursor: pointer;
}

#player-bar .volume-track::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    height: 8px;
    border-radius: var(--radius-pill);
    background: var(--md-surface-container-highest);
}

#player-bar .volume-fill {
    position: relative;
    height: 8px;
    border-radius: var(--radius-pill);
    background: var(--accent);
    width: 0%;
    transition: width 0.1s linear;
}

#player-bar .volume-thumb {
    position: absolute;
    left: 0%;
    top: 50%;
    width: 12px;
    height: 12px;
    margin-top: -6px;
    margin-left: -6px;
    border-radius: 50%;
    background: var(--text);
    transition: left 0.1s linear, width 0.1s, height 0.1s, margin-top 0.1s, margin-left 0.1s;
}

#player-bar .volume-track:hover .volume-thumb {
    width: 14px;
    height: 14px;
    margin-top: -7px;
    margin-left: -7px;
    background: var(--accent-hover);
}

#player-bar .volume-preview {
    font-size: var(--font-size-small);
    font-variant-numeric: tabular-nums;
    flex-shrink: 0;
}

#player-bar .queue-drawer {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 100%;
    margin-bottom: 6px;
    z-index: 46;
    background: var(--md-surface-container-high);
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius);
    width: min(460px, calc(100vw - 24px));
    margin-left: auto;
    margin-right: auto;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    animation: queue-slide-in 0.2s ease-out;
}

@keyframes queue-slide-in {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

#player-bar .queue-head {
    gap: 8px;
    padding: 10px 12px;
    border-bottom: 1px solid var(--back-border);
}

#player-bar .queue-title {
    font-weight: 600;
    margin: 0;
}

#player-bar .queue-list {
    max-height: 260px;
    overflow: auto;
    overscroll-behavior: contain;
}

#player-bar .queue-row {
    display: flex;
    align-items: center;
    width: 100%;
    min-height: var(--touch-target);
    padding: 8px 12px;
    gap: 10px;
    cursor: pointer;
    background: transparent;
    border: 0;
    border-radius: var(--radius-pill);
    color: inherit;
    font: inherit;
    text-align: left;
}

#player-bar .queue-row:hover {
    background: var(--flat-hover);
}

#player-bar .queue-row-active {
    background: var(--accent-soft);
    border-radius: var(--radius-pill);
}

#player-bar .queue-num {
    flex: none;
    min-width: 20px;
    text-align: right;
    color: var(--text-dim);
}

/* Autoplay is the last queue row; a separator makes it read as a setting
   rather than another track. */
#player-bar .queue-autoplay {
    border-top: 1px solid var(--back-border);
    color: var(--text-dim);
}

#player-bar .queue-autoplay.queue-row-active {
    color: var(--accent);
}

#player-bar .queue-autoplay > svg {
    flex: none;
    min-width: 20px;
}

#player-bar .queue-empty {
    padding: 20px 16px 24px;
    text-align: center;
    color: var(--text-dim);
    font-size: var(--font-size-small);
}

#player-bar .queue-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
}

#player-bar .queue-title-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

#player-bar .queue-artist-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: var(--font-size-small);
    color: var(--text-dim);
}

#player-bar .player-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    flex: none;
}

/* Phones get two rows: art / title / transport / actions, then a full-width
   seek line. A single row squeezed the title down to a few pixels. */
@media (max-width: 800px) {
    :root {
        --player-h: 92px;
    }

    #player-bar {
        padding: 6px 10px calc(6px + env(safe-area-inset-bottom));
    }

    #player-bar .player {
        display: grid;
        grid-template-columns: 42px minmax(0, 1fr) auto auto;
        grid-template-areas:
            "art meta transport actions"
            "seek seek seek seek";
        column-gap: 8px;
        row-gap: 4px;
    }

    #player-bar .art-wrap {
        grid-area: art;
    }

    #player-bar .art {
        width: 42px;
        height: 42px;
    }

    #player-bar .meta {
        grid-area: meta;
    }

    #player-bar .transport {
        grid-area: transport;
        gap: 4px;
    }

    #player-bar .player-actions {
        grid-area: actions;
        gap: 4px;
    }

    #player-bar .seek-wrap {
        grid-area: seek;
        width: 100%;
        min-width: 0;
        flex: none;
    }

    #player-bar .seek-times {
        display: none;
    }

    #player-bar .volume-wrap,
    #player-bar .transport .control-shuffle,
    #player-bar .transport .control-repeat {
        display: none;
    }

    #player-bar .transport .button,
    #player-bar .player-actions .button {
        min-width: var(--touch-target);
        min-height: var(--touch-target);
        padding: 0 6px;
    }
}

@media (max-width: 360px) {
    #player-bar .player {
        grid-template-columns: minmax(0, 1fr) auto auto;
        grid-template-areas:
            "meta transport actions"
            "seek seek seek";
    }

    #player-bar .art-wrap,
    #player-bar .player-actions .button:first-child {
        display: none;
    }
}
```

### `ui/src/components/SearchBar/SearchItem.tsx`

```tsx
/** One result row in the search popout (track, album or artist).
 */
import {
    Case,
    Container,
    DotSeperator,
    LinkButton,
    Switch,
    Text,
    type LinkButtonProps
} from "flufi-ui/components";
import type { SearchItem } from "../../common/net/types";
import { ArtistPfp, SetCover, TrackCover } from "../Library/Image";

export function SearchItemElem(props: { item: SearchItem, close?: () => void }) {
    const buttonProps: Omit<LinkButtonProps, "href"> = {
        noPadding: true,
        variant: "always-transparent"
    };

    return (
        <>
            <Switch value={props.item.type}>
                <Case value="artist" children={() => {
                    const item = props.item as Extract<SearchItem, { type: "artist" }>;

                    return (
                        <LinkButton {...buttonProps} href={`/artist/${item.uuid}`} onClick={props.close}>
                            <ArtistPfp {...item} size={40} />
                            <Container vertical centered_y>
                                <Text content={item.artist.name} />
                                <Container horizontal class="dim">
                                    <Text class="capitalised" content="artist" />
                                </Container>
                            </Container>
                        </LinkButton>
                    )
                }} />
                <Case value="set" children={() => {
                    const item = props.item as Extract<SearchItem, { type: "set" }>;

                    return (
                        <LinkButton {...buttonProps} href={`/set/${item.uuid}`} onClick={props.close}>
                            <SetCover {...item} size={40} />
                            <Container vertical centered_y>
                                <Text content={item.set.name} />
                                <Container horizontal class="dim" centered_y>
                                    <Text class="capitalised" content={item.set.kind} />
                                    <DotSeperator containerTextMargin />
                                    <Text content={item.artist?.name.value ?? "Unknown artist"} />
                                </Container>
                            </Container>
                        </LinkButton>
                    )
                }} />
                <Case value="track" children={() => {
                    const item = props.item as Extract<SearchItem, { type: "track" }>;
                    const href = item.track.set ? `/set/${item.track.set}` : "/";

                    return (
                        <LinkButton {...buttonProps} href={href} onClick={props.close}>
                            <TrackCover {...item} size={40} />
                            <Container vertical centered_y>
                                <Text content={item.track.name} />
                                <Container horizontal class="dim" centered_y>
                                    <Text class="capitalised" content={item.set?.name} />
                                    <DotSeperator containerTextMargin />
                                    <Text content={item.artist?.name.value ?? "Unknown artist"} />
                                </Container>
                            </Container>
                        </LinkButton>
                    )
                }} />
            </Switch>
        </>
    )
}
```

### `ui/src/components/SearchBar/style.css`

```css

.search-bar {
    width: 300px;
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius-pill);
    overflow: hidden;
    background: var(--surface-lift);
}

.search-bar .search-input {
    flex: 1;
    width: 100%;
}

.search-bar:focus-within {
    border-color: var(--accent);
    outline: 2px solid var(--accent);
    outline-offset: 1px;
}

.search-bar .search-input::placeholder {
    color: var(--text-dark);
}

.mobile .search-bar {
    min-height: var(--touch-target);
}

.search-popout > div {
    padding: 10px;
    gap: 10px;
    
    > .button {
        font-size: var(--font-size-medium);
        
        > img {
            border-radius: var(--radius);
        }
        
        > div {
            gap: 2px;
            
            > .dim {
                color: var(--text-dim);
                font-size: var(--font-size-small);
            }
            
            > div {
                text-wrap: nowrap;
                text-overflow: ellipsis;
                overflow: hidden;
                max-width: calc(270px - 40px);
                
                > span {
                    text-overflow: ellipsis;
                    overflow: hidden;

                    &.capitalised {
                        text-transform: capitalize;;
                    }
                }
            }
        }
    }
}

.mobile {
    #search-bar {
        width: unset;
    }
}

.search-popout.mobile-popout > div {
    > .button {
        > div {
            max-width: calc(100vw - 180px);
        }
    }
}
```

### `ui/src/components/Topbar/Topbar.tsx`

```tsx
/** Top bar: brand, search and navigation on one row at every width.
 */
import type { ComponentChildren } from "preact";
import { Home, LogOut, Menu, Music2, Plus } from "lucide-preact";
import { Container, HeaderContainer, IconButton, IconLinkButton, If, Text } from "flufi-ui/components";
import { MOBILE } from "flufi-ui/common";
import { SearchBar } from "../SearchBar/SearchBar";
import { currentUser, logout } from "../../common/auth";
import { toggleMobileSidebar } from "../LeftSidebar/LeftSidebar";

import "./style.css";

export function Topbar() {
    return (
        <HeaderContainer other={{ id: "topbar" }}>
            <Container class="middle">
                <IconLink href="/" label="mcmusic home" class="brand-link">
                    <span class="brand-mark"><Music2 size={18} /></span>
                    <span class="logo text">mcmusic</span>
                </IconLink>
                <If cond={MOBILE.value}>
                    <IconButton title="Open menu" onClick={toggleMobileSidebar}>
                        <Menu size={20} />
                    </IconButton>
                </If>
                <If cond={!MOBILE.value}>
                    <IconLink href="/" label="Home">
                        <Home size={20} />
                    </IconLink>
                </If>
                <SearchBar />
                <IconLink href="/upload" label="Add music">
                    <Plus size={20} />
                </IconLink>
                {currentUser.value && (
                    <span class="user-pill" title={currentUser.value.username}>
                        <Text class="user" content={currentUser.value.username} />
                    </span>
                )}
                <IconButton
                    title="Log out"
                    onClick={async () => {
                        await logout();
                        window.location.href = "/auth";
                    }}
                >
                    <LogOut size={18} />
                </IconButton>
            </Container>
        </HeaderContainer>
    )
}

/** flufi's link buttons take no title, so label them from the outside and give
 * the anchor a real accessible name. */
function IconLink(props: {
    href: string;
    label: string;
    children: ComponentChildren;
    class?: string;
}) {
    return (
        <span class="icon-tip" title={props.label}>
            <IconLinkButton href={props.href} class={props.class}>
                {props.children}
                <span class="sr-only">{props.label}</span>
            </IconLinkButton>
        </span>
    )
}
```

### `ui/src/components/Topbar/style.css`

```css
/* One horizontal chrome row. flufi's HeaderContainer is a column by default,
   so override it here; the title must share the row with search and actions. */
#topbar {
    display: flex;
    flex-direction: row;
    align-items: center;
    min-height: var(--topbar-h);
    height: var(--topbar-h);
    padding: 0 16px;
    border-bottom: 1px solid var(--layer-rim);
    background: var(--md-surface-container-low);
    position: relative;
    z-index: 2;
}

#topbar > .middle {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 8px;
    width: 100%;
    min-width: 0;
    height: 100%;
}

#topbar .brand-link {
    gap: 10px;
    padding: 0 6px 0 0;
    flex: none;
    text-decoration: none;
}

#topbar .brand-link .logo {
    white-space: nowrap;
}

#topbar .search-bar {
    width: min(380px, 34vw);
    min-width: 180px;
    margin-inline: auto;
}

#topbar .user-pill {
    display: inline-flex;
    align-items: center;
    min-height: 40px;
    max-width: 160px;
    padding: 0 16px;
    border-radius: var(--radius-pill);
    background: var(--md-secondary-container);
    color: var(--md-on-secondary-container);
    flex: none;
}

#topbar .user {
    max-width: 140px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.brand-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    color: var(--md-on-primary-container);
    background: var(--md-primary-container);
    border-radius: 14px;
    transition: transform var(--transition-fast) var(--spring-ease);
}

#topbar .brand-link:hover .brand-mark {
    transform: rotate(-8deg);
}

.mobile {
    #topbar {
        padding: 0 8px;
    }

    #topbar > .middle {
        gap: 4px;
    }

    #topbar .user-pill,
    #topbar .icon-tip[title="Home"] {
        display: none;
    }

    #topbar .brand-link {
        padding-right: 0;
        gap: 0;
    }

    /* The wordmark stays visible on phones; the icon is redundant there. */
    #topbar .brand-mark {
        display: none;
    }

    #topbar .brand-link .logo {
        font-size: var(--type-title-size);
    }

    #topbar .search-bar {
        width: auto;
        min-width: 70px;
        flex: 1;
        margin-inline: 0;
    }

    #topbar .icon-tip .button,
    #topbar > .middle > .button {
        min-width: var(--touch-target);
        min-height: var(--touch-target);
        padding: 0 6px;
    }
}
```

### `ui/src/components/Track/style.css`

```css

.track-row-wrap {
    display: flex;
    width: 100%;
    min-width: 0;
}

.track-row-wrap > .track {
    width: 100%;
}

.track {
    display: flex;
    align-items: center;
    padding: 6px 12px;
    gap: 8px;

    min-height: var(--touch-target);
    min-width: 0;
    border-radius: var(--radius-pill);

    transition: background var(--transition-fast), color var(--transition-fast);

    &.border {
        border: 1px solid var(--layer-rim);
        border-radius: var(--radius-lg);
    }

    &:hover {
        background: color-mix(in srgb, var(--accent) 10%, var(--prim));
    }

    &.current {
        background: var(--accent-soft);
        outline: 1px solid var(--accent);
        outline-offset: -1px;
    }

    &:has(.grip) {
        padding-left: 10px;
    }

    > .left {
        position: relative;
        display: flex;
        align-items: center;
        min-width: 15px;

        > .track-number {
            position: relative;
            text-align: right;
        }

        > svg {
            position: relative;
        }

        > .equaliser {
            width: 15px;
        }
    }

    /* Hover (not the current track): swap the number for a play icon. */
    &:not(.current):hover > .left {
        > .track-number { display: none; }
        > svg.play-icon { display: unset; }
        > svg.pause-icon { display: none; }
        > .equaliser { display: none; }
    }

    &:not(.current):hover > .left > svg.play-icon { display: unset; }

    /* Current track (playing or paused): highlight the title. */
    &.current > .center > .name {
        color: var(--accent);
        font-weight: 600;
    }

    &.current > .left {
        > .track-number { display: none; }
    }

    &.playing > .left {
        > svg.play-icon { display: none; }
        > svg.pause-icon { display: none; }
        > .equaliser { display: flex; }
    }

    &.current:not(.playing) > .left {
        > svg.play-icon { display: none; }
        > svg.pause-icon { display: unset; }
        > .equaliser { display: none; }
    }

    > .center {
        display: flex;
        flex-direction: column;
        flex: 1;
        min-width: 0;
        gap: 2px;
    }

    > .center > .name,
    > .center > .artist {
        display: block;
        min-width: 0;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    /* Duration column, right-aligned. */
    > .duration {
        flex: none;
        text-align: right;
        font-variant-numeric: tabular-nums;
        min-width: 32px;
    }

    /* Equaliser is shown only while the track plays; CSS handles the pulse. */
    .equaliser {
        display: flex;
    }
}
```

### `ui/src/pages/Artists/style.css`

```css
.artists .library-card {
    text-align: center;
    padding: 12px;
    border-radius: var(--radius);
    background: var(--md-surface-container-low);
}

.artists .artist-pfp {
    border-radius: 50%;
}
```

### `ui/src/pages/Home/Home.tsx`

```tsx
/** Home: a bold, flat greeting, real personalised shelves, then the library.
 *
 * Shelf titles come straight from /api/home. Nothing is relabelled as a Mix,
 * Radio destination or global chart; "Made for you" only appears when the
 * server actually produced that recommendation shelf.
 */
import { useEffect, useState } from "preact/hooks";
import {
    Button, Container, Content, Header2, Header3, Input, Loading, SelectBox, Text,
} from "flufi-ui/components";
import { ArrowDownUp, Disc3, ListFilter, Play, Sparkles } from "lucide-preact";
import { EmptyState } from "../../components/EmptyState/EmptyState";
import { SetCard } from "../../components/Library/Card";
import { TrackList } from "../../components/TrackList/TrackList";
import { API, parseArtistUuid } from "../../common/net/api";
import type { HomeSection, Set, Track } from "../../common/net/types";
import { playQueue } from "../../common/player";

import "./style.css";

const PAGE = 60;

const SORTS = [
    { value: "name", label: "A–Z" },
    { value: "artist", label: "Artist" },
    { value: "recent", label: "Recently added" },
];

function artistNames(set: Set): string {
    const names: string[] = [];
    for (const track of set.tracks.value) {
        for (const uuid of track.artists.value) {
            const name = parseArtistUuid(uuid).name;
            if (!names.includes(name)) names.push(name);
        }
    }
    return names.join(", ") || set.artistName || "";
}

function queueFor(section: HomeSection) {
    return section.tracks.map(t => ({
        id: t.uuid,
        title: t.name.value,
        artist: t.artists.value.map(u => parseArtistUuid(u).name).join(", "),
        setUuid: t.set ?? undefined,
        artistUuid: t.artists.value[0],
    }));
}

export function HomePage() {
    const [albums, setAlbums] = useState<Set[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [query, setQuery] = useState("");
    const [sort, setSort] = useState("name");
    const [singles, setSingles] = useState(false);
    const [count, setCount] = useState(PAGE);

    const [tracks, setTracks] = useState<Track[] | null>(null);
    const [shelves, setShelves] = useState<HomeSection[]>([]);

    useEffect(() => {
        API.listTracks(50).then(setTracks).catch(() => setTracks([]));
        API.home()
            .then(d => setShelves(d.sections.filter(s => s.tracks.length > 0).slice(0, 4)))
            .catch(() => { /* personalised shelves are optional */ });
    }, []);

    useEffect(() => {
        let cancelled = false;
        const timer = setTimeout(() => {
            setLoading(true);
            API.listAlbums({
                limit: count,
                offset: 0,
                q: query.trim(),
                sort,
                minTracks: singles ? 1 : 2,
            })
                .then((r) => {
                    if (cancelled) return;
                    setAlbums(r.albums);
                    setTotal(r.total);
                    setError(null);
                })
                .catch(() => {
                    if (cancelled) return;
                    setAlbums([]);
                    setTotal(0);
                    setError("Could not load albums. Check the connection and try again.");
                })
                .finally(() => {
                    if (!cancelled) setLoading(false);
                });
        }, query ? 250 : 0);

        return () => {
            cancelled = true;
            clearTimeout(timer);
        };
    }, [query, sort, singles, count]);

    function changeQuery(value: string) {
        setQuery(value);
        setCount(PAGE);
    }

    function changeSort(value: string | null) {
        setSort(value ?? "name");
        setCount(PAGE);
    }

    function toggleSingles() {
        setSingles(v => !v);
        setCount(PAGE);
    }

    async function playAlbum(set: Set) {
        try {
            const full = await API.getSet(set.uuid);
            const ts = full.tracks.value;
            if (ts.length === 0) return;
            const list = ts
                .filter(t => t.uuid)
                .map(t => ({
                    id: t.uuid,
                    title: t.name.value,
                    artist: t.artists.value.map(u => parseArtistUuid(u).name).join(", "),
                    setUuid: full.uuid,
                    artistUuid: t.artists.value[0] ?? null,
                }));
            if (list.length > 0) playQueue(list, 0);
        } catch {
            setError("Could not start that album.");
        }
    }

    function playShelf(section: HomeSection) {
        const list = queueFor(section);
        if (list.length) playQueue(list, 0);
    }

    const [hero, ...otherShelves] = shelves;
    const skeletonCount = loading && albums.length === 0 ? Math.min(total || PAGE, PAGE) : 0;

    return (
        <Content class="home">
            <Container extra_gap>
                {hero && (
                    <Container class="home-hero">
                        <div class="hero-badge"><Sparkles size={18} /> Your music</div>
                        <Header2 class="hero-title">{hero.title}</Header2>
                        <Text dim content="A real shelf from your listening history — press play whenever you're ready." />
                        <div class="hero-actions">
                            <Button variant="accent" class="hero-play" onClick={() => playShelf(hero)}>
                                <Play size={18} /> Play {hero.title}
                            </Button>
                            <Text dim content={`${hero.tracks.length} tracks`} />
                        </div>
                    </Container>
                )}

                {otherShelves.length > 0 && (
                    <Container class="home-shelves">
                        <Container horizontal centered_y class="shelves-head">
                            <Header3>From your listening</Header3>
                            {otherShelves.length > 0 && (
                                <Text dim content="Built from plays and likes on this server" />
                            )}
                        </Container>
                        <div class="shelf-chips">
                            {otherShelves.map(section => (
                                <Button
                                    key={section.title}
                                    variant="panel"
                                    class="shelf-chip"
                                    title={`Play ${section.title}`}
                                    onClick={() => playShelf(section)}
                                >
                                    <Play size={14} /> {section.title}
                                </Button>
                            ))}
                        </div>
                        {otherShelves.map(section => (
                            <Container key={section.title} class="home-shelf">
                                <Container horizontal centered_y class="shelf-head">
                                    <Header3>{section.title}</Header3>
                                    <Button variant="panel" title={`Play ${section.title}`} onClick={() => playShelf(section)}>
                                        <Play size={14} /> Play
                                    </Button>
                                </Container>
                                <TrackList tracks={section.tracks.slice(0, 8)} showDuration={true} />
                            </Container>
                        ))}
                    </Container>
                )}

                <Container class="home-library">
                    <Header2>Albums</Header2>
                    <Container horizontal centered_y class="album-controls">
                        <label class="control-with-icon">
                            <ListFilter size={15} aria-hidden="true" />
                            <Input
                                class="album-filter"
                                placeholder="Filter albums"
                                value={query}
                                onInput={changeQuery}
                            />
                        </label>
                        <label class="control-with-icon">
                            <ArrowDownUp size={15} aria-hidden="true" />
                            <SelectBox
                                class="album-sort"
                                options={SORTS}
                                value={sort}
                                onChange={changeSort}
                            />
                        </label>
                        <Button
                            variant={singles ? "accent" : "panel"}
                            title="Include one-song albums"
                            onClick={toggleSingles}
                        >
                            <Disc3 size={15} /> Singles
                        </Button>
                        {!loading && (
                            <Text dim content={`${total} album${total == 1 ? "" : "s"}`} />
                        )}
                    </Container>

                    {error && <Text class="error" content={error} />}

                    {loading && albums.length === 0
                        ? (
                            <div class="album-grid skeleton-grid">
                                {[...Array(skeletonCount)].map((_, i) => (
                                    <div key={i} class="skeleton-card">
                                        <div class="skeleton-cover" />
                                        <div class="skeleton-title" />
                                        <div class="skeleton-sub" />
                                    </div>
                                ))}
                            </div>
                        )
                        : albums.length === 0
                            ? (
                                <EmptyState
                                    icon={<Disc3 size={22} />}
                                    title={query ? "No matching albums" : "No albums yet"}
                                    body={query
                                        ? `Nothing matches “${query}”. Try a different filter.`
                                        : "Add music from the top bar and it will show up here."}
                                />
                            )
                            : (
                                <div class="album-grid">
                                    {albums.map(a => (
                                        <SetCard
                                            key={a.uuid}
                                            set={a}
                                            subtitle={artistNames(a) || a.artistName}
                                            onPlay={() => playAlbum(a)}
                                        />
                                    ))}
                                </div>
                            )}

                    {!loading && albums.length > 0 && albums.length < total && (
                        <Button
                            variant="panel"
                            class="load-more"
                            onClick={() => setCount(c => c + PAGE)}
                        >
                            Load more
                        </Button>
                    )}
                </Container>

                <Container class="home-songs">
                    <Header2>Songs</Header2>
                    <Loading loaded={tracks != null}>
                        {() => <TrackList tracks={tracks!} />}
                    </Loading>
                </Container>
            </Container>
        </Content>
    )
}
```

### `ui/src/pages/Home/style.css`

```css
/* Home uses the shell's own page padding; the grid stretches to the content
   width so album tiles fill the row instead of shrink-wrapping to the centre. */
.content-home {
    align-items: stretch;
    justify-content: flex-start;
}

/* Hero shelf: a flat tonal card, no gradient and no decorative shadow. */
.home-hero {
    align-items: flex-start;
    gap: 12px;
    padding: 28px;
    border-radius: var(--radius-xl);
    background: var(--md-primary-container);
    color: var(--md-on-primary-container);
}

.home-hero .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: var(--radius-pill);
    background: var(--md-secondary-container);
    color: var(--md-on-secondary-container);
    font-size: var(--type-label-size);
    font-weight: var(--type-label-weight);
}

.home-hero .hero-title {
    margin: 0;
    max-width: 22ch;
}

.home-hero .dim,
.home-hero .hero-actions .dim {
    color: var(--md-on-primary-container);
    opacity: 0.82;
}

.home-hero .hero-actions {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 8px;
}

.home-hero .hero-play {
    background: var(--accent);
    color: var(--text-on-light);
    border: 0;
}

.home-shelves {
    gap: 12px;
}

.home-shelves .shelves-head {
    justify-content: space-between;
    gap: 12px;
}

.shelf-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.home-shelf {
    padding: 16px;
    border-radius: var(--radius);
    background: var(--md-surface-container-low);
}

.home-shelf .shelf-head {
    gap: 10px;
    margin-bottom: 6px;
}

.home-shelf .shelf-head > :last-child {
    margin-left: auto;
}

.album-controls {
    gap: 10px;
    flex-wrap: wrap;
    margin: 10px 0 16px;
}

.album-controls .album-filter {
    width: 220px;
    min-width: 0;
}

.album-controls .album-sort {
    width: 170px;
}

.control-with-icon {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    min-width: 0;
    color: var(--text-dim);
}

.control-with-icon > svg {
    flex: none;
    color: var(--accent);
}


/* auto-fill keeps every column the same width, so the last card in a row can
   never overflow the pane or get clipped. min-width: 0 on cards lets them
   shrink below their content size inside grid cells. */
.album-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(clamp(150px, 12vw, 210px), 1fr));
    gap: 16px;
    width: 100%;
    overflow-x: hidden;
}

.album-grid .library-card {
    width: 100%;
    min-width: 0;
}

.load-more {
    margin-top: 16px;
}

/* Skeleton cards shown while the first page of albums loads. */
.skeleton-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(clamp(150px, 12vw, 210px), 1fr));
    gap: 16px;
    width: 100%;
    overflow-x: hidden;
}

.skeleton-card {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.skeleton-cover {
    width: 100%;
    aspect-ratio: 1 / 1;
    border-radius: var(--radius);
    background: var(--prim);
    position: relative;
    overflow: hidden;
}

.skeleton-cover::before {
    content: "";
    position: absolute;
    inset: 0;
    background: var(--surface-lift);
    animation: skeleton-pulse 1.5s infinite linear;
}

.skeleton-title {
    margin-top: 8px;
    height: 1.3em;
    border-radius: 4px;
    background: var(--prim);
    width: 70%;
    animation: skeleton-pulse 1.5s infinite linear;
}

.skeleton-sub {
    margin-top: 4px;
    height: 1em;
    border-radius: 4px;
    background: var(--prim);
    width: 55%;
    animation: skeleton-pulse 1.5s infinite linear;
}

@keyframes skeleton-pulse {
    0%, 100% { opacity: 0.35; }
    50% { opacity: 0.8; }
}

@media (max-width: 800px) {
    .album-grid,
    .skeleton-grid {
        grid-template-columns: repeat(auto-fill, minmax(122px, 1fr));
        gap: 12px;
    }

    .album-controls .album-filter,
    .album-controls .album-sort {
        flex: 1;
        width: auto;
    }
}
```

### `ui/src/pages/Likes/style.css`

```css
.likes-page .likes-head {
    gap: 12px;
    padding: 16px 20px;
    border-radius: var(--radius);
    background: var(--md-secondary-container);
    color: var(--md-on-secondary-container);
}

.likes-page .likes-head > :last-child {
    margin-left: auto;
}

.likes-page .likes-head svg {
    color: var(--md-on-secondary-container);
}
```

### `ui/src/pages/Playlists/Playlists.tsx`

```tsx
import { useEffect, useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import {
    Container, Content, FormalInput, Header2, Input, LinkButton, Loading, Text, TextIconButton, WrapList
} from "flufi-ui/components";
import { Plus } from "lucide-preact";
import { API, fallbackCover } from "../../common/net/api";
import { CoverArt } from "../../components/Library/CoverArt";

type PlaylistRow = { id: number; name: string; n: number; cover_id: number | null };

/**
 * Playlist grid. The card markup mirrors the library cards in
 * components/Library/Card.tsx, so playlists look like every other collection.
 */
export function PlaylistsPage() {
    const [playlists, setPlaylists] = useState<PlaylistRow[] | null>(null);
    const [error, setError] = useState<string | null>(null);
    const name = useSignal("");

    function load() {
        API.listPlaylists()
            .then(d => setPlaylists(d.playlists ?? []))
            .catch(e => { setError(String(e)); setPlaylists([]); });
    }

    useEffect(load, []);

    async function create() {
        setError(null);
        try {
            await API.createPlaylist(name.peek().trim());
            name.value = "";
            load();
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    return (
        <Content class="playlists">
            <Container extra_gap>
                <Header2>Playlists</Header2>
                <Container horizontal centered_y>
                    <FormalInput label="New playlist">
                        <Input value={name} onEnter={create} />
                    </FormalInput>
                    <TextIconButton variant="accent" disabled={name.value.trim() == ""} onClick={create}>
                        <Plus size={18} /> Create
                    </TextIconButton>
                </Container>
                {error && <Text class="error" content={error} />}

                <Loading loaded={playlists != null}>
                    {() => playlists!.length == 0
                        ? <Text dim content="No playlists yet. Make one above, then add songs from its page." />
                        : (
                            <WrapList min_size={140}>
                                {playlists!.map(p => (
                                    <LinkButton variant="always-transparent" class="library-card text" href={`/playlist/${p.id}`}>
                                        <CoverArt
                                            src={p.cover_id ? API.getTrackCoverUrl(String(p.cover_id)) : fallbackCover(p.name, "album")}
                                            name={p.name}
                                            kind="album"
                                            size={140}
                                        />
                                        <Text content={p.name} />
                                        <Text dim content={`${p.n} track${p.n == 1 ? "" : "s"}`} />
                                    </LinkButton>
                                ))}
                            </WrapList>
                        )}
                </Loading>
            </Container>
        </Content>
    )
}
```

### `ui/src/pages/Playlists/style.css`

```css
/* The one thing flufi-ui's Track does not give us: let the row fill the width
   next to the remove button (and let long titles truncate). */
.playlist-row > :first-child,
.playlist-result .grow {
    flex: 1;
    min-width: 0;
}

.playlists .library-card {
    padding: 12px;
    border-radius: var(--radius);
    background: var(--md-surface-container-low);
    text-align: center;
}
```

### `ui/src/pages/Profile/Profile.tsx`

```tsx
/** Public listening: a directory of what people are playing, and the
 *  per-user profile page the directory cards link to.
 */
import { useEffect, useState } from "preact/hooks";
import type { RoutePropsForPath } from "preact-iso";
import {
    Container, Content, Header2, Header3, LinkButton, Loading, Text,
} from "flufi-ui/components";
import { Headphones, UserRound } from "lucide-preact";
import { API, fallbackCover } from "../../common/net/api";
import type { PublicListening, PublicNow } from "../../common/net/types";
import { CoverArt } from "../../components/Library/CoverArt";
import { UserPfp } from "../../components/User/Pfp";

import "./style.css";

function fmtPosition(seconds: number, duration?: number): string {
    const s = Math.max(0, Math.floor(seconds || 0));
    const m = Math.floor(s / 60);
    const tail = `${String(s % 60).padStart(2, "0")}`;
    return duration ? `${m}:${tail} / ${fmt(duration)}` : `${m}:${tail}`;
}
function fmt(seconds: number): string {
    const s = Math.max(0, Math.floor(seconds || 0));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export function ListenersPage() {
    const [data, setData] = useState<PublicListening | null>(null);
    const [error, setError] = useState<string | null>(null);

    function load() {
        API.publicListening()
            .then(d => { setData(d); setError(null); })
            .catch(e => { setError(String(e)); setData({ ok: false, users: [], base_url: "", now: 0 }); });
    }
    useEffect(load, []);

    return (
        <Content class="profile-page">
            <Container extra_gap>
                <Container horizontal centered_y class="profile-head">
                    <Headphones size={20} />
                    <Header2>Listening now</Header2>
                </Container>
                <Text dim content="Public listening rooms from this server. Profiles show the current track in real time." />
                {error && <Text class="error" content={error} />}
                <Loading loaded={data != null}>
                    {() => {
                        const users = data?.users ?? [];
                        if (users.length === 0) {
                            return <Text dim content="Nobody is listening publicly right now." />;
                        }
                        const listening = users.filter(u => u.listening);
                        const idle = users.filter(u => !u.listening);
                        return (
                            <Container extra_gap>
                                {listening.length > 0 && (
                                    <Container>
                                        <Header3>Now playing</Header3>
                                        <Container class="listener-grid">
                                            {listening.map(u => <ListenerCard key={u.username} user={u} />)}
                                        </Container>
                                    </Container>
                                )}
                                {idle.length > 0 && (
                                    <Container>
                                        <Header3>Recently here</Header3>
                                        <Container horizontal wrap class="listener-chips">
                                            {idle.map(u => (
                                                <LinkButton key={u.username} href={`/u/${encodeURIComponent(u.username)}`} variant="panel">
                                                    <UserRound size={14} /> {u.username}
                                                </LinkButton>
                                            ))}
                                        </Container>
                                    </Container>
                                )}
                            </Container>
                        );
                    }}
                </Loading>
            </Container>
        </Content>
    );
}

function ListenerCard(props: { user: PublicListening["users"][number] }) {
    const u = props.user;
    return (
        <LinkButton
            variant="always-transparent"
            noPadding
            class="listener-card"
            href={`/u/${encodeURIComponent(u.username)}`}
        >
            <CoverArt
                src={u.cover_url || fallbackCover(u.username, "artist")}
                name={u.username}
                kind="artist"
                size={120}
            />
            <Text content={u.username} />
            <Text dim content={u.track ? `${u.track.title} — ${u.track.artist || "?"}` : "Idle"} />
            {u.track && (
                <Text dim class="listener-position" content={fmtPosition(u.position, u.track.duration)} />
            )}
        </LinkButton>
    );
}

export function ProfilePage(props: RoutePropsForPath<"/u/:username">) {
    const [data, setData] = useState<PublicNow | null>(null);
    const [error, setError] = useState<string | null>(null);
    const username = decodeURIComponent(props.username || "");

    useEffect(() => {
        let cancelled = false;
        setData(null);
        API.publicNow(username)
            .then(d => { if (!cancelled) { setData(d); setError(null); } })
            .catch(e => { if (!cancelled) setError(String(e)); });
        return () => { cancelled = true; };
    }, [username]);

    return (
        <Content class="profile-page">
            <Container extra_gap>
                <Container horizontal centered_y class="profile-head">
                    <UserPfp username={username} size={64} />
                    <Container vertical>
                        <Header2>{username}</Header2>
                        <Text dim content="Public listening profile" />
                    </Container>
                </Container>
                {error && <Text class="error" content={error} />}
                <Loading loaded={data != null || error != null}>
                    {() => data ? (
                        data.listening && data.track ? (
                            <Container horizontal wrap class="profile-now">
                                <CoverArt
                                    src={API.getTrackCoverUrl(String((data.track as any).id ?? (data.track as any).uuid ?? ""))}
                                    name={String((data.track as any).title ?? username)}
                                    kind="track"
                                    size={140}
                                />
                                <Container vertical>
                                    <Header3>Listening now</Header3>
                                    <Text content={String((data.track as any).title ?? "")} />
                                    <Text dim content={String((data.track as any).artist ?? "")} />
                                    <Text dim content={fmtPosition(data.position, Number((data.track as any).duration) || 0)} />
                                    <LinkButton href="/listeners">See everyone listening</LinkButton>
                                </Container>
                            </Container>
                        ) : (
                            <Text dim content={`${username} isn't listening right now.`} />
                        )
                    ) : null}
                </Loading>
            </Container>
        </Content>
    );
}
```

### `ui/src/pages/Search/style.css`

```css
.search-page .search-page-field {
    gap: 12px;
    max-width: 720px;
    min-height: var(--touch-target);
    padding: 0 18px;
    border-radius: var(--radius-pill);
    background: var(--md-surface-container-high);
    border: 1px solid var(--layer-rim);
}

.search-page .search-page-field > :last-child {
    flex: 1;
}

.search-page .search-page-field:focus-within {
    border-color: var(--accent);
    outline: 2px solid var(--accent);
    outline-offset: 2px;
}

.search-page .search-results {
    border: 0;
    border-radius: var(--radius);
    background: var(--md-surface-container-low);
    overflow: hidden;
}

.search-page .search-results > .button {
    min-height: var(--touch-target);
    border-radius: var(--radius-lg);
}
```

### `ui/src/pages/Settings/Settings.tsx`

```tsx
import { useCallback, useEffect, useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import {
    Button, Container, Content, FormalInput, Header2, Header3, Input, Loading,
    Seperator, Slider, Text, TextIconButton, TextIconLinkButton, WrapList
} from "flufi-ui/components";
import {
    BookOpen, Check, CircleCheck, CircleDashed, Download, ExternalLink, KeyRound,
    Link2, LogOut, Mail, RefreshCw, Save, Send, Settings as SettingsGlyph,
    Smartphone, Sparkles, Unlink, WifiOff,
} from "lucide-preact";
import { API, userFromJson } from "../../common/net/api";
import { SELFHOST_GUIDE } from "../../common/links";
import type { DiscordStatus, RoturStatus } from "../../common/net/types";
import { currentUser, logout } from "../../common/auth";
import { activityError } from "../../common/player";
import { flushOutbox, pendingWrites } from "../../common/net/api";
import { PasswordInput } from "../../components/PasswordInput/PasswordInput";
import {
    applyPrefs, loadPrefs, playfulMotion, setAccentPreference, setAutoplayPreference,
    setIconFilledPreference, setIconStrokePreference, setPalettePreference,
    setPlayfulMotionPreference, type Settings as Prefs,
} from "../../common/prefs";
import {
    DEFAULT_ICON_STROKE, ICON_STROKE_CHOICES, PALETTE_FAMILIES, resolvePalette,
} from "../../common/theme";

import "./style.css";

// Every checkbox the legacy client exposed, as (server key, label) pairs.
// They are still stored server-side so Android/Qt keep honouring them.
const TOGGLES: [string, string][] = [
    ["covers", "Show cover art"],
    ["hide_explicit", "Hide explicit tracks"],
    ["autoplay", "Autoplay"],
    ["prefetch", "Prefetch the next track"],
    ["offline_audio", "Keep audio offline (downloads)"],
    ["remember_volume", "Remember volume"],
    ["private", "Private listening"],
    ["yt_stats", "Show YouTube stats"],
    ["rotur_activity", "Share as Rotur activity"],
    ["discord_activity", "Share as Discord activity"],
    ["show_room_url", "Show my room URL"],
];

/**
 * Settings page: account, linked services (Rotur + Discord), password, email,
 * builds/version, offline sync, volume and the server-stored preferences.
 */
export function SettingsPage() {
    const [settings, setSettings] = useState<Prefs | null>(null);
    const [loadFailed, setLoadFailed] = useState(false);
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [dirty, setDirty] = useState(false);
    const [saving, setSaving] = useState(false);
    const oldPw = useSignal("");
    const newPw = useSignal("");
    const email = useSignal("");

    const [rotur, setRotur] = useState<RoturStatus | null>(null);
    const [roturError, setRoturError] = useState<string | null>(null);
    const [discord, setDiscord] = useState<DiscordStatus | null>(null);
    const [discordError, setDiscordError] = useState<string | null>(null);
    const [builds, setBuilds] = useState<any[]>([]);
    const [version, setVersion] = useState<any>(null);
    const [ping, setPing] = useState<any>(null);
    const [publicUrl, setPublicUrl] = useState<string | null>(null);
    const [pending, setPending] = useState(0);
    const [emailTarget, setEmailTarget] = useState("");

    const loadRotur = useCallback(async () => {
        try {
            setRotur(await API.roturStatus());
            setRoturError(null);
        } catch (e) {
            setRoturError(e instanceof Error ? e.message : String(e));
        }
    }, []);

    const loadDiscord = useCallback(async () => {
        try {
            setDiscord(await API.discordStatus() as DiscordStatus);
            setDiscordError(null);
        } catch (e) {
            setDiscordError(e instanceof Error ? e.message : String(e));
        }
    }, []);

    const loadMeta = useCallback(async () => {
        try {
            const [b, v, p, pg, pub] = await Promise.all([
                API.builds().catch(() => ({ builds: [] })),
                API.version().catch(() => null),
                pendingWrites().catch(() => 0),
                API.ping().catch(() => null),
                API.publicListening().catch(() => null),
            ]);
            setBuilds(b.builds ?? []);
            setVersion(v);
            setPing(pg);
            setPublicUrl(pub?.base_url ?? null);
            setPending(p);
        } catch { /* all sources are optional */ }
    }, []);

    useEffect(() => {
        loadPrefs().then(s => {
            setSettings(s ?? {});
            if (s == null) {
                setLoadFailed(true);
                setError("Could not load preferences. Saving is disabled so nothing is overwritten.");
            }
        });
        email.value = currentUser.value?.email ?? "";
        void loadMeta();
    }, []);

    // The OAuth redirect returns here; refresh both link states on focus and
    // visibility so neither is ever stale after a hand-off.
    useEffect(() => {
        void loadRotur();
        void loadDiscord();
        const refresh = () => {
            if (document.visibilityState === "visible") {
                void loadRotur();
                void loadDiscord();
                void loadMeta();
            }
        };
        document.addEventListener("visibilitychange", refresh);
        window.addEventListener("focus", refresh);
        return () => {
            document.removeEventListener("visibilitychange", refresh);
            window.removeEventListener("focus", refresh);
        };
    }, [loadRotur, loadDiscord, loadMeta]);

    function set(key: string, value: unknown) {
        setSettings(s => ({ ...(s ?? {}), [key]: value }));
        // Preview appearance changes before Save; Save mirrors them to the server.
        if (key === "theme") setPalettePreference(String(value));
        if (key === "accent") setAccentPreference(String(value ?? ""));
        if (key === "iconStroke") setIconStrokePreference(value);
        if (key === "iconFilled") setIconFilledPreference(value);
        setDirty(true);
        setMessage(null);
    }

    async function save() {
        if (loadFailed) return;
        setError(null);
        setMessage(null);
        setSaving(true);
        try {
            await API.saveSettings(settings ?? {});
            applyPrefs(settings ?? {});
            // Autoplay is mirrored locally for instant queue-toggle behavior.
            if (settings && "autoplay" in settings)
                setAutoplayPreference(settings.autoplay !== false);
            setDirty(false);
            setMessage("Preferences saved.");
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setSaving(false);
        }
    }

    async function changePassword() {
        setError(null);
        setMessage(null);
        try {
            await API.changePassword(oldPw.peek(), newPw.peek());
            oldPw.value = "";
            newPw.value = "";
            setMessage("Password changed.");
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    async function saveEmail() {
        setError(null);
        setMessage(null);
        try {
            const me = await API.setEmail(email.peek().trim());
            currentUser.value = userFromJson(me);
            setMessage("Email saved — password resets go there.");
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    async function unlinkRotur() {
        if (!window.confirm("Unlink Rotur from this account?")) return;
        setRoturError(null);
        try {
            await API.roturUnlink();
            await loadRotur();
            setMessage("Rotur account unlinked.");
        } catch (e) {
            setRoturError(e instanceof Error ? e.message : String(e));
        }
    }

    async function unlinkDiscord() {
        if (!window.confirm("Unlink Discord from this account?")) return;
        setDiscordError(null);
        try {
            await API.discordUnlink();
            await loadDiscord();
            setMessage("Discord account unlinked.");
        } catch (e) {
            setDiscordError(e instanceof Error ? e.message : String(e));
        }
    }

    async function emailBuild(kind: string) {
        setError(null);
        const target = emailTarget.trim() || email.peek().trim() || currentUser.value?.email || "";
        if (!target) {
            setError("Set an email address above first.");
            return;
        }
        try {
            await API.emailBuild(target, kind);
            setMessage(`Build link sent to ${target}.`);
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    async function syncNow() {
        try {
            const n = await flushOutbox();
            setPending(await pendingWrites());
            setMessage(n ? `Synced ${n} offline change${n === 1 ? "" : "s"}.` : "Everything is up to date.");
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    const roturLinked = rotur?.linked ?? false;
    const roturLabel = describeRotur(rotur);
    const roturDetail = activityError.value
        ? `Activity error: ${activityError.value}`
        : !rotur?.activity?.ready && roturLinked
            ? (rotur?.activity?.reason ?? "Activity is not ready.")
            : roturDetailReady(rotur);
    const discordLinked = discord?.linked ?? false;
    const discordLabel = describeDiscord(discord);
    const discordDetail = discordPresenceHint(discord?.presence ?? null);

    return (
        <Content class="settings">
            <Loading loaded={settings != null}>
                {() => (
                    <Container extra_gap>
                        <Header2>Settings</Header2>
                        {(message || error) && (
                            <span class={error ? "error status-line" : "status status-line"} role="status">
                                {error ?? message}
                            </span>
                        )}

                        <Container class="settings-card">
                            <Header3>Account</Header3>
                            <Text content={currentUser.value?.username ?? "—"} />
                            <Text dim content={currentUser.value?.is_admin ? "Administrator" : "Listener"} />
                            <TextIconButton onClick={() => logout().then(() => { window.location.href = "/auth"; })}>
                                <LogOut size={18} /> Log out
                            </TextIconButton>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Appearance</Header3>
                            <Text dim content="Palettes follow your device's light or dark setting. Pick a colour family, then save preferences." />
                            <WrapList min_size={150}>
                                {PALETTE_FAMILIES.map(f => {
                                    const active = resolvePalette(settings!.theme);
                                    const selected = active.family === f.id;
                                    const preview = f[active.mode];
                                    return (
                                        <Button
                                            key={f.id}
                                            class="palette-card"
                                            variant={selected ? "accent-subtle" : "panel"}
                                            title={`Use ${f.name} palette`}
                                            onClick={() => set("theme", f.id)}
                                        >
                                            <span
                                                class="palette-card-swatch"
                                                style={{ background: preview.bg, borderColor: preview.line }}
                                            >
                                                <span style={{ background: preview.accent }} />
                                            </span>
                                            <Text content={f.name} />
                                            {selected && <Check size={16} class="palette-card-check" />}
                                        </Button>
                                    );
                                })}
                            </WrapList>

                            <Text dim content="Icon width scales Lucide outlines. Filled mode fills circles and squares only; paths stay outlined." />
                            <WrapList min_size={110}>
                                {ICON_STROKE_CHOICES.map(choice => {
                                    const selected =
                                        Number(settings!.iconStroke ?? DEFAULT_ICON_STROKE) === choice;
                                    return (
                                        <Button
                                            key={choice}
                                            class="icon-choice"
                                            variant={selected ? "accent-subtle" : "panel"}
                                            title={`Use ${choice}x Lucide icons`}
                                            onClick={() => set("iconStroke", choice)}
                                        >
                                            <SettingsGlyph
                                                size={18}
                                                class="icon-choice-sample"
                                            />
                                            <Text content={`${choice}x`} />
                                            {selected && (
                                                <Check size={15} class="palette-card-check" />
                                            )}
                                        </Button>
                                    );
                                })}
                            </WrapList>
                            <Button
                                class="icon-toggle"
                                variant={settings!.iconFilled ? "accent-subtle" : "panel"}
                                onClick={() => set("iconFilled", !settings!.iconFilled)}
                            >
                                <CircleCheck size={16} />
                                <Text content="Filled icons" />
                                {!!settings!.iconFilled && (
                                    <Check size={15} class="palette-card-check" />
                                )}
                            </Button>
                            <Button
                                class="icon-toggle"
                                variant={playfulMotion.value ? "accent-subtle" : "panel"}
                                title="Stored on this device; reduced-motion settings still win"
                                onClick={() => setPlayfulMotionPreference(!playfulMotion.value)}
                            >
                                <Sparkles size={16} />
                                <Text content="Playful motion" />
                                {playfulMotion.value && (
                                    <Check size={15} class="palette-card-check" />
                                )}
                            </Button>
                            <Text dim content="Springs, shape morphs and the wavy progress bar follow this switch; your device's reduced-motion setting always wins." />
                        </Container>

                        <Seperator />

                        <Container class="settings-card selfhost-panel">
                            <Header3>Server &amp; self-hosting</Header3>
                            <Text dim content="This server's details and the guide to running your own." />
                            <div class="server-facts">
                                <Text content={location.origin} />
                                {publicUrl && publicUrl !== location.origin && (
                                    <Text dim content={`Public URL: ${publicUrl}`} />
                                )}
                                {settings!.room_url && (
                                    <Text dim content={`Room: ${settings!.room_url}`} />
                                )}
                                {ping && (
                                    <Text dim content={`${ping.service ?? "mcmusic"} API ${ping.api ?? 3} · uptime ${Math.round((ping.uptime ?? 0) / 60)} min`} />
                                )}
                                {version && (
                                    <Text dim content={`Build ${version.build ?? "?"} · shell ${version.shell ?? "?"}`} />
                                )}
                            </div>
                            <a class="selfhost-link" href={SELFHOST_GUIDE} target="_blank" rel="noopener noreferrer">
                                <BookOpen size={16} /> Self-hosting guide <ExternalLink size={13} />
                            </a>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Email</Header3>
                            <Text dim content="Password reset links and app downloads are sent here." />
                            <FormalInput label="Email address">
                                <Input
                                    value={email}
                                    placeholder="you@example.com"
                                    onInput={(v: string) => { email.value = v; }}
                                />
                            </FormalInput>
                            <TextIconButton variant="accent" onClick={saveEmail}>
                                <Mail size={16} /> Save email
                            </TextIconButton>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Rotur status</Header3>
                            <Container horizontal centered_y class="status-line" other={{ role: "status" }}>
                                {roturLinked && rotur?.session_valid
                                    ? <CircleCheck size={18} class="status-ok" />
                                    : <CircleDashed size={18} class="status-idle" />}
                                <Text content={roturLabel} />
                                <TextIconButton title="Refresh Rotur status" onClick={loadRotur}>
                                    <RefreshCw size={14} />
                                </TextIconButton>
                            </Container>
                            <Text dim class={roturLinked && !rotur?.activity?.ready ? "warning" : ""}
                                content={roturError ?? roturDetail} />
                            <Container horizontal centered_y wrap class="status-actions">
                                <TextIconLinkButton variant="accent" href={API.roturAuthorizeUrl()}>
                                    <Link2 size={16} /> {roturLinked ? "Reconnect Rotur" : "Sign in with Rotur"}
                                </TextIconLinkButton>
                                {roturLinked && (
                                    <TextIconButton variant="danger-subtle" onClick={unlinkRotur}>
                                        <Unlink size={16} /> Unlink
                                    </TextIconButton>
                                )}
                            </Container>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Discord</Header3>
                            <Container horizontal centered_y class="status-line" other={{ role: "status" }}>
                                {discordLinked && discord?.session_valid
                                    ? <CircleCheck size={18} class="status-ok" />
                                    : <CircleDashed size={18} class="status-idle" />}
                                <Text content={discordLabel} />
                                <TextIconButton title="Refresh Discord status" onClick={loadDiscord}>
                                    <RefreshCw size={14} />
                                </TextIconButton>
                            </Container>
                            <Text dim content={discordError ?? discordDetail} />
                            <Container horizontal centered_y wrap class="status-actions">
                                <TextIconLinkButton
                                    variant="accent"
                                    href={discord?.configured ? API.discordAuthorizeUrl() : "#"}
                                >
                                    <Link2 size={16} /> {discordLinked ? "Reconnect Discord" : "Link Discord"}
                                </TextIconLinkButton>
                                {discordLinked && (
                                    <TextIconButton variant="danger-subtle" onClick={unlinkDiscord}>
                                        <Unlink size={16} /> Unlink
                                    </TextIconButton>
                                )}
                            </Container>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Change password</Header3>
                            <FormalInput label="Current password">
                                <PasswordInput value={oldPw} />
                            </FormalInput>
                            <FormalInput label="New password">
                                <PasswordInput value={newPw} />
                            </FormalInput>
                            <TextIconButton
                                variant="accent"
                                disabled={oldPw.value == "" || newPw.value.length < 6}
                                onClick={changePassword}
                            >
                                <KeyRound size={18} /> Change password
                            </TextIconButton>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Offline sync</Header3>
                            <Text dim content={`${pending} change${pending === 1 ? "" : "s"} waiting to sync.`} />
                            <Container horizontal centered_y wrap class="status-actions">
                                <TextIconButton variant="panel" disabled={pending === 0} onClick={syncNow}>
                                    <RefreshCw size={15} /> Sync now
                                </TextIconButton>
                                <WifiOff size={14} />
                                <Text dim content="Likes and playlist edits made offline are replayed." />
                            </Container>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Get the app</Header3>
                            {builds.length === 0
                                ? <Text dim content="No builds are published yet." />
                                : builds.map(b => (
                                    <Container horizontal centered_y wrap class="build-row" key={b.kind}>
                                        <Smartphone size={16} />
                                        <Container vertical class="build-meta">
                                            <Text content={b.label} />
                                            <Text dim content={b.available
                                                ? `${b.version || "latest"} · ${b.note || ""}`
                                                : "Not built yet"} />
                                        </Container>
                                        {b.available && (
                                            <>
                                                <a href={b.url} class="build-link" download>
                                                    <Download size={14} /> Download
                                                </a>
                                                <TextIconButton
                                                    title={`Email ${b.label} to ${emailTarget || "your address"}`}
                                                    onClick={() => emailBuild(b.kind)}
                                                >
                                                    <Send size={14} /> Email
                                                </TextIconButton>
                                            </>
                                        )}
                                    </Container>
                                ))}
                            <FormalInput label="Send a build to (optional)">
                                <Input value={emailTarget} placeholder="you@example.com"
                                    onInput={(v: string) => setEmailTarget(v)} />
                            </FormalInput>
                            <Text dim content="No build for your device? The self-hosting guide explains how to serve the web app and install clients yourself." />
                            <a class="selfhost-link compact" href={SELFHOST_GUIDE} target="_blank" rel="noopener noreferrer">
                                <BookOpen size={14} /> Read the guide <ExternalLink size={12} />
                            </a>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Playback</Header3>
                            <Container horizontal centered_y>
                                <Text content={`Volume ${Math.round(Number(settings!.volume ?? 0.8) * 100)}%`} />
                                <Slider
                                    value={Number(settings!.volume ?? 0.8)}
                                    start={0} end={1} step={0.01}
                                    onChange={(v) => set("volume", v)}
                                    class="grow"
                                />
                            </Container>
                            <WrapList min_size={160}>
                                {TOGGLES.map(([key, label]) => (
                                    <Button
                                        key={key}
                                        variant={settings![key] ? "accent-subtle" : "panel"}
                                        title={settings![key] ? "On" : "Off"}
                                        onClick={() => set(key, !settings![key])}
                                    >
                                        {settings![key] && <Check size={15} />}
                                        {label}
                                    </Button>
                                ))}
                            </WrapList>
                            <Container horizontal centered_y class="save-row">
                                <TextIconButton
                                    variant="accent"
                                    disabled={saving || !dirty || loadFailed}
                                    onClick={save}
                                >
                                    <Save size={18} /> {saving ? "Saving…" : "Save preferences"}
                                </TextIconButton>
                                {dirty && !loadFailed && <Text dim content="Unsaved changes" />}
                            </Container>
                            <Text dim content="Stored on the server and shared with the Android/Qt clients." />
                        </Container>

                        {settings!.room_url && (
                            <Container class="settings-card">
                                <Header3>Listen along</Header3>
                                <Text selectable content={String(settings!.room_url)} />
                            </Container>
                        )}
                    </Container>
                )}
            </Loading>
        </Content>
    )
}

/** Legacy RoturLink.describe(): explain what the server can actually do. */
function describeRotur(s: RoturStatus | null): string {
    if (!s) return "Checking link status…";
    if (!s.configured) return "RoturLink is not configured on this server.";
    if (!s.linked) return "Not linked — sign in with Rotur to share activity.";
    if (!s.session_valid) return "Linked, but the session needs a refresh — sign in again.";
    return `Linked as @${s.rotur_username || s.rotur_id || "Rotur"}`;
}

function roturDetailReady(s: RoturStatus | null): string {
    if (!s) return "Checking link status…";
    if (!s.linked) return "Linking shares what you play as Rotur activity.";
    if (!s.activity.ready) return s.activity.reason;
    return "Activity sharing is ready.";
}

function describeDiscord(s: DiscordStatus | null): string {
    if (!s) return "Checking link status…";
    if (!s.configured)
        return `Discord linking needs ${(s.missing?.length ? s.missing : ["DISCORD_CLIENT_SECRET"]).join(" and ")}`;
    if (!s.linked) return "Not linked — control channels can still use /login";
    if (!s.session_valid) return `Linked as ${s.discord_username || s.discord_id} (refresh needed)`;
    return `Linked as ${s.discord_username || s.discord_id}`;
}

function discordPresenceHint(presence: DiscordStatus["presence"]): string {
    if (!presence) return "Shares what you play in your Discord profile when the toggle is on.";
    if (!presence.configured)
        return "Needs a Discord application id on the server (DISCORD_CLIENT_ID is enough).";
    if (!presence.available)
        return "The Discord desktop app has to run on the server — it isn't running right now.";
    return "Shares what you play in your Discord profile, with a link to the track.";
}
```

