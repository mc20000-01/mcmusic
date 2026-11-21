/** Track list with a header row; clicking a row plays it and replaces the queue.
 */
import { useSignal, type Signal } from "@preact/signals";
import type { Track } from "../../common/net/types";
import { isSignal, type Signalish } from "flufi-ui/types";
import { TrackElem } from "../Track/Track";
import { Container } from "flufi-ui";

export function TrackList(props: {
    tracks: Signalish<Track[]>
}) {
    let tracks: Signal<Track[]>;
    if (props.tracks == null)
        tracks = useSignal<Track[]>([]);
    else if (isSignal(props.tracks))
        tracks = props.tracks as Signal<Track[]>;
    else
        tracks = useSignal(props.tracks as Track[]);
    
    return (
        <Container class="track-list">
            {tracks.value.map((t, i) => (
                <TrackElem index={i} track={t} />
            ))}
        </Container>
    )
}