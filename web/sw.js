/* ==========================================================================
   mcmusic service worker
   · app shell: network-first, cached fallback (updates never break offline)
   · read-only API GETs: revalidated in the background; a cached body is
     served once the network has been given a short grace period
   · audio + artwork: served from the media cache, including Range requests
   · the shell cache is versioned; bumping it also drops the API cache, so stale
     JSON shapes never outlive the app that wrote them; media survives updates
   ========================================================================== */

const SHELL = "mcmusic-shell-v10";
const API = "mcmusic-api-v2";
const MEDIA = "mcmusic-media-v1";
const MEDIA_MAX = 400;                        // tracks + artwork kept offline
const MEDIA_INDEX = "/__mcmusic_media_index"; // eviction order; never fetched
const API_SWR_MS = 900;                       // grace period for a cached API body

const ASSETS = [
  "/",
  "/manifest.webmanifest",
  "/icon.svg",
  "/icon-192.png",
  "/icon-512.png",
  "/static/css/variables.css",
  "/static/css/base.css",
  "/static/css/layout.css",
  "/static/css/components.css",
  "/static/css/theme.css",
  "/static/css/mobile.css",
  "/static/css/link.css",
  "/static/js/app.js",
  "/static/js/api.js",
  "/static/js/auth.js",
  "/static/js/cache.js",
  "/static/js/icons.js",
  "/static/js/mobile.js",
  "/static/js/player.js",
  "/static/js/rotur.js",
  "/static/js/ui.js",
  "/static/js/views.js",
];

/* API responses that are safe to serve stale when offline. */
const API_CACHEABLE = [
  /^\/api\/(tracks|search|albums|album|artists|artist|home|likes|playlists|settings)(\?|$)/,
  /^\/api\/playlists\/\d+$/,
];

const FORBIDDEN_API = /^\/api\/(playback|queue|me|version|channels|bot)/;

function offlineJson() {
  return new Response(JSON.stringify({ error: "offline" }), {
    status: 503,
    headers: { "Content-Type": "application/json" },
  });
}

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(SHELL);
    await Promise.all(
      ASSETS.map((url) =>
        cache.add(new Request(url, { cache: "reload" })).catch(() => null)
      )
    );
    // Never skipWaiting automatically: an update must not interrupt playback.
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys
        .filter(
          (k) =>
            (k.startsWith("mcmusic-shell-") && k !== SHELL) ||
            (k.startsWith("mcmusic-api-") && k !== API)
        )
        .map((k) => caches.delete(k))
    );
    await self.clients.claim();
  })());
});

self.addEventListener("message", (event) => {
  const data = event.data || {};
  if (data.type === "SKIP_WAITING") {
    self.skipWaiting();
  } else if (data.type === "CACHE_URLS" && Array.isArray(data.urls)) {
    event.waitUntil((async () => {
      const cache = await caches.open(MEDIA);
      await Promise.all(
        data.urls.slice(0, 12).map(async (url) => {
          if (await cache.match(url)) return;
          try {
            const res = await fetch(url, { credentials: "same-origin" });
            if (res.ok && res.status === 200) {
              await cache.put(url, res.clone());
              await rememberMedia(cache, url);
            }
          } catch (e) { /* ignore */ }
        })
      );
    })());
  } else if (data.type === "CLEAR_MEDIA") {
    event.waitUntil(caches.delete(MEDIA));
  }
});

/* ── media cache budget ─────────────────────────────────────────────────── */
/* Quota is finite and a cached track is several MB, so keep the cache bounded.
   Insertion order lives inside the cache itself, which means the limit survives
   worker restarts without a second store to keep in sync. */
async function rememberMedia(cache, url) {
  const key = new URL(url, self.registration.scope).href;
  let order = [];
  try {
    const index = await cache.match(MEDIA_INDEX);
    if (index) order = await index.json();
  } catch (e) { order = []; }
  if (!Array.isArray(order)) order = [];

  order = order.filter((u) => u !== key);
  order.push(key);

  const drop = order.slice(0, Math.max(0, order.length - MEDIA_MAX));
  if (drop.length) await Promise.all(drop.map((u) => cache.delete(u)));

  await cache.put(MEDIA_INDEX, new Response(JSON.stringify(order.slice(-MEDIA_MAX)), {
    headers: { "Content-Type": "application/json" },
  }));
}

/* ── audio: Range-aware cache ───────────────────────────────────────────── */
async function audioResponse(request) {
  const cache = await caches.open(MEDIA);
  let cached = await cache.match(request.url);
  if (!cached) {
    // A fresh full response can be stored; partial responses cannot.
    const res = await fetch(request);
    if (res.status === 200) {
      await cache.put(request.url, res.clone()).catch(() => {});
      await rememberMedia(cache, request.url);
    }
    return res;
  }

  const range = request.headers.get("range");
  if (!range) {
    const body = await cached.arrayBuffer();
    return new Response(body, {
      status: 200,
      headers: {
        "Content-Type": cached.headers.get("Content-Type") || "audio/mpeg",
        "Content-Length": String(body.byteLength),
        "Accept-Ranges": "bytes",
        "Cache-Control": "private, max-age=86400",
      },
    });
  }

  const buf = await cached.arrayBuffer();
  const size = buf.byteLength;
  const m = /bytes=(\d*)-(\d*)/.exec(range);
  let start = m && m[1] ? parseInt(m[1], 10) : 0;
  let end = m && m[2] ? parseInt(m[2], 10) : size - 1;
  if (!isFinite(start) || start < 0) start = 0;
  if (!isFinite(end) || end >= size) end = size - 1;
  if (start > end) {
    return new Response(null, {
      status: 416,
      headers: { "Content-Range": `bytes */${size}` },
    });
  }

  const slice = buf.slice(start, end + 1);
  return new Response(slice, {
    status: 206,
    statusText: "Partial Content",
    headers: {
      "Content-Type": cached.headers.get("Content-Type") || "audio/mpeg",
      "Content-Range": `bytes ${start}-${end}/${size}`,
      "Content-Length": String(slice.byteLength),
      "Accept-Ranges": "bytes",
      "Cache-Control": "private, max-age=86400",
    },
  });
}

/* ── fetch routing ──────────────────────────────────────────────────────── */
self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // audio
  if (/^\/api\/tracks\/\d+\/stream$/.test(url.pathname)) {
    event.respondWith(
      audioResponse(req).catch(() =>
        new Response("", { status: 503, statusText: "offline" })
      )
    );
    return;
  }

  // artwork — cache first, then network
  if (/^\/api\/tracks\/\d+\/cover$/.test(url.pathname)) {
    event.respondWith((async () => {
      const cache = await caches.open(MEDIA);
      const hit = await cache.match(req.url);
      if (hit) return hit;
      try {
        const res = await fetch(req);
        if (res.ok) {
          cache.put(req.url, res.clone()).catch(() => {});
          rememberMedia(cache, req.url).catch(() => {});
        }
        return res;
      } catch (e) {
        return new Response("", { status: 404 });
      }
    })());
    return;
  }

  // API
  if (url.pathname.startsWith("/api/")) {
    if (FORBIDDEN_API.test(url.pathname)) return;
    const cacheable = API_CACHEABLE.some((re) => re.test(url.pathname + url.search));
    if (!cacheable) return;

    event.respondWith((async () => {
      const cache = await caches.open(API);
      const hit = await cache.match(req);
      const network = fetch(req).then((res) => {
        if (res.ok) cache.put(req, res.clone()).catch(() => {});
        return res;
      });

      // Even when the cached body wins the race below, the revalidation must
      // be allowed to finish and refresh the cache for the next navigation.
      event.waitUntil(network.catch(() => null));

      if (!hit) {
        try {
          return await network;
        } catch (e) {
          return offlineJson();
        }
      }

      // Fresh wins when the server answers promptly; a slow or offline server
      // never blocks a cached library view from rendering.
      const fresh = await Promise.race([
        network.catch(() => null),
        new Promise((resolve) => setTimeout(() => resolve(null), API_SWR_MS)),
      ]);
      return fresh || hit;
    })());
    return;
  }

  // navigations
  if (req.mode === "navigate") {
    event.respondWith((async () => {
      try {
        const res = await fetch(req);
        // Never let an error page or a login redirect become the offline shell.
        if (res.ok && !res.redirected) {
          const cache = await caches.open(SHELL);
          cache.put("/", res.clone()).catch(() => {});
        }
        return res;
      } catch (e) {
        const cache = await caches.open(SHELL);
        const hit = (await cache.match("/")) || (await cache.match(req));
        return hit || new Response("offline", { status: 503 });
      }
    })());
    return;
  }

  // static assets: network first, cached copy when the server is asleep.
  // Cache-first felt faster but hid deploys behind one stale load, and a
  // deploy you can't see is a deploy you don't trust.
  if (url.pathname.startsWith("/static/") || url.pathname === "/manifest.webmanifest") {
    event.respondWith((async () => {
      const cache = await caches.open(SHELL);
      try {
        const res = await fetch(req);
        if (res.ok) {
          cache.put(req, res.clone()).catch(() => {});
          return res;
        }
        throw new Error(`status ${res.status}`);
      } catch (e) {
        const hit = (await cache.match(req)) || (await cache.match(req, { ignoreSearch: true }));
        return hit || new Response("", { status: 404 });
      }
    })());
  }
});
