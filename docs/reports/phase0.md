# mcmusic 4.2.0 — Phase 0 report

Branch: `design-4.2.0` (base `d108ef6`). This is the foundations phase; no version bump or release action is included.

## What changed

- Added `design/tokens.json` as the single source of truth: five fixed family ids/names, byte-identical legacy swatches from the previous release, HCT seeds, shape (4/8/12/16/28/36 + pill), 4px spacing, M3 type scale, motion settings, legacy aliases and the Lucide icon list.
- Added `scripts/gen-tokens.mjs` using `@material/material-color-utilities@0.3.0` HCT (`SchemeTonalSpot`, `TonalPalette`) to generate `design/tokens.generated.json`, `ui/src/env.css`, and marked blocks in web `theme.ts`, Android `Design.kt`, iOS `Theme.swift`, Qt `theme.py` and embed `widgets.js`. Generated files are committed; `--check` fails on staleness.
- Added `scripts/gen-lucide.mjs`, which reads `lucide-static@1.80.0` SVGs and generates web/Kotlin/Swift/Qt icon maps plus 127 Android vector drawables. No glyph geometry is hand-copied; legacy names stay as aliases. `--check` fails on staleness and on obsolete drawables.
- Replaced the flufi-ui Google Fonts CDN import with locally bundled `@fontsource-variable` Inter, JetBrains Mono and Lexend; `scripts/strip-font-cdn.mjs` removes the CDN import during `scripts/build_ui.sh` and fails on any unexpected remote `@import`.
- Added flatness (`tests/test_no_gradients.py`), WCAG AA contrast (`tests/test_contrast.py`) and generated-freshness (`tests/test_generated_fresh.py`) gates with no allowlist, and wired them into CI as `design-checks`. The `python-checks` job now installs the same pinned UI dependencies because its Node-based tests import the UI sources.
- Removed all pre-existing gradients, blur/glass, backdrop and decorative-shadow identifiers from web, Android, iOS and Qt UI sources so those gates start green. Deleted unused `Glass.kt` and the kyant backdrop dependency; cover/wave/code paths now use flat tonal surfaces. Also flattened the Android app-widget background (`LinearGradient` → solid tonal fill) and two SwiftUI card/field shadows, and strengthened `tests/test_no_gradients.py` with Android/SwiftUI/Qt gradient and shadow primitives so these cannot be reintroduced unnoticed.
- Restored all legacy `dim`/`dim2` swatches byte-for-byte from `HEAD`; added `accentText` and contrast-safe `accentFg`/`outlineVariant` roles without changing stored palette ids or family names.
- Updated `docs/design-4.2.md` with the source-verified feature truth audit, licence evidence, font decision, phase plan and verification limits.

## What was run

- `node scripts/gen-tokens.mjs --check` — pass.
- `node scripts/gen-lucide.mjs --check` — pass.
- `python -m py_compile app/linux/mcmusic_linux/theme.py app/linux/mcmusic_linux/icons.py` — pass.
- `node --check web/embed/widgets.js` — pass.
- `./scripts/build_ui.sh` — pass; `tsc --noEmit`, Vite build and CDN import strip all succeeded.
- `python -m pytest tests/test_no_gradients.py tests/test_contrast.py tests/test_generated_fresh.py -q` — 3 passed.
- Full non-Qt suite (`python -m pytest tests -q` with the CI Qt ignores) — 95 passed, 1 skipped, 2 subtests passed.
- Qt offscreen suite (`QT_QPA_PLATFORM=offscreen`, audio stub) — 35 passed.
- `./scripts/check-versions.sh`, `./tests/test_check_versions.sh`, `./tests/test_publish_release.sh` — all passed with versions still at 4.1.0.
- Lucide generator idempotence: two consecutive generations produced identical hashes; a deliberately modified generated body was detected by `--check`; all 127 generated drawables parsed as XML and all 77 Kotlin drawable references resolved.
- CI run `45772955489` for the first Phase 0 commit passed every job except `Python checks`: Qt, Windows, Web UI, Web, design checks, macOS, Android and iOS were green. The only failure was an environment gap — `Python checks` runs Node-based tests but had no `ui/node_modules`. Added `actions/setup-node@v4` plus `npm --prefix ui ci` to that job and amended this phase before rerunning CI.

## What was not done and why

- No version bump or release publication: that is Phase 5, after Phases 1–4 are CI-green. Version carriers remain consistent at 4.1.0.
- No mockup-driven layout work: no mockup images were supplied, so Phase 0 only fixes tokens, generated assets and flatness. Visual structure arrives in Phases 1–4 from the written brief.
- No device rendering verification: no web/Android/iOS/Qt device farm is available locally; CI and later phases cover builds where possible.
- No macOS codesign validation: `codesign` is unavailable on Linux and there is no paid Apple Developer account.
- No live database changes, branch sync, redeploy or secret rotation: those require explicit user permission and are outside this design phase.
- No hand-edited generated files: every generated block is reproducible from `design/tokens.json` or `lucide-static`.

## Full authored file contents

The files below are reproduced in full. Generated outputs (`design/tokens.generated.json`, `ui/src/env.css`, `ui/src/common/theme.ts`, `ui/src/common/lucide.tsx`, `gui/android/.../Design.kt`, `gui/android/.../Lucide.kt`, `app/ios/McMusic/Theme.swift`, `app/ios/McMusic/Lucide.swift`, `app/linux/mcmusic_linux/theme.py`, `app/linux/mcmusic_linux/icons.py`, `web/embed/widgets.js` and the Android drawables) are committed and reproducible with the two generators; they are not duplicated here.

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
    "circle-alert", "circle-check", "circle-help", "circle-x", "clock", "coffee", "compass",
    "disc-3", "download", "dumbbell", "ellipsis", "eye-off", "flame", "film", "folder-plus",
    "grip-vertical", "hard-drive", "headphones", "heart", "house", "image", "inbox", "info",
    "key", "library", "link", "list", "list-music", "list-plus", "loader-circle", "lock",
    "log-in", "log-out", "mail", "message-circle", "mic-vocal", "monitor", "moon", "music",
    "palette", "pause", "pencil", "picture-in-picture-2", "play", "plus", "radio", "refresh-cw",
    "repeat", "repeat-1", "search", "server", "settings", "shield", "shield-alert", "shield-check",
    "shuffle", "skip-back", "skip-forward", "smartphone", "sparkles", "star", "trash-2",
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
  ];
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

### `scripts/gen-lucide.mjs`

```js
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
        const relative = command !== letter;
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
const remoteImport = /@import\s+(?:url\()?\s*["']?https?:\/\/[^"')]+["']?\s*\)?\s*;/gi;

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

### `scripts/build_ui.sh`

```sh
#!/usr/bin/env bash
# Build the v3 web client into web/ui/ — what the Flask app serves at /.
#
#   ./scripts/build_ui.sh
#
# CI, the release workflow and any deployment should call this instead of
# npm directly, so a missing lockfile or a silently broken build fails here.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to build the web UI (install Node 20+)" >&2
  exit 1
fi

(
  cd ui
  if [ ! -d node_modules ] || [ package-lock.json -nt node_modules/.package-lock.json ]; then
    npm ci --no-audit --no-fund
  fi
  npm run build
)

# Stable URL for the embed gallery and widget pages, which have no bundler.
# Append the static violet-dark fallback after flufi's :root so non-SPA pages
# start on the default palette; the SPA then pins its palette inline at runtime.
cat ui/node_modules/flufi-ui/dist/style.css ui/src/env.css > web/ui/flufi-ui.css

# Fonts are served from the locally bundled @fontsource-variable packages;
# flufi-ui's own stylesheet still starts with a Google Fonts CDN import.
node scripts/strip-font-cdn.mjs .

test -f web/ui/index.html
echo "built web/ui ($(du -sh web/ui | cut -f1))"
```

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  pull_request:
  # CI must also run on main: release.yml gates publishing on a CI run for the
  # exact pushed SHA (see its ci-gate job).
  push:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  # Do not cancel main runs: the release gate waits for the run matching the
  # pushed SHA. PR/branch runs still cancel superseded duplicates.
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}

jobs:
  web-checks:
    name: Web checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - name: Validate service worker is parseable
        run: node --check web/sw.js

  design-checks:
    name: Design token and flatness checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: ui/package-lock.json
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install UI dependencies for generation
        run: npm --prefix ui ci --no-audit --no-fund
      - name: Generated token/icon files must be current
        run: |
          node scripts/gen-tokens.mjs --check
          node scripts/gen-lucide.mjs --check
      - name: Install test dependencies
        run: python -m pip install pytest
      - name: Design gates (flatness, WCAG AA, generated freshness)
        run: python -m pytest tests/test_no_gradients.py tests/test_contrast.py tests/test_generated_fresh.py -q

  ui-checks:
    name: Web UI build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: ui/package-lock.json
      # npm run build runs `tsc --noEmit -p tsconfig.app.json` before Vite, so
      # types are checked here. There is no ESLint config in the repo; no new
      # lint dependency is added for that reason.
      - name: Build the v3 client (ui/ -> web/ui/)
        run: ./scripts/build_ui.sh

  android-checks:
    name: Android build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'
      - uses: android-actions/setup-android@v3
        with:
          packages: "platforms;android-36 build-tools;36.0.0"
      - uses: gradle/actions/setup-gradle@v4
      - name: Compile and package the debug APK
        run: (cd gui/android && ./gradlew :app:assembleDebug --no-daemon --stacktrace)
      - name: Run Android JVM unit tests
        # CleartextPolicy is pure JVM code (no emulator); these tests prove the
        # private-range parsing without DNS or sockets.
        run: (cd gui/android && ./gradlew :app:testDebugUnitTest --no-daemon --stacktrace)
      - name: Build and verify the signed release APK
        run: |
          set -euo pipefail
          version=$(grep -oP 'versionName\s*=\s*"\K[^"]+' gui/android/app/build.gradle.kts | head -1)
          rm -f gui/android/app/build/outputs/apk/release/app-release.apk
          (cd gui/android && ./gradlew :app:assembleRelease --no-daemon --stacktrace)
          apk=gui/android/app/build/outputs/apk/release/app-release.apk
          aapt="$ANDROID_HOME/build-tools/36.0.0/aapt"
          apksigner="$ANDROID_HOME/build-tools/36.0.0/apksigner"
          badging=$("$aapt" dump badging "$apk")
          apk_version=$(grep -m1 -o "versionName='[^']*'" <<<"$badging" | cut -d"'" -f2)
          if [ "$apk_version" != "$version" ]; then
            echo "APK version $apk_version does not match Gradle version $version" >&2
            exit 1
          fi
          signer=$("$apksigner" verify --print-certs "$apk" | tr '[:upper:]' '[:lower:]')
          if ! grep -q 0b0fd0fa35ff712901d42cab215d5e3cb706daef57bffa7ebef61cacda1dc4ce <<<"$signer"; then
            echo "APK has an unexpected signer certificate" >&2
            exit 1
          fi
      - name: Upload APKs
        uses: actions/upload-artifact@v4
        with:
          name: mcmusic-apks
          path: |
            gui/android/app/build/outputs/apk/debug/app-debug.apk
            gui/android/app/build/outputs/apk/release/app-release.apk
          if-no-files-found: error

  python-checks:
    name: Python checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      # Generated-freshness and icon-pref tests invoke Node against the UI
      # sources, so this job needs the same pinned dependencies as design-checks.
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: ui/package-lock.json
      - name: Install UI dependencies for Node-based tests
        run: npm --prefix ui ci --no-audit --no-fund
      # The unused imports and shadowed locals that used to trip this check
      # are gone, so pyflakes is now a release-blocking gate.
      - name: Pyflakes
        run: |
          pip install pyflakes
          python -m pyflakes app/linux src music_activity tools
      - name: Compile key Python modules
        run: |
          python -m py_compile \
            src/mcmusic.py \
            src/config.py \
            src/auth.py \
            src/database.py \
            src/next_song_model.py \
            src/routes/system_routes.py \
            src/routes/library_routes.py \
            src/routes/personal_routes.py \
            src/routes/auth_routes.py \
            src/routes/channel_routes.py \
            src/zip_import.py \
            src/flufi_pages.py \
            src/discord_link.py \
            tools/import_zip.py \
            src/discord_bot.py \
            src/music_channels.py \
            src/originchats.py \
            algo/encoding.py \
            algo/mdl.py
      - name: Install test dependencies
        run: pip install -r requirements.txt pytest
      - name: Run Python test suite
        # Qt-dependent suites live in qt-checks, which installs PySide6 and
        # sets QT_QPA_PLATFORM=offscreen. Running them here without Qt would
        # turn a packaging detail into a false failure.
        run: |
          python -m pytest tests -q \
            --ignore=tests/test_qt_ui.py \
            --ignore=tests/test_qt_client.py \
            --ignore=tests/test_qt_icons.py \
            --ignore=tests/test_widgets.py \
            --ignore=tests/test_no_qt_shadowing.py \
            --ignore=tests/test_qt_selftest.py \
            --ignore=tests/test_updates.py
      - name: Check version sources
        run: ./scripts/check-versions.sh
      - name: Test version consistency checker
        run: ./tests/test_check_versions.sh
      - name: Test release publish script
        # Fake gh shim: no release is created and no tag is pushed here.
        run: ./tests/test_publish_release.sh
      - name: Shellcheck shell scripts
        run: |
          sudo apt-get update
          sudo apt-get install -y --no-install-recommends shellcheck
          shellcheck scripts/*.sh tests/*.sh

  qt-checks:
    name: Qt tests (offscreen)
    runs-on: ubuntu-latest
    timeout-minutes: 20
    env:
      QT_QPA_PLATFORM: offscreen
      # GitHub runners have no sound card; constructing QAudioOutput there can
      # segfault inside Qt's platform plugin. The opt-in stub replaces only the
      # audio backend, so all client logic still runs for real.
      MC_MUSIC_QT_AUDIO_STUB: "1"
      # QSettings caches its native path on first use, so isolate the whole
      # process before any Qt suite creates a QApplication. The runner context
      # is not available at job level; github.workspace is.
      XDG_CONFIG_HOME: ${{ github.workspace }}/.mcmusic-config
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install Qt runtime libraries
        run: |
          sudo apt-get update
          sudo apt-get install -y --no-install-recommends \
            libegl1 libgl1 libxkbcommon0 libdbus-1-3 libpulse0
      - name: Install Python and Qt test dependencies
        # Full PySide6 (not PySide6-Essentials) supplies QtMultimedia.
        run: pip install -r requirements.txt pytest PySide6
      - name: Verify QtMultimedia is importable
        # The Qt suites skip themselves when PySide6/QtMultimedia cannot be
        # imported. Fail here instead so a missing module cannot turn a broken
        # setup into a green run of skipped tests. The audio backend is stubbed
        # only because runners have no sound card; Python errors and crashes in
        # the client still fail this job.
        run: python -c 'from PySide6 import QtMultimedia; from PySide6.QtWidgets import QApplication'
      - name: Run Qt tests
        # These suites have segfaulted in some sandboxes. A crash gives a
        # non-zero exit code and fails the job; it is not masked here.
        run: |
          python -m pytest \
            tests/test_qt_ui.py \
            tests/test_qt_client.py \
            tests/test_qt_icons.py \
            tests/test_widgets.py \
            tests/test_no_qt_shadowing.py \
            tests/test_qt_selftest.py \
            tests/test_updates.py \
            -q

  macos-checks:
    name: macOS native build
    runs-on: macos-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Build native Qt .app and .dmg
        run: |
          set -euo pipefail
          version=$(sed -n 's/^FALLBACK_VERSION[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' app/linux/mcmusic_linux/version.py | head -1)
          MAKE_DMG=1 VERSION="$version" ./app/macos/build.sh
      - name: Verify the bundle contains no web engine or HTML
        run: |
          set -euo pipefail
          app=app/macos/dist/mcmusic.app
          test -f "$app/Contents/MacOS/mcmusic"
          test -f "$app/Contents/Info.plist"
          /usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$app/Contents/Info.plist" | grep -qx 'dev.mcmusic.app'
          if find "$app" \( -iname 'QtWebEngine*' -o -iname 'QtWebKit*' -o -iname 'index.html' \) | grep -q .; then
            echo "macOS bundle contains a web engine or HTML assets" >&2
            exit 1
          fi
          echo "verified: native Qt bundle, no HTML/WebView"
      - uses: actions/upload-artifact@v4
        with:
          name: mcmusic-macos
          path: |
            app/macos/dist/mcmusic.app
            app/macos/dist/mcmusic-*.dmg
          if-no-files-found: error

  windows-checks:
    name: Windows native build
    runs-on: windows-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Build native Qt .exe and .zip
        shell: pwsh
        run: |
          $version = (Select-String -Path 'app/linux/mcmusic_linux/version.py' -Pattern 'FALLBACK_VERSION\s*=\s*"([^"]+)"').Matches[0].Groups[1].Value
          ./app/windows/build.ps1 -Version $version -Zip
      - name: Verify the build contains no web engine or HTML
        shell: pwsh
        run: |
          $exe = "app/windows/dist/mcmusic/mcmusic.exe"
          if (-not (Test-Path $exe)) { throw "missing $exe" }
          $web = Get-ChildItem -Path "app/windows/dist/mcmusic" -Recurse -File |
            Where-Object { $_.Name -match 'QtWebEngine|QtWebKit|index\.html' }
          if ($web) { throw "Windows build contains a web engine or HTML: $($web.FullName -join ', ')" }
          $meta = Get-Content "app/windows/dist/mcmusic/version.json" -Raw | ConvertFrom-Json
          if ($meta.name -ne 'mcmusic') { throw "unexpected version metadata" }
          Write-Host "verified: native Qt exe, no HTML/WebView"
      - uses: actions/upload-artifact@v4
        with:
          name: mcmusic-windows
          path: |
            app/windows/dist/mcmusic
            app/windows/dist/mcmusic-windows-*.zip
          if-no-files-found: error

  ios-checks:
    name: iOS native build
    runs-on: macos-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v5
      - name: Install XcodeGen
        run: brew install xcodegen
      - name: Prepare app icon
        run: |
          set -euo pipefail
          mkdir -p app/ios/McMusic/Assets.xcassets/AppIcon.appiconset
          sips -z 1024 1024 web/icon-512.png --out app/ios/McMusic/Assets.xcassets/AppIcon.appiconset/icon-1024.png >/dev/null
      - name: Generate Xcode project
        run: xcodegen generate --spec app/ios/project.yml --project app/ios
      - name: Build and test unsigned iOS Simulator app
        run: |
          set -euo pipefail
          # Build the shippable app on its own so XCTest frameworks do not end
          # up embedded in the uploaded bundle.
          derived=build/ios
          common=(-project app/ios/McMusic.xcodeproj -configuration Release CODE_SIGNING_ALLOWED=NO)
          xcodebuild "${common[@]}" -scheme McMusicApp -derivedDataPath "$derived" \
            -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
            ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO build
          # Tests get a separate derived-data path for the same reason.
          sim_id=$(xcrun simctl list devices available -j | python3 -c 'import json,sys; d=json.load(sys.stdin); devs=[x for r in d["devices"].values() for x in r if x.get("isAvailable") and x["name"].startswith("iPhone")]; print(devs[0]["udid"] if devs else "")')
          if [ -n "$sim_id" ]; then
            xcodebuild "${common[@]}" -scheme McMusic -derivedDataPath build/ios-tests \
              -sdk iphonesimulator -destination "platform=iOS Simulator,id=$sim_id" \
              test
          else
            echo "no iPhone simulator available; skipping test action" >&2
          fi
      - name: Verify the iOS bundle is native
        run: |
          set -euo pipefail
          app=$(find build/ios/Build/Products -maxdepth 2 -type d -name 'McMusic.app' | head -1)
          test -n "$app"
          test -f "$app/McMusic"
          plutil -lint "$app/Info.plist"
          /usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$app/Info.plist" | grep -qx 'dev.mcmusic.ios'
          if find "$app" \( -iname '*WebView*' -o -iname 'index.html' -o -iname '*XCTest*' \) | grep -q .; then
            echo "iOS bundle contains a web view, HTML or test frameworks" >&2
            exit 1
          fi
          echo "verified: native SwiftUI app, no HTML/WebView/test frameworks"
      - uses: actions/upload-artifact@v4
        with:
          name: mcmusic-ios-simulator
          path: build/ios/Build/Products/Release-iphonesimulator/McMusic.app
          if-no-files-found: error
```

### `tests/test_no_gradients.py`

```python
"""Reject gradient, blur, shadow and glass rendering primitives in UI sources.

There is deliberately no allowlist and no suppression mechanism: every
occurrence reported by this scan is a hard failure.  Comments are blanked out
for the *scan only* (so prose such as "no gradients" is not an offence); the
failure report always quotes the original line verbatim.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Directory globs plus one explicit file.  No exclusions.
SCAN_ROOTS = (
    "ui/src",
    "ui/index.html",
    "web/embed",
    "gui/android/app/src/main/java",
    "gui/android/app/src/main/res",
    "app/ios/McMusic",
    "app/linux/mcmusic_linux",
)
EXTENSIONS = frozenset({".css", ".ts", ".tsx", ".js", ".html", ".kt", ".swift", ".py", ".xml"})

# Literal identifiers, matched as literal (case-insensitive) text -- never as a
# pattern that could abstract away a variable or a different identifier.
LITERAL_TOKENS = (
    "linear-gradient",
    "radial-gradient",
    "conic-gradient",
    "createLinearGradient",
    "createRadialGradient",
    # Android/SwiftUI/Qt rendering primitives, regardless of call style.
    "LinearGradient",
    "RadialGradient",
    "SweepGradient",
    "QConicalGradient",
    "angularGradient",
    "EllipticalGradient",
    "Brush.linearGradient",
    "Brush.radialGradient",
    "Brush.sweepGradient",
    "CAGradientLayer",
    "backdrop-filter",
    "-webkit-backdrop-filter",
    "backdrop_filter",
    "NSVisualEffectView",
    "UIBlurEffect",
    "ultraThinMaterial",
    "GaussianBlur",
    "QGraphicsBlurEffect",
    "setGraphicsEffect",
    "Modifier.blur",
    "Modifier.shadow",
    "shadowElevation",
    "QGraphicsDropShadowEffect",
    ".shadow(",
    "box-shadow",
    "drop-shadow",
    "text-shadow",
    "liquidGlass",
    "glass_border",
    "glass_highlight",
    "glass_strong",
)

# Bare identifiers need word boundaries so e.g. `realGlass` or `glassPane`
# are not silently conflated with the forbidden identifier `glass`.
IDENTIFIER_TOKENS = ("glass",)

_LINE_COMMENTS = {
    ".py": ("#",),
    ".ts": ("//",),
    ".tsx": ("//",),
    ".js": ("//",),
    ".kt": ("//",),
    ".swift": ("//",),
}
_BLOCK_COMMENTS = {
    ".css": (("/*", "*/"),),
    ".html": (("<!--", "-->"),),
    ".xml": (("<!--", "-->"),),
    ".py": (('"""', '"""'), ("'''", "'''")),  # docstrings are comments here
    ".ts": (("/*", "*/"),),
    ".tsx": (("/*", "*/"),),
    ".js": (("/*", "*/"),),
    ".kt": (("/*", "*/"),),
    ".swift": (("/*", "*/"),),
}
_QUOTED = frozenset({".py", ".ts", ".tsx", ".js", ".kt", ".swift"})


def _scan_text(line, suffix, state):
    """Blank out comments in `line`, preserving offsets and original characters."""
    chars = list(line)
    line_markers = _LINE_COMMENTS.get(suffix, ())
    blocks = _BLOCK_COMMENTS.get(suffix, ())
    index = 0
    quote = ""
    while index < len(chars):
        if state["block_end"]:
            end = state["block_end"]
            stop = line.find(end, index)
            if stop < 0:
                for pos in range(index, len(chars)):
                    chars[pos] = " "
                return "".join(chars)
            for pos in range(index, stop + len(end)):
                chars[pos] = " "
            index = stop + len(end)
            state["block_end"] = ""
            continue
        for opener, closer in blocks:
            if line.startswith(opener, index):
                for pos in range(index, index + len(opener)):
                    chars[pos] = " "
                index += len(opener)
                state["block_end"] = closer
                break
        if state["block_end"]:
            continue
        if quote:
            if line.startswith(quote, index):
                index += len(quote)
                quote = ""
            else:
                index += 1
            continue
        if suffix in _QUOTED and chars[index] in "'\"`":
            mark = chars[index]
            if suffix == ".py":
                triple = mark * 3
                quote = triple if line.startswith(triple, index) else mark
            else:
                quote = mark
            index += len(quote)
            continue
        if any(line.startswith(marker, index) for marker in line_markers):
            for pos in range(index, len(chars)):
                chars[pos] = " "
            return "".join(chars)
        index += 1
    return "".join(chars)


def _tokens_on_line(line, suffix, state):
    scanned = _scan_text(line, suffix, state).casefold()
    hits = []
    for token in LITERAL_TOKENS:
        if token.casefold() in scanned:
            hits.append(token)
    for token in IDENTIFIER_TOKENS:
        pattern = r"(?<![a-z0-9_$])" + token.casefold() + r"(?![a-z0-9_$])"
        if re.search(pattern, scanned):
            hits.append(token)
    # Visual blur APIs only.  A generic JS/DOM `.blur()` is focus management,
    # not a rendering effect, so bare `blur(` is not a token; CSS needs a
    # `filter:` declaration and Kotlin needs a call/import context.
    if re.search(r"(?:-webkit-)?filter\s*:\s*[^;}\n]*\bblur\s*\(", scanned):
        hits.append("filter: blur(")
    if suffix == ".kt":
        if re.search(r"(?<![a-z0-9_$])blur\s*\(", scanned):
            hits.append("blur(")
        if re.search(r"\bimport\s+[a-z0-9_.]*\.blur\s*$", scanned):
            hits.append("import ...blur")
    for match in re.finditer(r"elevation-([12])\s*:\s*([^;}\n]+)", scanned):
        value = match.group(2).strip()
        if value.casefold() != "none":
            hits.append("elevation-%s: %s" % (match.group(1), value))
    return list(dict.fromkeys(hits))


def _source_files():
    for root in SCAN_ROOTS:
        path = ROOT / root
        if path.is_file():
            if path.suffix in EXTENSIONS:
                yield path
        elif path.is_dir():
            for candidate in sorted(path.rglob("*")):
                if candidate.is_file() and candidate.suffix in EXTENSIONS:
                    yield candidate


def test_no_gradients_blurs_shadows_or_glass():
    violations = []
    for path in _source_files():
        state = {"block_end": ""}
        with path.open(encoding="utf-8", errors="replace") as source:
            for number, line in enumerate(source, 1):
                hits = _tokens_on_line(line, path.suffix, state)
                if hits:
                    text = line.rstrip("\r\n")
                    violations.append(
                        "%s:%d: %s: %s"
                        % (path.relative_to(ROOT).as_posix(), number, ", ".join(hits), text)
                    )
    assert not violations, (
        "%d forbidden rendering identifier(s) in UI sources (no allowlist):\n%s"
        % (len(violations), "\n".join(violations))
    )
```

### `tests/test_contrast.py`

```python
"""WCAG contrast gates for every committed token family in light and dark mode.

Reads design/tokens.generated.json (the committed generated artifact) and uses
the standard sRGB relative-luminance formula.  Failing pairs are all reported
together with exact family/mode/pair/colors/ratio: nothing is suppressed or
exempted and no threshold is relaxed.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "design" / "tokens.generated.json"

TEXT_MIN = 4.5
BOUNDARY_MIN = 3.0

TEXT_PAIRS = (
    ("onPrimary", "primary"),
    ("onPrimaryContainer", "primaryContainer"),
    ("onSecondary", "secondary"),
    ("onSecondaryContainer", "secondaryContainer"),
    ("onTertiary", "tertiary"),
    ("onTertiaryContainer", "tertiaryContainer"),
    ("onError", "error"),
    ("onErrorContainer", "errorContainer"),
    ("onBackground", "background"),
    ("onSurface", "surface"),
    ("onSurfaceVariant", "surfaceVariant"),
    ("fg", "bg"),
    ("fg", "surface"),
    ("dim", "bg"),
    ("dim", "surface"),
    ("accentText", "bg"),
    ("accentFg", "accent"),
    # `accent` is a bright legacy brand *fill*; `onPrimary` is the M3 foreground
    # paired only with the generated darker `primary` role. Text on the legacy
    # accent is checked by accentFg/accent above.
)
BOUNDARY_PAIRS = (
    ("outline", "background"),
    ("outlineVariant", "surfaceContainerLowest"),
)


def _channel(value):
    value = value / 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _luminance(hex_color):
    if not isinstance(hex_color, str) or len(hex_color) != 7 or not hex_color.startswith("#"):
        raise ValueError("expected #RRGGBB, got %r" % (hex_color,))
    red, green, blue = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def _contrast(foreground, background):
    light, dark = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def _color(variant, name):
    if name in variant["roles"]:
        return variant["roles"][name]
    return variant["legacy"].get(name)


def test_generated_tokens_meet_wcag_contrast():
    data = json.loads(TOKENS.read_text(encoding="utf-8"))
    families = data["families"]
    assert len(families) == 5, "expected exactly 5 families, found %d: %s" % (
        len(families), ", ".join(sorted(families))
    )

    failures = []
    checked = 0
    for family in sorted(families):
        for mode in ("light", "dark"):
            variant = families[family][mode]
            for pairs, minimum in ((TEXT_PAIRS, TEXT_MIN), (BOUNDARY_PAIRS, BOUNDARY_MIN)):
                for foreground_name, background_name in pairs:
                    foreground = _color(variant, foreground_name)
                    background = _color(variant, background_name)
                    if foreground is None or background is None:
                        if (foreground_name, background_name) == ("accent", "onPrimary"):
                            continue  # not meaningful when a legacy accent is absent
                        failures.append(
                            "%s/%s %s/%s: missing color (%r on %r)"
                            % (family, mode, foreground_name, background_name, foreground, background)
                        )
                        continue
                    ratio = _contrast(foreground, background)
                    checked += 1
                    if ratio < minimum:
                        failures.append(
                            "%s/%s %s/%s: %.2f:1 < %.1f:1 (%s on %s)"
                            % (family, mode, foreground_name, background_name,
                               ratio, minimum, foreground, background)
                        )

    assert not failures, (
        "%d of %d checked token pairs fail WCAG contrast:\n%s"
        % (len(failures), checked, "\n".join(failures))
    )
```

### `tests/test_generated_fresh.py`

```python
"""Generated design artifacts must match their sources in the working tree.

Runs each generator's own ``--check`` mode.  The only skip is a genuinely
missing Node executable (detected with ``shutil.which``); a stale artifact or a
generator error is always a failure with the combined stdout/stderr reported.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")
if NODE is None:
    pytest.skip(
        "node executable not found via shutil.which('node'); "
        "cannot run token generators",
        allow_module_level=True,
    )

SCRIPTS = ("scripts/gen-tokens.mjs", "scripts/gen-lucide.mjs")


def test_generated_files_are_fresh():
    failures = []
    for relative in SCRIPTS:
        script = ROOT / relative
        if not script.is_file():
            continue  # the optional icon generator is not present in this tree
        result = subprocess.run(
            [NODE, str(script), "--check"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        combined = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0:
            failures.append(
                "node %s --check exited %d\n%s"
                % (relative, result.returncode, combined.rstrip())
            )

    assert not failures, (
        "generated files are stale (run the generators listed above):\n%s"
        % "\n".join(failures)
    )
```

### `docs/design-4.2.md`

```markdown
# mcmusic 4.2.0 — Phase 0 design / feature specification

## 0. Status and inputs

- This document is the Phase 0 design record. It changes documentation only: no code, tokens, tests, CI or generated files are edited here.
- **No mockup images were supplied in the chat; only the written structure brief was available.** The written structure is authoritative. Visual details below are derived from Google app / Material 3 Expressive principles, not from pixel references.
- Platforms in scope, in delivery order: web, Android, iOS, Qt/desktop.

## 1. Foundations — single source of truth

- `design/tokens.json` is the single source of truth for 4.2.0. Its own note says to change values there and run `node scripts/gen-tokens.mjs` and `node scripts/gen-lucide.mjs` (`design/tokens.json:3`).
- Generated targets are produced by **both** generators, both of which are present in Phase 0 and support `--check`:
  - `scripts/gen-tokens.mjs` reads `design/tokens.json`, derives Material 3 roles with `@material/material-color-utilities@0.3.0` HCT, and writes `design/tokens.generated.json`, `ui/src/env.css`, and the marked blocks in `ui/src/common/theme.ts`, `gui/android/.../Design.kt`, `app/ios/McMusic/Theme.swift`, `app/linux/mcmusic_linux/theme.py` and `web/embed/widgets.js`.
  - `scripts/gen-lucide.mjs` reads every glyph from `ui/node_modules/lucide-static/icons/*.svg` and writes the marked blocks in `ui/src/common/lucide.tsx`, `gui/android/.../Lucide.kt`, `app/ios/McMusic/Lucide.swift`, `app/linux/mcmusic_linux/icons.py` plus 127 Android vector drawables. No glyph geometry is hand-copied.
- Generated files must never be hand-edited. `ui/src/env.css:1-2` is already marked as generated and flat-only.

### Palette and aliases

- Family ids and displayed family names are unchanged: `violet`/Violet, `indigo`/Indigo, `sky`/Sky, `aqua`/Aqua, `mint`/Mint (`design/tokens.json:54-130`; iOS `app/ios/McMusic/Theme.swift:6-10`).
- All legacy aliases must keep resolving: empty, `auto`, `system`, `flufi`, `dark`, `dusk`, `paper`, `light`, `ink`, `amoled`, `midnight`, `tide`, `forest`, `rose`, `copper`, `mocha` (`design/tokens.json:36-53`). Existing resolvers already implement the contract: web `ui/src/common/theme.ts:1-10,839-859`, Android `gui/android/.../Design.kt:221-252`, iOS `app/ios/McMusic/Theme.swift:12-28`, embed palette docs `src/routes/system_routes.py:505,512`.
- Legacy swatches stay byte-identical so stored user settings and embed tags keep working (`design/tokens.json:3`; `ui/src/common/theme.ts:31-35`; `src/database.py` track data is unaffected).

### Shape, spacing, type

- Shape scale: `4 / 8 / 12 / 16 / 28 / 36` plus pill (`design/tokens.json:4-11`). Cards use 28, hero cards 36, chips and buttons are pill, covers stay in the 20–28 range (`design/tokens.json:12-16`). Generated CSS exposes the same values at `ui/src/env.css:34-44`.
- Spacing is a strict 4px grid (`design/tokens.json:18`).
- Every interactive target is at least 48×48 CSS/dp/pt (`design/tokens.json:16`; `ui/src/env.css:44`). Current web override of 40px in `ui/src/app.css:133-140` is below the 4.2.0 floor and must be raised in Phase 1.
- Material 3 type scale, sizes/line heights from `design/tokens.json:29-35`: display 36/44 (700), headline 28/36 (700), title 22/28 (700), body 16/24 (400), label 14/20 (600).
- **Keep Lexend for 4.2.0.** Lexend is referenced in the client (`ui/src/app.css:119-124`, `ui/src/pages/Set/style.css:27`) and requested through the flufi-ui CDN import. No local font binaries were found in the tracked tree (search for `*.woff`, `*.woff2`, `*.ttf`, `*.otf` outside `node_modules` returned none), so do not claim Lexend is already bundled locally.
- **Google Sans Flex licence evidence:** fetched `https://raw.githubusercontent.com/googlefonts/googlesans-flex/main/OFL.txt`. It states: `Copyright 2022 The Google Sans Flex Project Authors (github.com/googlefonts/googlesans-flex)` and `SIL Open Font License, Version 1.1`. The licence permits bundling/embedding/redistribution with software subject to its conditions (OFL 1.1, clauses 1–5).
- **Decision:** Google Sans Flex is bundleable OFL, but it is **not adopted** for 4.2.0. No mockups were supplied; changing the face without a visual reference would be a branding risk.
- **Font delivery:** Phase 0 adds `@fontsource-variable/inter`, `@fontsource-variable/jetbrains-mono` and `@fontsource-variable/lexend` (all OFL-1.1) as local dependencies, imports them from `ui/src/main.tsx`, and adds `scripts/strip-font-cdn.mjs` to `scripts/build_ui.sh`. The build strips the Google Fonts CDN `@import` carried by `flufi-ui/dist/style.css` (and fails on any unexpected remote `@import`), so no CDN font request ships. The font family remains Lexend as before.

## 2. Visual language

- Flat tonal containers only. No gradients, blur, glass, backdrop effects or decorative shadows. The generated baseline already sets `--elevation-1/2: none` and `--shadow-raised: none` (`ui/src/env.css:24-29`).
- Pre-4.2 exceptions (canvas gradients, widget washes, glass brush/highlight, `Glass.kt`, kyant backdrop dependency) are removed in Phase 0 so `tests/test_no_gradients.py` can gate every later phase with no allowlist.
- Icons are Lucide only: web registry `ui/src/common/lucide.tsx:1-20`, policy `docs/ui-references.md:26-28`, Android `gui/android/.../ui/Lucide.kt`, iOS `app/ios/McMusic/Lucide.swift:3-9`, Qt `app/linux/mcmusic_linux/icons.py:1-5`. No emoji, icon fonts, SF Symbols or hand-written one-off SVGs.
- Cover placeholders: a flat tonal container with a Lucide glyph/shape rotating among circle, squircle (rounded rect), cookie, flower and pentagon. Real artwork is shown as-is — never re-tinted or gradient-washed. Current fallback is a text-initial SVG (`ui/src/common/net/api.ts:176-180`) and must be replaced in Phase 1; the new glyph names must be included in the Lucide generated target.

## 3. Dynamic colour

- Web and Android are first-class for dynamic colour: derive a tonal scheme from the current cover's dominant colour through HCT, then fall back to the selected family palette when there is no artwork or extraction fails. The HCT machinery already exists in the shared generator (`scripts/gen-tokens.mjs:7-19,41-48`; `ui/src/common/theme.ts:13-19`).
- iOS and Qt stay on static family palettes in 4.2.0 (`app/ios/McMusic/Theme.swift:4-10,72-80`; `app/linux/mcmusic_linux/theme.py:3-30`).
- Android additionally supports the Wallpaper palette (Material You, Android 12+). The app's `minSdk`/`targetSdk` are 34 (`gui/android/app/build.gradle.kts:13-14`), so the platform APIs are available; there is no current `DynamicColors`/wallpaper usage in `gui/android/app/src/main`, so this is new Phase 2 work.
- Dynamic schemes never change a family id or a legacy alias; they only supply tonal role values for the active surface.

## 4. Motion and feedback

- Medium spring with damping ~0.7 (`design/tokens.json:19-21`), press scale 0.96 (`design/tokens.json:21`), play/pause shape morph with ~320ms duration (`design/tokens.json:22`), wavy progress while playing and flat progress when paused (`design/tokens.json:23-24`).
- Android and iOS haptics on primary transport/press actions. No haptic calls exist today (`gui/android/app/src/main` and `app/ios` have no `performHaptic`/`UIFeedback` matches), so this is new native work in Phases 2 and 3.
- Honour platform reduced-motion settings: disable springs, morphs and waves (`design/tokens.json:27`; existing web precedent `ui/src/components/Equaliser/style.css:12-16`).
- Playful motion is a user setting keyed `playfulMotion`, default on (`design/tokens.json:25-26`). It is not yet present in client prefs; Phases 1–4 must wire it.

## 5. Feature truth audit (source-verified)

| Claim / surface | Actual state in source | 4.2.0 rule |
| --- | --- | --- |
| Dolby Atmos / Spatial Audio / Spatial Mix | No matches for `Dolby`, `Atmos`, `Spatial` in `src/`, `ui/src/`, `gui/android/...`, `app/ios/`, `app/linux/`, `web/`. `src/song_meta.py:20` only treats `mix` as a title-noise token. | Never show these labels. |
| “Mix” chips | No Mix chip/shelf exists. Home sections are `Made for you`, `Discover`, `Your top tracks`, `Recently added`, `Most liked on YouTube` (`src/routes/personal_routes.py:472-478`); radio is a separate action (`ui/src/pages/Set/Set.tsx:147-149`). | Use `Mix` **only** for a server-generated mix. Otherwise omit the chip; do not relabel radio or a filtered library as a Mix. |
| Lossless badge / codec | `src/config.py:89` allows `.mp3/.m4a/.aac/.opus/.flac/.wav/.webm/.ogg`; `src/yt_playlist_to_mp3.py:25,143` exposes the same download formats. Metadata read in `src/routes/library_routes.py:30-54` has no codec/bitrate; `tracks` schema has no codec/bitrate columns (`src/database.py:25-44`). | Show `Lossless` only for real `flac`, `alac` or `wav`. Otherwise show actual codec/bitrate from file metadata; never infer quality from a container or extension alone. |
| Explicit `E` | Real flag chain exists: `explicit_auto`/`explicit_ovr` (`src/database.py:40-41`), override wins in `track_dict` (`src/database.py:468-474`), auto detection from YouTube `age_limit >= 18` or an `[explicit]` title marker (`src/library_scan.py:302-304`), admin override endpoint (`src/routes/library_routes.py:273-280`), web `hide_explicit` pref and info dialog (`ui/src/common/prefs.ts:43,71,90`; `ui/src/components/TrackInfo/TrackInfoDialog.tsx:62,103-116`). | Show `E` only when the resolved flag is true from a real tag/age limit/admin override. Never infer it from genre, mood or artwork. |
| `Made for you` | Real: `/api/home` emits it from `recommend(uid, 30)` (`src/routes/personal_routes.py:458-486`); `recommend` uses plays/likes/genre affinity and calls `rank_for` from the model (`src/routes/personal_routes.py:382-455`). The model is gated by observations/work rate (`src/next_song_model.py:146-152,162-170`) and the affinity fallback remains real. Faves is rebuilt from `listening_events` (`src/routes/personal_routes.py:168-192`). Empty sections are dropped (`src/routes/personal_routes.py:484`). | Keep `Made for you`. If no recommendation/history backs it, use `Pick up where you left off` (recent plays) or `Most played` (play counts), not a fake personalised claim. |
| Radio / Mixes | The brief’s rule is `no Radio backend -> Mixes only if real else omit`. Source check finds a real similarity endpoint: `GET /api/radio/<tid>` returns up to 40 similar tracks (`src/routes/personal_routes.py:509-532`), used by web `ui/src/common/net/api.ts:387-391`, Android `gui/android/.../data/Api.kt:394-396` and iOS `app/ios/McMusic/Repo.swift:179-180`. There is no dedicated curated Radio/Mixes product backend. | Do not present a curated `Radio` destination or `Mixes` tab. Keep the existing `Start radio` action because it is backed by real data; label it Radio, not Mix. If that endpoint is ever removed, omit the surface entirely. |
| Browse / Charts | Genres are real tag data shown via `ui/src/components/GenreList/GenreList.tsx:1-12` and carried in API state (`ui/src/common/net/api.ts:230,248`). User-visible ranking shelves come from plays/YouTube likes (`src/routes/personal_routes.py:464-477`); detailed listening top-tracks exist only behind the admin gate (`src/routes/system_routes.py:1618-1654`). | Build Browse from actual genre tags. Build Charts from real listening stats or likes; use `Your top tracks` / `Most liked on YouTube` for user-facing shelves until a public stats endpoint exists. No fabricated global chart. |
| Sing Mode | Synced vs plain lyrics are distinguished at source (`src/lyrics.py:36-41,49-52`) and exposed with `source` (`src/routes/library_routes.py:354-372`). Web parses LRC (`ui/src/components/Lyrics/LyricsPanel.tsx:1-4,44-65`); Android parses LRC timestamps and highlights by playback position (`gui/android/.../ui/screens/Player.kt:527-560,587-597`). | Enable Sing Mode only for genuine time-synced LRC/`lrclib-synced` lyrics. Plain lyrics get a read-only lyrics sheet. |

## 6. Phase plan

Each phase is a **separate commit** and must be **CI-green before the next phase starts** (`.github/workflows/ci.yml:1`; release already requires passing CI for the commit, `.github/workflows/release.yml:32-50`).

| Phase | Commit scope | Exit gate |
| --- | --- | --- |
| Phase 0 — foundations | This design record; token contract, alias/name guarantees, licence/font decision, feature truth audit, both generators, generated files, local fonts, flatness/contrast/freshness gates and removal of pre-existing gradient/glass/shadow effects in all four clients. | CI green; doc and audit reviewed; no hand-edited generated files. |
| Phase 1 — web | `ui/` + built `web/ui/`: shell/transport rebuild, Home/Search/Library, Lyrics\|Up next, wavy progress, morphing play, tonal pills/covers, playful motion, truth-checked labels. | CI green; built stylesheet contains no Google Fonts CDN import. |
| Phase 2 — Android | `gui/android/`: generated palette/Lucide targets, cover-derived HCT dynamic colour, Wallpaper palette (Android 12+), haptics, motion, truth-checked labels. | CI green; Android build/tests pass. |
| Phase 3 — iOS | `app/ios/`: static family palettes, generated tokens/icons, motion settings, haptics, truth-checked labels. | CI green; unsigned Simulator build passes. |
| Phase 4 — Qt | `app/linux/`: static family palettes, generated tokens/icons, flat painting, motion settings, truth-checked labels. | CI green; Linux/deb build passes. |
| Phase 5 — version/release | Align version surfaces: Android `versionName`/`versionCode` (`gui/android/app/build.gradle.kts:15-16`), iOS `MARKETING_VERSION`/`CURRENT_PROJECT_VERSION` (`app/ios/project.yml:48-49`), Qt `app/linux/mcmusic_linux/version.py:9-21`, and server `BUILD`/`SHELL_VERSION` reporting (`src/config.py:124`, `src/mcmusic.py:371-376`). Publish via the existing release workflow. | CI green plus release verification; no phase after this. |

## 7. Verification limits

- Mockups are unavailable: visual fidelity to a reference cannot be checked, so structure and the written brief govern.
- Device rendering cannot be verified locally for web, Android, iOS or Qt at this stage.
- Codesign is unavailable on Linux; macOS signing verification happens in CI/release (`.github/workflows/release.yml:181-185`).
- There is no paid Apple Developer account, so device builds and store distribution are out of local reach; CI builds/tests the unsigned iOS Simulator target.
- Local `apt-get` is unavailable; native dependency installation and system-level packaging checks must rely on the existing CI images.
- Live database changes require explicit user permission; this Phase 0 work reads source only and does not mutate data.
```
