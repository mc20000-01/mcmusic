/* ==========================================================================
   mcmusic — API client
   Session-cookie auth only. No tokens in storage, no Authorization header
   from the browser; bots authenticate server-side with their own credential.
   ========================================================================== */

import * as cache from "./cache.js";

export class ApiError extends Error {
  constructor(message, status, json) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.json = json || {};
  }
}

let base = "/api";

export function setBase(path) {
  base = String(path).replace(/\/$/, "");
}

function emit(name, detail) {
  try {
    window.dispatchEvent(new CustomEvent(name, { detail }));
  } catch (e) { /* ignore */ }
}

async function once(path, method, body, opts) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const res = await fetch(`${base}/${path}`, {
    method,
    headers,
    credentials: "same-origin",
    body: body === undefined ? undefined : JSON.stringify(body),
    ...opts,
  });

  const limit = res.headers.get("X-RateLimit-Limit");
  if (limit) {
    emit("mc:ratelimit", {
      limit,
      remaining: res.headers.get("X-RateLimit-Remaining"),
      reset: res.headers.get("X-RateLimit-Reset"),
    });
  }

  let json = {};
  const type = res.headers.get("Content-Type") || "";
  if (type.includes("json")) {
    try {
      json = await res.json();
    } catch (e) {
      json = {};
    }
  } else {
    const text = await res.text().catch(() => "");
    if (text) json = { error: text.slice(0, 200) };
  }

  if (!res.ok) throw new ApiError(json.error || `HTTP ${res.status}`, res.status, json);
  return json;
}

/**
 * Perform an API call. GETs fall back to the offline cache when the network
 * is gone, so a cached library still renders without a connection; the few
 * replay-safe writes are queued instead of failing (see flushOutbox).
 */
export async function api(path, method = "GET", body = undefined, opts = {}) {
  const m = String(method).toUpperCase();
  try {
    return await once(path, m, body, opts);
  } catch (e) {
    const offline = (typeof navigator !== "undefined" && navigator.onLine === false) ||
      e.name === "TypeError";
    if (m === "GET" && offline && "caches" in window) {
      const url = new URL(`${base}/${path}`, location.origin);
      const hit = await caches.match(url.toString()).catch(() => null);
      if (hit) {
        emit("mc:cachehit", { path });
        return hit.json();
      }
    }
    if (m !== "GET" && offline && replayable(m, path)) {
      await enqueue(path, m, body);
      return { queued: true, offline: true };
    }
    if (offline) emit("mc:offline", { path });
    throw e;
  }
}

/* ── offline writes ──────────────────────────────────────────────────────── */
/* Only replay-safe mutations are queued. Adding a track to a playlist is keyed
   on (playlist_id, track_id) so a repeat is a no-op; renames and deletes set an
   absolute state rather than adding to one, so replaying them converges; and a
   like made with no network never reached the server, so replaying it restores
   the state the listener asked for. Anything else fails loudly rather than
   quietly duplicating on the server. */
const REPLAYABLE = [
  // A like is a toggle on the server, so two offline taps are two writes. They
  // must not be collapsed by the de-duplication below, or replaying them flips
  // the state once and leaves the server opposite to what the listener saw.
  { method: "POST", path: /^like\/\d+$/, toggle: true },
  { method: "POST", path: /^playlists\/\d+\/tracks$/ },
  { method: "PATCH", path: /^playlists\/\d+$/ },
  { method: "DELETE", path: /^playlists\/\d+$/ },
  { method: "DELETE", path: /^playlists\/\d+\/tracks\/\d+$/ },
];

function rule(method, path) {
  return REPLAYABLE.find((r) => r.method === method && r.path.test(path)) || null;
}

function replayable(method, path) {
  return !!rule(method, path);
}

async function queued() {
  const list = await cache.get(cache.K.outbox, []);
  return Array.isArray(list) ? list : [];
}

/** How many writes are still waiting for the network. */
export async function pendingWrites() {
  return (await queued()).length;
}

async function enqueue(path, method, body) {
  const same = (a, b) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
  // Repeated toggles are meaningful, so only non-toggle writes are de-duplicated.
  const keepAll = !!rule(method, path)?.toggle;
  const items = (await queued()).filter(
    (e) => keepAll || !(e.method === method && e.path === path && same(e.body, body))
  );
  items.push({ path, method, ...(body === undefined ? {} : { body }), at: Date.now() });
  const kept = items.slice(-100);
  await cache.set(cache.K.outbox, kept);
  emit("mc:queued", { path, method, pending: kept.length });
}

/**
 * Replay queued writes oldest-first. A network failure stops the run so later
 * edits keep their order; a response the server will always reject is dropped
 * and reported instead of blocking the queue forever.
 */
async function runFlush() {
  if (typeof navigator !== "undefined" && navigator.onLine === false) return 0;
  let sent = 0;
  let list = await queued();
  while (list.length) {
    const item = list[0];
    try {
      await once(item.path, item.method, item.body);
      sent += 1;
    } catch (e) {
      // A delete that finds the playlist or track already gone has reached
      // the state the listener wanted, so it is done, not failed.
      const gone = item.method === "DELETE" && e instanceof ApiError &&
        (e.status === 404 || e.status === 410);
      const permanent = e instanceof ApiError &&
        e.status >= 400 && e.status < 500 && e.status !== 429;
      if (!gone && !permanent) break;
      if (!gone) emit("mc:syncfail", { path: item.path, error: e.message });
    }
    list = list.slice(1);
    await cache.set(cache.K.outbox, list);
  }
  if (sent) emit("mc:synced", { count: sent, pending: (await queued()).length });
  return sent;
}

let inFlight = null;

/**
 * Replay the queue, joining a run that is already under way instead of
 * reporting nothing to sync. Callers share the same promise, so a second
 * caller (the reconnect listener and the Settings button, say) sees the count
 * the run actually sent.
 */
export function flushOutbox() {
  if (inFlight) return inFlight;
  inFlight = runFlush().finally(() => { inFlight = null; });
  return inFlight;
}

if (typeof window !== "undefined") {
  const kick = () => { flushOutbox().catch(() => {}); };
  window.addEventListener("online", kick);
  window.addEventListener("load", kick);
}

export const get = (p, opts) => api(p, "GET", undefined, opts);
export const post = (p, body, opts) => api(p, "POST", body, opts);
export const put = (p, body, opts) => api(p, "PUT", body, opts);
export const patch = (p, body, opts) => api(p, "PATCH", body, opts);
export const remove = (p, opts) => api(p, "DELETE", undefined, opts);

/** Binary fetch used for prefetching audio into the media cache. */
export async function raw(url, opts = {}) {
  return fetch(url, { credentials: "same-origin", ...opts });
}

export function streamUrlFor(id) {
  return `${base}/tracks/${id}/stream`;
}

export function coverUrlFor(id) {
  return `${base}/tracks/${id}/cover`;
}
