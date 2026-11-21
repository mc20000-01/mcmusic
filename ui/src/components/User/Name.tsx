/** Username label with an admin badge.
 */
import { Text } from "flufi-ui/components";
import { addClass } from "flufi-ui/common";
import type { User } from "../../common/net/types";

export type UsernameProps = {
    class?: string
} & (
    { username: string } |
    { user: User }
);

export function Username(props: UsernameProps) {
    // TODO: display name
    
    let name: string;
    if ("username" in props)
        name = props.username;
    else
        name = props.user.username;
    
    return (
        <Text
            class={addClass("username", props.class)}
            content={name}
        />
    )
}
