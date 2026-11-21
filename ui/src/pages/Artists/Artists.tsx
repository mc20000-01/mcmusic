/** Artist grid, one card per normalized artist name.
 */
import { useEffect, useState } from "preact/hooks";
import { Container, Content, Header2, Loading, WrapList } from "flufi-ui/components";
import type { Artist } from "../../common/net/types";
import { API } from "../../common/net/api";
import { ArtistCard } from "../../components/Library/Card";

import "./style.css";

export function ArtistsPage() {
    const [artists, setArtists] = useState<Artist[] | null>(null);

    useEffect(() => {
        API.listArtists().then(setArtists).catch(() => setArtists([]));
    }, []);

    return (
        <Content class="artists">
            <Loading loaded={artists != null}>
                {() => (
                    <Container extra_gap>
                        <Header2>Artists</Header2>
                        <WrapList min_size={128}>
                            {artists!.map(a => (
                                <ArtistCard artist={a} />
                            ))}
                        </WrapList>
                    </Container>
                )}
            </Loading>
        </Content>
    )
}
