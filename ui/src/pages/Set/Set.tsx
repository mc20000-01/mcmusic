/** Album page: cover, artist link, play control and the album's track list.
 */
import { Button, Container, Content, Loading, Text } from "flufi-ui";
import { useEffect, useState } from "preact/hooks";
import type { Artist, Set, Track } from "../../common/net/types";
import { openContextMenu } from "flufi-ui/components";
import { API } from "../../common/net/api";
import type { RoutePropsForPath } from "preact-iso";
import { ArtistPfp } from "../../components/Library/Image";
import { SetCover } from "../../components/Library/Image";
import { titleCase } from "../../common";
import { TrackList } from "../../components/TrackList/TrackList";
import { currentId, enqueueTrack, isPlaying, playQueue, playTrack, togglePlay } from "../../common/player";
import { parseArtistUuid } from "../../common/net/api";
import { ListPlus, Pause, Play, Shuffle } from "lucide-preact";

import "./style.css";

function trackArtists(track: Track): string {
    return track.artists.value.map(u => parseArtistUuid(u).name).join(", ");
}

function albumArtistName(set: Set): string {
    return set.artistName || parseArtistUuid(set.artist).name;
}

function totalDuration(tracks: Track[]): number {
    return tracks.reduce((sum, t) => sum + (t.duration.value ?? 0), 0);
}

export function SetPage(props: RoutePropsForPath<"/set/:uuid">) {
    const [artist, setArtist] = useState<Artist | null>(null);
    const [set, setSet] = useState<Set | null>(null);
    const [playlists, setPlaylists] = useState<{ id: number; name: string }[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        setSet(null);
        setArtist(null);
        setError(null);

        API.getSet(props.uuid)
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

        API.listPlaylists()
            .then(d => {
                if (cancelled) return;
                setPlaylists((d.playlists ?? []).map((p: { id: number; name: string }) => ({ id: p.id, name: p.name })));
            })
            .catch(() => { /* playlists are optional */ });

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
                    const s = set!;
                    const tracks = s.tracks.value;
                    const first = tracks[0];
                    const playing = first != null
                        && currentId.value === first.uuid
                        && isPlaying.value;
                    const albArtist = albumArtistName(s);
                    const mins = Math.floor(totalDuration(tracks) / 60);
                    const secs = Math.floor(totalDuration(tracks) % 60);
                    const year = first?.year.value ?? null;

                    function openPlaylistMenu(trackUuid: string) {
                        const items = playlists.map(p => ({
                            type: "button" as const,
                            label: p.name,
                            click: () => API.addToPlaylist(p.id, trackUuid),
                        }));
                        if (items.length === 0) {
                            openContextMenu([
                                {
                                    type: "button" as const,
                                    label: "No playlists yet",
                                    icon: <ListPlus size={14} />,
                                    click: () => { window.location.href = "/playlists"; },
                                },
                            ]);
                            return;
                        }
                        openContextMenu(items);
                    }

                    function onRowContextMenu(track: Track, event: MouseEvent) {
                        const name = track.name.value;
                        const artists = trackArtists(track);
                        openContextMenu([
                            {
                                type: "button" as const,
                                label: "Play track",
                                icon: <Play size={14} />,
                                click: () => playTrack(track.uuid, { title: name, artist: artists, setUuid: s.uuid, artistUuid: track.artists.value[0] ?? undefined }),
                            },
                            {
                                type: "button" as const,
                                label: "Add to queue",
                                icon: <ListPlus size={14} />,
                                click: () => enqueueTrack(track.uuid, {
                                    title: name,
                                    artist: artists,
                                    setUuid: s.uuid,
                                    artistUuid: track.artists.value[0] ?? undefined,
                                }),
                            },
                            {
                                type: "separator" as const,
                            },
                            {
                                type: "button" as const,
                                label: "Add to playlist",
                                icon: <ListPlus size={14} />,
                                click: () => openPlaylistMenu(track.uuid),
                            },
                            {
                                type: "separator" as const,
                            },
                            {
                                type: "button" as const,
                                label: "Go to artist",
                                click: () => {
                                    const first = track.artists.value[0];
                                    if (first) window.location.href = `/artist/${first}`;
                                },
                            },
                        ], event);
                    }

                    return (
                        <Container extra_gap>
                            <Container horizontal class="top">
                                <SetCover set={s} size={180} class="cover" />
                                <Container class="info">
                                    <Text dim class="kind" content={titleCase(s.kind.value)} />
                                    <h1 class="album-title" title={s.name.value}>
                                        {s.name.value}
                                    </h1>
                                    <Container horizontal centered_y class="artist-credit">
                                        <Text dim content="by" />
                                        <div class="artist-wrap">
                                            {artist
                                                ? <a
                                                    href={`/artist/${artist.uuid}`}
                                                    class="artist-link"
                                                    title={artist.name.value}
                                                >
                                                    <ArtistPfp artist={artist} size={28} class="artist-pfp" />
                                                    <span class="artist-name">{artist.name.value}</span>
                                                </a>
                                                : (
                                                    <span class="artist-name">{s.artistName ?? ""}</span>
                                                )}
                                        </div>
                                        {!playing && first && (
                                            <Button
                                                variant="accent"
                                                class="play-album"
                                                title="Play album"
                                                onClick={() => {
                                                    const list = tracks.map(t => ({
                                                        id: t.uuid,
                                                        title: t.name.value,
                                                        artist: trackArtists(t),
                                                        setUuid: s.uuid,
                                                        artistUuid: t.artists.value[0] ?? undefined,
                                                    }));
                                                    playQueue(list, 0);
                                                }}
                                            >
                                                <Play size={16} /> Play
                                            </Button>
                                        )}
                                        {playing && first && (
                                            <Button
                                                variant="accent"
                                                class="play-album"
                                                title="Pause album"
                                                onClick={() => togglePlay()}
                                            >
                                                <Pause size={16} /> Pause
                                            </Button>
                                        )}
                                        <Button
                                            variant="panel"
                                            class="shuffle-album"
                                            title="Shuffle album"
                                            onClick={() => {
                                                const t = tracks[Math.floor(Math.random() * tracks.length)];
                                                playTrack(t.uuid, {
                                                    title: t.name.value,
                                                    artist: trackArtists(t),
                                                    setUuid: s.uuid,
                                                    artistUuid: t.artists.value[0] ?? undefined,
                                                });
                                            }}
                                        >
                                            <Shuffle size={16} /> Shuffle
                                        </Button>
                                        <Button
                                            variant="panel"
                                            class="add-playlist-album"
                                            title="Add album to playlist"
                                            onClick={() => first && openPlaylistMenu(first.uuid)}
                                        >
                                            <ListPlus size={16} /> Add to playlist
                                        </Button>
                                    </Container>
                                    <Container horizontal class="meta">
                                        {year && <Text dim content={String(year)} />}
                                        {year && <Text dim content=" · " />}
                                        <Text dim content={`${tracks.length} track${tracks.length == 1 ? "" : "s"}`} />
                                        <Text dim content={` · ${mins}:${String(secs).padStart(2, "0")}`} />
                                    </Container>
                                </Container>
                            </Container>
                            <TrackList
                                tracks={s.tracks}
                                albumArtist={albArtist}
                                showDuration={true}
                                onContextMenu={onRowContextMenu}
                            />
                        </Container>
                    );
                }}
            </Loading>
        </Content>
    )
}
