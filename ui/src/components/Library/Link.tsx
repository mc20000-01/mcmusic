import { Text, TextIconLinkButton } from "flufi-ui/components";
import { artistLink, setLink } from "../../common/link";
import type { Artist, Set } from "../../common/net/types";
import { ArtistPfp, SetCover } from "./Image";
import { addClass } from "flufi-ui";

export type SharedLinkProps = {
    class?: string
};
export type ArtistLinkProps = /* { uuid: Uuid, serverUrl: string } */
    | { artist: Artist };
export function ArtistLink(props: ArtistLinkProps & SharedLinkProps) {
    // TODO: allow for uuid and serverUrl and make it fetch name
    
    return (
        <TextIconLinkButton class={addClass("library-link", props.class)} href={artistLink(props)}>
            <ArtistPfp {...props} size={20} />
            <Text content={props.artist.name} />
        </TextIconLinkButton>
    )
}

export type SetLinkProps = /* { uuid: Uuid, serverUrl: string } */
    | { set: Set };
export function SetLink(props: SetLinkProps & SharedLinkProps) {
    // TODO: allow for uuid and serverUrl and make it fetch name
    
    return (
        <TextIconLinkButton class={addClass("library-link", props.class)} href={setLink(props)}>
            <SetCover {...props} size={20} />
            <Text content={props.set.name} />
        </TextIconLinkButton>
    )
}
