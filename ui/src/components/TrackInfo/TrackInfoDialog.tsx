/** Track details dialog: the metadata the library knows plus the recorded
 *  YouTube sources. Admins can flip the explicit override from here.
 */
import { useEffect, useState } from "preact/hooks";
import {
    Button, Container, Header3, Loading, Seperator, Text, TextIconButton,
} from "flufi-ui/components";
import { Check, ExternalLink, Info, X } from "lucide-preact";
import { API, getTrackInfo, type ApiJson } from "../../common/net/api";
import { currentUser } from "../../common/auth";
import { refreshLibrary } from "../../common/net/api";

import "./style.css";

function count(n: any): string {
    const v = Number(n);
    return Number.isFinite(v) ? v.toLocaleString() : "—";
}

export function TrackInfoDialog(props: {
    trackId: string;
    title: string;
    onClose: () => void;
}) {
    const [info, setInfo] = useState<ApiJson | null>(null);
    const [sources, setSources] = useState<ApiJson[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [explicit, setExplicit] = useState<boolean | null>(null);

    useEffect(() => {
        let cancelled = false;
        Promise.all([
            getTrackInfo(props.trackId),
            API.trackSources(props.trackId).catch(() => ({ sources: [] })),
        ]).then(([i, s]) => {
            if (cancelled) return;
            setInfo(i);
            setSources(s.sources ?? []);
            setExplicit(i.explicit == null ? null : !!i.explicit);
        }).catch(e => {
            if (!cancelled) setError(e instanceof Error ? e.message : String(e));
        });
        return () => { cancelled = true; };
    }, [props.trackId]);

    async function saveExplicit(value: boolean | null) {
        try {
            await API.patchTrack(props.trackId, { explicit: value });
            setExplicit(value);
            refreshLibrary();
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    const rows: [string, string][] = [];
    if (info) {
        rows.push(["Length", formatDuration(info.duration)]);
        rows.push(["Track", info.track_no || "—"]);
        rows.push(["Year", info.year || "—"]);
        rows.push(["Genre", info.genre || "—"]);
        rows.push(["Explicit", explicit == null ? "Auto" : explicit ? "Yes" : "No"]);
        if (info.yt_channel) rows.push(["Channel", info.yt_channel]);
        if (info.yt_likes != null) rows.push(["YT likes", count(info.yt_likes)]);
        if (info.yt_views != null) rows.push(["YT views", count(info.yt_views)]);
        if (info.yt_date) rows.push(["Uploaded", info.yt_date]);
        if (info.has_lyrics) rows.push(["Lyrics", info.lyrics_source || "stored"]);
    }

    return (
        <div class="dialog-backdrop" onClick={props.onClose}>
            <div
                class="track-info-dialog container"
                role="dialog"
                aria-modal="true"
                aria-label="Track info"
                onClick={(e: MouseEvent) => e.stopPropagation()}
            >
                <Container horizontal centered_y class="dialog-head">
                    <Info size={17} />
                    <Header3 class="dialog-title">{props.title}</Header3>
                    <TextIconButton variant="always-transparent" title="Close" onClick={props.onClose}>
                        <X size={16} />
                    </TextIconButton>
                </Container>
                <Seperator />
                <Loading loaded={info != null || error != null}>
                    {() => error ? (
                        <Text class="error" content={error} />
                    ) : (
                        <Container extra_gap class="dialog-body">
                            <div class="kv">
                                {rows.map(([k, v]) => (
                                    <div class="kv-row" key={k}>
                                        <Text dim content={k} />
                                        <Text content={v} />
                                    </div>
                                ))}
                            </div>

                            {currentUser.value?.is_admin && (
                                <Container>
                                    <Text dim content="Explicit override" />
                                    <Container horizontal centered_y wrap>
                                        <Button
                                            variant={explicit === null ? "accent-subtle" : "panel"}
                                            onClick={() => saveExplicit(null)}
                                        >Auto</Button>
                                        <Button
                                            variant={explicit === false ? "accent-subtle" : "panel"}
                                            onClick={() => saveExplicit(false)}
                                        >Not explicit</Button>
                                        <Button
                                            variant={explicit === true ? "accent-subtle" : "panel"}
                                            onClick={() => saveExplicit(true)}
                                        ><Check size={14} /> Explicit</Button>
                                    </Container>
                                </Container>
                            )}

                            <Container>
                                <Text dim content={`Sources (${sources.length})`} />
                                {sources.length === 0 ? (
                                    <Text dim content="No sources recorded." />
                                ) : sources.map((s, i) => (
                                    <Container horizontal centered_y class="source-row" key={`${s.yt_id}-${i}`}>
                                        <Text content={s.title || s.yt_id || "Source"} />
                                        {s.url && (
                                            <a href={s.url} target="_blank" rel="noopener noreferrer" title="Open source">
                                                <ExternalLink size={14} />
                                            </a>
                                        )}
                                    </Container>
                                ))}
                            </Container>
                        </Container>
                    )}
                </Loading>
            </div>
        </div>
    );
}

function formatDuration(seconds: any): string {
    const n = Number(seconds);
    if (!Number.isFinite(n) || n <= 0) return "—";
    const m = Math.floor(n / 60);
    return `${m}:${String(Math.floor(n % 60)).padStart(2, "0")}`;
}
