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

export type PaletteMode = "light" | "dark";
export type FamilyId = "violet" | "indigo" | "sky" | "aqua" | "mint";

export interface PaletteTokens {
    bg: string;
    bg2: string;
    surface: string;
    surface2: string;
    fg: string;
    dim: string;
    dim2: string;
    line: string;
    line2: string;
    accent: string;
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

export const PALETTE_FAMILIES: readonly PaletteFamily[] = [
    {
        id: "violet",
        name: "Violet",
        light: {
            bg: "#F5F2FF", bg2: "#EDE7FF", surface: "#FFFFFF", surface2: "#F7F4FF",
            fg: "#08060D", dim: "#473872", dim2: "#6A54AA", line: "#DACDFF", line2: "#CAB8FF",
            accent: "#9F7EFF",
        },
        dark: {
            bg: "#171721", bg2: "#222130", surface: "#2A293C", surface2: "#444361",
            fg: "#FFFFFF", dim: "#AAAAB7", dim2: "#8B8A9D", line: "#35344B", line2: "#605F78",
            accent: "#9F7EFF",
        },
    },
    {
        id: "indigo",
        name: "Indigo",
        light: {
            bg: "#F2F4FF", bg2: "#E8EBFF", surface: "#FFFFFF", surface2: "#F5F6FF",
            fg: "#08060D", dim: "#3B4172", dim2: "#5761AA", line: "#CFD5FF", line2: "#BAC3FF",
            accent: "#8293FF",
        },
        dark: {
            bg: "#12171F", bg2: "#1B212D", surface: "#212838", surface2: "#36425B",
            fg: "#FFFFFF", dim: "#A4A9B5", dim2: "#828999", line: "#2A3346", line2: "#545E73",
            accent: "#8293FF",
        },
    },
    {
        id: "sky",
        name: "Sky",
        light: {
            bg: "#F1F8FE", bg2: "#E7F3FE", surface: "#FFFFFF", surface2: "#F4F9FE",
            fg: "#08060D", dim: "#385272", dim2: "#527CA9", line: "#CCE5FE", line2: "#B6DAFE",
            accent: "#7BBDFE",
        },
        dark: {
            bg: "#182127", bg2: "#222F39", surface: "#2A3A46", surface2: "#455F72",
            fg: "#FFFFFF", dim: "#ABB7BF", dim2: "#8B9BA7", line: "#354A58", line2: "#607787",
            accent: "#7BBDFE",
        },
    },
    {
        id: "aqua",
        name: "Aqua",
        light: {
            bg: "#F1FBFC", bg2: "#E7F9FA", surface: "#FFFFFF", surface2: "#F4FCFD",
            fg: "#08060D", dim: "#386168", dim2: "#53939A", line: "#CDF3F5", line2: "#B6EDF1",
            accent: "#7CE0E6",
        },
        dark: {
            bg: "#15241C", bg2: "#1F3328", surface: "#263F32", surface2: "#3E6751",
            fg: "#FFFFFF", dim: "#A8BAB0", dim2: "#87A093", line: "#30503F", line2: "#5A7D6B",
            accent: "#7CE0E6",
        },
    },
    {
        id: "mint",
        name: "Mint",
        light: {
            bg: "#F1FFF5", bg2: "#E7FFEE", surface: "#FFFFFF", surface2: "#F4FFF7",
            fg: "#08060D", dim: "#386E4C", dim2: "#52A76F", line: "#CCFFDC", line2: "#B6FFCC",
            accent: "#7BFFA4",
        },
        dark: {
            bg: "#15241A", bg2: "#1F3425", surface: "#26412E", surface2: "#3E694B",
            fg: "#FFFFFF", dim: "#A8BBAE", dim2: "#87A28F", line: "#30513A", line2: "#5A7F66",
            accent: "#7BFFA4",
        },
    },
];

function concrete(family: PaletteFamily, mode: PaletteMode): Palette {
    const tokens = family[mode];
    return {
        ...tokens,
        id: `${family.id}-${mode}`,
        family: family.id,
        mode,
    };
}

/** Every pinned half of every family, keyed by its concrete id. */
export const PALETTE_VARIANTS: Record<string, Palette> = Object.fromEntries(
    PALETTE_FAMILIES.flatMap(f => ([
        [`${f.id}-light`, concrete(f, "light")] as [string, Palette],
        [`${f.id}-dark`, concrete(f, "dark")] as [string, Palette],
    ])),
);

/** Legacy settings/embed ids. Aliases resolve to a concrete variant where the
 *  old name already implied light or dark; bare family names stay adaptive. */
export const PALETTE_ALIASES: Record<string, string> = {
    "": "violet",
    auto: "violet",
    system: "violet",
    flufi: "violet-dark",
    dark: "violet-dark",
    dusk: "violet-dark",
    paper: "violet-light",
    light: "violet-light",
    ink: "indigo-dark",
    amoled: "indigo-dark",
    midnight: "sky-dark",
    tide: "aqua-dark",
    forest: "mint-dark",
    rose: "violet-dark",
    copper: "violet-dark",
    mocha: "violet-dark",
};

export const DEFAULT_PALETTE = "violet";
export const DEFAULT_ACCENT = "";

/** Shared foreground/status colours. Kept here so no UI stylesheet needs to
 *  hardcode a hex. Built-in accents are light, so they use INK; a custom accent
 *  override picks whichever foreground has the better contrast. */
const INK = "#08060D";
const WHITE = "#FFFFFF";
const SUCCESS = "#1DB954";
const WARNING = "#FFBF69";

/** Pick ink or white for text/icon painted on an accent fill. Unparseable
 *  CSS colours keep the built-in ink foreground. */
function readableOn(color: string): string {
    const value = color.trim();
    const hex = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(value);
    const rgb = /^rgba?\(\s*(\d+)\s*[,\s]\s*(\d+)\s*[,\s]\s*(\d+)/i.exec(value);
    let channels: number[] | null = null;
    if (hex) {
        const digits = hex[1].length === 3
            ? hex[1].split("").map(c => c + c).join("")
            : hex[1];
        channels = [0, 2, 4].map(i => parseInt(digits.slice(i, i + 2), 16));
    } else if (rgb) {
        channels = [Number(rgb[1]), Number(rgb[2]), Number(rgb[3])];
    }
    if (!channels) return INK;
    const [r, g, b] = channels.map(c => {
        const v = Math.min(255, Math.max(0, c)) / 255;
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    return luminance > 0.229 ? INK : WHITE;
}

/** Fallbacks for canvas code, which cannot consume CSS color-mix(). */
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

/** Translate the sheet's tokens into the flufi-ui custom properties, plus the
 *  few shared extras the shell uses. */
export function paletteVars(p: Palette, accentOverride = ""): Record<string, string> {
    const accent = accentOverride.trim() || p.accent;
    const hoverTarget = p.mode === "light" ? p.fg : WHITE;
    const shadow = p.mode === "light" ? "rgba(8, 6, 13, 0.42)" : "rgba(0, 0, 0, 0.55)";
    const shadowDeep = p.mode === "light"
        ? "rgba(8, 6, 13, 0.64)"
        : "rgba(0, 0, 0, 0.85)";
    return {
        "--back": p.bg,
        "--back-raised": p.bg2,
        "--flat-hover": `color-mix(in srgb, ${p.line} 32%, ${p.bg})`,
        "--prim": p.surface,
        "--prim-brighter": p.surface2,
        "--seco": p.bg2,
        "--tert": p.line,
        "--tert-hover": p.line2,
        "--text": p.fg,
        "--text-bright": p.fg,
        "--text-dim": p.dim,
        "--text-dark": p.dim2,
        "--accent": accent,
        "--accent-hover": `color-mix(in srgb, ${accent} 82%, ${hoverTarget})`,
        "--text-on-light": readableOn(accent),
        "--back-border": p.line,
        "--prim-border": p.line2,
        "--shadow": shadow,
        "--shadow-raised": `0 10px 30px -18px ${shadowDeep}`,
        "--backdrop": "rgba(8, 6, 13, 0.72)",
        "--success": SUCCESS,
        "--warning": WARNING,
        "--equaliser": "var(--accent)",
        "--radius": "10px",
    };
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
    return currentPalette;
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
        for (const [name, value] of Object.entries(paletteVars(palette, accent)))
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

// Establish an inline palette before components mount: later equal-specificity
// flufi-ui :root rules cannot beat these inline properties.
applyPalette(DEFAULT_PALETTE, DEFAULT_ACCENT);
