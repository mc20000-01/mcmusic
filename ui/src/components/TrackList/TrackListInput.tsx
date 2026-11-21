/** Track list with add/remove/reorder controls for playlists and sets.
 */
import { signal, Signal, useSignal } from "@preact/signals";
import { Container, Text, UploadBox } from "flufi-ui/components";
import { addClass, tryExtractName } from "flufi-ui/common";
import { isSignal, type Option, type Signalish, type Uuid } from "flufi-ui/types";
import { TrackInput } from "../Track/Track";
import { UploadCloud } from "lucide-preact";
import type { Track } from "../../common/net/types";
import { API } from "../../common/net/api";

import "./style.css";

// TODO: make dragging between tracks better

export function TrackListInput(props: {
    class?: string,
    tracks?: Signalish<Track[]>,
    dirty?: Signal<boolean>
    artists?: Uuid[],
    uploadData?: {
        set: Uuid
    }
}) {
    let tracks: Signal<Track[]>;
    if (props.tracks == null)
        tracks = useSignal<Track[]>([]);
    else if (isSignal(props.tracks))
        tracks = props.tracks as Signal<Track[]>;
    else
        tracks = useSignal(props.tracks as Track[]);
    
    const dragIndex = useSignal<Option<number>>(null);
    
    function reorder(from: number, to: number) {
        if (from == to)
            return;
        
        const newTracks = [...tracks.peek()];
        
        const [moved] = newTracks.splice(from, 1);
        
        newTracks.splice(to, 0, moved);
        
        tracks.value = newTracks;
        
        if (props.dirty)
            props.dirty.value = true;
    }
    
    return (
        <Container class={addClass(
            "track-list",
            "track-list-input",
            "upload",
            props.class
        )}>
            {props.uploadData != null && (
                <UploadBox
                    class="less-padding"
                    addFile={async (f) => {
                        console.log(f, tryExtractName(f.name));
                        
                        tracks.value = [
                            ...tracks.peek(),
                            await API.getTrack(await API.uploadTrack({
                                name: tryExtractName(f.name),
                                artists: props.artists ?? [],
                                file: f,
                                set: props.uploadData?.set
                            }))
                        ];
                        
                        if (props.dirty)
                            props.dirty.value = true;
                    }}
                >
                    <UploadCloud size={20} />
                    <Text content="Drag or drop audio files here, or click to browse" />
                </UploadBox>
            )}
            <Container class="tracks">
                {tracks.value.map((track, index) => (
                    <TrackInput
                        key={index}
                        track={track as any}
                        index={index}
                        onDelete={() => {
                            tracks.value = tracks.value.toSpliced(index, 1);
                        }}
                        onDragStart={() => {
                            dragIndex.value = index;
                        }}
                        onTrackDroppedOn={() => {
                            if (dragIndex.peek())
                                reorder(dragIndex.peek()!, index);
                            
                            dragIndex.value = null;
                        }}
                    />
                ))}
            </Container>
        </Container>
    )
}

export type UploadTrackListTrack = {
    name: Signal<string>,
    artists: Signal<Uuid[]>,
    file: Signal<Option<File>>
};

export function UploadTrackListInput(props: {
    class?: string,
    tracks?: Signalish<UploadTrackListTrack[]>,
    dirty?: Signal<boolean>
    artists?: Uuid[]
}) {
    let tracks: Signal<UploadTrackListTrack[]>;
    if (props.tracks == null)
        tracks = useSignal<UploadTrackListTrack[]>([]);
    else if (isSignal(props.tracks))
        tracks = props.tracks as Signal<UploadTrackListTrack[]>;
    else
        tracks = useSignal(props.tracks as UploadTrackListTrack[]);
    
    const dragIndex = useSignal<Option<number>>(null);
    
    function reorder(from: number, to: number) {
        if (from == to)
            return;
        
        const newTracks = [...tracks.peek()];
        
        const [moved] = newTracks.splice(from, 1);
        
        newTracks.splice(to, 0, moved);
        
        tracks.value = newTracks;
        
        if (props.dirty)
            props.dirty.value = true;
    }
    
    return (
        <Container class={addClass(
            "track-list",
            "track-list-input",
            "upload",
            props.class
        )}>
            <UploadBox
                class="less-padding"
                addFile={(f) => {
                    console.log(f, tryExtractName(f.name));
                    
                    tracks.value = [
                        ...tracks.peek(),
                        {
                            name: signal(tryExtractName(f.name)),
                            artists: signal(props.artists ?? []),
                            file: signal(f)
                        }
                    ];
                    
                    if (props.dirty)
                        props.dirty.value = true;
                }}
            >
                <UploadCloud size={20} />
                <p>Drag or drop audio files here, or click to browse</p>
            </UploadBox>
            <Container class="tracks">
                {tracks.value.map((track, index) => (
                    <TrackInput
                        key={index}
                        track={track as any}
                        index={index}
                        onDelete={() => {
                            tracks.value = tracks.value.toSpliced(index, 1);
                        }}
                        onDragStart={() => {
                            dragIndex.value = index;
                        }}
                        onTrackDroppedOn={() => {
                            if (dragIndex.peek())
                                reorder(dragIndex.peek()!, index);
                            
                            dragIndex.value = null;
                        }}
                    />
                ))}
            </Container>
        </Container>
    )
}
