/* ==========================================================================
   mcmusic — offline cache manager
   IndexedDB holds structured state (settings, last queue, track metadata);
   CacheStorage holds audio files and artwork so playback survives offline.
   The service worker reads the same media cache, so a prewarmed track plays
   with no network at all.
   ========================================================================== */

const DB_NAME = "mcmusic";
const DB_VERSION = 1;
const STORE = "kv";
const MEDIA = "mcmusic-media-v1";

let dbp = null;

function openDB() {
  if (dbp) return dbp;
  dbp = new Promise((resolve, reject) => {
    if (!("indexedDB" in window)) return reject(new Error("no indexedDB"));
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE);
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  }).catch((e) => {
    console.warn("cache: indexedDB unavailable", e);
    return null;
  });
  return dbp;
}

async function idb(mode, fn) {
  const db = await openDB();
  if (!db) return null;
  return new Promise((resolve) => {
    let tx;
    try {
      tx = db.transaction(STORE, mode);
    } catch (e) {
      resolve(null);
      return;
    }
    const store = tx.objectStore(STORE);
    let out = null;
    try {
      out = fn(store);
    } catch (e) {
      resolve(null);
      return;
    }
    tx.oncomplete = () => resolve(out && "result" in out ? out.result : out);
    tx.onerror = () => resolve(null);
    tx.onabort = () => resolve(null);
  });
}

export async function get(key, fallback = null) {
  const v = await idb("readonly", (s) => s.get(key));
  return v === undefined || v === null ? fallback : v;
}

export async function set(key, value) {
  return idb("readwrite", (s) => s.put(value, key));
}

export async function del(key) {
  return idb("readwrite", (s) => s.delete(key));
}

/* ── media cache ─────────────────────────────────────────────────────────── */

export async function mediaCache() {
  if (!("caches" in window)) return null;
  try {
    return await caches.open(MEDIA);
  } catch (e) {
    return null;
  }
}

export function streamUrl(trackId) {
  return `/api/tracks/${trackId}/stream`;
}

export function artUrl(trackId) {
  return `/api/tracks/${trackId}/cover`;
}

async function cached(cache, url) {
  try {
    return await cache.match(url);
  } catch (e) {
    return null;
  }
}

/** Cache one URL fully (audio needs a non-Range request to be storable). */
export async function remember(url, { force = false } = {}) {
  const cache = await mediaCache();
  if (!cache) return false;
  if (!force && (await cached(cache, url))) return true;
  try {
    const res = await fetch(url, { credentials: "same-origin", cache: "no-store" });
    if (!res.ok) return false;
    // A 206 partial body cannot be stored; retry the object without a Range.
    if (res.status === 206) return false;
    await cache.put(url, res.clone());
    return true;
  } catch (e) {
    return false;
  }
}

export async function isCached(url) {
  const cache = await mediaCache();
  return !!(cache && (await cached(cache, url)));
}

/** Warm the next few tracks so transitions are gapless and offline-safe. */
export async function prefetch(tracks, { count = 3, art = true } = {}) {
  if (!tracks || !tracks.length) return 0;
  if (navigator.connection?.saveData) return 0;
  let done = 0;
  const slice = tracks.slice(0, count);
  for (const t of slice) {
    if (!t || !t.id) continue;
    try {
      if (await remember(streamUrl(t.id))) done += 1;
      if (art) await remember(artUrl(t.id));
    } catch (e) {
      /* one bad track must not stop the rest */
    }
  }
  return done;
}

export async function clearMedia() {
  try {
    await caches.delete(MEDIA);
    return true;
  } catch (e) {
    return false;
  }
}

export async function stats() {
  const out = { audio: 0, bytes: 0, quota: 0, persisted: false };
  try {
    const cache = await mediaCache();
    if (cache) {
      const keys = await cache.keys();
      out.audio = keys.filter((k) => k.url.includes("/stream")).length;
    }
  } catch (e) { /* ignore */ }
  try {
    if (navigator.storage?.estimate) {
      const est = await navigator.storage.estimate();
      out.bytes = est.usage || 0;
      out.quota = est.quota || 0;
    }
    if (navigator.storage?.persisted) out.persisted = await navigator.storage.persisted();
  } catch (e) { /* ignore */ }
  return out;
}

export async function requestPersistence() {
  try {
    if (navigator.storage?.persist) return await navigator.storage.persist();
  } catch (e) { /* ignore */ }
  return false;
}

/* ── explicit downloads ──────────────────────────────────────────────────── */
/* An entry only counts as downloaded while its audio is still in CacheStorage,
   so a browser eviction or a manual clear drops it from the list instead of
   leaving a dead row behind. */

const DL_KEY = "downloads:index";

async function readIndex() {
  const v = await get(DL_KEY, []);
  return Array.isArray(v) ? v : [];
}

async function writeIndex(list) {
  return set(DL_KEY, list);
}

export async function downloadTrack(t) {
  if (!t || !t.id) return false;
  const cache = await mediaCache();
  if (!cache) return false;
  const ok = await remember(streamUrl(t.id));
  if (!ok) return false;
  await remember(artUrl(t.id));

  let bytes = 0;
  try {
    const res = await cache.match(streamUrl(t.id));
    if (res) bytes = (await res.clone().blob()).size;
  } catch (e) {
    /* the size is cosmetic; keep the download */
  }

  const list = (await readIndex()).filter((d) => d.id !== t.id);
  list.unshift({
    id: t.id,
    title: t.title || "Unknown",
    artist: t.artist || "",
    album: t.album || "",
    duration: Number(t.duration) || 0,
    bytes,
    added: Math.floor(Date.now() / 1000),
  });
  await writeIndex(list);
  return true;
}

export async function downloadMany(tracks, onProgress) {
  let done = 0;
  for (const t of tracks || []) {
    if (!t || !t.id) continue;
    if (await downloadTrack(t)) done += 1;
    if (onProgress) onProgress(done, tracks.length);
  }
  return done;
}

export async function removeDownload(id) {
  const cache = await mediaCache();
  if (cache) {
    for (const url of [streamUrl(id), artUrl(id)]) {
      try {
        await cache.delete(url);
      } catch (e) {
        /* keep going: the index is what the UI reads */
      }
    }
  }
  await writeIndex((await readIndex()).filter((d) => d.id !== id));
  return true;
}

export async function listDownloads() {
  const listed = await readIndex();
  const cache = await mediaCache();
  if (!cache) return [];
  const out = [];
  for (const d of listed) {
    if (await cached(cache, streamUrl(d.id))) out.push(d);
  }
  return out;
}

export async function isDownloaded(id) {
  return (await readIndex()).some((d) => d.id === id);
}

export async function clearDownloads() {
  const listed = await readIndex();
  for (const d of listed) await removeDownload(d.id);
  await writeIndex([]);
  return listed.length;
}

/* ── convenience keys ────────────────────────────────────────────────────── */
export const K = {
  settings: "settings",
  player: "player:state",
  user: "user",
  meta: "library:meta",
  build: "app:build",
  outbox: "outbox",

};
