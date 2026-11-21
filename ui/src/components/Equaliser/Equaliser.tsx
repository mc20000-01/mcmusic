/** Animated 'now playing' bars shown next to the active track.
 */
import { Image } from "flufi-ui/components";

import "./style.css";

export function Equaliser(props: {
    size?: number
}) {
    // Vite fingerprints this, so resolve it against the client's own base URL.
    return (
        <Image
            src="/static/ui/assets/equaliser.gif"
            size={props.size ?? 15}
        />
    )
}
