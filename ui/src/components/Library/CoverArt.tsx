/** Cover image with a flat tonal Lucide placeholder.
 *
 * `fallbackCover()` returns a `placeholder:` sentinel instead of a text-initial
 * SVG. This component renders that sentinel as a real DOM surface so it picks
 * up the active palette's CSS variables; real artwork is shown untouched.
 */
import { Circle, Cookie, Flower, Pentagon, Squircle } from "lucide-preact";
import { addClass } from "flufi-ui";
import { DESIGN_BLOBS } from "../../common/blobs.generated";
import { BlobAccent } from "../Playful/BlobAccent";

import "./style.css";

export type CoverKind = "track" | "artist" | "album";

// The glyph is decorative; the five canonical blob paths are authoritative.
const PLACEHOLDER_GLYPHS = [Circle, Squircle, Cookie, Flower, Pentagon] as const;

function glyphIndex(name: string, kind: CoverKind): number {
    let hash = kind.length * 17;
    for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
    return hash % PLACEHOLDER_GLYPHS.length;
}

function parsePlaceholder(src: string): { name: string; kind: CoverKind } | null {
    if (!src.startsWith("placeholder:")) return null;
    const [, rawKind, encoded = ""] = src.split(":");
    const kind = (rawKind === "artist" || rawKind === "track" ? rawKind : "album") as CoverKind;
    let name = "?";
    try { name = decodeURIComponent(encoded) || "?"; } catch { /* keep ? */ }
    return { name, kind };
}

export function CoverArt(props: {
    src?: string | null;
    name: string;
    kind?: CoverKind;
    size?: number;
    class?: string;
    lazy?: boolean;
    alt?: string;
    onClick?: () => void;
}) {
    const classes = addClass("cover-art", props.class, props.onClick && "cover-clickable");
    const style = props.size != null ? { width: props.size, height: props.size } : undefined;
    const placeholder = parsePlaceholder(props.src ?? "");
    if (placeholder) {
        const index = glyphIndex(placeholder.name, placeholder.kind);
        const blob = DESIGN_BLOBS[index] ?? DESIGN_BLOBS[0];
        const Glyph = PLACEHOLDER_GLYPHS[index];
        return (
            <div
                class={addClass(classes, "cover-placeholder")}
                data-shape={String(index)}
                data-blob={blob.id}
                data-kind={placeholder.kind}
                style={style}
                role="img"
                aria-label={`${placeholder.name} artwork placeholder`}
                onClick={props.onClick}
            >
                <BlobAccent id={blob.id as "blob-1" | "blob-2" | "blob-3" | "blob-4" | "blob-5"} class="cover-blob" />
                <Glyph size={Math.max(20, Math.min(56, (props.size ?? 64) * 0.42))} aria-hidden="true" />
            </div>
        );
    }
    if (!props.src) {
        return <div class={addClass(classes, "cover-placeholder", "cover-empty")} style={style} aria-hidden="true" />;
    }
    return (
        <img
            class={classes}
            src={props.src}
            alt={props.alt ?? ""}
            loading={props.lazy ? "lazy" : "eager"}
            draggable={false}
            style={style}
            onClick={props.onClick}
        />
    );
}
