import { useEffect, useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import type { RoutePropsForPath } from "preact-iso";
import { useLocation } from "preact-iso";
import {
    Container, Content, FormalInput, Header2, IconButton, Input, Loading, Text, TextIconButton
} from "flufi-ui/components";
import { Pencil, Plus, Search, Trash2, X } from "lucide-preact";
import { API } from "../../common/net/api";
import type { Track } from "../../common/net/types";
import { TrackElem } from "../../components/Track/Track";

// A track row in a playlist: flufi's Track on the left, remove on the right.
// `.playlist-row` is the only custom rule needed (flex sizing).
import "./style.css";

type Playlist = { id: number; name: string; tracks: Track[] };
type Result = { id: string; title: string; artist: string };

export function PlaylistPage(props: RoutePropsForPath<"/playlist/:id">) {
    const loc = useLocation();
    const id = props.id;
    const [playlist, setPlaylist] = useState<Playlist | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [editing, setEditing] = useState(false);
    const name = useSignal("");
    const query = useSignal("");
    const [results, setResults] = useState<Result[]>([]);

    function load() {
        API.playlistTracks(id)
            .then(p => {
                setPlaylist(p);
                name.value = p.name;
            })
            .catch(e => setError(e instanceof Error ? e.message : String(e)));
    }

    useEffect(load, [id]);

    // Track search for "Add songs", debounced like the topbar search.
    useEffect(() => {
        const q = query.value.trim();
        if (!q) { setResults([]); return; }
        const timer = setTimeout(() => {
            API.search(q, ["track"])
                .then(items => setResults(items
                    .filter((i): i is Extract<typeof i, { type: "track" }> => i.type == "track")
                    .slice(0, 8)
                    .map(i => ({
                        id: i.uuid,
                        title: i.track.name.value,
                        artist: i.artist?.name.value ?? "",
                    }))))
                .catch(() => setResults([]));
        }, 250);
        return () => clearTimeout(timer);
    }, [query.value]);

    async function act(fn: () => Promise<unknown>) {
        setError(null);
        try {
            await fn();
            load();
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    return (
        <Content class="playlist">
            <Loading loaded={playlist != null}>
                {() => (
                    <Container extra_gap>
                        <Container horizontal centered_y wrap>
                            {editing
                                ? <Input value={name} />
                                : <Header2>{playlist!.name}</Header2>}
                            {editing ? (
                                <TextIconButton
                                    variant="accent"
                                    disabled={name.value.trim() == ""}
                                    onClick={() => act(async () => {
                                        await API.renamePlaylist(id, name.peek().trim());
                                        setEditing(false);
                                    })}
                                >
                                    Save
                                </TextIconButton>
                            ) : (
                                <IconButton title="Rename" onClick={() => setEditing(true)}>
                                    <Pencil size={16} />
                                </IconButton>
                            )}
                            <IconButton
                                title="Delete playlist"
                                variant="danger-subtle"
                                onClick={() => act(async () => {
                                    await API.deletePlaylist(id);
                                    loc.route("/playlists");
                                })}
                            >
                                <Trash2 size={16} />
                            </IconButton>
                        </Container>

                        <Text dim content={`${playlist!.tracks.length} track${playlist!.tracks.length == 1 ? "" : "s"}`} />
                        {error && <Text class="error" content={error} />}

                        {playlist!.tracks.length == 0
                            ? <Text dim content="Empty playlist — add songs below." />
                            : playlist!.tracks.map((t, i) => (
                                <Container horizontal centered_y class="playlist-row">
                                    <TrackElem track={t} index={i} />
                                    <IconButton
                                        title="Remove from playlist"
                                        variant="danger-subtle"
                                        onClick={() => act(() => API.removeFromPlaylist(id, t.uuid))}
                                    >
                                        <X size={14} />
                                    </IconButton>
                                </Container>
                            ))}

                        <Container extra_gap>
                            <Header2>Add songs</Header2>
                            <FormalInput label="Search the library">
                                <Input value={query} />
                            </FormalInput>
                            {results.map(r => (
                                <Container horizontal centered_y class="playlist-result">
                                    <Search size={15} />
                                    <Text class="grow" content={`${r.title}${r.artist ? " · " + r.artist : ""}`} />
                                    <IconButton
                                        title="Add"
                                        onClick={() => act(async () => {
                                            await API.addToPlaylist(id, r.id);
                                            query.value = "";
                                            setResults([]);
                                        })}
                                    >
                                        <Plus size={16} />
                                    </IconButton>
                                </Container>
                            ))}
                        </Container>
                    </Container>
                )}
            </Loading>
        </Content>
    )
}
