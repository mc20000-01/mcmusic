/** Read-only genre tag list.
 */
import { TagList } from "flufi-ui/components";
import type { Signalish } from "flufi-ui/types";

// NOTE: GenreList is basically just a tag list wrapper, for if i want
//       to add auto-complete n shit later lol

export function GenreList(props: { tags: Signalish<string[]>, link?: boolean }) {
    return (
        <TagList {...props} />
    )
}
