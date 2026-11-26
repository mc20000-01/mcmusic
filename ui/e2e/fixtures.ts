/** Shared Playwright fixture for the responsive regression suite.
 *
 * Every test gets a fresh page, a signed-in session, a restored "currently
 * playing" track, and fully stubbed API traffic. Nothing here talks to a real
 * mcmusic server, and no cover id is handed to CoverArt: the library stubs are
 * empty and the restored track has a non-numeric id, so artwork is rendered as
 * a local placeholder instead of fetching an image.
 */
import { expect, test as base, type Page, type Route } from "@playwright/test";

const ORIGIN = "http://127.0.0.1:4173";

export const VIEWPORT_WIDTHS = [320, 360, 390, 430, 600, 768, 800, 900, 1024, 1100, 1280, 1366, 1536] as const;
export const VIEWPORT_HEIGHTS = [360, 640, 800] as const;

export const ROUTES = [
    "/",
    "/search",
    "/likes",
    "/artists",
    "/artist/artist%3A%3AE2E%20Artist",
    "/playlists",
    "/playlist/1",
    "/downloads",
    "/listeners",
    "/u/e2e-user",
    "/upload",
    "/set/album%3A%3AE2E%20Album",
    "/settings",
    "/devices",
    "/admin",
    "/auth",
] as const;

const USER = {
    id: 42,
    username: "e2e-user",
    display_name: "E2E User",
    email: "e2e@example.invalid",
    is_admin: true,
    provider: "local",
    rotur_id: null,
    rotur_linked: false,
};

const SETTINGS = {
    volume: 0.8,
    covers: true,
    hide_explicit: false,
    offline_audio: false,
    rotur_activity: false,
    discord_activity: false,
    theme: "",
    accent: "",
    autoplay: false,
};

// Raw server-shaped row: `trackFromJson()` and the playback command handler in
// ui/src/common/net/api.ts both understand this shape.
const NOW_PLAYING_TRACK = {
    id: 4242,
    title: "E2E Track",
    artist: "E2E Artist",
    album: "E2E Album",
    duration: 180,
    track_no: 1,
    year: 2026,
    liked: false,
};

const PLAYBACK_STATE = {
    state: {
        track_id: NOW_PLAYING_TRACK.id,
        position: 12,
        duration: NOW_PLAYING_TRACK.duration,
        playing: false,
        queue: [],
        device: "e2e-web",
        device_name: "E2E Web",
        track: NOW_PLAYING_TRACK,
    },
    commands: [],
};

const ROTUR_STATUS = {
    linked: false,
    configured: true,
    has_tokens: false,
    session_valid: false,
    rotur_id: null,
    rotur_username: null,
    activity: { ready: false, reason: "Rotur account is not linked." },
};

// Safe defaults for endpoints the suite does not care about but that pages do
// read while they render (arrays must be arrays, `ok` must be present).
const SAFE_JSON = {
    ok: true,
    status: "ok",
    total: 0,
    count: 0,
    tracks: [],
    albums: [],
    artists: [],
    sections: [],
    playlists: [],
    requests: [],
    users: [],
    codes: [],
    devices: [],
    tokens: [],
    rooms: [],
    events: [],
    listeners: [],
    by_event: {},
    top_tracks: [],
    state: null,
    commands: [],
};

type PlayerSnapshot = {
    version: 1;
    track: {
        id: string;
        title: string;
        artist: string;
        album: string;
        setUuid?: string;
        artistUuid?: string;
        liked: boolean;
    };
    queue: { id: string; title: string; artist: string; setUuid?: string; artistUuid?: string }[];
    queueIndex: number;
    position: number;
    duration: number;
    repeatMode: "off" | "all" | "one";
    shuffleEnabled: boolean;
    modelShuffle: boolean;
    autoplay: boolean;
    saved: number;
};

// `ui/src/common/player.ts` restores this snapshot at import time, which is
// what makes PlayerBar render without waiting for a playback command. The id
// is deliberately non-numeric so `API.getTrackCoverUrl()` falls back to a
// `placeholder:` sentinel and no cover request is made.
const PLAYER_SNAPSHOT: PlayerSnapshot = {
    version: 1,
    track: {
        id: "e2e-track",
        title: "E2E Track",
        artist: "E2E Artist",
        album: "E2E Album",
        setUuid: "album::E2E%20Album",
        artistUuid: "artist::E2E%20Artist",
        liked: false,
    },
    queue: [{
        id: "e2e-track",
        title: "E2E Track",
        artist: "E2E Artist",
        setUuid: "album::E2E%20Album",
        artistUuid: "artist::E2E%20Artist",
    }],
    queueIndex: 0,
    position: 12,
    duration: 180,
    repeatMode: "off",
    shuffleEnabled: false,
    modelShuffle: false,
    autoplay: false,
    saved: Date.now(),
};

/** One-frame silent WAV so the restored <audio> element never reports an error. */
function silentWav(): Buffer {
    const wav = Buffer.alloc(46);
    wav.write("RIFF", 0);
    wav.writeUInt32LE(38, 4);
    wav.write("WAVE", 8);
    wav.write("fmt ", 12);
    wav.writeUInt32LE(16, 16);
    wav.writeUInt16LE(1, 20); // PCM
    wav.writeUInt16LE(1, 22); // mono
    wav.writeUInt32LE(8000, 24);
    wav.writeUInt32LE(16000, 28);
    wav.writeUInt16LE(2, 32);
    wav.writeUInt16LE(16, 34);
    wav.write("data", 36);
    wav.writeUInt32LE(2, 40);
    wav.writeInt16LE(0, 44);
    return wav;
}

const STREAM_BODY = silentWav();

async function json(route: Route, body: unknown, status = 200) {
    await route.fulfill({
        status,
        contentType: "application/json; charset=utf-8",
        body: JSON.stringify(body),
    });
}

async function installStubs(page: Page) {
    // Registered first, so every more specific stub below overrides it. This
    // also blocks the external avatar host used by the profile page.
    await page.route("**/*", async route => {
        const url = route.request().url();
        if (url.startsWith(ORIGIN) || url.startsWith("data:") || url.startsWith("blob:")) {
            await route.continue();
        } else {
            await route.abort();
        }
    });

    await page.route("**/sw.js", route =>
        route.fulfill({ status: 404, contentType: "text/plain", body: "no service worker in tests" }));

    // Generic library endpoints first; the stream/cover routes below are more
    // specific and therefore take precedence.
    await page.route("**/api/tracks*", route => json(route, { tracks: [], total: 0 }));
    await page.route("**/api/tracks/**/stream", route =>
        route.fulfill({ status: 200, contentType: "audio/wav", body: STREAM_BODY }));
    await page.route("**/api/tracks/**/cover", route =>
        route.fulfill({ status: 404, contentType: "application/json", body: "{}" }));

    await page.route("**/api/albums*", route => json(route, { albums: [], total: 0 }));
    await page.route("**/api/album*", route => json(route, { album: "E2E Album", artist: "E2E Artist", tracks: [] }));
    await page.route("**/api/artists*", route => json(route, { artists: [], total: 0 }));
    await page.route("**/api/artist*", route => json(route, { artist: "E2E Artist", tracks: [] }));

    await page.route("**/api/me", route => json(route, USER));
    await page.route("**/api/settings", route => json(route, SETTINGS));
    await page.route("**/api/home", route => json(route, { sections: [], albums: [] }));
    await page.route("**/api/playback", route => json(route, PLAYBACK_STATE));
    await page.route("**/api/devices/heartbeat", route => json(route, { ok: true }));
    await page.route("**/api/devices/tokens", route => json(route, { tokens: [] }));
    await page.route("**/api/devices**", route => json(route, { devices: [], ok: true }));
    await page.route("**/api/auth/rotur/status", route => json(route, ROTUR_STATUS));
    await page.route("**/api/auth/rotur/authorize**", route =>
        route.fulfill({
            status: 200,
            contentType: "text/html; charset=utf-8",
            body: "<!doctype html><title>OAuth stub</title><h1>oauth stub</h1>",
        }));

    // Last-resort API answer. Must stay JSON: `API.once()` calls `res.json()`.
    await page.route("**/api/**", route => json(route, SAFE_JSON));
}

export const test = base.extend<{ signedInPage: Page }>({
    signedInPage: async ({ page }, use) => {
        await page.addInitScript((snapshot: PlayerSnapshot) => {
            // The production bundle is served under /static/ui/, but preact-iso
            // routes against the origin root. Do this before any app script runs,
            // and only for the app document: OAuth redirects land on a real /api
            // URL and must keep it.
            if (location.pathname !== "/static/ui/" && location.pathname !== "/static/ui") return;
            history.replaceState(null, "", "/");
            try {
                localStorage.setItem("mcmusic:player:v1", JSON.stringify(snapshot));
                localStorage.setItem("mcmusic:lyricsOpen", "false");
            } catch { /* private mode: the app still renders */ }
        }, PLAYER_SNAPSHOT);

        await installStubs(page);
        await use(page);
    },
});

/** Load the built app through /static/ui/, then switch to a client-side route.
 *  The initial history entry is always "/" (see the init script above), so
 *  preact-iso sees the route the production server would give it.
 */
export async function openRoute(page: Page, route: string) {
    await page.goto("/static/ui/", { waitUntil: "domcontentloaded" });
    if (route !== "/") {
        await page.evaluate((target) => {
            history.pushState(null, "", target);
            window.dispatchEvent(new PopStateEvent("popstate"));
        }, route);
    }
    await expect(page.locator("#app > div").first()).toBeVisible();
    await expect(page.locator('main[class^="content-"]')).toBeVisible();
    await page.evaluate(async () => {
        await document.fonts.ready;
        await new Promise<void>(resolve =>
            requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
    });
    // Route data is stubbed and local, but <Loading> still resolves on a microtask.
    await page.waitForTimeout(120);
}

export type LayoutViolation = string;

/** Layout invariants shared by every route/size combination. */
export async function checkLayout(page: Page, label: string) {
    const violations: LayoutViolation[] = await page.evaluate(() => {
        const out: string[] = [];
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const NAME = (el: Element) => {
            const id = el.id ? `#${el.id}` : "";
            const cls = typeof el.className === "string" && el.className
                ? `.${el.className.trim().split(/\s+/).slice(0, 2).join(".")}`
                : "";
            return `${el.tagName.toLowerCase()}${id}${cls}`;
        };
        const hidden = (el: Element, cs: CSSStyleDeclaration, r: DOMRect) =>
            cs.display === "none" || cs.visibility === "hidden" || Number(cs.opacity) === 0 ||
            r.width <= 0 || r.height <= 0;

        if (document.documentElement.scrollWidth > vw + 1) {
            out.push(`document scrollWidth ${document.documentElement.scrollWidth} > innerWidth ${vw}`);
        }

        for (const selector of ["#topbar", "#player-bar", "#left-sidebar", 'main[class^="content-"]']) {
            for (const el of Array.from(document.querySelectorAll(selector))) {
                const cs = getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                if (hidden(el, cs, rect)) continue;
                if (el.scrollWidth > el.clientWidth + 1) {
                    out.push(`${selector} scrollWidth ${el.scrollWidth} > clientWidth ${el.clientWidth}`);
                }
            }
        }

        for (const bar of Array.from(document.querySelectorAll("#topbar, #player-bar"))) {
            const barStyle = getComputedStyle(bar);
            if (barStyle.display === "none" || barStyle.visibility === "hidden") continue;
            for (const el of Array.from(bar.querySelectorAll('button, a, [role="slider"]'))) {
                const cs = getComputedStyle(el);
                const r = el.getBoundingClientRect();
                if (hidden(el, cs, r)) continue;
                const what = `${NAME(bar)} ${NAME(el)}`;

                if (r.left < -1 || r.top < -1 || r.right > vw + 1 || r.bottom > vh + 1) {
                    out.push(`${what} box (${r.left.toFixed(1)},${r.top.toFixed(1)},${r.right.toFixed(1)},${r.bottom.toFixed(1)}) outside ${vw}x${vh}`);
                }

                const cx = r.left + r.width / 2;
                const cy = r.top + r.height / 2;
                if (cx >= 0 && cy >= 0 && cx < vw && cy < vh) {
                    const hit = document.elementFromPoint(cx, cy);
                    if (!hit || !(hit === el || el.contains(hit))) {
                        out.push(`${what} centre obscured by ${hit ? NAME(hit) : "nothing"}`);
                    }
                }

                if (r.width < 44 || r.height < 44) {
                    out.push(`${what} touch target ${r.width.toFixed(1)}x${r.height.toFixed(1)} < 44x44`);
                }
            }
        }

        return out;
    });
    expect(violations, `${label}:\n${violations.join("\n")}`).toEqual([]);
}
