/** Album page: cover, artist link and the album's track list.
 */
import { Container, Content,  Loading, Text, type Uuid } from "flufi-ui";
import { useEffect, useState } from "preact/hooks";
import type { Artist, Set } from "../../common/net/types";

import { API } from "../../common/net/api";
import type { RoutePropsForPath } from "preact-iso";
import { ArtistLink } from "../../components/Library/Link";
import { SetCover } from "../../components/Library/Image";
import { titleCase } from "../../common";
import { TrackList } from "../../components/TrackList/TrackList";

import "./style.css";

export function SetPage(props: RoutePropsForPath<"/set/:uuid">) {
    const [artist, setArtist] = useState<Artist | null>(null);
    const [set, setSet] = useState<Set | null>(null);
    
    useEffect(() => {
        API.getSet(props.uuid as Uuid)
            .then(async r => {
                setSet(r);
                setArtist(await API.getArtist(r.artist));
            })
    }, [props.uuid]);

    return (
        <Content class="set">
            <Loading loaded={set !== null && artist !== null}>
                {() => (
                    <Container extra_gap>
                        <Container horizontal class="top">
                            <SetCover set={set!} size={180} />
                            <Container>
                                <Text dim content={titleCase(set!.kind.value)} />
                                <Text extra_big content={set!.name} selectable />
                                <Container horizontal>
                                    <Text dim content="by" />
                                    <ArtistLink artist={artist!} />
                                </Container>
                            </Container>
                        </Container>
                        <TrackList tracks={set?.tracks.value!} />
                    </Container>
                )}
            </Loading>
        </Content>
    )
}
