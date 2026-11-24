import { signal } from "@preact/signals";
import type { Option } from "flufi-ui/types";
import type {
    Artist, HomePayload, PlaybackResponse, PublicListening, PublicNow, RoturStatus,
    SearchItem, Set as SetEntity, Track, User,
} from "./types";
import * as idb from "../idb";

const BASE = "/api";

export type ApiJson = Record<string, any>;

function emit(name: string, detail?: unknown) {
    try {
        window.dispatchEvent(new CustomEvent(name, { detail }));
    } catch { /* no window during tests */ }
}

function offline(e: unknown): boolean {
    const message = e instanceof Error ? e.message : String(e);
    return (typeof navigator !== "undefined" && navigator.onLine === false) ||
        e instanceof TypeError ||
        // The service worker answers cacheable GETs with a 503 JSON body while
        // offline; that error must use the same CacheStorage fallback as a
        // genuine network failure.
        message === "offline" || /HTTP 503$/.test(message);
}

async function once(path: string, method: string, body?: unknown): Promise<ApiJson> {
    const res = await fetch(`${BASE}/${path}`, {
        method,
        credentials: "same-origin",
        headers: body === undefined ? undefined : { "content-type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `${method} ${path} -> HTTP ${res.status}`);
    return data;
}

async function get(path: string): Promise<ApiJson> {
    try {
        return await once(path, "GET");
    } catch (e) {
        // The service worker caches the same read-only GETs the legacy client
        // used; serve that body when the network is gone instead of an error.
        if (!offline(e) || typeof caches === "undefined") throw e;
        const url = new URL(`${BASE}/${path}`, location.origin).toString();
        const hit = await caches.match(url).catch(() => undefined);
        if (hit) {
            emit("mc:cachehit", { path });
            return hit.json();
        }
        emit("mc:offline", { path });
        throw e;
    }
}

/**
 * Only replay-safe writes are queued. Likes are toggles, so every tap is kept;
 * playlist adds/removes and renames converge when replayed. Others fail loudly.
 */
type OutboxEntry = { path: string; method: string; body?: unknown; at: number };
const REPLAYABLE: { method: string; path: RegExp; toggle?: boolean }[] = [
    { method: "POST", path: /^like\/\d+$/, toggle: true },
    { method: "POST", path: /^playlists\/\d+\/tracks$/ },
    { method: "PATCH", path: /^playlists\/\d+$/ },
    { method: "DELETE", path: /^playlists\/\d+$/ },
    { method: "DELETE", path: /^playlists\/\d+\/tracks\/\d+$/ },
];
function replayRule(method: string, path: string) {
    return REPLAYABLE.find(r => r.method === method && r.path.test(path));
}

const OUTBOX_KEY = "outbox";
const OUTBOX_STORE = "session";
async function queued(): Promise<OutboxEntry[]> {
    try {
        const v = await idb.get<OutboxEntry[]>(OUTBOX_KEY, OUTBOX_STORE);
        return Array.isArray(v) ? v : [];
    } catch { return []; }
}
export async function pendingWrites(): Promise<number> {
    return (await queued()).length;
}
async function enqueue(path: string, method: string, body?: unknown) {
    const same = (a: unknown, b: unknown) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
    const keepAll = !!replayRule(method, path)?.toggle;
    const items = (await queued()).filter(e =>
        keepAll || !(e.method === method && e.path === path && same(e.body, body)));
    items.push({ path, method, ...(body === undefined ? {} : { body }), at: Date.now() });
    const kept = items.slice(-100);
    await idb.set(OUTBOX_KEY, kept, OUTBOX_STORE);
    emit("mc:queued", { path, method, pending: kept.length });
}

async function send(path: string, method: string, body?: unknown): Promise<ApiJson> {
    try {
        return await once(path, method, body);
    } catch (e) {
        if (!offline(e) || !replayRule(method, path)) throw e;
        await enqueue(path, method, body);
        return { queued: true, offline: true };
    }
}

let flushInFlight: Promise<number> | null = null;
/** Replay queued writes oldest-first; a network error stops the run. */
export function flushOutbox(): Promise<number> {
    if (flushInFlight) return flushInFlight;
    flushInFlight = (async () => {
        if (typeof navigator !== "undefined" && navigator.onLine === false) return 0;
        let list = await queued();
        let sent = 0;
        while (list.length) {
            const item = list[0];
            try {
                await once(item.path, item.method, item.body);
                sent += 1;
            } catch (e) {
                const gone = item.method === "DELETE" && /HTTP (404|410)$/.test(String(e));
                const permanent = /HTTP 4\d\d$/.test(String(e)) && !/HTTP 429$/.test(String(e));
                if (!gone && !permanent) break;
                if (!gone) emit("mc:syncfail", { path: item.path, error: String(e) });
            }
            list = list.slice(1);
            await idb.set(OUTBOX_KEY, list, OUTBOX_STORE);
        }
        if (sent) emit("mc:synced", { count: sent, pending: (await queued()).length });
        return sent;
    })().finally(() => { flushInFlight = null; });
    return flushInFlight;
}

if (typeof window !== "undefined") {
    window.addEventListener("online", () => { void flushOutbox().catch(() => {}); });
    window.addEventListener("load", () => { void flushOutbox().catch(() => {}); });
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") void flushOutbox().catch(() => {});
    });
}

// ---------------------------------------------------------------- ids
// mcmusic keys albums by name and artists by name, so the client's uuids are
// "album:<cover id>:<name>" / "artist:<cover id>:<name>" with the name
// URI-encoded (so a slash in an album name is safe in a path segment).
export function artistUuid(name: string, coverId?: number | null): string {
    return `artist:${coverId ?? ""}:${encodeURIComponent(name || "Unknown Artist")}`;
}

export function parseArtistUuid(uuid: string): { coverId: number | null; name: string } {
    const [, cover, ...rest] = String(uuid).split(":");
    return {
        coverId: cover ? Number(cover) || null : null,
        name: decodeURIComponent(rest.join(":")) || "Unknown Artist",
    };
}

export function albumUuid(album: string, coverId?: number | null): string {
    return `album:${coverId ?? ""}:${encodeURIComponent(album || "Unknown Album")}`;
}

export function parseAlbumUuid(uuid: string): { coverId: number | null; name: string } {
    const [, cover, ...rest] = String(uuid).split(":");
    return {
        coverId: cover ? Number(cover) || null : null,
        name: decodeURIComponent(rest.join(":")) || "Unknown Album",
    };
}

export function coverUrl(id?: number | null): string {
    return id ? `${BASE}/tracks/${id}/cover` : "";
}

export function fallbackCover(name: string, kind: "track" | "artist" | "album" = "album"): string {
    const initial = (name || "?").trim().charAt(0).toUpperCase() || "?";
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#241c26"/><text x="32" y="43" font-size="28" text-anchor="middle" fill="#e9dce6" font-family="sans-serif">${initial}</text><title>${kind}</title></svg>`;
    return `data:image/svg+xml,${encodeURIComponent(svg)}`;
}

// ---------------------------------------------------------------- json -> model
export function userFromJson(d: ApiJson): User {
    return {
        uuid: String(d.id ?? d.uid ?? ""),
        username: String(d.username ?? ""),
        display_name: d.display_name ?? null,
        email: d.email ?? null,
        is_admin: !!d.is_admin,
        avatar_url: d.avatar_url,
        provider: d.provider,
        rotur_id: d.rotur_id ?? null,
        rotur_linked: d.rotur_linked ?? (d.rotur_id != null),
        playing: null,
    };
}

export function trackFromJson(d: ApiJson, setUuid: string | null): Track {
    const names: string[] = (Array.isArray(d.artists) && d.artists.length
        ? d.artists
        : d.artist ? [d.artist] : []) as string[];
    return {
        uuid: String(d.id),
        name: signal(String(d.title ?? "")),
        artists: signal(names.map((n) => artistUuid(n))),
        set: setUuid,
        duration: signal(Number(d.duration ?? 0) || 0),
        year: signal(d.year ?? null),
        trackNo: signal(Number(d.track_no ?? 0) || 0),
        liked: d.liked == null ? undefined : !!d.liked,
    };
}

/** Raw track row for the track-info dialog and the admin explicit flag. */
export async function getTrackInfo(uuid: string): Promise<ApiJson> {
    const t = (await libraryIndex()).get(String(uuid));
    if (!t) throw new Error(`no track ${uuid}`);
    return t;
}

function setFromJson(album: string, tracks: ApiJson[], coverId: number | null, artist?: string): SetEntity {
    const artistName = artist || tracks[0]?.artist || "Unknown Artist";
    const uuid = albumUuid(album, coverId);
    return {
        uuid,
        kind: signal("album"),
        name: signal(album),
        release: signal(null),
        genres: signal([]),
        artist: artistUuid(artistName),
        artistName,
        tracks: signal(tracks.map((t) => trackFromJson(t, uuid))),
    };
}

function artistFromJson(name: string, coverId: number | null, tracks: ApiJson[] = []): Artist {
    const byAlbum = new Map<string, ApiJson[]>();
    for (const t of tracks) {
        const album = t.album || "Unknown Album";
        if (!byAlbum.has(album)) byAlbum.set(album, []);
        byAlbum.get(album)!.push(t);
    }
    return {
        uuid: artistUuid(name, coverId),
        name: signal(name),
        bio: signal(""),
        genres: signal([]),
        sets: signal([...byAlbum.entries()].map(([album, list]) =>
            setFromJson(album, list, list[0]?.id ?? null, name))),
    };
}

function artistStub(name: string): Artist {
    return artistFromJson(name || "Unknown Artist", null);
}

// ---------------------------------------------------------------- library cache
let indexPromise: Promise<Map<string, ApiJson>> | null = null;

function libraryIndex(): Promise<Map<string, ApiJson>> {
    if (!indexPromise) {
        indexPromise = get("tracks?limit=2000")
            .then((d) => new Map<string, ApiJson>((d.tracks ?? []).map((t: ApiJson) => [String(t.id), t])))
            .catch((e) => { indexPromise = null; throw e; });
    }
    return indexPromise;
}

export function refreshLibrary() {
    indexPromise = null;
}

// ---------------------------------------------------------------- api
export const API = {
    me: () => get("me"),
    login: (username: string, password: string) =>
        send("login", "POST", { username, password }),
    register: (data: { username: string; password: string; invite?: string; email?: string }) =>
        send("register", "POST", data),
    logout: () => send("logout", "POST"),

    // ------------------------------------------------------------- password resets
    requestReset: (email: string) => send("auth/reset/request", "POST", { email }),
    checkReset: (token: string) => send("auth/reset/check", "POST", { token }),
    confirmReset: (token: string, password: string) =>
        send("auth/reset/confirm", "POST", { token, password }),

    async listAlbums(opts: {
        limit?: number, offset?: number, q?: string, sort?: string, minTracks?: number
    } = {}): Promise<{ albums: SetEntity[], total: number }> {
        const params = new URLSearchParams({
            limit: String(opts.limit ?? 60),
            offset: String(opts.offset ?? 0),
            min_tracks: String(opts.minTracks ?? 1),
        });
        if (opts.q) params.set("q", opts.q);
        if (opts.sort) params.set("sort", opts.sort);

        const d = await get(`albums?${params}`);
        // Tracks with no album of their own list under their song name, which
        // would turn the grid into 1,000 one-song "albums". The server keeps
        // those out unless the Singles filter asks for them.
        return {
            total: d.total ?? 0,
            albums: (d.albums ?? []).map((a: ApiJson) =>
                setFromJson(a.album, [], a.cover_id ?? null, a.artist)),
        };
    },

    async listTracks(limit = 50): Promise<Track[]> {
        const d = await get(`tracks?limit=${limit}`);
        return (d.tracks ?? []).map((t: ApiJson) => trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null));
    },

    async listArtists(): Promise<Artist[]> {
        const d = await get("artists");
        return (d.artists ?? []).map((a: ApiJson) => artistFromJson(a.artist, a.cover_id ?? null));
    },

    async getArtist(uuidOrName: string): Promise<Artist> {
        const { name, coverId } = uuidOrName.startsWith("artist:")
            ? parseArtistUuid(uuidOrName)
            : { name: uuidOrName, coverId: null };
        const d = await get(`artist?name=${encodeURIComponent(name)}`);
        return artistFromJson(name, coverId, d.tracks ?? []);
    },

    getArtistPfpUrl(uuid: string): string {
        const { coverId, name } = parseArtistUuid(uuid);
        return coverUrl(coverId) || fallbackCover(name, "artist");
    },

    async getArtistPfp(uuid: string): Promise<Blob> {
        return (await fetch(this.getArtistPfpUrl(uuid), { credentials: "same-origin" })).blob();
    },

    async getSet(uuid: string): Promise<SetEntity> {
        const { name } = parseAlbumUuid(uuid);
        const d = await get(`album?name=${encodeURIComponent(name)}`);
        const tracks: ApiJson[] = d.tracks ?? [];
        return setFromJson(name, tracks, tracks[0]?.id ?? null, tracks[0]?.artist);
    },

    getSetCoverUrl(uuid: string): string {
        const { coverId, name } = parseAlbumUuid(uuid);
        return coverUrl(coverId) || fallbackCover(name, "album");
    },

    async getSetCover(uuid: string): Promise<Blob> {
        return (await fetch(this.getSetCoverUrl(uuid), { credentials: "same-origin" })).blob();
    },

    async getTrack(uuid: string): Promise<Track> {
        const t = (await libraryIndex()).get(String(uuid));
        if (!t) throw new Error(`no track ${uuid}`);
        return trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null);
    },

    streamUrl: (uuid: string) => `${BASE}/tracks/${uuid}/stream`,
    getTrackCoverUrl: (uuid: string) => coverUrl(Number(uuid)) || fallbackCover(uuid, "track"),
    lyrics: (uuid: string) => get(`tracks/${uuid}/lyrics`),
    trackSources: (uuid: string): Promise<{ sources: ApiJson[] }> =>
        get(`tracks/${uuid}/sources`) as Promise<{ sources: ApiJson[] }>,
    patchTrack: (uuid: string, patch: { explicit?: boolean | null }) =>
        send(`tracks/${uuid}`, "PATCH", patch),

    // ------------------------------------------------------ home / likes / radio
    async home(): Promise<HomePayload> {
        const d = await get("home");
        const sections: HomePayload["sections"] = (d.sections ?? []).map((s: ApiJson) => ({
            title: String(s.title ?? ""),
            tracks: (s.tracks ?? []).map((t: ApiJson) =>
                trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null)),
        }));
        return { sections, albums: d.albums ?? [] };
    },

    async likes(): Promise<Track[]> {
        const d = await get("likes");
        return (d.tracks ?? []).map((t: ApiJson) =>
            trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null));
    },
    like: (uuid: string): Promise<{ liked?: boolean; queued?: boolean }> =>
        send(`like/${uuid}`, "POST"),

    async radio(uuid: string): Promise<Track[]> {
        const d = await get(`radio/${uuid}`);
        return (d.tracks ?? []).map((t: ApiJson) =>
            trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null));
    },

    // ---------------------------------------------------------- public / social
    publicListening: (): Promise<PublicListening> => get("public/listening") as Promise<PublicListening>,
    publicNow: (username: string): Promise<PublicNow> =>
        get(`public/now/${encodeURIComponent(username)}`) as Promise<PublicNow>,

    // --------------------------------------------------------------- playback
    playback: (device?: string): Promise<PlaybackResponse> =>
        get(device ? `playback?device=${encodeURIComponent(device)}` : "playback") as Promise<PlaybackResponse>,
    playbackPush: (body: ApiJson) => send("playback", "POST", body),
    deviceHeartbeat: (body: ApiJson) => send("devices/heartbeat", "POST", body),
    version: () => get("version"),
    ping: () => get("ping"),

    // --------------------------------------------------------------- builds
    builds: () => get("builds"),
    emailBuild: (email: string, kind: string) =>
        send("builds/email", "POST", { email, build: kind }),
    setEmail: (email: string) => send("auth/email", "POST", { email }),

    async getTrackAudio(uuid: string): Promise<Blob> {
        const res = await fetch(API.streamUrl(uuid), { credentials: "same-origin" });
        if (!res.ok) throw new Error(`audio ${uuid} -> HTTP ${res.status}`);
        return res.blob();
    },

    async getTrackCover(uuid: string): Promise<Blob> {
        return (await fetch(this.getTrackCoverUrl(uuid), { credentials: "same-origin" })).blob();
    },

    async search(q: string, filter?: string[]): Promise<SearchItem[]> {
        const d = await get(`search?q=${encodeURIComponent(q)}`);
        const out: SearchItem[] = [];
        const want = (t: string) => !filter || filter.includes(t);
        if (want("artist")) {
            for (const a of d.artists ?? []) {
                out.push({
                    type: "artist",
                    uuid: artistUuid(a.artist, a.cover_id),
                    artist: artistFromJson(a.artist, a.cover_id ?? null),
                });
            }
        }
        if (want("set")) {
            for (const a of d.albums ?? []) {
                out.push({
                    type: "set",
                    uuid: albumUuid(a.album, a.cover_id),
                    set: setFromJson(a.album, [], a.cover_id ?? null, a.artist),
                    artist: artistStub(a.artist),
                });
            }
        }
        if (want("track")) {
            for (const t of d.tracks ?? []) {
                out.push({
                    type: "track",
                    uuid: String(t.id),
                    track: trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null),
                    set: t.album ? setFromJson(t.album, [], t.id, t.artist) : null,
                    artist: artistStub(t.artist),
                });
            }
        }
        return out;
    },

    requestDownload: (url: string) => send("requests", "POST", { url }),
    requests: () => get("requests"),

    // ------------------------------------------------------------ playlists
    listPlaylists: () => get("playlists"),

    async playlistTracks(id: number | string): Promise<{ id: number; name: string; tracks: Track[] }> {
        const d = await get(`playlists/${id}`);
        return {
            id: d.id,
            name: d.name ?? "",
            tracks: (d.tracks ?? []).map((t: ApiJson) =>
                trackFromJson(t, t.album ? albumUuid(t.album, t.id) : null)),
        };
    },

    createPlaylist: (name: string) => send("playlists", "POST", { name }),
    renamePlaylist: (id: number | string, name: string) => send(`playlists/${id}`, "PATCH", { name }),
    deletePlaylist: (id: number | string) => send(`playlists/${id}`, "DELETE"),
    addToPlaylist: (id: number | string, trackId: number | string) =>
        send(`playlists/${id}/tracks`, "POST", { track_id: Number(trackId) }),
    removeFromPlaylist: (id: number | string, trackId: number | string) =>
        send(`playlists/${id}/tracks/${trackId}`, "DELETE"),

    // ------------------------------------------------------------- settings
    getSettings: () => get("settings"),
    saveSettings: (patch: Record<string, unknown>) => send("settings", "PUT", patch),
    changePassword: (oldPw: string, newPw: string) =>
        send("password", "POST", { old: oldPw, new: newPw }),

    // ---------------------------------------------------------- linked accounts
    roturStatus: async (): Promise<RoturStatus> => (await get("auth/rotur/status")) as RoturStatus,
    roturUnlink: () => send("auth/rotur/unlink", "POST"),
    roturAuthorizeUrl: (next = "/settings") =>
        `${BASE}/auth/rotur/authorize?next=${encodeURIComponent(next)}`,
    roturActivity: (body: { track_id: number | string | null; playing: boolean; position?: number }) =>
        send("auth/rotur/activity", "POST", body),

    discordStatus: () => get("auth/discord/status"),
    discordUnlink: () => send("auth/discord/unlink", "POST"),
    discordAuthorizeUrl: (next = "/settings") =>
        `${BASE}/auth/discord/authorize?next=${encodeURIComponent(next)}`,
    discordActivity: (body: { track_id: number | string | null; playing: boolean; position?: number }) =>
        send("auth/discord/activity", "POST", body),

    // -------------------------------------------------------- control channels
    channels: (state = false) => get(`channels${state ? "?state=1" : ""}`),
    bindChannel: (body: { platform: string; channel_id: string; mode?: string; guild_id?: string }) =>
        send("channels", "POST", body),
    unbindChannel: (id: number) => send(`channels/${id}`, "DELETE"),
    channelState: (id: number) => get(`channels/${id}/state`),

    // -------------------------------------------------------------- devices
    deviceCode: () => send("devices/code", "POST"),
    devices: () => get("devices"),
    activateDevice: (id: number) => send(`devices/${id}/activate`, "POST"),
    renameDevice: (id: number, name: string) => send(`devices/${id}`, "PATCH", { name }),
    forgetDevice: (id: number) => send(`devices/${id}`, "DELETE"),
    clearDevices: () => send("devices/clear", "POST"),
    cleanupDevices: () => send("devices/cleanup", "POST"),
    deviceTokens: () => get("devices/tokens"),
    revokeDeviceToken: (id: number) => send(`devices/tokens/${id}/revoke`, "POST"),

    // ---------------------------------------------------------------- admin
    adminStats: () => get("admin/stats"),
    adminDevices: () => get("admin/devices"),
    adminEnrich: () => get("admin/enrich"),
    startEnrich: (force = false) => send("admin/enrich", "POST", { force }),
    adminLyrics: () => get("admin/lyrics"),
    startLyrics: () => send("admin/lyrics", "POST"),
    adminRooms: () => get("admin/rooms"),
    adminCloseRoom: (code: string) => send(`admin/rooms/${encodeURIComponent(code)}`, "DELETE"),
    adminRequests: () => get("admin/requests"),
    adminRequestLog: (id: number) => get(`admin/requests/${id}/log?tail=20000`),
    adminReqAction: (id: number, action: "approve" | "reject") => send(`requests/${id}/${action}`, "POST"),
    adminReqCancel: (id: number) => send(`admin/requests/${id}/cancel`, "POST"),
    adminReqRetry: (id: number) => send(`admin/requests/${id}/retry`, "POST"),
    adminReqDelete: (id: number) => send(`admin/requests/${id}`, "DELETE"),
    adminUsers: () => get("admin/users"),
    adminSetAdmin: (id: number, isAdmin: boolean) =>
        send(`admin/users/${id}/admin`, "POST", { is_admin: isAdmin }),
    adminDeleteUser: (id: number) => send(`admin/users/${id}`, "DELETE"),
    adminInviteCodes: () => get("admin/invite-codes"),
    adminCreateInvite: (data: { uses?: number; hours?: number; note?: string; for_user?: string }) =>
        send("admin/invite-codes", "POST", data),
    adminRevokeInvite: (id: number) => send(`admin/invite-codes/${id}`, "DELETE"),
    adminScan: () => send("admin/scan", "POST"),

    // The library is server-side; this UI has no upload/delete endpoints.
    uploadTrack: (): Promise<string> => Promise.reject(new Error("uploads are not supported")),
    uploadSet: (): Promise<string> => Promise.reject(new Error("uploads are not supported")),
    uploadArtist: (): Promise<string> => Promise.reject(new Error("uploads are not supported")),
    deleteTrack: (): Promise<void> => Promise.reject(new Error("deletes are not supported")),
    deleteSet: (): Promise<void> => Promise.reject(new Error("deletes are not supported")),
    deleteArtist: (): Promise<void> => Promise.reject(new Error("deletes are not supported")),
};

export type { Option };
