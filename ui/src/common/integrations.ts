/** Background integrations booted once from the app shell:
 *  - service worker registration, install prompt and update-ready reload;
 *  - device heartbeat + playback presence publishing;
 *  - remote command polling from /api/playback.
 */
import { signal } from "@preact/signals";
import { API, trackFromJson, albumUuid } from "./net/api";
import {
    enqueueTrack, isPlaying, playNext, playPrev, playQueue, playbackSnapshot,
    removeQueueIndex, seekTo, togglePlay,
} from "./player";
import { peekAuth } from "./auth";

export const pwaUpdateReady = signal(false);
export const pwaInstallAvailable = signal(false);

let deferredInstall: (Event & { prompt?: () => Promise<void> }) | null = null;
export async function installPwa() {
    if (!deferredInstall?.prompt) return;
    await deferredInstall.prompt();
    deferredInstall = null;
    pwaInstallAvailable.value = false;
}

// ---------------------------------------------------------------- service worker
export function bootPwa() {
    if (typeof navigator === "undefined" || !("serviceWorker" in navigator)) return;

    window.addEventListener("beforeinstallprompt", (e) => {
        e.preventDefault();
        deferredInstall = e as Event & { prompt?: () => Promise<void> };
        pwaInstallAvailable.value = true;
    });
    window.addEventListener("appinstalled", () => {
        deferredInstall = null;
        pwaInstallAvailable.value = false;
    });

    let refreshing = false;
    navigator.serviceWorker.addEventListener("controllerchange", () => {
        if (refreshing) return;
        refreshing = true;
        window.location.reload();
    });

    navigator.serviceWorker.register("/sw.js", { scope: "/" })
        .then(reg => {
            reg.addEventListener("updatefound", () => {
                const installing = reg.installing;
                if (!installing) return;
                installing.addEventListener("statechange", () => {
                    if (installing.state === "installed" && navigator.serviceWorker.controller) {
                        pwaUpdateReady.value = true;
                    }
                });
            });
            // An update that finished while the tab was closed is already waiting.
            if (reg.waiting && navigator.serviceWorker.controller) pwaUpdateReady.value = true;
        })
        .catch(() => { /* offline / unsupported: the app still works online */ });
}

export function activateUpdate() {
    navigator.serviceWorker?.getRegistration().then(reg => reg?.waiting?.postMessage({ type: "SKIP_WAITING" })).catch(() => {});
}

// ---------------------------------------------------------------- playback sync
const DEVICE_KEY = "mcmusic:device";
const NAME_KEY = "mcmusic:deviceName";

function deviceHash(): string {
    try {
        let id = localStorage.getItem(DEVICE_KEY);
        if (!id) {
            id = `web-${Math.random().toString(36).slice(2)}-${Date.now().toString(36)}`;
            localStorage.setItem(DEVICE_KEY, id);
        }
        return id;
    } catch {
        return `web-${Math.random().toString(36).slice(2)}`;
    }
}

function deviceName(): string {
    try {
        const saved = localStorage.getItem(NAME_KEY);
        if (saved) return saved;
    } catch { /* noop */ }
    const ua = navigator.userAgent || "Browser";
    const browser = /Firefox/i.test(ua) ? "Firefox"
        : /Edg\//i.test(ua) ? "Edge"
        : /Chrome/i.test(ua) ? "Chrome"
        : /Safari/i.test(ua) ? "Safari" : "Browser";
    return `${browser} web`;
}

let booted = false;
/** Start heartbeat + command polling once auth is available. */
export function bootPlaybackSync() {
    if (booted) return;
    booted = true;
    const device = deviceHash();
    const name = deviceName();

    function publish() {
        if (!peekAuth()) return;
        const snap = playbackSnapshot();
        const body = {
            device,
            track_id: snap.trackId == null ? null : Number(snap.trackId),
            position: Math.floor(snap.position),
            duration: Math.floor(snap.duration),
            playing: snap.playing,
            queue: snap.upcoming.map(Number),
        };
        void API.playbackPush(body).catch(() => {});
        void API.deviceHeartbeat({
            device_hash: device,
            name,
            track_id: body.track_id,
            position: body.position,
            paused: snap.playing ? 0 : 1,
        }).catch(() => {});
    }

    async function poll() {
        if (!peekAuth()) return;
        try {
            const res = await API.playback(device);
            for (const cmd of res.commands ?? []) {
                try { await applyCommand(cmd.action, cmd.arg ?? {}); } catch { /* one bad command is skipped */ }
            }
        } catch { /* offline: no commands */ }
    }

    // Publish on transport changes and periodically while playing.
    window.addEventListener("mc:playbackchange", publish);
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") { publish(); void poll(); }
    });
    setInterval(() => { if (!document.hidden) publish(); }, 15_000);
    setInterval(() => { if (!document.hidden) void poll(); }, 3_000);
    void poll();
    publish();
}

async function applyCommand(action: string, arg: Record<string, any>) {
    switch (action) {
        case "play":
            if (!isPlaying.value) togglePlay();
            break;
        case "pause":
            if (isPlaying.value) togglePlay();
            break;
        case "toggle":
            togglePlay();
            break;
        case "skip":
        case "next":
            playNext();
            break;
        case "prev":
            playPrev();
            break;
        case "seek":
            if (arg.position != null) seekTo(Number(arg.position));
            break;
        case "remove":
            removeQueueIndex(Number(arg.index));
            break;
        case "enqueue":
        case "play_track": {
            const raw = arg.track;
            let id = String(arg.track_id ?? "");
            if (!id && raw?.id != null) id = String(raw.id);
            if (!id) break;
            const track = raw
                ? trackFromJson(raw, raw.album ? albumUuid(raw.album, raw.id) : null)
                : await API.getTrack(id).catch(() => null);
            const meta = track ? {
                title: track.name.value,
                artist: track.artists.value.join(", "),
                setUuid: track.set ?? undefined,
                artistUuid: track.artists.value[0],
            } : { title: `Track ${id}`, artist: "" };
            if (action === "enqueue") {
                enqueueTrack(id, meta);
            } else {
                // Chat "play" replaces the queue, as in the legacy client.
                playQueue([{ id, ...meta }], 0);
            }
            break;
        }
    }
}
