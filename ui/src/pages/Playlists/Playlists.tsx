import { useEffect, useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import {
    Container, Content, FormalInput, Header2, Image, Input, LinkButton, Loading, Text, TextIconButton, WrapList
} from "flufi-ui/components";
import { Plus } from "lucide-preact";
import { API, fallbackCover } from "../../common/net/api";

type PlaylistRow = { id: number; name: string; n: number; cover_id: number | null };

/**
 * Playlist grid. The card markup mirrors the library cards in
 * components/Library/Card.tsx, so playlists look like every other collection.
 */
export function PlaylistsPage() {
    const [playlists, setPlaylists] = useState<PlaylistRow[] | null>(null);
    const [error, setError] = useState<string | null>(null);
    const name = useSignal("");

    function load() {
        API.listPlaylists()
            .then(d => setPlaylists(d.playlists ?? []))
            .catch(e => { setError(String(e)); setPlaylists([]); });
    }

    useEffect(load, []);

    async function create() {
        setError(null);
        try {
            await API.createPlaylist(name.peek().trim());
            name.value = "";
            load();
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    return (
        <Content class="playlists">
            <Container extra_gap>
                <Header2>Playlists</Header2>
                <Container horizontal centered_y>
                    <FormalInput label="New playlist">
                        <Input value={name} onEnter={create} />
                    </FormalInput>
                    <TextIconButton variant="accent" disabled={name.value.trim() == ""} onClick={create}>
                        <Plus size={18} /> Create
                    </TextIconButton>
                </Container>
                {error && <Text class="error" content={error} />}

                <Loading loaded={playlists != null}>
                    {() => playlists!.length == 0
                        ? <Text dim content="No playlists yet. Make one above, then add songs from its page." />
                        : (
                            <WrapList min_size={140}>
                                {playlists!.map(p => (
                                    <LinkButton variant="always-transparent" class="library-card text" href={`/playlist/${p.id}`}>
                                        <Image
                                            src={p.cover_id ? API.getTrackCoverUrl(String(p.cover_id)) : fallbackCover(p.name, "album")}
                                            size={140}
                                        />
                                        <Text content={p.name} />
                                        <Text dim content={`${p.n} track${p.n == 1 ? "" : "s"}`} />
                                    </LinkButton>
                                ))}
                            </WrapList>
                        )}
                </Loading>
            </Container>
        </Content>
    )
}
