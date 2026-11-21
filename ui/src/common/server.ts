/** Server URL helpers shared by the API adapter and media URLs.
 */
import { signal, type Signal } from "@preact/signals";
import { peekAuth, peekPrimaryServerAuth, setPrimaryServerAuth } from "./auth";
import { authedFetch, handleFlufimusicError } from "./net/utils";
import type {
    AllowedUser,
    Artist,
    SearchFilter,
    SearchItem,
    Set as SetEntity,
    Track,
    UploadArtistData,
    UploadSet,
    UploadTrack,
    User,
    UserUpdateData
} from "./net/types";
import { createQuery } from "flufi-ui/common";
import { CalendarDate, type Option, type Uuid } from "flufi-ui/types";

export abstract class Server {
    public abstract login(): Promise<void>;
    public abstract getIndex(): Promise<string>;
    public abstract isOk(): Promise<boolean>;
    
    public abstract isAllowed(): Promise<boolean>;
    public abstract getAllowedList(): Promise<AllowedUser[]>;
    
    public abstract getMe(): Promise<User>;
    public abstract updateMe(data: UserUpdateData): Promise<User>;
    
    public abstract addRecentSet(uuid: Uuid): Promise<void>;
    public abstract addRecentArtist(uuid: Uuid): Promise<void>;
    
    public abstract search(query: string, filter?: SearchFilter): Promise<SearchItem[]>;
    
    public abstract listArtists(): Promise<Artist[]>;
    public abstract getArtist(uuid: Uuid): Promise<Artist>;
    public abstract getArtistPfp(uuid: Uuid, size?: number): Promise<Blob>;
    public abstract getArtistPfpUrl(uuid: Uuid, size?: number): string;
    public abstract uploadArtist(data: UploadArtistData): Promise<Uuid>;
    public abstract uploadArtistPfp(uuid: Uuid, pfp: File): Promise<void>;
    public abstract updateArtistName(uuid: Uuid, name: string): Promise<void>;
    public abstract addArtistSet(artist: Uuid, set: Uuid): Promise<void>;
    public abstract replaceArtistSets(artist: Uuid, sets: Uuid[]): Promise<void>;
    public abstract deleteArtist(uuid: Uuid): Promise<void>;
    
    public abstract uploadSet(data: UploadSet): Promise<Uuid>;
    public abstract getSet(uuid: Uuid): Promise<SetEntity>;
    public abstract getSetCover(uuid: Uuid, size?: number): Promise<Blob>;
    public abstract getSetCoverUrl(uuid: Uuid, size?: number): string;
    public abstract uploadSetCover(uuid: Uuid, cover: File): Promise<void>;
    public abstract replaceSetTracks(set: Uuid, tracks: Uuid[]): Promise<void>;
    public abstract addSetTrack(set: Uuid, track: Uuid): Promise<void>;
    public abstract deleteSet(uuid: Uuid): Promise<void>;
    
    public abstract uploadTrack(data: UploadTrack): Promise<Uuid>;
    public abstract getTrack(uuid: Uuid): Promise<Track>;
    public abstract getTrackAudio(uuid: Uuid): Promise<Blob>;
    public abstract getTrackCover(uuid: Uuid): Promise<Blob>;
    public abstract getTrackCoverUrl(uuid: Uuid): string;
    public abstract deleteTrack(uuid: Uuid): Promise<void>;

    public abstract get name(): string;
}

type ApiJson = Record<string, any>;

function artistFromJson(data: ApiJson, serverUrl: string): Artist {
    return {
        uuid: data.uuid,
        serverUrl,
        
        name: signal(data.name),
        bio: signal(data.bio),
        genres: signal(data.genres ?? []),
        
        sets: signal((data.sets ?? []).map((s: any) => setFromJson(s, serverUrl))),
    };
}

function setFromJson(data: ApiJson, serverUrl: string): SetEntity {
    const release = typeof data.release === "string" ? CalendarDate.fromString(data.release) : null;
    return {
        uuid: data.uuid,
        serverUrl,
        
        kind: signal(String(data.kind ?? "album").toLowerCase() as SetEntity["kind"]["value"]),
        name: signal(data.name),
        release: signal(release),
        genres: signal(data.genres ?? []),
        
        artist: data.artist,
        tracks: signal((data.tracks ?? []).map((t: any) => trackFromJson(t, serverUrl))),
    };
}

function trackFromJson(data: ApiJson, serverUrl: string): Track {
    return {
        uuid: data.uuid,
        serverUrl,
        
        name: signal(data.name),
        
        artists: signal(data.artists ?? []),
        set: data.set ?? null,
    };
}

function searchItemFromJson(data: ApiJson, serverUrl: string): SearchItem {
    switch (data.type) {
        case "artist":
            return { type: "artist", uuid: data.uuid, artist: artistFromJson(data.artist, serverUrl), serverUrl };
        case "set":
            return {
                type: "set",
                uuid: data.uuid,
                set: setFromJson(data.set, serverUrl),
                artist: data.artist ? artistFromJson(data.artist, serverUrl) : null,
                serverUrl
            };
        case "track":
            return {
                type: "track",
                uuid: data.uuid,
                track: trackFromJson(data.track, serverUrl),
                set: data.set ? setFromJson(data.set, serverUrl) : null,
                artist: data.artist ? artistFromJson(data.artist, serverUrl) : null,
                serverUrl
            };
        default:
            throw new Error(`unknown search item type: ${data.type}`);
    }
}

export class FlufimusicServer extends Server {
    user: Signal<Option<User>> = signal(null);

    constructor(public url: string, public primary: boolean) {
        super();
    }

    private async requestJson(path: string, func: string, init?: RequestInit, authenticated = false): Promise<ApiJson> {
        const response = authenticated
            ? await authedFetch(`${this.url}${path}`, init, this.primary)
            : await fetch(`${this.url}${path}`, init);
        const result = await response.json();
        if (!response.ok)
            handleFlufimusicError(result, func, this.primary);
        return result;
    }
    private async requestBlob(path: string, func: string, authenticated = false): Promise<Blob> {
        const response = authenticated
            ? await authedFetch(`${this.url}${path}`, undefined, this.primary)
            : await fetch(`${this.url}${path}`);
        if (!response.ok) {
            const result = await response.json();
            handleFlufimusicError(result, func, this.primary);
        }
        return response.blob();
    }
    private async requestText(path: string, func: string, authenticated = false): Promise<string> {
        const response = authenticated
            ? await authedFetch(`${this.url}${path}`, undefined, this.primary)
            : await fetch(`${this.url}${path}`);
        if (!response.ok) {
            const result = await response.json();
            handleFlufimusicError(result, func, this.primary);
        }
        return response.text();
    }

    public async login(): Promise<void> {
        if (!this.primary || peekPrimaryServerAuth() == null) {
            if (peekAuth() == null) {
                console.warn("cannot login, no auth yet");
                return;
            }
        }

        const res = await this.requestJson("/user/me", "Server.login()", undefined, true);
        if (this.primary && (!peekPrimaryServerAuth() || peekPrimaryServerAuth()?.type == "rotur")) {
            setPrimaryServerAuth({ type: "local", token: res.user.primary_token });
        }
        this.user.value = res.user;
    }
    public getIndex(): Promise<string> {
        return this.requestText("/", "Server.getIndex()");
    }
    public async isOk(): Promise<boolean> {
        return (await this.requestText("/ok", "Server.isOk()")).trim() === "true";
    }

    public async isAllowed(): Promise<boolean> {
        return (await this.requestText("/allowed", "Server.isAllowed()", true)).trim() === "true";
    }
    public async getAllowedList(): Promise<AllowedUser[]> {
        const response = await fetch(`${this.url}/allowed/list`);
        if (!response.ok) {
            const result = await response.json();
            handleFlufimusicError(result, "Server.getAllowedList()", this.primary);
        }
        return response.json();
    }

    public async getMe(): Promise<User> {
        const res = await this.requestJson("/user/me", "Server.getMe()", undefined, true);
        this.user.value = res.user;
        return res.user;
    }
    public async updateMe(data: UserUpdateData): Promise<User> {
        const res = await this.requestJson("/user/me", "Server.updateMe()", {
            method: "PATCH",
            body: JSON.stringify(data),
            headers: { "content-type": "application/json" }
        }, true);
        const user = res.user ?? res;
        this.user.value = user;
        return user;
    }

    public async addRecentSet(uuid: Uuid): Promise<void> {
        await this.requestJson(`/user/recent/set${createQuery(["uuid", uuid])}`, "Server.addRecentSet()", { method: "POST" }, true);
    }
    public async addRecentArtist(uuid: Uuid): Promise<void> {
        await this.requestJson(`/user/recent/artist${createQuery(["uuid", uuid])}`, "Server.addRecentArtist()", { method: "POST" }, true);
    }

    public async search(q: string, filter?: SearchFilter): Promise<SearchItem[]> {
        const query = createQuery(["q", q], filter && ["filter", filter]);
        const res = await this.requestJson(`/search${query}`, "Server.search()");
        return res.items.map((item: ApiJson) => searchItemFromJson(item, this.url));
    }

    public async listArtists(): Promise<Artist[]> {
        const res = await this.requestJson("/artist/list", "Server.listArtists()");
        return (res.data as ApiJson[]).map(artist => artistFromJson(artist, this.url));
    }
    public async getArtist(uuid: Uuid): Promise<Artist> {
        const res = await this.requestJson(`/artist${createQuery(["uuid", uuid])}`, "Server.getArtist()");
        return artistFromJson(res.data, this.url);
    }
    public getArtistPfp(uuid: Uuid, size?: number): Promise<Blob> {
        return this.requestBlob(`/artist/pfp${createQuery(["uuid", uuid], size != null && ["size", size])}`, "Server.getArtistPfp()");
    }
    public getArtistPfpUrl(uuid: Uuid, size?: number): string {
        return `${this.url}/artist/pfp${createQuery(["uuid", uuid], size != null && ["size", size])}`;
    }
    public async uploadArtist(data: UploadArtistData): Promise<Uuid> {
        const res = await this.requestJson("/artist", "Server.uploadArtist()", {
            method: "POST",
            body: JSON.stringify({ name: data.name, bio: data.bio, genres: data.genres }),
            headers: { "content-type": "application/json" }
        }, true);
        try {
            if (data.pfp)
                await this.uploadArtistPfp(res.uuid, data.pfp);
        } catch (e) {
            // delete the set if it failed to upload cover
            this.deleteArtist(res.uuid);
            throw e;
        }
        return res.uuid;
    }
    public async uploadArtistPfp(uuid: Uuid, pfp: File): Promise<void> {
        await this.requestJson(`/artist/pfp${createQuery(["uuid", uuid])}`, "Server.uploadArtistPfp()", {
            method: "PUT",
            body: pfp
        }, true);
    }
    public async updateArtistName(uuid: Uuid, name: string): Promise<void> {
        await this.requestJson(`/artist/name${createQuery(["uuid", uuid])}`, "Server.updateArtistName()", {
            method: "PATCH",
            body: JSON.stringify({ name }),
            headers: { "content-type": "application/json" }
        }, true);
    }
    public async addArtistSet(artist: Uuid, set: Uuid): Promise<void> {
        await this.requestJson(`/artist/sets${createQuery(["artist", artist], ["set", set])}`, "Server.addArtistSet()", { method: "POST" }, true);
    }
    public async replaceArtistSets(artist: Uuid, sets: Uuid[]): Promise<void> {
        await this.requestJson(`/artist/sets${createQuery(["artist", artist])}`, "Server.replaceArtistSets()", {
            method: "PATCH",
            body: JSON.stringify(sets),
            headers: { "content-type": "application/json" }
        }, true);
    }
    public async deleteArtist(uuid: Uuid): Promise<void> {
        await this.requestJson(`/artist${createQuery(["artist", uuid])}`, "Server.deleteArtist()", { method: "DELETE" }, true);
    }

    public async uploadSet(data: UploadSet): Promise<Uuid> {
        const res = await this.requestJson("/set", "Server.uploadSet()", {
            method: "POST",
            body: JSON.stringify({
                type: data.kind,
                name: data.name,
                release: data.release?.toString() ?? null,
                genres: data.genres,
                artist: data.artist,
                tracks: data.tracks
            }),
            headers: { "content-type": "application/json" }
        }, true);
        try {
            if (data.cover)
                await this.uploadSetCover(res.uuid, data.cover);
        } catch (e) {
            // delete the set if it failed to upload cover
            this.deleteSet(res.uuid);
            throw e;
        }
        try {
            if (data.artist)
                await this.addArtistSet(data.artist, res.uuid);
        } catch (e) {
            // delete the set if it failed to add it to the artist
            this.deleteSet(res.uuid);
            throw e;
        }
        return res.uuid;
    }
    public async getSet(uuid: Uuid): Promise<SetEntity> {
        const res = await this.requestJson(`/set${createQuery(["uuid", uuid])}`, "Server.getSet()");
        return setFromJson(res.data, this.url);
    }
    public getSetCover(uuid: Uuid, size?: number): Promise<Blob> {
        return this.requestBlob(`/set/cover${createQuery(["uuid", uuid], size != null && ["size", size])}`, "Server.getSetCover()");
    }
    public getSetCoverUrl(uuid: Uuid, size?: number): string {
        return `${this.url}/set/cover${createQuery(["uuid", uuid], size != null && ["size", size])}`;
    }
    public async uploadSetCover(uuid: Uuid, cover: File): Promise<void> {
        await this.requestJson(`/set/cover${createQuery(["uuid", uuid])}`, "Server.uploadSetCover()", {
            method: "PUT",
            body: cover
        }, true);
    }
    public async replaceSetTracks(set: Uuid, tracks: Uuid[]): Promise<void> {
        await this.requestJson(`/set/tracks${createQuery(["set", set])}`, "Server.replaceSetTracks()", {
            method: "PATCH",
            body: JSON.stringify(tracks),
            headers: { "content-type": "application/json" }
        }, true);
    }
    public async addSetTrack(set: Uuid, track: Uuid): Promise<void> {
        await this.requestJson(`/set/tracks${createQuery(["set", set], ["track", track])}`, "Server.addSetTrack()", { method: "POST" }, true);
    }
    public async deleteSet(uuid: Uuid): Promise<void> {
        await this.requestJson(`/set${createQuery(["uuid", uuid])}`, "Server.deleteSet()", { method: "DELETE" }, true);
    }

    public async uploadTrack(data: UploadTrack): Promise<Uuid> {
        if (!data.file)
            throw new Error("track upload requires an audio file");
        const body = new FormData();
        body.append("metadata", JSON.stringify({ name: data.name, artists: data.artists, set: data.set }));
        body.append("audio", data.file, data.file.name);
        const res = await this.requestJson("/track", "Server.uploadTrack()", { method: "POST", body }, true);
        return res.uuid;
    }
    public async getTrack(uuid: Uuid): Promise<Track> {
        const res = await this.requestJson(`/track${createQuery(["uuid", uuid])}`, "Server.getTrack()");
        return trackFromJson(res.data, this.url);
    }
    public getTrackAudio(uuid: Uuid): Promise<Blob> {
        return this.requestBlob(`/track/audio${createQuery(["uuid", uuid])}`, "Server.getTrackAudio()", true);
    }
    public getTrackCover(uuid: Uuid): Promise<Blob> {
        return this.requestBlob(`/track/cover${createQuery(["uuid", uuid])}`, "Server.getTrackCover()");
    }
    public getTrackCoverUrl(uuid: Uuid): string {
        return `${this.url}/track/cover${createQuery(["uuid", uuid])}`;
    }
    public async deleteTrack(uuid: Uuid): Promise<void> {
        await this.requestJson(`/track${createQuery(["uuid", uuid])}`, "Server.deleteTrack()", { method: "DELETE" }, true);
    }
    
    public get name(): string {
        return this.url;
    }
}
