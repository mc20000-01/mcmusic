/** One result row in the search popout (track, album or artist).
 */
import {
    Case,
    Container,
    DotSeperator,
    Image,
    LinkButton,
    Switch,
    Text,
    type LinkButtonProps
} from "flufi-ui/components";
import { API } from "../../common/net/api";
import type { SearchItem } from "../../common/net/types";
import { ArtistPfp, SetCover } from "../Library/Image";

export function SearchItemElem(props: { item: SearchItem, close?: () => void }) {
    const buttonProps: Omit<LinkButtonProps, "href"> = {
        noPadding: true,
        variant: "always-transparent"
    };

    return (
        <>
            <Switch value={props.item.type}>
                <Case value="artist" children={() => {
                    const item = props.item as Extract<SearchItem, { type: "artist" }>;

                    return (
                        <LinkButton {...buttonProps} href={`/artist/${item.uuid}`} onClick={props.close}>
                            <ArtistPfp {...item} size={40} />
                            <Container vertical centered_y>
                                <Text content={item.artist.name} />
                                <Container horizontal class="dim">
                                    <Text class="capitalised" content="artist" />
                                </Container>
                            </Container>
                        </LinkButton>
                    )
                }} />
                <Case value="set" children={() => {
                    const item = props.item as Extract<SearchItem, { type: "set" }>;

                    return (
                        <LinkButton {...buttonProps} href={`/set/${item.uuid}`} onClick={props.close}>
                            <SetCover {...item} size={40} />
                            <Container vertical centered_y>
                                <Text content={item.set.name} />
                                <Container horizontal class="dim" centered_y>
                                    <Text class="capitalised" content={item.set.kind} />
                                    <DotSeperator containerTextMargin />
                                    <Text content={item.artist?.name.value ?? "Unknown artist"} />
                                </Container>
                            </Container>
                        </LinkButton>
                    )
                }} />
                <Case value="track" children={() => {
                    const item = props.item as Extract<SearchItem, { type: "track" }>;
                    const href = item.track.set ? `/set/${item.track.set}` : "/";

                    return (
                        <LinkButton {...buttonProps} href={href} onClick={props.close}>
                            <Image
                                src={API.getTrackCoverUrl(item.uuid)}
                                size={40}
                            />
                            <Container vertical centered_y>
                                <Text content={item.track.name} />
                                <Container horizontal class="dim" centered_y>
                                    <Text class="capitalised" content={item.set?.name} />
                                    <DotSeperator containerTextMargin />
                                    <Text content={item.artist?.name.value ?? "Unknown artist"} />
                                </Container>
                            </Container>
                        </LinkButton>
                    )
                }} />
            </Switch>
        </>
    )
}
