import { useEffect, useState } from "preact/hooks";
import { Container, Header3, IconButton, Text } from "flufi-ui/components";
import { X } from "lucide-preact";
import { API } from "../../common/net/api";

import "./style.css";

/**
 * Lyrics drawer over the player bar. The server returns either synced LRC or
 * plain text; both are shown verbatim in a <pre> so line breaks and timestamps
 * are preserved.
 */
export function LyricsPanel(props: { trackId: string, onClose: () => void }) {
    const [text, setText] = useState<string | null>(null);
    const [source, setSource] = useState<string>("");
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        setText(null);
        setError(null);
        API.lyrics(props.trackId)
            .then(d => {
                if (cancelled) return;
                setText(d.lyrics || "");
                setSource(d.source || "");
            })
            .catch(e => { if (!cancelled) setError(e instanceof Error ? e.message : String(e)); });
        return () => { cancelled = true; };
    }, [props.trackId]);

    return (
        <Container class="lyrics-panel">
            <Container horizontal centered_y>
                <Header3>Lyrics</Header3>
                {source && <Text dim content={source} />}
                <IconButton title="Close lyrics" onClick={props.onClose}><X size={15} /></IconButton>
            </Container>
            {error && <Text class="error" content={error} />}
            {text == null && !error && <Text dim content="Loading…" />}
            {text != null && text.trim() == "" && (
                <Text dim content="No lyrics found for this track." />
            )}
            {text != null && text.trim() != "" && <pre class="lyrics-text">{text}</pre>}
        </Container>
    )
}
