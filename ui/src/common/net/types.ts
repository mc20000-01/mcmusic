/** Client-side entity types. Names/fields are signals, matching flufi-ui.
 * mcmusic keys albums and artists by name, so client ids are ordinary strings
 * ("album:<cover>:<name>" / "artist:<cover>:<name>"), not flufi's UUID shape.
 */
import type { Signal } from "@preact/signals";
import type { CalendarDate, Option } from "flufi-ui/types";

export type Uuid = string;

// general
export type Artist = {
    uuid: Uuid,
    serverUrl?: string

    name: Signal<string>,
    bio: Signal<string>
    genres: Signal<string[]>,

    sets: Signal<Set[]>,
};

export type SetKind = "album" | "ep" | "single";
export type Set = {
    uuid: Uuid,
    serverUrl?: string,

    kind: Signal<SetKind>,
    name: Signal<string>,
    release: Signal<Option<CalendarDate>>,
    genres: Signal<string[]>, // set?

    artist: Uuid,
    artistName?: string,
    tracks: Signal<Track[]>,
};

export type Track = {
    uuid: Uuid,
    serverUrl?: string,

    name: Signal<string>,

    artists: Signal<Uuid[]>,
    set: Option<Uuid>,
    duration: Signal<number>,
    year: Signal<Option<string>>,
    trackNo: Signal<number>,
    /** Present on endpoints that know the listener's likes. */
    liked?: boolean;
};

export type Playing = {
    server_uuid: Option<string>,
    track_uuid: Uuid,
    set_uuid: Option<Uuid>,
    playlist_uuid: Option<Uuid>,
    track_number: Option<number>
};

export type User = {
    uuid: Uuid,
    username: string,
    display_name: Option<string>,
    email?: Option<string>,
    is_admin?: boolean,
    avatar_url?: string,
    provider?: string,
    primary_token?: string,
    rotur_id?: string | null,
    rotur_linked?: boolean,

    playing: Option<Playing>
};

/** GET /api/home — personalised shelves plus recent albums. */
export type HomeSection = {
    title: string;
    tracks: Track[];
};
export type HomePayload = {
    sections: HomeSection[];
    albums: { album: string; artist: string; n: number; cover_id: number }[];
};

/** GET /api/public/listening — public "listening now" directory. */
export type PublicListener = {
    username: string;
    listening: boolean;
    position: number;
    updated: number;
    track: {
        id: number;
        title: string;
        artist: string;
        album: string;
        duration: number;
    } | null;
    profile_url: string;
    cover_url: string;
};
export type PublicListening = {
    ok: boolean;
    users: PublicListener[];
    base_url: string;
    now: number;
};

/** GET /api/public/now/<username> — the standalone profile payload. */
export type PublicNow = {
    ok: boolean;
    user: { username: string };
    listening: boolean;
    position: number;
    updated: number;
    track: Track | null;
    profile_url: string;
    cover_url: string;
    base_url: string;
};

/** GET /api/playback — account playback state and queued commands. */
export type PlaybackCommand = {
    id: number;
    action: string;
    arg: Record<string, any>;
};
export type PlaybackResponse = {
    state: {
        track_id: number | null;
        position: number;
        duration: number;
        playing: boolean;
        queue: number[];
        device?: string;
        device_name?: string;
        track?: Track | null;
    } | null;
    commands: PlaybackCommand[];
};

/** Response from GET /api/auth/rotur/status. */
export type RoturStatus = {
    linked: boolean;
    configured: boolean;
    has_tokens: boolean;
    session_valid: boolean;
    rotur_id: string | null;
    rotur_username: string | null;
    activity: {
        ready: boolean;
        reason: string;
    };
};

/** Response from GET /api/auth/discord/status. */
export type DiscordStatus = {
    linked: boolean;
    configured: boolean;
    missing: string[];
    discord_id: string | null;
    discord_username: string | null;
    session_valid: boolean;
    presence: {
        configured?: boolean;
        available?: boolean;
        [key: string]: any;
    } | null;
};

// request specific
export type SearchFilter = ("artist" | "set" | "track")[];
export type SearchItem = {
    type: "artist",
    uuid: Uuid,
    artist: Artist,
    serverUrl?: string
} | {
    type: "set",
    uuid: Uuid,
    set: Set,
    artist: Artist | null,
    serverUrl?: string
} | {
    type: "track",
    uuid: Uuid,
    track: Track,
    set: Set | null,
    artist: Artist | null,
    serverUrl?: string
}

export type UploadArtistData = {
    name: string,
    pfp?: File,
    bio: string,
    genres: string[]
};
export type UploadSet = {
    kind: SetKind,
    name: string,
    cover?: Option<File>,
    release: Option<CalendarDate>,
    genres: string[], // set?

    artist: Uuid,
    tracks: Uuid[]
};
export type UploadTrack = {
    name: string,
    artists: Uuid[],
    file: Option<File>,
    set?: Uuid
};

export type UserUpdateData = {
    display_name?: Option<string>,
    avatar_url?: string
};

export type ArtistUpdateData = {
    name: string
};

export type AllowedUser = string;
