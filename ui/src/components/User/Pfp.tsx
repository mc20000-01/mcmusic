/** User avatar with a generated fallback.
 */
import { Container, Image } from "flufi-ui/components";
import { addClass, addStyles } from "flufi-ui/common";
import type { User } from "../../common/net/types";

import "./style.css";

export type UserPfpProps = {
    size?: number,
    override?: string,
    class?: string
} & (
    { username: string } |
    { user: User }
);

export function UserPfp(props: UserPfpProps) {
    let username: string;
    if ("username" in props)
        username = props.username;
    else
        username = props.user.username;
    
    return (
        <Container
            class={addClass("pfp", props.class)}
            other={{
                style: addStyles(
                    props.size != null && {
                        "width": props.size,
                        "height": props.size
                    }
                ),
            }}
        >
            <Image class="pfp" src={`https://avatars.rotur.dev/${username}`} />
            <Image class="overlay" src={`https://avatars.rotur.dev/.overlay/${username}`} />
        </Container>
    )
}