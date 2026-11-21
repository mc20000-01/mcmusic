/** Home: a grid of multi-track albums plus the most recently added tracks.
 */
import { useEffect, useState } from "preact/hooks";
import { Container, Content, Header2, Loading, WrapList } from "flufi-ui/components";
import { SetCard } from "../../components/Library/Card";
import { TrackList } from "../../components/TrackList/TrackList";
import { API } from "../../common/net/api";
import type { Set, Track } from "../../common/net/types";

import "./style.css";

export function HomePage() {
    const [albums, setAlbums] = useState<Set[] | null>(null);
    const [tracks, setTracks] = useState<Track[] | null>(null);

    useEffect(() => {
        API.listAlbums().then(setAlbums).catch(() => setAlbums([]));
        API.listTracks(50).then(setTracks).catch(() => setTracks([]));
    }, []);

    return (
        <Content class="home">
            <Loading loaded={albums != null}>
                {() => (
                    <Container extra_gap>
                        <Container>
                            <Header2>Albums</Header2>
                            <WrapList min_size={140}>
                                {albums!.map(a => (
                                    <SetCard set={a} />
                                ))}
                            </WrapList>
                        </Container>
                        <Container>
                            <Header2>Songs</Header2>
                            <Loading loaded={tracks != null}>
                                {() => <TrackList tracks={tracks!} />}
                            </Loading>
                        </Container>
                    </Container>
                )}
            </Loading>
        </Content>
    )
}
