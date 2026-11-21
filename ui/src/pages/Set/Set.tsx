/** Album page: cover, artist link, play control and the album's track list.
 */
import { Button, Container, Content, Loading, Text, type Uuid } from "flufi-ui";
import { useEffect, useState } from "preact/hooks";
import type { Artist, Set, Track } from "../../common/net/types";

import { API } from "../../common/net/api";
import type { RoutePropsForPath } from "preact-iso";
import { ArtistLink } from "../../components/Library/Link";
import { SetCover } from "../../components/Library/Image";
import { titleCase } from "../../common";
import { TrackList } from "../../components/TrackList/TrackList";
import { currentId, isPlaying, playTrack, togglePlay } from "../../common/player";
import { parseArtistUuid } from "../../common/net/api";
import { Pause, Play } from "lucide-preact";

import "./style.css";

function trackArtists(track: Track): string {
    return track.artists.value.map(u => parseArtistUuid(u).name).join(", ");
}

export function SetPage(props: RoutePropsForPath<"/set/:uuid">) {
    const [artist, setArtist] = useState<Artist | null>(null);
    const [set, setSet] = useState<Set | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        setSet(null);
        setArtist(null);
        setError(null);

        API.getSet(props.uuid as Uuid)
            .then(async (r) => {
                if (cancelled) return;
                setSet(r);
                if (r.tracks.value.length == 0) {
                    setError("This album is empty or no longer exists.");
                    return;
                }
                const a = await API.getArtist(r.artist).catch(() => null);
                if (!cancelled) setArtist(a);
            })
            .catch(() => {
                if (!cancelled) setError("Could not load this album. Check the connection and try again.");
            });

        return () => { cancelled = true; };
    }, [props.uuid]);

    if (error) {
        return (
            <Content class="set">
                <Container class="set-error">
                    <Text content={error} />
                    <Button
                        variant="panel"
                        onClick={() => window.location.reload()}
                    >
                        Try again
                    </Button>
                </Container>
            </Content>
        );
    }

    return (
        <Content class="set">
            <Loading loaded={set !== null}>
                {() => {
                    const tracks = set!.tracks.value;
                    const first = tracks[0];
                    const playing = first != null
                        && currentId.value === first.uuid
                        && isPlaying.value;

                    return (
                        <Container extra_gap>
                            <Container horizontal class="top">
                                <SetCover set={set!} size={180} class="cover" />
                                <Container class="info">
                                    <Text dim content={titleCase(set!.kind.value)} />
                                    <h1 class="album-title" title={set!.name.value}>
                                        {set!.name.value}
                                    </h1>
                                    {artist
                                        ? <ArtistLink artist={artist} />
                                        : <Text dim content={set!.artistName ?? ""} />}
                                    <Text
                                        dim
                                        content={`${tracks.length} track${tracks.length == 1 ? "" : "s"}`}
                                    />
                                    {first && (
                                        <Button
                                            variant="accent"
                                            class="play-album"
                                            title={playing ? "Pause album" : "Play album"}
                                            onClick={() => playing
                                                ? togglePlay()
                                                : playTrack(first.uuid, {
                                                    title: first.name.value,
                                                    artist: trackArtists(first),
                                                })}
                                        >
                                            {playing ? <Pause size={16} /> : <Play size={16} />}
                                            {playing ? "Pause" : "Play"}
                                        </Button>
                                    )}
                                </Container>
                            </Container>
                            <TrackList tracks={set!.tracks} />
                        </Container>
                    );
                }}
            </Loading>
        </Content>
    )
}
