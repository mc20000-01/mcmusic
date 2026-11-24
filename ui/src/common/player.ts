import { effect, signal } from "@preact/signals";
import { API } from "./net/api";
import { peekAuth } from "./auth";
import { autoplay, discordActivity, roturActivity, setAutoplayPreference, volume } from "./prefs";

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
    liked?: boolean;
};
export type QueueItem = {
    id: string;
    title: string;
    artist: string;
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
/** Last listening-activity delivery failure, surfaced in Settings. */
export const activityError = signal<string | null>(null);
/** Whether the queue drawer is open; shared with the global keyboard shortcuts. */
export const queueOpen = signal(false);
/** Like state of the current track, kept in sync with the Likes view. */
export const currentLiked = signal(false);

/** The current queue (array of { id, title, artist }) and the index within it. */
export const queue = signal<QueueItem[]>([]);
export const queueIndex = signal(-1);

/** Let the presence/command layer publish immediately after transport changes. */
function emitPlaybackChange() {
    try {
        window.dispatchEvent(new CustomEvent("mc:playbackchange"));
    } catch { /* no window during tests */ }
}
export type RepeatMode = "off" | "all" | "one";
export const repeatMode = signal<RepeatMode>("off");
export const shuffleEnabled = signal(false);
/** True when the server's MDL chose the queue order instead of Math.random. */
export const modelShuffle = signal(false);
export { autoplay };

// ---------------------------------------------------------------- persistence
// Mirrors the legacy player snapshot: a reload or background update restores
// the paused queue and position, without ever auto-resuming audio.
const SNAPSHOT_KEY = "mcmusic:player:v1";
const SNAPSHOT_MAX_AGE = 7 * 24 * 60 * 60 * 1000;
const STALE_POSITION_AGE = 30 * 60 * 1000;
type Snapshot = {
    version: 1;
    track: NowPlaying | null;
    queue: QueueItem[];
    queueIndex: number;
    position: number;
    duration: number;
    repeatMode: RepeatMode;
    shuffleEnabled: boolean;
    modelShuffle?: boolean;
    autoplay: boolean;
    saved: number;
};
let restoring = true;
let lastSave = 0;

function snapshot(): Snapshot {
    const t = nowPlaying.value;
    return {
        version: 1,
        track: t ? { ...t } : null,
        queue: queue.value.map(x => ({ ...x })),
        queueIndex: queueIndex.value,
        position: audio.currentTime || position.value || 0,
        duration: audio.duration || duration.value || 0,
        repeatMode: repeatMode.value,
        shuffleEnabled: shuffleEnabled.value,
        modelShuffle: modelShuffle.value,
        autoplay: autoplay.value,
        saved: Date.now(),
    };
}

/** Throttled for timeupdate; callers pass true for state changes/unload. */
export function saveSnapshot(force = false) {
    if (restoring) return;
    if (!force && Date.now() - lastSave < 5000) return;
    lastSave = Date.now();
    try {
        localStorage.setItem(SNAPSHOT_KEY, JSON.stringify(snapshot()));
    } catch { /* private mode / quota: playback still works */ }
}

function validTrack(v: any): v is QueueItem {
    return v != null && typeof v.id === "string" && v.id !== "" &&
        typeof v.title === "string";
}

function restoreSnapshot() {
    try {
        const raw = localStorage.getItem(SNAPSHOT_KEY);
        if (!raw) return;
        const s = JSON.parse(raw) as Snapshot;
        if (s?.version !== 1 || !Number.isFinite(s.saved)) return;
        const age = Date.now() - s.saved;
        if (age < 0 || age > SNAPSHOT_MAX_AGE) return;
        const list: QueueItem[] = Array.isArray(s.queue) ? s.queue.filter(validTrack) : [];
        const idx = Math.max(-1, Math.min(Number(s.queueIndex) || 0, list.length - 1));
        queue.value = list;
        queueIndex.value = idx;
        repeatMode.value = s.repeatMode === "one" || s.repeatMode === "all" ? s.repeatMode : "off";
        shuffleEnabled.value = !!s.shuffleEnabled;
        modelShuffle.value = !!s.modelShuffle;
        if (typeof s.autoplay === "boolean") setAutoplayPreference(s.autoplay);
        const track = list[idx];
        if (!track) return;
        currentId.value = track.id;
        nowPlaying.value = {
            id: track.id,
            title: track.title,
            artist: track.artist || "",
            setUuid: track.setUuid,
            artistUuid: track.artistUuid,
            liked: (track as any).liked,
        };
        currentLiked.value = !!(track as any).liked;
        duration.value = Number(s.duration) || 0;
        const stale = age > STALE_POSITION_AGE;
        const at = stale ? 0 : Math.max(0, Number(s.position) || 0);
        position.value = at;
        audio.src = API.streamUrl(track.id);
        audio.load();
        // Seek once the stream knows its real duration; stale positions start
        // from the beginning, as in the legacy client.
        if (at > 0) {
            const seek = () => {
                if (Number.isFinite(audio.duration) && audio.duration > 0) {
                    audio.currentTime = Math.min(at, audio.duration - 0.25);
                }
                audio.removeEventListener("loadedmetadata", seek);
            };
            audio.addEventListener("loadedmetadata", seek);
        }
        playError.value = null;
    } catch { /* a corrupt snapshot must never block startup */ }
}

// ---------------------------------------------------------------- activity
/**
 * Publish listening state to the linked sinks whose toggles are enabled.
 * The signature de-duplicates repeats and throttles progress to 15s buckets;
 * pausing and changing tracks always produce a new signature.
 */
let lastActivitySignature = "";
async function publishActivity() {
    if (!peekAuth() || (!roturActivity.value && !discordActivity.value)) {
        activityError.value = null;
        return;
    }
    const id = currentId.value;
    const playing = !audio.paused;
    if (!playing && !id) return;
    const signature = `${id}:${playing}:${Math.floor(audio.currentTime / 15)}`;
    if (signature === lastActivitySignature) return;
    lastActivitySignature = signature;

    const body = {
        track_id: id == null ? null : Number(id),
        playing,
        position: Math.floor(audio.currentTime || 0),
    };
    const errors: string[] = [];
    const message = (e: unknown) => e instanceof Error ? e.message : String(e);
    const jobs: Promise<unknown>[] = [];
    if (roturActivity.value) {
        jobs.push(API.roturActivity(body).catch(e => { errors.push(`Rotur: ${message(e)}`); }));
    }
    if (discordActivity.value) {
        jobs.push(API.discordActivity(body).catch(e => { errors.push(`Discord: ${message(e)}`); }));
    }
    // Activity is best effort; a dead Discord client must not break playback.
    await Promise.allSettled(jobs);
    activityError.value = errors.length ? errors.join(" · ") : null;
}

/** Turning a sink off clears any presence it may have left on the server. */
let wasRoturActivity = roturActivity.value;
effect(() => {
    const on = roturActivity.value;
    if (wasRoturActivity && !on) {
        void API.roturActivity({
            track_id: currentId.peek() == null ? null : Number(currentId.peek()),
            playing: false,
            position: Math.floor(audio.currentTime || 0),
        }).catch(() => { /* best effort */ });
    }
    wasRoturActivity = on;
});

audio.addEventListener("play", () => {
    isPlaying.value = true;
    void publishActivity();
    saveSnapshot(true);
    emitPlaybackChange();
});
audio.addEventListener("pause", () => {
    isPlaying.value = false;
    void publishActivity();
    saveSnapshot(true);
    emitPlaybackChange();
});
audio.addEventListener("ended", () => { void handleEnded(); });
audio.addEventListener("error", () => {
    isPlaying.value = false;
    playError.value = "Couldn't play this track.";
});
audio.addEventListener("timeupdate", () => {
    position.value = audio.currentTime;
    void publishActivity();
    saveSnapshot();
});
audio.addEventListener("loadedmetadata", () => { duration.value = audio.duration || 0; });

// Safari refuses a zero-volume autoplay, so clamp to a whisper, not silence.
effect(() => { audio.volume = Math.max(0.001, Math.min(1, volume.value)); });

window.addEventListener("pagehide", () => {
    saveSnapshot(true);
    if (roturActivity.value && !audio.paused) {
        // keepalive: the page is going away, but a stale Rotur presence would
        // otherwise outlive the tab that was actually playing.
        try {
            void fetch("/api/auth/rotur/activity", {
                method: "POST",
                credentials: "same-origin",
                headers: { "content-type": "application/json" },
                body: JSON.stringify({ playing: false }),
                keepalive: true,
            }).catch(() => {});
        } catch { /* best effort during unload */ }
    }
});
document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") saveSnapshot(true);
});

// Count a replay in a new listening session, but not every double-click.
const lastPlayReport = new Map<string, number>();

export function playTrack(id: string, meta?: Omit<NowPlaying, "id"> & { setUuid?: string; artistUuid?: string }) {
    if (currentId.value !== id) {
        currentId.value = id;
        playError.value = null;
        audio.src = API.streamUrl(id);
    }
    if (meta) {
        nowPlaying.value = { id, ...meta };
        if (meta.liked != null) currentLiked.value = !!meta.liked;
    }
    void audio.play()
        .then(() => { void publishActivity(); })
        .catch(() => {
            isPlaying.value = false;
            playError.value = "Couldn't start playback. Try again.";
        });

    const now = Date.now();
    if (now - (lastPlayReport.get(id) ?? 0) > 60_000) {
        lastPlayReport.set(id, now);
        void fetch("/api/plays", {
            method: "POST",
            credentials: "same-origin",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ track_id: Number(id) }),
        }).catch(() => { /* play counts are best effort */ });
    }
    saveSnapshot(true);
}

function setQueue(list: QueueItem[], index?: number) {
    queue.value = list;
    if (index !== undefined) queueIndex.value = index;
    saveSnapshot(true);
    emitPlaybackChange();
}
function setQueueIndex(index: number) {
    queueIndex.value = index;
    saveSnapshot(true);
    emitPlaybackChange();
}

export function playQueue(list: QueueItem[], startIndex = 0) {
    if (list.length === 0) return;
    const index = Math.max(0, Math.min(startIndex, list.length - 1));
    setQueue(list, index);
    const cur = list[index];
    playTrack(cur.id, { title: cur.title, artist: cur.artist, setUuid: cur.setUuid, artistUuid: cur.artistUuid });
}

/** Append a track to the current queue without interrupting playback. */
export function enqueueTrack(id: string, meta?: Omit<NowPlaying, "id"> & { setUuid?: string; artistUuid?: string }) {
    setQueue([...queue.value, {
        id,
        title: meta?.title ?? id,
        artist: meta?.artist ?? "",
        setUuid: meta?.setUuid,
        artistUuid: meta?.artistUuid,
    }]);
}

/** Remove one queue occurrence (used by chat `remove` commands). */
export function removeQueueIndex(index: number) {
    const q = queue.value;
    if (!Number.isInteger(index) || index < 0 || index >= q.length) return;
    if (index < queueIndex.value) queueIndex.value -= 1;
    setQueue(q.filter((_, i) => i !== index));
}

export function playQueueIndex(index: number) {
    if (index < 0 || index >= queue.value.length) return;
    setQueueIndex(index);
    const cur = queue.value[index];
    playTrack(cur.id, { title: cur.title, artist: cur.artist, setUuid: cur.setUuid, artistUuid: cur.artistUuid });
}

export function playNext(opts?: { allowWrap?: boolean }) {
    const q = queue.value;
    if (q.length === 0) return;
    if (shuffleEnabled.value && !modelShuffle.value && q.length > 1) {
        let nextIdx = queueIndex.value;
        while (nextIdx === queueIndex.value) {
            nextIdx = Math.floor(Math.random() * q.length);
        }
        playQueueIndex(nextIdx);
        return;
    }
    const next = queueIndex.value + 1;
    if (next < q.length) {
        playQueueIndex(next);
        return;
    }
    // Manual Next intentionally stops here: only natural `ended` may call radio.
    if (repeatMode.value === "all" || opts?.allowWrap) playQueueIndex(0);
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

function trackFromRadio(t: { uuid: string; name: { value: string }; artists?: { value: string[] }; set?: string | null }): QueueItem {
    const names = (t.artists?.value ?? []).map(u => {
        const parts = String(u).split(":");
        try { return decodeURIComponent(parts.slice(2).join(":")); }
        catch { return parts.slice(2).join(":") || ""; }
    });
    return {
        id: String(t.uuid),
        title: t.name.value,
        artist: names.join(", "),
        setUuid: t.set ?? undefined,
        artistUuid: t.artists?.value?.[0],
    };
}

let radioBusy = false;
/** Append up to five unseen radio tracks and play the first new one. */
async function autoplayRadio(seed: QueueItem) {
    if (radioBusy) return;
    radioBusy = true;
    try {
        const tracks = await API.radio(seed.id);
        const have = new Set(queue.value.map(t => t.id));
        const add: QueueItem[] = [];
        for (const t of tracks) {
            const item = trackFromRadio(t);
            if (!item.id || have.has(item.id)) continue;
            have.add(item.id);
            add.push(item);
            if (add.length === 5) break;
        }
        if (!add.length) {
            setQueueIndex(-1);
            return;
        }
        const firstNew = queue.value.length;
        setQueue([...queue.value, ...add]);
        playQueueIndex(firstNew);
    } catch {
        setQueueIndex(-1);
    } finally {
        radioBusy = false;
    }
}

async function handleEnded() {
    isPlaying.value = false;
    void publishActivity();
    const q = queue.value;
    const idx = queueIndex.value;
    if (q.length === 0 || idx < 0) {
        saveSnapshot(true);
        return;
    }
    if (repeatMode.value === "one") {
        audio.currentTime = 0;
        void audio.play().catch(() => { isPlaying.value = false; });
        saveSnapshot(true);
        return;
    }
    if (idx + 1 < q.length) {
        playQueueIndex(idx + 1);
        return;
    }
    if (repeatMode.value === "all") {
        playQueueIndex(0);
        return;
    }
    // Only now — at the actual end — may radio extend the queue.
    if (autoplay.value) {
        await autoplayRadio(q[idx]);
        return;
    }
    setQueueIndex(-1);
}

/** Start a radio around one track from a track menu; no queue is required. */
export async function startRadio(id: string, meta?: Omit<NowPlaying, "id">) {
    try {
        const tracks = await API.radio(id);
        const seed: QueueItem = {
            id,
            title: meta?.title ?? id,
            artist: meta?.artist ?? "",
            setUuid: meta?.setUuid,
            artistUuid: meta?.artistUuid,
        };
        const list = [seed, ...tracks.map(trackFromRadio)];
        playQueue(list, 0);
    } catch { /* the caller can report the failure */ }
}

export function toggleTrack(id: string, meta?: Omit<NowPlaying, "id">) {
    if (currentId.value === id) {
        if (audio.paused) void audio.play().catch(() => {});
        else audio.pause();
        return;
    }
    playTrack(id, meta);
}

export function togglePlay() {
    if (!currentId.value) return;
    if (audio.paused) void audio.play().catch(() => {});
    else audio.pause();
}

export function seekTo(seconds: number) {
    if (Number.isFinite(seconds)) {
        audio.currentTime = Math.max(0, seconds);
        saveSnapshot();
        emitPlaybackChange();
    }
}

export function setVolume(value: number) {
    volume.value = Math.min(1, Math.max(0, value));
}

export function toggleMute() {
    audio.muted = !audio.muted;
}

/** Toggle the current track's like. Optimistic, with rollback on failure;
 *  offline likes are queued by the API layer and the optimistic value stays. */
export async function toggleCurrentLike() {
    const id = currentId.value;
    if (!id) return;
    const before = currentLiked.value;
    currentLiked.value = !before;
    try {
        const r = await API.like(id);
        if (r.liked != null) currentLiked.value = !!r.liked;
    } catch {
        currentLiked.value = before;
    }
}

/**
 * Turn shuffle on with the server's MDL order when it has earned the right to
 * choose. Until then (and whenever the call fails) the existing random order
 * is the fallback, so the button behaves exactly as before.
 */
export async function setShuffle(on: boolean) {
    shuffleEnabled.value = on;
    if (!on) {
        modelShuffle.value = false;
        saveSnapshot(true);
        return;
    }
    const q = queue.value.slice();
    const current = currentId.value;
    if (q.length > 1 && current) {
        try {
            const orderedIds = await API.modelRank(current, q.map(item => item.id));
            if (orderedIds.length > 1 && shuffleEnabled.value && currentId.value === current) {
                const byId = new Map(q.map(item => [item.id, item]));
                const ranked = orderedIds.map(id => byId.get(id)).filter((x): x is QueueItem => !!x);
                const seen = new Set(ranked.map(item => item.id));
                const ordered = [...ranked, ...q.filter(item => !seen.has(item.id))];
                const index = Math.max(0, ordered.findIndex(item => item.id === current));
                setQueue(ordered, index);
                modelShuffle.value = true;
                saveSnapshot(true);
                return;
            }
        } catch { /* offline or server error: random shuffle still works */ }
    }
    modelShuffle.value = false;
    saveSnapshot(true);
}

function applyRepeat(mode: RepeatMode) {
    repeatMode.value = mode;
    saveSnapshot(true);
}

export function setRepeatMode(mode: RepeatMode) {
    applyRepeat(mode);
    if (mode !== "off") setAutoplay(false);
}

/** Any repeat mode on switches autoplay off; autoplay on switches repeat off. */
export function setAutoplay(on: boolean) {
    setAutoplayPreference(on);
    if (on) applyRepeat("off");
    else saveSnapshot(true);
    void publishActivity();
}

export function cycleRepeat(): RepeatMode {
    const order: RepeatMode[] = ["off", "all", "one"];
    const i = order.indexOf(repeatMode.value);
    const next = order[(i + 1) % order.length];
    setRepeatMode(next);
    return next;
}

/** Snapshot used by the playback-presence/device sync layer. */
export function playbackSnapshot() {
    return {
        trackId: currentId.value,
        position: audio.currentTime || 0,
        duration: audio.duration || duration.value || 0,
        playing: !audio.paused,
        upcoming: queue.value.slice(queueIndex.value + 1).map(t => t.id),
    };
}

export function formatTime(seconds: number): string {
    if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${String(s).padStart(2, "0")}`;
}

restoreSnapshot();
restoring = false;
lastSave = Date.now();
