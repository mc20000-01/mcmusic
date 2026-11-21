/** Artist page: hero artwork, albums and every credited track.
 */
import type { RoutePropsForPath } from "preact-iso";
import { useEffect, useState } from "preact/hooks";
import {
    Container,
    Content,
    Header3,
    Loading,
    Text,
    WrapList
} from "flufi-ui/components";

import type { Artist } from "../../common/net/types";

import "./style.css";
import { API } from "../../common/net/api";
import { ArtistPfp } from "../../components/Library/Image";
import { SetCard } from "../../components/Library/Card";

export function ArtistPage(props: RoutePropsForPath<"/artist/:uuid">) {
    const [artist, setArtist] = useState<Artist | null>(null);
    
    useEffect(() => {
        API.getArtist(props.uuid)
            .then(r => {
                setArtist(r);
            })
    }, [props.uuid]);
    
    return (
        <Content class="artist">
            <Loading loaded={artist != null}>
                {() => (
                    <Container extra_gap>
                        <Container horizontal class="top">
                            <ArtistPfp artist={artist!} size={168} />
                            <Container>
                                <Text extra_big content={artist!.name} selectable />
                                <Text dim content={artist!.bio} />
                            </Container>
                        </Container>
                        <Container>
                            <Header3>Discography</Header3>
                            <WrapList min_size={128}>
                                {artist?.sets.value.map(s => (
                                    <SetCard set={s} />
                                ))}
                            </WrapList>
                        </Container>
                    </Container>
                )}
            </Loading>
        </Content>
    )
}
