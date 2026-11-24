/** Liked tracks, with a one-click “play all” and per-track unlike. */
import { useEffect, useState } from "preact/hooks";
import { Button, Container, Content, Header2, Loading, openContextMenu, Text } from "flufi-ui/components";
import { Heart, Play } from "lucide-preact";
import { API } from "../../common/net/api";
import type { Track } from "../../common/net/types";
import { playQueue } from "../../common/player";
import { TrackList } from "../../components/TrackList/TrackList";
import { parseArtistUuid } from "../../common/net/api";

import "./style.css";

function artistNames(track: Track): string {
    return track.artists.value.map(u => parseArtistUuid(u).name).join(", ");
}

export function LikesPage() {
    const [tracks, setTracks] = useState<Track[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    function load() {
        API.likes()
            .then(r => { setTracks(r); setError(null); })
            .catch(e => { setError(String(e)); setTracks([]); });
    }
    useEffect(load, []);

    async function unlike(uuid: string) {
        try {
            await API.like(uuid);
            setTracks(rows => rows?.filter(t => t.uuid !== uuid) ?? rows);
        } catch { /* keep the row on failure */ }
    }

    function playAll() {
        if (!tracks?.length) return;
        playQueue(tracks.map(t => ({
            id: t.uuid,
            title: t.name.value,
            artist: artistNames(t),
            setUuid: t.set ?? undefined,
            artistUuid: t.artists.value[0],
        })), 0);
    }

    return (
        <Content class="likes-page">
            <Container extra_gap>
                <Container horizontal centered_y class="likes-head">
                    <Heart size={20} />
                    <Header2>Liked songs</Header2>
                    {tracks && tracks.length > 0 && (
                        <Button variant="accent" onClick={playAll}>
                            <Play size={16} /> Play all
                        </Button>
                    )}
                </Container>
                {error && <Text class="error" content={error} />}
                <Loading loaded={tracks != null}>
                    {() => tracks!.length === 0 ? (
                        <Text dim content="Nothing liked yet. Tap the heart on a track or press L while it plays." />
                    ) : (
                        <TrackList
                            tracks={tracks!}
                            showDuration={true}
                            onContextMenu={(track, event) => {
                                openContextMenu([
                                    { type: "button", label: "Unlike", icon: <Heart size={14} />,
                                      click: () => unlike(String(track.uuid)) },
                                    { type: "separator" },
                                    { type: "button", label: "Refresh", click: load },
                                ], event);
                            }}
                        />
                    )}
                </Loading>
            </Container>
        </Content>
    );
}
