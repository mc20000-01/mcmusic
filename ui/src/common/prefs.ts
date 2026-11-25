import { signal } from "@preact/signals";
import { API } from "./net/api";
import {
    applyIconStyle, applyPalette, DEFAULT_ACCENT, DEFAULT_ICON_FILLED,
    DEFAULT_ICON_STROKE, DEFAULT_PALETTE, normalizeIconStroke, type IconStroke,
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

export type Settings = Record<string, any>;

export async function loadPrefs(): Promise<Settings | null> {
    try {
        const s = await API.getSettings();
        volume.value = Math.min(1, Math.max(0, Number(s.volume ?? 0.8)));
        covers.value = s.covers !== false;
        hideExplicit.value = !!s.hide_explicit;
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
    if (s.rotur_activity != null) roturActivity.value = !!s.rotur_activity;
    if (s.discord_activity != null) discordActivity.value = !!s.discord_activity;
    if (s.theme != null) setPalettePreference(String(s.theme));
    if (s.accent != null) setAccentPreference(String(s.accent));
    if (s.iconStroke != null) setIconStrokePreference(s.iconStroke);
    if (s.iconFilled != null) setIconFilledPreference(s.iconFilled);
    if (s.autoplay != null && localAutoplayValue() == null) autoplay.value = s.autoplay !== false;
}
