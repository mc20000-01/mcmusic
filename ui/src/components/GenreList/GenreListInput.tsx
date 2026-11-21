/** Editable genre tags.
 */
import type { Signal } from "@preact/signals";
import { TagListInput } from "flufi-ui/components";
import type { Signalish } from "flufi-ui/types";

export function GenreListInput(props: {
    value?: Signalish<string[]>,
    onChange?: (tags: string[]) => void,
    dirty?: Signal<boolean>,
    inputPlaceholder?: string,
    class?: string
}) {
    return (
        <TagListInput inputPlaceholder="genre names (comma seperated)" {...props} />
    )
}
