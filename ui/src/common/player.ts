import { effect, signal } from "@preact/signals";
import { API } from "./net/api";
import { volume } from "./prefs";

// One <audio> for the whole app, driven by signals so any track row and the
// player bar stay in sync.
const audio = new Audio();
audio.preload = "auto";

export type NowPlaying = {
    id: string;
    title: string;
    artist: string;
    album?: string;
    setUuid?: string;
    artistUuid?: string;
};

export const currentId = signal<string | null>(null);
export const nowPlaying = signal<NowPlaying | null>(null);
export const isPlaying = signal(false);
export const position = signal(0);
export const duration = signal(0);
/** Set when the stream fails, so the bar can say so instead of sitting silent. */
export const playError = signal<string | null>(null);

/** The current queue (array of { id, title, artist }) and the index within it. */
export const queue = signal<{ id: string; title: string; artist: string; setUuid?: string; artistUuid?: string }[]>([]);
export const queueIndex = signal(-1);
export type RepeatMode = "off" | "all" | "one";
export const repeatMode = signal<RepeatMode>("off");
export const shuffleEnabled = signal(false);

audio.addEventListener("play", () => { isPlaying.value = true; });
audio.addEventListener("pause", () => { isPlaying.value = false; });
audio.addEventListener("ended", () => {
    isPlaying.value = false;
    const q = queue.value;
    const idx = queueIndex.value;
    if (q.length === 0 || idx < 0) return;
    if (repeatMode.value === "one") {
        audio.currentTime = 0;
        audio.play().catch(() => { isPlaying.value = false; });
        return;
    }
    const nextIdx = idx + 1;
    if (nextIdx < q.length) {
        playQueueIndex(nextIdx);
        return;
    }
    if (repeatMode.value === "all") {
        playQueueIndex(0);
        return;
    }
    queueIndex.value = -1;
});
audio.addEventListener("error", () => {
    isPlaying.value = false;
    playError.value = "Couldn't play this track.";
});
audio.addEventListener("timeupdate", () => { position.value = audio.currentTime; });
audio.addEventListener("loadedmetadata", () => { duration.value = audio.duration || 0; });

// Safari refuses a zero-volume autoplay, so clamp to a whisper, not silence.
effect(() => { audio.volume = Math.max(0.001, Math.min(1, volume.value)); });

const reported = new Set<string>();

export function playTrack(id: string, meta?: Omit<NowPlaying, "id"> & { setUuid?: string; artistUuid?: string }) {
    if (currentId.value !== id) {
        currentId.value = id;
        playError.value = null;
        audio.src = API.streamUrl(id);
    }
    if (meta) nowPlaying.value = { id, ...meta };
    audio.play().catch(() => {
        isPlaying.value = false;
        playError.value = "Couldn't start playback. Try again.";
    });

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

export function playQueue(list: { id: string; title: string; artist: string; setUuid?: string; artistUuid?: string }[], startIndex = 0) {
    queue.value = list;
    queueIndex.value = Math.max(0, Math.min(startIndex, list.length - 1));
    const cur = list[queueIndex.value];
    playTrack(cur.id, { title: cur.title, artist: cur.artist, setUuid: cur.setUuid, artistUuid: cur.artistUuid });
}

export function playQueueIndex(index: number) {
    if (index < 0 || index >= queue.value.length) return;
    queueIndex.value = index;
    const cur = queue.value[index];
    playTrack(cur.id, { title: cur.title, artist: cur.artist, setUuid: cur.setUuid, artistUuid: cur.artistUuid });
}

export function playNext(opts?: { allowWrap?: boolean }) {
    const q = queue.value;
    if (q.length === 0) return;
    if (shuffleEnabled.value && q.length > 1) {
        let nextIdx = queueIndex.value;
        if (q.length === 1) nextIdx = 0;
        else {
            while (nextIdx === queueIndex.value) {
                nextIdx = Math.floor(Math.random() * q.length);
            }
        }
        playQueueIndex(nextIdx);
        return;
    }
    const next = queueIndex.value + 1;
    if (next < q.length) {
        playQueueIndex(next);
        return;
    }
    if (repeatMode.value === "all" || opts?.allowWrap) {
        playQueueIndex(0);
    }
}

export function playPrev() {
    const q = queue.value;
    if (q.length === 0) return;
    if (audio.currentTime > 3) {
        seekTo(0);
        return;
    }
    const prev = queueIndex.value - 1;
    if (prev >= 0) {
        playQueueIndex(prev);
        return;
    }
    if (repeatMode.value === "all") {
        playQueueIndex(q.length - 1);
        return;
    }
    seekTo(0);
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

export function setVolume(value: number) {
    volume.value = Math.min(1, Math.max(0, value));
}

export function toggleMute() {
    audio.muted = !audio.muted;
}

export function setShuffle(on: boolean) {
    shuffleEnabled.value = on;
}

export function cycleRepeat(): RepeatMode {
    const order: RepeatMode[] = ["off", "all", "one"];
    const i = order.indexOf(repeatMode.value);
    const next = order[(i + 1) % order.length];
    repeatMode.value = next;
    return next;
}

export function formatTime(seconds: number): string {
    if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${String(s).padStart(2, "0")}`;
}
