/** Animated 'now playing' marker shown next to the active track.
 * Uses the same Lucide language as the rest of the controls; the motion is a
 * small CSS pulse so it matches the accent colour instead of a fixed GIF.
 */
import { AudioLines } from "lucide-preact";
import { addClass } from "flufi-ui";

import "./style.css";

export function Equaliser(props: {
    size?: number;
    class?: string;
}) {
    return (
        <AudioLines
            size={props.size ?? 15}
            class={addClass("equaliser", props.class)}
            aria-label="Now playing"
        />
    );
}
