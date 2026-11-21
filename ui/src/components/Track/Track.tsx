/** A single track row: number/play affordance, title, artist, duration and
 * per-row actions. The whole row is a transparent flufi-ui Button, so it is
 * keyboard-focusable and every child stays a flufi-ui component.
 *
 * Album-page behaviour:
 *  - the artist is hidden when it matches the album artist (shown only for
 *    featured / different artists);
 *  - a duration column sits on the right;
 *  - hovering shows a play icon in place of the number;
 *  - the current track is highlighted (accent title) with an animated
 *    equaliser while playing and a paused icon when paused;
 *  - double-click plays; right-click opens a context menu via onContextMenu.
 */
import type { Track } from "../../common/net/types";
import { Button, Container, Text } from "flufi-ui/components";
import { addClass } from "flufi-ui/common";
import { TrackNumber } from "../TrackNumber/TrackNumber";
import { Pause, Play } from "lucide-preact";
import { Equaliser } from "../Equaliser/Equaliser";
import { currentId, formatTime, isPlaying, playTrack, toggleTrack } from "../../common/player";
import { parseArtistUuid } from "../../common/net/api";

import "./style.css";

// peak types???
export type TrackWithOptionalUuid = Track & { uuid?: string };
export type TrackWithOptionalUuidAndSet = TrackWithOptionalUuid & { set?: string };

export type TrackContext = {
    /** Album artist name; the track's own artists are hidden when they match it. */
    albumArtist?: string;
    /** Show a right-aligned duration column. */
    showDuration?: boolean;
    /** Fired on right-click; the parent opens a context menu. */
    onContextMenu?: (track: TrackWithOptionalUuid, event: MouseEvent) => void;
};

function artistNames(track: TrackWithOptionalUuid): string {
    const list = track.artists?.value ?? [];
    return list.map((u) => parseArtistUuid(u).name).join(", ");
}

function trackArtistsMatchAlbum(track: TrackWithOptionalUuid, albumArtist?: string): boolean {
    if (!albumArtist) return false;
    const names = (track.artists?.value ?? []).map((u) => parseArtistUuid(u).name);
    return names.length > 0 && names.every((n) => n === albumArtist);
}

export function TrackElem(props: {
    track: TrackWithOptionalUuid,
    index?: number,
    playing?: boolean,
    class?: string
} & TrackContext) {
    const { track, index, albumArtist, showDuration, onContextMenu } = props;
    const active = track.uuid != null && currentId.value === track.uuid;
    const playing = active && isPlaying.value;
    const name = track.name.value;
    const artists = artistNames(track);
    const showArtist = Boolean(artists) && !trackArtistsMatchAlbum(track, albumArtist);
    const dur = track.duration?.value ?? 0;
    const setUuid = track.set ?? undefined;
    const artistUuid = track.artists.value[0] ?? undefined;

    function onDblClick() {
        if (track.uuid == null) return;
        playTrack(String(track.uuid), {
            title: name,
            artist: artists,
            setUuid,
            artistUuid,
        });
    }

    function onContextMenuOpen(event: MouseEvent) {
        event.preventDefault();
        onContextMenu?.(track, event);
    }

    // flufi's Button forwards only onClick/title/etc., so the mouse handlers
    // live on a native wrapper that the button bubbles through.
    return (
        <div class="track-row-wrap" onDblClick={onDblClick} onContextMenu={onContextMenuOpen}>
            <Button
                variant="always-transparent"
                noPadding
                class={addClass(
                    "track",
                    playing && "playing",
                    active && "current",
                    props.class
                )}
                disabled={track.uuid == null}
                onClick={() => {
                    if (track.uuid == null) return;
                    toggleTrack(String(track.uuid), {
                        title: name,
                        artist: artists,
                        setUuid,
                        artistUuid,
                    });
                }}
            >
                <Container horizontal no_gap centered_y class="left">
                    <TrackNumber index={index} />
                    {active && playing ? (
                        <Equaliser size={15} class="equaliser" />
                    ) : active ? (
                        <Pause size={15} class="pause-icon" />
                    ) : (
                        <Play size={15} class="play-icon" />
                    )}
                </Container>
                <Container vertical class="center">
                    <Text class={addClass("name", playing && "playing")} content={track.name} />
                    {showArtist && (
                        <Text class="artist" dim content={artists} />
                    )}
                </Container>
                {showDuration && dur > 0 && (
                    <Text class="duration" content={formatTime(dur)} />
                )}
            </Button>
        </div>
    )
}
