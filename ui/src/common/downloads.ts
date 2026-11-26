/** Offline downloads for the web client.
 *
 * Audio blobs live in CacheStorage so MediaElement Range requests can reuse
 * them; the small index of what the user chose lives in IndexedDB. Downloading
 * a track records its id, keeps the streamed bytes under a stable URL, and
 * points playback at that URL while offline.
 */
import { signal } from "@preact/signals";
import * as idb from "./idb";
import { API } from "./net/api";

const INDEX_KEY = "downloads:index";
const STORE = "session";

export type DownloadEntry = {
    id: string;
    title: string;
    artist: string;
    at: number;
    bytes: number;
};

export const downloads = signal<DownloadEntry[]>([]);
export const downloadBusy = signal<string | null>(null);

export async function loadDownloads() {
    try {
        const v = await idb.get<DownloadEntry[]>(INDEX_KEY, STORE);
        downloads.value = Array.isArray(v) ? v : [];
    } catch {
        downloads.value = [];
    }
}

async function persist() {
    await idb.set(INDEX_KEY, downloads.value, STORE);
}

/** Cache URL used for offline audio. The service worker passes Range requests
 *  to its media cache; this key keeps our entries separate from artwork. */
export function offlineUrl(id: string): string {
    return `/api/tracks/${id}/stream`;
}

export async function isCached(id: string): Promise<boolean> {
    if (typeof caches === "undefined") return false;
    const hit = await caches.match(offlineUrl(id)).catch(() => undefined);
    return !!hit;
}

/** Fill the browse cache without adding a track to the Downloads list. Used
 *  when "Keep audio offline" is on: anything you browse stays playable. */
export async function cacheForBrowse(id: string): Promise<void> {
    if (typeof caches === "undefined" || await isCached(id)) return;
    const res = await fetch(API.streamUrl(id), { credentials: "same-origin" });
    if (!res.ok) throw new Error(`cache failed (HTTP ${res.status})`);
    const blob = await res.blob();
    const cache = await caches.open("mcmusic-media-v1");
    await cache.put(offlineUrl(id), new Response(blob, {
        headers: {
            "content-type": res.headers.get("content-type") || "audio/mpeg",
            "accept-ranges": "bytes",
            "content-length": String(blob.size),
        },
    }));
}

export async function downloadTrack(id: string, title: string, artist: string): Promise<void> {
    downloadBusy.value = id;
    try {
        const res = await fetch(API.streamUrl(id), { credentials: "same-origin" });
        if (!res.ok) throw new Error(`download failed (HTTP ${res.status})`);
        const blob = await res.blob();
        if (typeof caches !== "undefined") {
            const cache = await caches.open("mcmusic-media-v1");
            await cache.put(offlineUrl(id), new Response(blob, {
                headers: {
                    "content-type": res.headers.get("content-type") || "audio/mpeg",
                    "accept-ranges": "bytes",
                    "content-length": String(blob.size),
                },
            }));
        }
        const rest = downloads.value.filter(d => d.id !== id);
        downloads.value = [{ id, title, artist, at: Date.now(), bytes: blob.size }, ...rest];
        await persist();
    } finally {
        downloadBusy.value = null;
    }
}

export async function removeDownload(id: string): Promise<void> {
    downloads.value = downloads.value.filter(d => d.id !== id);
    await persist();
    if (typeof caches !== "undefined") {
        const cache = await caches.open("mcmusic-media-v1").catch(() => null);
        await cache?.delete(offlineUrl(id)).catch(() => false);
    }
}

export async function clearDownloads(): Promise<void> {
    for (const d of downloads.value) {
        if (typeof caches !== "undefined") {
            const cache = await caches.open("mcmusic-media-v1").catch(() => null);
            await cache?.delete(offlineUrl(d.id)).catch(() => false);
        }
    }
    downloads.value = [];
    await persist();
}

export function downloadStats() {
    const bytes = downloads.value.reduce((n, d) => n + d.bytes, 0);
    return { count: downloads.value.length, bytes };
}

void loadDownloads();
