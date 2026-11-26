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
