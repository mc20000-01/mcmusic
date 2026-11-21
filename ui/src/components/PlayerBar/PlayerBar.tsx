/** Bottom player bar: artwork, transport (prev / play-pause / next / shuffle /
 * repeat / volume / queue), a seek bar with filled progress, the track title
 * and artist as links, and the lyrics toggle. Also installs Media Session and
 * keyboard controls (space, arrows).
 */
import { useEffect, useRef, useState } from "preact/hooks";
import {
    Container,
    FooterContainer,
    IconButton,
    Slider,
    Text,
    TextIconButton,
} from "flufi-ui/components";
import {
    ArrowLeft,
    ArrowRight,
    MicVocal,
    Pause,
    Play,
    Repeat,
    Shuffle,
    Volume2,
    VolumeX,
    X,
} from "lucide-preact";
import {
    currentId,
    duration,
    formatTime,
    isPlaying,
    nowPlaying,
    playError,
    playNext,
    playPrev,
    playQueueIndex,
    queue,
    queueIndex,
    repeatMode,
    seekTo,
    setShuffle,
    setVolume,
    shuffleEnabled,
    cycleRepeat,
    togglePlay,
    toggleMute,
    position,
} from "../../common/player";
import { volume } from "../../common/prefs";
import { LyricsPanel } from "../Lyrics/LyricsPanel";

import "./style.css";

function setLinkHref(uuid: string): string {
    return `/set/${uuid}`;
}

export function PlayerBar() {
    const track = nowPlaying.value;
    const [showLyrics, setShowLyrics] = useState(() => {
        const v = localStorage.getItem("mcmusic:lyricsOpen");
        return v === "true";
    });
    const [muted, setMuted] = useState(false);
    const [showQueue, setShowQueue] = useState(false);
    const [seekHover, setSeekHover] = useState<number | null>(null);
    const [seekDragging, setSeekDragging] = useState(false);
    const [volumeHover, setVolumeHover] = useState<number | null>(null);
    const seekRef = useRef<HTMLDivElement>(null);
    const volRef = useRef<HTMLDivElement>(null);

    if (!track) return null;

    const setUuid = (track as any).setUuid ?? null;
    const artistUuid = (track as any).artistUuid ?? null;
    const album = (track as any).album ?? "";

    // Persist lyrics open/closed.
    useEffect(() => {
        localStorage.setItem("mcmusic:lyricsOpen", showLyrics ? "true" : "false");
    }, [showLyrics]);

    // Media Session API (lock screen, media keys, artwork).
    useEffect(() => {
        if (!("mediaSession" in navigator)) return;
        const cover = `/api/tracks/${currentId.value ?? track.id}/cover`;
        navigator.mediaSession.metadata = new MediaMetadata({
            title: track.title,
            artist: track.artist,
            album,
            artwork: [{ src: cover, sizes: "512x512", type: "image/jpeg" }],
        });
        const setHandler = (action: string) => {
            switch (action) {
                case "play":
                case "pause":
                    togglePlay();
                    break;
                case "previoustrack":
                    playPrev();
                    break;
                case "nexttrack":
                    playNext();
                    break;
            }
        };
        for (const action of ["play", "pause", "previoustrack", "nexttrack"]) {
            try { (navigator.mediaSession as any).setActionHandler(action, setHandler); } catch { /* noop */ }
        }
        return () => {
            for (const action of ["play", "pause", "previoustrack", "nexttrack"]) {
                try { (navigator.mediaSession as any).setActionHandler(action, null); } catch { /* noop */ }
            }
        };
    }, [track.id, track.title, track.artist, album]);

    // Global keyboard controls.
    useEffect(() => {
        function onKey(e: KeyboardEvent) {
            if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
            if (e.key === " ") { e.preventDefault(); togglePlay(); return; }
            if (e.key === "ArrowLeft") { e.preventDefault(); seekTo(Math.max(0, position.value - 5)); return; }
            if (e.key === "ArrowRight") { e.preventDefault(); seekTo(Math.min(duration.value, position.value + 5)); return; }
        }
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [position.value, duration.value]);

    const playedPct = duration.value > 0 ? (position.value / duration.value) * 100 : 0;
    const isMutedEffective = muted || volume.value <= 0;

    function onSeekMove(clientX: number) {
        const rect = seekRef.current?.getBoundingClientRect();
        if (!rect) return;
        const frac = (clientX - rect.left) / rect.width;
        const t = Math.max(0, Math.min(duration.value, frac * duration.value));
        setSeekHover(t);
        if (seekDragging) seekTo(t);
    }

    function onSeekClick(clientX: number) {
        const rect = seekRef.current?.getBoundingClientRect();
        if (!rect) return;
        const frac = (clientX - rect.left) / rect.width;
        seekTo(Math.max(0, Math.min(duration.value, frac * duration.value)));
        setSeekDragging(false);
    }

    function onVolumeMove(clientX: number) {
        const rect = volRef.current?.getBoundingClientRect();
        if (!rect) return;
        const frac = (clientX - rect.left) / rect.width;
        const v = Math.max(0, Math.min(1, frac));
        setVolumeHover(v);
        if (!muted) setVolume(v);
    }

    const queueTracks = queue.value;

    return (
        <>
            <LyricsPanel
                trackId={track.id}
                open={showLyrics}
                onOpen={() => setShowLyrics(true)}
                onClose={() => setShowLyrics(false)}
            />
            <FooterContainer other={{ id: "player-bar" }}>
                <Container horizontal centered_y class="player">
                    {/* Cover art — 56px, opens the album. */}
                    <div class="art-wrap">
                        <img
                            class="art"
                            src={`/api/tracks/${currentId.value ?? track.id}/cover`}
                            alt=""
                            draggable="false"
                            onClick={() => { if (setUuid) window.location.href = setLinkHref(setUuid); }}
                        />
                    </div>

                    {/* Transport controls. */}
                    <Container horizontal centered_y class="transport" gap>
                        <IconButton
                            title="Previous"
                            onClick={playPrev}
                        >
                            <ArrowLeft size={17} />
                        </IconButton>
                        <IconButton
                            title={isPlaying.value ? "Pause" : "Play"}
                            onClick={togglePlay}
                            class="play-pause"
                        >
                            {isPlaying.value ? <Pause size={19} /> : <Play size={19} />}
                        </IconButton>
                        <IconButton
                            title="Next"
                            onClick={playNext}
                        >
                            <ArrowRight size={17} />
                        </IconButton>
                        <IconButton
                            title={shuffleEnabled.value ? "Shuffle on" : "Shuffle off"}
                            variant={shuffleEnabled.value ? "accent-subtle" : "always-transparent"}
                            onClick={() => setShuffle(!shuffleEnabled.value)}
                        >
                            <Shuffle size={16} />
                        </IconButton>
                        <IconButton
                            title={repeatMode.value === "one" ? "Repeat one" : repeatMode.value === "all" ? "Repeat all" : "Repeat off"}
                            variant={repeatMode.value !== "off" ? "accent-subtle" : "always-transparent"}
                            onClick={() => cycleRepeat()}
                        >
                            <Repeat size={16} />
                        </IconButton>
                    </Container>

                    {/* Title / artist links. */}
                    <Container vertical class="meta">
                        <div class="title-row">
                            <a
                                href={setUuid ? setLinkHref(setUuid) : "/"}
                                class="title-link"
                                title={track.title}
                                onClick={(e) => {
                                    if (setUuid) { e.preventDefault(); window.location.href = setLinkHref(setUuid); }
                                }}
                            >
                                {track.title}
                            </a>
                        </div>
                        <div class="artist-row">
                            {artistUuid ? (
                                <a
                                    href={`/artist/${artistUuid}`}
                                    class="artist-link"
                                    title={track.artist}
                                    onClick={(e) => { e.preventDefault(); window.location.href = `/artist/${artistUuid}`; }}
                                >
                                    {track.artist}
                                </a>
                            ) : (
                                <span class="artist-link">{track.artist}</span>
                            )}
                        </div>
                        {playError.value && (
                            <Text class="play-error" role="status" content={playError.value} />
                        )}
                    </Container>

                    {/* Seek bar with filled progress. */}
                    <div class="seek-wrap">
                        <div
                            class="seek-track"
                            ref={seekRef}
                            onMouseMove={(e) => onSeekMove(e.clientX)}
                            onMouseLeave={() => setSeekHover(null)}
                            onMouseDown={(e) => { setSeekDragging(true); onSeekClick(e.clientX); }}
                            onMouseUp={() => setSeekDragging(false)}
                            onClick={(e) => onSeekClick(e.clientX)}
                            role="slider"
                            aria-label="Seek"
                            aria-valuenow={position.value}
                            aria-valuemin={0}
                            aria-valuemax={duration.value}
                            tabIndex={-1}
                        >
                            <div class="seek-fill" style={{ width: `${playedPct}%` }} />
                            {seekHover != null && !seekDragging && duration.value > 0 && (
                                <div class="seek-preview" style={{ left: `${(seekHover / duration.value) * 100}%` }}>
                                    {formatTime(seekHover)}
                                </div>
                            )}
                            <div class="seek-thumb" style={{ left: `${playedPct}%` }} />
                        </div>
                        <div class="seek-times">
                            <Text dim content={formatTime(position.value)} />
                            <Text dim content={formatTime(duration.value)} />
                        </div>
                    </div>

                    {/* Volume with mute. */}
                    <Container horizontal centered_y class="volume-wrap" gap>
                        <IconButton
                            title={isMutedEffective ? "Unmute" : "Mute"}
                            onClick={() => { setMuted(!muted); toggleMute(); }}
                        >
                            {isMutedEffective ? <VolumeX size={16} /> : <Volume2 size={16} />}
                        </IconButton>
                        <div
                            class="volume-track"
                            ref={volRef}
                            onMouseMove={(e) => onVolumeMove(e.clientX)}
                            onMouseLeave={() => setVolumeHover(null)}
                            onMouseDown={(e) => { onVolumeMove(e.clientX); }}
                            onClick={(e) => onVolumeMove(e.clientX)}
                        >
                            <div class="volume-fill" style={{ width: `${Math.max(0, volume.value) * 100}%` }} />
                            <div class="volume-thumb" style={{ left: `${Math.max(0, volume.value) * 100}%` }} />
                        </div>
                        {volumeHover != null && (
                            <Text dim class="volume-preview" content={`${Math.round(volumeHover * 100)}%`} />
                        )}
                    </Container>

                    {/* Queue + lyrics. */}
                    <IconButton
                        title="Queue"
                        variant={showQueue ? "accent-subtle" : "always-transparent"}
                        onClick={() => setShowQueue(!showQueue)}
                    >
                        <X size={16} />
                    </IconButton>
                    <IconButton
                        title={showLyrics ? "Hide lyrics" : "Lyrics"}
                        variant={showLyrics ? "accent-subtle" : "always-transparent"}
                        onClick={() => setShowLyrics(!showLyrics)}
                    >
                        <MicVocal size={16} />
                    </IconButton>
                </Container>

                {showQueue && queueTracks.length > 0 && (
                    <Container class="queue-drawer">
                        <Container horizontal centered_y class="queue-head">
                            <Text class="queue-title" content="Queue" />
                            <Text dim content={` · ${queueTracks.length} track${queueTracks.length == 1 ? "" : "s"}`} />
                            <IconButton title="Close queue" onClick={() => setShowQueue(false)}>
                                <X size={14} />
                            </IconButton>
                        </Container>
                        <div class="queue-list">
                            {queueTracks.map((t, i) => (
                                <Container
                                    key={t.id}
                                    horizontal centered_y
                                    class={`queue-row${i === queueIndex.value ? " queue-row-active" : ""}`}
                                    onClick={() => playQueueIndex(i)}
                                >
                                    <Text dim content={i + 1} class="queue-num" />
                                    <div class="queue-info">
                                        <div class="queue-title-text">{t.title}</div>
                                        <div class="queue-artist-text">{t.artist}</div>
                                    </div>
                                    {i === queueIndex.value && <Text dim content={formatTime(position.value)} />}
                                </Container>
                            ))}
                        </div>
                    </Container>
                )}
            </FooterContainer>
        </>
    );
}
