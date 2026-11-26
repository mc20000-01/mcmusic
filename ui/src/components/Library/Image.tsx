import { addClass } from "flufi-ui";
import {
    API, parseAlbumUuid, parseArtistUuid,
} from "../../common/net/api";
import type { Artist, SearchItem, Set, Track, Uuid } from "../../common/net/types";
import { covers } from "../../common/prefs";
import { CoverArt } from "./CoverArt";

import "./style.css";

// "Covers" off (Settings) hides artwork without removing the layout box.
function artwork(src: string, name: string, kind: "artist" | "album" | "track",
                 size: number | undefined, cls: string | undefined, lazy?: boolean) {
    if (!covers.value)
        return <div class={addClass("library-img", "no-art", cls)} style={{ width: size, height: size }} aria-hidden="true" />;
    return (
        <CoverArt
            src={src}
            name={name}
            kind={kind}
            size={size}
            class={addClass("library-img", cls)}
            lazy={lazy}
        />
    );
}

export type SharedImageProps = {
    size?: number,
    class?: string,
    lazy?: boolean
};

export type ArtistImageProps = { uuid: Uuid }
    | { artist: Artist }
    | Extract<SearchItem, { type: "artist" }>;
export function ArtistPfp(props: SharedImageProps & ArtistImageProps) {
    const uuid = "uuid" in props ? props.uuid : props.artist.uuid;
    const name = "artist" in props ? props.artist.name.value : parseArtistUuid(uuid).name;
    return artwork(API.getArtistPfpUrl(uuid), name, "artist", props.size,
        addClass("artist-pfp", props.class), props.lazy)
}

export type SetImageProps = { uuid: Uuid }
    | { set: Set }
    | Extract<SearchItem, { type: "set" }>;
export function SetCover(props: SharedImageProps & SetImageProps) {
    const uuid = "uuid" in props ? props.uuid : props.set.uuid;
    const name = "set" in props ? props.set.name.value : parseAlbumUuid(uuid).name;
    return artwork(API.getSetCoverUrl(uuid), name, "album", props.size,
        addClass("set-cover", props.class), props.lazy)
}

export type TrackImageProps = { uuid: Uuid }
    | { track: Track }
    | Extract<SearchItem, { type: "track" }>;
export function TrackCover(props: SharedImageProps & TrackImageProps) {
    const uuid = "uuid" in props ? props.uuid : props.track.uuid;
    const name = "track" in props && "name" in props.track ? props.track.name.value : uuid;
    return artwork(API.getTrackCoverUrl(uuid), name, "track", props.size,
        addClass("track-cover", props.class), props.lazy)
}
