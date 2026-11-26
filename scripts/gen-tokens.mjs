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
