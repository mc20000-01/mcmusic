/** Track index cell that turns into a play/pause icon for the active track.
 */

import { Container, Text } from "flufi-ui/components";

import "./style.css";

export function TrackNumber(props: { index?: number }) {
    // bouta start spamming <TrackNumber /> everywhere
    if (props.index == null)
        return null;
    
    return (
        <Container class="track-number">
            <Text content={props.index + 1} />
        </Container>
    )
}
