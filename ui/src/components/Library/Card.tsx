import type { Set } from "../../common/net/types";
import { LinkButton, Text } from "flufi-ui";
import { addClass } from "flufi-ui";
import { ArtistPfp, SetCover } from "./Image";
import { setLink } from "../../common/link";
import type { Artist } from "../../common/net/types";
import { artistLink } from "../../common/link";
import { Play } from "lucide-preact";

export function SetCard(props: {
    set: Set,
    class?: string,
    /** Album artist, shown under the title on the albums grid. */
    subtitle?: string,
    /** Renders a hover play button when the caller can start playback. */
    onPlay?: () => void,
}) {
    const href = setLink({ set: props.set });

    return (
        <div class={addClass(props.class, "library-card")}>
            <div class="cover-wrap">
                <LinkButton
                    variant="always-transparent"
                    class="cover-link text"
                    href={href}
                >
                    <SetCover set={props.set} lazy />
                </LinkButton>
                {props.onPlay && (
                    <button
                        type="button"
                        class="card-play"
                        title={`Play ${props.set.name.value}`}
                        aria-label={`Play ${props.set.name.value}`}
                        onClick={props.onPlay}
                    >
                        <Play size={16} />
                    </button>
                )}
            </div>
            <LinkButton
                variant="always-transparent"
                class="library-link text"
                href={href}
            >
                <Text class="card-title" content={props.set.name} />
                {props.subtitle && (
                    <Text class="card-sub" dim content={props.subtitle} />
                )}
            </LinkButton>
        </div>
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
            <ArtistPfp artist={props.artist} lazy />
            <Text content={props.artist.name} />
        </LinkButton>
    )
}
