import { Container, Image } from "flufi-ui/components";
import { API } from "../../common/net/api";
import type { Artist, SearchItem, Set, Track, Uuid } from "../../common/net/types";
import { addClass } from "flufi-ui";
import { covers } from "../../common/prefs";

import "./style.css";

// "Covers" off (Settings) hides artwork without removing the layout box.
function artwork(src: string, size: number | undefined, cls: string | undefined, lazy?: boolean) {
    if (!covers.value) return <Container class={addClass("library-img", cls, "no-art")} other={{ style: { width: size, height: size } }} />;
    return <Image src={src} size={size} class={addClass("library-img", cls)} lazy={lazy} />;
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
    return artwork(API.getArtistPfpUrl(uuid), props.size,
        addClass("artist-pfp", props.class), props.lazy)
}

export type SetImageProps = { uuid: Uuid }
    | { set: Set }
    | Extract<SearchItem, { type: "set" }>;
export function SetCover(props: SharedImageProps & SetImageProps) {
    const uuid = "uuid" in props ? props.uuid : props.set.uuid;
    return artwork(API.getSetCoverUrl(uuid), props.size,
        addClass("set-cover", props.class), props.lazy)
}

export type TrackImageProps = { uuid: Uuid }
    | { track: Track }
    | Extract<SearchItem, { type: "track" }>;
export function TrackCover(props: SharedImageProps & TrackImageProps) {
    const uuid = "uuid" in props ? props.uuid : props.track.uuid;
    return artwork(API.getTrackCoverUrl(uuid), props.size,
        addClass("track-cover", props.class), props.lazy)
}
