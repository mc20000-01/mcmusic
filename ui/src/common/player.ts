import { effect, signal } from "@preact/signals";
import { API } from "./net/api";
import { volume } from "./prefs";

// One <audio> for the whole app, driven by signals so any track row and the
// player bar stay in sync.
const audio = new Audio();
audio.preload = "auto";

export type NowPlaying = { id: string; title: string; artist: string };

export const currentId = signal<string | null>(null);
export const nowPlaying = signal<NowPlaying | null>(null);
export const isPlaying = signal(false);
export const position = signal(0);
export const duration = signal(0);

audio.addEventListener("play", () => { isPlaying.value = true; });
audio.addEventListener("pause", () => { isPlaying.value = false; });
audio.addEventListener("ended", () => { isPlaying.value = false; });
audio.addEventListener("timeupdate", () => { position.value = audio.currentTime; });
audio.addEventListener("loadedmetadata", () => { duration.value = audio.duration || 0; });

// Safari refuses a zero-volume autoplay, so clamp to a whisper, not silence.
effect(() => { audio.volume = Math.max(0.001, Math.min(1, volume.value)); });

const reported = new Set<string>();

export function playTrack(id: string, meta?: Omit<NowPlaying, "id">) {
    if (currentId.value !== id) {
        currentId.value = id;
        audio.src = API.streamUrl(id);
    }
    if (meta) nowPlaying.value = { id, ...meta };
    audio.play().catch(() => { isPlaying.value = false; });

    if (!reported.has(id)) {
        reported.add(id);
        fetch("/api/plays", {
            method: "POST",
            credentials: "same-origin",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ track_id: Number(id) }),
        }).catch(() => { /* play counts are best effort */ });
    }
}

export function toggleTrack(id: string, meta?: Omit<NowPlaying, "id">) {
    if (currentId.value === id) {
        if (audio.paused) audio.play().catch(() => {});
        else audio.pause();
        return;
    }
    playTrack(id, meta);
}

export function togglePlay() {
    if (!currentId.value) return;
    if (audio.paused) audio.play().catch(() => {});
    else audio.pause();
}

export function seekTo(seconds: number) {
    if (Number.isFinite(seconds)) audio.currentTime = seconds;
}

export function formatTime(seconds: number): string {
    if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${String(s).padStart(2, "0")}`;
}
