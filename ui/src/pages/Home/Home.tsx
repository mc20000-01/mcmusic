/** Home: the albums grid plus the most recently added tracks.
 */
import { useEffect, useState } from "preact/hooks";
import { Button, Container, Content, Header2, Input, Loading, SelectBox, Text } from "flufi-ui/components";
import { SetCard } from "../../components/Library/Card";
import { TrackList } from "../../components/TrackList/TrackList";
import { API } from "../../common/net/api";
import type { Set, Track } from "../../common/net/types";
import { parseArtistUuid } from "../../common/net/api";
import { playQueue } from "../../common/player";

import "./style.css";

const PAGE = 60;

const SORTS = [
    { value: "name", label: "A–Z" },
    { value: "artist", label: "Artist" },
    { value: "recent", label: "Recently added" },
];

function artistNames(set: Set): string {
    const names: string[] = [];
    for (const track of set.tracks.value) {
        for (const uuid of track.artists.value) {
            const name = parseArtistUuid(uuid).name;
            if (!names.includes(name)) names.push(name);
        }
    }
    return names.join(", ") || set.artistName || "";
}

export function HomePage() {
    const [albums, setAlbums] = useState<Set[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [query, setQuery] = useState("");
    const [sort, setSort] = useState("name");
    const [singles, setSingles] = useState(false);
    const [count, setCount] = useState(PAGE);

    const [tracks, setTracks] = useState<Track[] | null>(null);

    useEffect(() => {
        API.listTracks(50).then(setTracks).catch(() => setTracks([]));
    }, []);

    useEffect(() => {
        let cancelled = false;
        const timer = setTimeout(() => {
            setLoading(true);
            API.listAlbums({
                limit: count,
                offset: 0,
                q: query.trim(),
                sort,
                minTracks: singles ? 1 : 2,
            })
                .then((r) => {
                    if (cancelled) return;
                    setAlbums(r.albums);
                    setTotal(r.total);
                    setError(null);
                })
                .catch(() => {
                    if (cancelled) return;
                    setAlbums([]);
                    setTotal(0);
                    setError("Could not load albums. Check the connection and try again.");
                })
                .finally(() => {
                    if (!cancelled) setLoading(false);
                });
        }, query ? 250 : 0);

        return () => {
            cancelled = true;
            clearTimeout(timer);
        };
    }, [query, sort, singles, count]);

    function changeQuery(value: string) {
        setQuery(value);
        setCount(PAGE);
    }

    function changeSort(value: string | null) {
        setSort(value ?? "name");
        setCount(PAGE);
    }

    function toggleSingles() {
        setSingles(v => !v);
        setCount(PAGE);
    }

    async function playAlbum(set: Set) {
        try {
            const full = await API.getSet(set.uuid);
            const ts = full.tracks.value;
            if (ts.length === 0) return;
            const list = ts
                .filter(t => t.uuid)
                .map(t => ({
                    id: t.uuid,
                    title: t.name.value,
                    artist: t.artists.value.map(u => parseArtistUuid(u).name).join(", "),
                    setUuid: full.uuid,
                    artistUuid: t.artists.value[0] ?? null,
                }));
            if (list.length > 0) {
                playQueue(list, 0);
            }
        } catch {
            setError("Could not start that album.");
        }
    }

    // Skeleton cards shown while the first page of albums loads.
    const skeletonCount = loading && albums.length === 0 ? Math.min(total || PAGE, PAGE) : 0;

    return (
        <Content class="home">
            <Container extra_gap>
                <Container>
                    <Header2>Albums</Header2>
                    <Container horizontal centered_y class="album-controls">
                        <Input
                            class="album-filter"
                            placeholder="Filter albums"
                            value={query}
                            onInput={changeQuery}
                        />
                        <SelectBox
                            class="album-sort"
                            options={SORTS}
                            value={sort}
                            onChange={changeSort}
                        />
                        <Button
                            variant={singles ? "accent" : "panel"}
                            title="Include one-song albums"
                            onClick={toggleSingles}
                        >
                            Singles
                        </Button>
                        {!loading && (
                            <Text dim content={`${total} album${total == 1 ? "" : "s"}`} />
                        )}
                    </Container>

                    {error && <Text class="error" content={error} />}

                    {loading && albums.length === 0
                        ? (
                            <div class="album-grid skeleton-grid">
                                {[...Array(skeletonCount)].map((_, i) => (
                                    <div key={i} class="skeleton-card">
                                        <div class="skeleton-cover" />
                                        <div class="skeleton-title" />
                                        <div class="skeleton-sub" />
                                    </div>
                                ))}
                            </div>
                        )
                        : albums.length === 0
                            ? (
                                <Text
                                    dim
                                    content={query
                                        ? `No albums match “${query}”.`
                                        : "No albums yet. Add music to get started."}
                                />
                            )
                            : (
                                <div class="album-grid">
                                    {albums.map(a => (
                                        <SetCard
                                            key={a.uuid.value}
                                            set={a}
                                            subtitle={a.artistName}
                                            onPlay={() => playAlbum(a)}
                                        />
                                    ))}
                                </div>
                            )}

                    {!loading && albums.length > 0 && albums.length < total && (
                        <Button
                            variant="panel"
                            class="load-more"
                            onClick={() => setCount(c => c + PAGE)}
                        >
                            Load more
                        </Button>
                    )}
                </Container>

                <Container>
                    <Header2>Songs</Header2>
                    <Loading loaded={tracks != null}>
                        {() => <TrackList tracks={tracks!} />}
                    </Loading>
                </Container>
            </Container>
        </Content>
    )
}
