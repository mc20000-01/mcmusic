/** A single track row: number/play affordance, title, artist, duration and
 * per-row actions. The whole row is a transparent flufi-ui Button, so it is
 * keyboard-focusable and every child stays a flufi-ui component.
 */
import type { Signal } from "@preact/signals";
import type { Track } from "../../common/net/types";
import { Button, Container, IconButton, If, Input, Text } from "flufi-ui/components";
import { addClass } from "flufi-ui/common";
import type { Uuid } from "flufi-ui/types";
import { TrackNumber } from "../TrackNumber/TrackNumber";
import { GripVertical, Pause, Play, X } from "lucide-preact";
import { Equaliser } from "../Equaliser/Equaliser";
import { currentId, isPlaying, toggleTrack } from "../../common/player";
import { parseArtistUuid } from "../../common/net/api";

import "./style.css";

// peak types???
export type TrackWithOptionalUuid = Track & { uuid?: Uuid };
export type TrackWithOptionalUuidAndSet = TrackWithOptionalUuid & { set?: string };

function artistNames(track: TrackWithOptionalUuid): string {
    const list = track.artists?.value ?? [];
    return list.map((u) => parseArtistUuid(u).name).join(", ");
}

export function TrackElem(props: {
    track: TrackWithOptionalUuid,
    index?: number,
    playing?: boolean,
    class?: string
}) {
    const active = props.track.uuid != null && currentId.value === props.track.uuid;
    const playing = active && isPlaying.value;

    return (
        <Button
            variant="always-transparent"
            noPadding
            class={addClass(
                "track",
                playing && "playing",
                props.class
            )}
            disabled={props.track.uuid == null}
            onClick={() => {
                if (props.track.uuid == null) return;
                toggleTrack(String(props.track.uuid), {
                    title: props.track.name.value,
                    artist: artistNames(props.track),
                });
            }}
        >
            <Container horizontal no_gap centered_y class="left">
                <TrackNumber index={props.index} />
                {playing ? <Pause size={15} /> : <Play size={15} />}
                {playing && <Equaliser size={15} />}
            </Container>
            <Text class="name" content={props.track.name} />
            <Text class="artist" dim content={artistNames(props.track)} />
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
