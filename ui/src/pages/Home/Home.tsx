/** Home: a bold, flat greeting, real personalised shelves, then the library.
 *
 * Shelf titles come straight from /api/home. Nothing is relabelled as a Mix,
 * Radio destination or global chart; "Made for you" only appears when the
 * server actually produced that recommendation shelf.
 */
import { useEffect, useState } from "preact/hooks";
import {
    Button, Container, Content, Header2, Header3, Input, Loading, SelectBox, Text,
} from "flufi-ui/components";
import { ArrowDownUp, Disc3, ListFilter, Play, Sparkles } from "lucide-preact";
import { BlobAccent } from "../../components/Playful/BlobAccent";
import { EmptyState } from "../../components/EmptyState/EmptyState";
import { SetCard } from "../../components/Library/Card";
import { TrackList } from "../../components/TrackList/TrackList";
import { API, parseArtistUuid } from "../../common/net/api";
import type { HomeSection, Set, Track } from "../../common/net/types";
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

function queueFor(section: HomeSection) {
    return section.tracks.map(t => ({
        id: t.uuid,
        title: t.name.value,
        artist: t.artists.value.map(u => parseArtistUuid(u).name).join(", "),
        setUuid: t.set ?? undefined,
        artistUuid: t.artists.value[0],
    }));
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
    const [shelves, setShelves] = useState<HomeSection[]>([]);

    useEffect(() => {
        API.listTracks(50).then(setTracks).catch(() => setTracks([]));
        API.home()
            .then(d => setShelves(d.sections.filter(s => s.tracks.length > 0).slice(0, 4)))
            .catch(() => { /* personalised shelves are optional */ });
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
            if (list.length > 0) playQueue(list, 0);
        } catch {
            setError("Could not start that album.");
        }
    }

    function playShelf(section: HomeSection) {
        const list = queueFor(section);
        if (list.length) playQueue(list, 0);
    }

    const [hero, second, ...otherShelves] = shelves;
    const skeletonCount = loading && albums.length === 0 ? Math.min(total || PAGE, PAGE) : 0;
    const secondaryAlbum = albums[0] ?? null;

    return (
        <Content class="home">
            <Container extra_gap>
                <div class="home-hero-row">
                    {hero ? (
                        <Container class="home-hero hero-primary">
                            <BlobAccent id="blob-3" class="hero-blob blob-tertiary" />
                            <div class="hero-badge"><Sparkles size={18} /> Your music</div>
                            <Header2 class="hero-title">{hero.title}</Header2>
                            <Text dim content="A real shelf from your listening history — press play whenever you're ready." />
                            <div class="hero-actions">
                                <Button variant="accent" class="hero-play" onClick={() => playShelf(hero)}>
                                    <Play size={18} /> Play {hero.title}
                                </Button>
                                <Text dim content={`${hero.tracks.length} tracks`} />
                            </div>
                        </Container>
                    ) : (
                        <Container class="home-hero hero-primary">
                            <BlobAccent id="blob-3" class="hero-blob blob-tertiary" />
                            <div class="hero-badge"><Sparkles size={18} /> Your library</div>
                            <Header2 class="hero-title">Start with your music</Header2>
                            <Text dim content="Add music and real shelves built from plays and likes appear here." />
                            <div class="hero-actions">
                                <a class="button variant-accent hero-play" href="/upload">Add music</a>
                            </div>
                        </Container>
                    )}

                    <Container class="home-hero hero-secondary">
                        <BlobAccent id="blob-5" class="hero-blob blob-secondary" />
                        {second ? (
                            <>
                                <div class="hero-badge"><Disc3 size={16} /> From your listening</div>
                                <Header3 class="hero-title">{second.title}</Header3>
                                <Text dim content="Built from plays and likes on this server." />
                                <div class="hero-actions">
                                    <Button variant="panel" class="hero-play" onClick={() => playShelf(second)}>
                                        <Play size={16} /> Play
                                    </Button>
                                    <Text dim content={`${second.tracks.length} tracks`} />
                                </div>
                            </>
                        ) : secondaryAlbum ? (
                            <>
                                <div class="hero-badge"><Disc3 size={16} /> From your library</div>
                                <Header3 class="hero-title">{artistNames(secondaryAlbum) || secondaryAlbum.name.value}</Header3>
                                <Text dim content={`${secondaryAlbum.tracks.value.length} tracks in this album.`} />
                                <div class="hero-actions">
                                    <Button variant="panel" class="hero-play" onClick={() => void playAlbum(secondaryAlbum)}>
                                        <Play size={16} /> Play album
                                    </Button>
                                </div>
                            </>
                        ) : (
                            <>
                                <div class="hero-badge"><Disc3 size={16} /> Your library</div>
                                <Header3 class="hero-title">Albums live here</Header3>
                                <Text dim content="Nothing is invented while your library is empty." />
                                <div class="hero-actions">
                                    <a class="button variant-panel hero-play" href="/playlists">Open library</a>
                                </div>
                            </>
                        )}
                    </Container>
                </div>

                {otherShelves.length > 0 && (
                    <Container class="home-shelves">
                        <Container horizontal centered_y class="shelves-head">
                            <Header3>From your listening</Header3>
                            {otherShelves.length > 0 && (
                                <Text dim content="Built from plays and likes on this server" />
                            )}
                        </Container>
                        <div class="shelf-chips">
                            {otherShelves.map(section => (
                                <Button
                                    key={section.title}
                                    variant="panel"
                                    class="shelf-chip"
                                    title={`Play ${section.title}`}
                                    onClick={() => playShelf(section)}
                                >
                                    <Play size={14} /> {section.title}
                                </Button>
                            ))}
                        </div>
                        {otherShelves.map(section => (
                            <Container key={section.title} class="home-shelf">
                                <Container horizontal centered_y class="shelf-head">
                                    <Header3>{section.title}</Header3>
                                    <Button variant="panel" title={`Play ${section.title}`} onClick={() => playShelf(section)}>
                                        <Play size={14} /> Play
                                    </Button>
                                </Container>
                                <TrackList tracks={section.tracks.slice(0, 8)} showDuration={true} />
                            </Container>
                        ))}
                    </Container>
                )}

                <Container class="home-library">
                    <Header2>Albums</Header2>
                    <Container horizontal centered_y class="album-controls">
                        <label class="control-with-icon">
                            <ListFilter size={15} aria-hidden="true" />
                            <Input
                                class="album-filter"
                                placeholder="Filter albums"
                                value={query}
                                onInput={changeQuery}
                            />
                        </label>
                        <label class="control-with-icon">
                            <ArrowDownUp size={15} aria-hidden="true" />
                            <SelectBox
                                class="album-sort"
                                options={SORTS}
                                value={sort}
                                onChange={changeSort}
                            />
                        </label>
                        <Button
                            variant={singles ? "accent" : "panel"}
                            title="Include one-song albums"
                            onClick={toggleSingles}
                        >
                            <Disc3 size={15} /> Singles
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
                                <EmptyState
                                    icon={<Disc3 size={22} />}
                                    title={query ? "No matching albums" : "No albums yet"}
                                    body={query
                                        ? `Nothing matches “${query}”. Try a different filter.`
                                        : "Add music from the top bar and it will show up here."}
                                />
                            )
                            : (
                                <div class="album-grid">
                                    {albums.map(a => (
                                        <SetCard
                                            key={a.uuid}
                                            set={a}
                                            subtitle={artistNames(a) || a.artistName}
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

                <Container class="home-songs">
                    <Header2>Songs</Header2>
                    <Loading loaded={tracks != null}>
                        {() => <TrackList tracks={tracks!} />}
                    </Loading>
                </Container>
            </Container>
        </Content>
    )
}
