import { signal } from "@preact/signals";
import { API } from "./net/api";

// Server-stored preferences. The v3 client honours the ones that change what
// it renders/plays; the rest are kept for the Android/Qt/legacy clients.
export const volume = signal(0.8);
export const covers = signal(true);
export const hideExplicit = signal(false);

export type Settings = Record<string, any>;

export async function loadPrefs(): Promise<Settings | null> {
    try {
        const s = await API.getSettings();
        volume.value = Math.min(1, Math.max(0, Number(s.volume ?? 0.8)));
        covers.value = s.covers !== false;
        hideExplicit.value = !!s.hide_explicit;
        return s;
    } catch {
        return null;
    }
}

export function applyPrefs(s: Settings) {
    if (s.volume != null) volume.value = Math.min(1, Math.max(0, Number(s.volume)));
    if (s.covers != null) covers.value = !!s.covers;
    if (s.hide_explicit != null) hideExplicit.value = !!s.hide_explicit;
}
