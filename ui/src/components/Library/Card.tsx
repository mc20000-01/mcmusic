import type { Set } from "../../common/net/types";
import { LinkButton, Text } from "flufi-ui";
import { addClass } from "flufi-ui";
import { ArtistPfp, SetCover } from "./Image";
import { setLink } from "../../common/link";
import type { Artist } from "../../common/net/types";
import { artistLink } from "../../common/link";

export function SetCard(props: {
    set: Set,
    class?: string
}) {
    return (
        <LinkButton
            variant="always-transparent"
            class={addClass(props.class, "library-card", "text")}
            href={setLink({ set: props.set })}
        >
            <SetCover set={props.set} />
            <Text content={props.set.name} />
        </LinkButton>
    )
}

export function ArtistCard(props: {
    artist: Artist,
    class?: string
}) {
    return (
        <LinkButton
            variant="always-transparent"
            class={addClass(props.class, "library-card", "text")}
            href={artistLink({ artist: props.artist })}
        >
            <ArtistPfp artist={props.artist} />
            <Text content={props.artist.name} />
        </LinkButton>
    )
}
