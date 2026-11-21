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
import type { Signal } from "@preact/signals";
import type { Track } from "../../common/net/types";
import { Button, Container, IconButton, If, Text } from "flufi-ui/components";
import { addClass } from "flufi-ui/common";
import type { Uuid } from "flufi-ui/types";
import { TrackNumber } from "../TrackNumber/TrackNumber";
import { GripVertical, Pause, Play, X } from "lucide-preact";
import { Equaliser } from "../Equaliser/Equaliser";
import { currentId, formatTime, isPlaying, playTrack, toggleTrack } from "../../common/player";
import { parseArtistUuid } from "../../common/net/api";

import "./style.css";

// peak types???
export type TrackWithOptionalUuid = Track & { uuid?: Uuid };
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
    const setUuid = track.set ?? null;
    const artistUuid = track.artists.value[0] ?? null;

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

    return (
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
            onDoubleClick={onDblClick}
            onContextMenu={onContextMenuOpen}
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
    )
}

// NOTE: similar to tag component, X only shows when onDelete is assigned
// NOTE: same with dragging
export function TrackInput(props: {
    track: TrackWithOptionalUuidAndSet,
    index?: number,
    name?: Signal<string>,
    dirty?: Signal<boolean>,

    onDelete?: () => void,

    onDragStart?: () => void,
    onDragOver?: () => void,
    onTrackDroppedOn?: () => void

    class?: string
}) {
    return (
        <Container
            other={{
                draggable: props.onDragStart != null,
                onDragStart: () => props.onDragStart?.(),
                onDragOver: (ev: DragEvent) => {
                    ev.preventDefault();
                    props.onDragOver?.();
                },
                onDrop: () => props.onTrackDroppedOn?.(),
            }}
            class={addClass(
                "track",
                "track-input",
                props.class
            )}

        >
            <Container
                horizontal no_gap centered_y
            >
                <If cond={props.onDragStart != null}>
                    <GripVertical class="grip" size={15} />
                </If>
                <TrackNumber index={props.index} />
            </Container>
            <Input dirty={props.dirty} value={props.track.name} class="flat name" />
            {props.onDelete && (
                <IconButton variant="danger-subtle" class="delete" onClick={props.onDelete}>
                    <X size={13} />
                </IconButton>
            )}
        </Container>
    )
}
