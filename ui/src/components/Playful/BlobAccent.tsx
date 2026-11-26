/** Flat tonal blob used only for placeholders and decorative accents.
 *
 * Geometry comes from the generated design tokens; real cover art is never
 * clipped or tinted. The SVG is aria-hidden: it carries no information.
 */
import { DESIGN_BLOBS } from "../../common/blobs.generated";

import "./style.css";

export type BlobId = "blob-1" | "blob-2" | "blob-3" | "blob-4" | "blob-5";

export function BlobAccent(props: {
    id: BlobId;
    class?: string;
    title?: string;
}) {
    const blob = DESIGN_BLOBS.find(b => b.id === props.id) ?? DESIGN_BLOBS[0];
    return (
        <svg
            class={`blob-accent${props.class ? ` ${props.class}` : ""}`}
            data-blob={blob.id}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden="true"
            focusable="false"
        >
            {props.title && <title>{props.title}</title>}
            <path d={blob.path} />
        </svg>
    );
}
