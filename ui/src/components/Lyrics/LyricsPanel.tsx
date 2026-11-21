import { useEffect, useRef, useState } from "preact/hooks";
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
    const [attempt, setAttempt] = useState(0);

    // Keep the latest onClose in a ref so the key listener is registered once
    // instead of every time the player redraws its position.
    const onClose = useRef(props.onClose);
    onClose.current = props.onClose;

    useEffect(() => {
        const onKey = (e: KeyboardEvent) => {
            if (e.key === "Escape") onClose.current();
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, []);

    useEffect(() => {
        let cancelled = false;
        setText(null);
        setError(null);
        setSource("");
        API.lyrics(props.trackId)
            .then(d => {
                if (cancelled) return;
                setText(d.lyrics || "");
                setSource(d.source || "");
            })
            .catch(e => {
                if (!cancelled) setError(e instanceof Error ? e.message : String(e));
            });
        return () => { cancelled = true; };
    }, [props.trackId, attempt]);

    return (
        <Container class="lyrics-panel" other={{ role: "dialog", "aria-label": "Lyrics" }}>
            <Container horizontal centered_y class="head">
                <Header3>Lyrics</Header3>
                {source && <Text dim class="source" content={source} />}
                <IconButton title="Close lyrics" onClick={props.onClose}>
                    <X size={15} />
                </IconButton>
            </Container>
            {error && (
                <Container class="lyrics-state">
                    <Text class="error" content={error} />
                    <button
                        type="button"
                        class="retry"
                        onClick={() => setAttempt(a => a + 1)}
                    >
                        Try again
                    </button>
                </Container>
            )}
            {text == null && !error && <Text dim class="lyrics-state" content="Loading lyrics…" />}
            {text != null && text.trim() == "" && (
                <Text dim class="lyrics-state" content="No lyrics found for this track." />
            )}
            {text != null && text.trim() != "" && <pre class="lyrics-text">{text}</pre>}
        </Container>
    )
}
