/** Synced lyrics panel.
 *
 * Fetches (cached server-side) lyrics for a track, parses LRC into
 * {time, text} lines and highlights the current line as the track plays.
 * Renders a right-side drawer above the player bar (full screen on mobile)
 * with a slide animation, text-size control and per-track open/closed state.
 */
import { useEffect, useRef, useState, useCallback } from "preact/hooks";
import { Button, Container, Header3, Text, TextIconButton } from "flufi-ui/components";
import {
    AArrowDown,
    AArrowUp,
    AudioLines,
    AudioWaveform,
    LocateFixed,
    MicVocal,
    Sparkles,
    X,
} from "lucide-preact";
import { EmptyState } from "../EmptyState/EmptyState";
import {
    LyricVisualizer,
    VISUALIZER_LABELS,
    VISUALIZER_MODES,
    readVisualizerMode,
    saveVisualizerMode,
    type VisualizerMode,
} from "./LyricVisualizer";
import { API } from "../../common/net/api";
import { position, seekTo } from "../../common/player";

import "./style.css";

type LrcLine = { time: number; text: string };

const SIZE_KEY = "mcmusic:lyricsSize";

const VISUALIZER_ICONS = {
    bars: AudioLines,
    wave: AudioWaveform,
    glow: Sparkles,
};

function parseLrc(text: string): LrcLine[] {
    const lines = text.split(/\r?\n/);
    const out: LrcLine[] = [];
    const tagRe = /\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]/g;

    for (const raw of lines) {
        const times: number[] = [];
        let lastIndex = 0;
        let m: RegExpExecArray | null = null;
        tagRe.lastIndex = 0;
        while ((m = tagRe.exec(raw)) !== null) {
            const min = parseInt(m[1], 10);
            const sec = parseInt(m[2], 10);
            const ms = m[3] ? parseInt(String(m[3]).padEnd(3, "0"), 10) : 0;
            times.push(min * 60 + sec + ms / 1000);
            lastIndex = tagRe.lastIndex;
        }
        const lyric = raw.slice(lastIndex).trim();

        // Skip metadata lines like [ar:], [ti:], [al:], [by:], [offset:]
        if (/^\[(ar|ti|al|by|offset|re|ue):/i.test(raw)) continue;

        if (times.length && lyric) {
            for (const t of times) out.push({ time: t, text: lyric });
        } else if (!times.length && lyric) {
            out.push({ time: -1, text: lyric });
        }
    }

    out.sort((a, b) => a.time - b.time);
    return out;
}

function sourceLabel(source: string, synced: boolean): string {
    const s = (source || "").toLowerCase();
    const via = s.includes("lrclib") ? "via LRCLIB" : s.includes("stored") ? "stored" : "";
    return synced ? `Synced${via ? ` · ${via}` : ""}` : `Plain${via ? ` · ${via}` : ""}`;
}

export function LyricsPanel(props: {
    trackId: string;
    open: boolean;
    onOpen: () => void;
    onClose: () => void;
}) {
    const { trackId, open, onOpen, onClose } = props;
    const [lines, setLines] = useState<LrcLine[]>([]);
    const [synced, setSynced] = useState(false);
    const [source, setSource] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [size, setSize] = useState(() => {
        const v = localStorage.getItem(SIZE_KEY);
        return v ? parseFloat(v) : 1;
    });
    const [manualScroll, setManualScroll] = useState(false);
    const [activeIndex, setActiveIndex] = useState(-1);
    const [visualizerMode, setVisualizerMode] = useState<VisualizerMode>(readVisualizerMode);
    const [singMode, setSingMode] = useState(false);

    const containerRef = useRef<HTMLDivElement>(null);
    const scrollTimeoutRef = useRef<number>(0);
    const programmaticScrollRef = useRef(false);
    const sizeRef = useRef(size);
    sizeRef.current = size;
    const prevOpenRef = useRef(open);
    useEffect(() => {
        if (!prevOpenRef.current && open) onOpen();
        prevOpenRef.current = open;
    }, [open, onOpen]);

    useEffect(() => {
        localStorage.setItem(SIZE_KEY, String(size));
    }, [size]);

    useEffect(() => {
        saveVisualizerMode(visualizerMode);
    }, [visualizerMode]);

    // Sing Mode is a display mode only, and only real LRC timestamps earn it.
    useEffect(() => {
        if (!synced) setSingMode(false);
    }, [synced]);

    const changeSize = useCallback((delta: number) => {
        setSize((s) => {
            return Math.min(1.8, Math.max(0.6, s + delta));
        });
    }, []);

    const jumpToCurrent = useCallback(() => {
        setManualScroll(false);
        scrollToActive();
    }, []);

    const scrollToActive = useCallback(() => {
        const el = containerRef.current;
        if (!el || activeIndex < 0) return;
        const node = el.querySelector(`[data-line="${activeIndex}"]`);
        if (!node) return;
        const elRect = el.getBoundingClientRect();
        const nodeRect = node.getBoundingClientRect();
        const offset =
            nodeRect.top - elRect.top + el.scrollTop - elRect.height / 2 + nodeRect.height / 2;
        programmaticScrollRef.current = true;
        el.scrollTo({ top: offset, behavior: "smooth" });
        window.clearTimeout(scrollTimeoutRef.current);
        scrollTimeoutRef.current = window.setTimeout(() => {
            programmaticScrollRef.current = false;
        }, 600);
    }, [activeIndex]);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setError(null);
        API.lyrics(trackId)
            .then((d) => {
                if (cancelled) return;
                const text = d.lyrics || "";
                const parsed = parseLrc(text);
                setLines(parsed);
                setSynced(parsed.some((l) => l.time >= 0));
                setSource(d.source || "");
                setLoading(false);
            })
            .catch((e) => {
                if (cancelled) return;
                setError(e instanceof Error ? e.message : String(e));
                setLoading(false);
            });
        return () => { cancelled = true; };
    }, [trackId]);

    useEffect(() => {
        if (!open) return;
        let scheduled = false;
        function onTime() {
            if (manualScroll) return;
            if (scheduled) return;
            scheduled = true;
            requestAnimationFrame(() => {
                scheduled = false;
                const now = position.value;
                let idx = -1;
                for (let i = lines.length - 1; i >= 0; i--) {
                    if (lines[i].time >= 0 && lines[i].time <= now) {
                        idx = i;
                        break;
                    }
                }
                setActiveIndex(idx);
                if (idx >= 0) scrollToActive();
            });
        }
        const unsub = position.subscribe(onTime);
        onTime();
        return () => {
            unsub();
            window.clearTimeout(scrollTimeoutRef.current);
        };
    }, [open, lines, manualScroll, scrollToActive]);

    function onContainerScroll() {
        if (programmaticScrollRef.current) return;
        setManualScroll(true);
        window.clearTimeout(scrollTimeoutRef.current);
        scrollTimeoutRef.current = window.setTimeout(() => setManualScroll(false), 400);
    }

    if (!open) return null;

    const missing = loading === false && lines.length === 0 && !error;
    const showLyrics = lines.length > 0 && !error && !loading;

    return (
        <Container
            class="lyrics-panel"
            other={{
                role: "dialog",
                "aria-modal": "true",
                "aria-label": "Lyrics",
                onScroll: onContainerScroll,
                ref: containerRef,
            }}
        >
            <Container horizontal centered_y class="head">
                <TextIconButton
                    variant="always-transparent"
                    title="Close lyrics"
                    onClick={onClose}
                >
                    <X size={15} />
                </TextIconButton>
                <Header3 class="title">Lyrics</Header3>
                <Container horizontal class="controls">
                    <div class="visualizer-modes" role="group" aria-label="Lyric visualizer mode">
                        {VISUALIZER_MODES.map((mode) => {
                            const Icon = VISUALIZER_ICONS[mode];
                            const active = visualizerMode === mode;
                            return (
                                <button
                                    key={mode}
                                    type="button"
                                    class={`visualizer-mode${active ? " visualizer-mode-active" : ""}`}
                                    title={`${VISUALIZER_LABELS[mode]} visualizer`}
                                    aria-label={`${VISUALIZER_LABELS[mode]} visualizer mode`}
                                    aria-pressed={active}
                                    onClick={() => setVisualizerMode(mode)}
                                >
                                    <Icon size={14} aria-hidden="true" />
                                </button>
                            );
                        })}
                    </div>
                    {source && (
                        <Text dim class="source" content={sourceLabel(source, synced)} />
                    )}
                    {synced && (
                        <Button
                            class="sing-toggle"
                            variant={singMode ? "accent-subtle" : "panel"}
                            title="Larger karaoke-style lines. This does not record your voice."
                            onClick={() => setSingMode(v => !v)}
                        >
                            <MicVocal size={14} /> {singMode ? "Reading" : "Sing along"}
                        </Button>
                    )}
                    <TextIconButton
                        variant="always-transparent"
                        title="Smaller text"
                        onClick={() => changeSize(-0.15)}
                        disabled={size <= 0.6}
                    >
                        <AArrowDown size={14} />
                    </TextIconButton>
                    <TextIconButton
                        variant="always-transparent"
                        title="Larger text"
                        onClick={() => changeSize(0.15)}
                        disabled={size >= 1.8}
                    >
                        <AArrowUp size={14} />
                    </TextIconButton>
                    {manualScroll && synced && (
                        <TextIconButton
                            variant="accent-subtle"
                            title="Jump to current line"
                            onClick={jumpToCurrent}
                        >
                            <LocateFixed size={14} /> Jump to current
                        </TextIconButton>
                    )}
                </Container>
            </Container>

            {error && (
                <Container class="lyrics-state">
                    <Text class="error" content={error} />
                    <button
                        type="button"
                        class="retry"
                        onClick={() => {
                            setLoading(true);
                            setError(null);
                            void API.lyrics(trackId)
                                .then((d) => {
                                    const parsed = parseLrc(d.lyrics || "");
                                    setLines(parsed);
                                    setSynced(parsed.some((l) => l.time >= 0));
                                    setSource(d.source || "");
                                    setLoading(false);
                                })
                                .catch((e) => {
                                    setError(e instanceof Error ? e.message : String(e));
                                    setLoading(false);
                                });
                        }}
                    >
                        Try again
                    </button>
                </Container>
            )}
            {loading && !error && (
                <Container class="lyrics-state">
                    <Text dim content="Loading lyrics…" />
                </Container>
            )}
            {missing && !error && !loading && (
                <EmptyState
                    class="lyrics-empty"
                    icon={<MicVocal size={22} />}
                    title="No lyrics found"
                    body="This track does not have a synced or plain lyrics file yet."
                />
            )}
            {showLyrics && (
                <LyricVisualizer mode={visualizerMode} activeIndex={activeIndex} />
            )}
            {showLyrics && (
                <div
                    class={`lyrics-text${singMode && synced ? " sing-along" : ""}`}
                    style={{ fontSize: `${sizeRef.current}rem` }}
                >
                    {lines.map((line, i) => {
                        const active = i === activeIndex;
                        return (
                            <div
                                key={i}
                                data-line={i}
                                class={`lyrics-line${active ? " lyrics-line-active" : ""}${synced ? "" : " lyrics-line-static"}`}
                                onClick={() => {
                                    if (line.time >= 0) {
                                        setManualScroll(false);
                                        seekTo(line.time);
                                        setActiveIndex(i);
                                        scrollToActive();
                                    }
                                }}
                            >
                                {line.text}
                            </div>
                        );
                    })}
                    {synced && activeIndex < 0 && position.value > 0 && (
                        <Container class="lyrics-state" centered_x>
                            <Text dim content="Waiting for the track to start…" />
                        </Container>
                    )}
                </div>
            )}
        </Container>
    );
}
