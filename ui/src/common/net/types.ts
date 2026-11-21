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
