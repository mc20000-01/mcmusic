/** Track list with a header row; clicking a row plays it and replaces the queue.
 */
import { useSignal, type Signal } from "@preact/signals";
import type { Track } from "../../common/net/types";
import { isSignal, type Signalish } from "flufi-ui/types";
import { TrackElem, type TrackContext } from "../Track/Track";
import { Container } from "flufi-ui";

export function TrackList(props: {
    tracks: Signalish<Track[]>
    /** Album artist name; hides matching artists on each row. */
    albumArtist?: string;
    /** Show a right-aligned duration column. */
    showDuration?: boolean;
    /** Right-click handler that opens a context menu. */
    onContextMenu?: (track: Track, event: MouseEvent) => void;
}) {
    let tracks: Signal<Track[]>;
    if (props.tracks == null)
        tracks = useSignal<Track[]>([]);
    else if (isSignal(props.tracks))
        tracks = props.tracks as Signal<Track[]>;
    else
        tracks = useSignal(props.tracks as Track[]);

    const ctx: TrackContext = {
        albumArtist: props.albumArtist,
        showDuration: props.showDuration,
        onContextMenu: props.onContextMenu
            ? (t: Track, e: MouseEvent) => props.onContextMenu!(t, e)
            : undefined,
    };

    return (
        <Container class="track-list">
            {tracks.value.map((t, i) => (
                <TrackElem key={t.uuid} index={i} track={t} {...ctx} />
            ))}
        </Container>
    )
}
