/** Bottom player bar: artwork, transport (prev / play-pause / next / shuffle /
 * repeat / volume / queue), a seek bar with filled progress, the track title
 * and artist as links, and the lyrics toggle. Also installs Media Session and
 * the full set of legacy keyboard shortcuts.
 */
import { useEffect, useRef, useState } from "preact/hooks";
import { Container, FooterContainer, IconButton, Text } from "flufi-ui/components";
import {
    Heart,
    ListMusic,
    MicVocal,
    Pause,
    Play,
    Radio,
    Repeat,
    Shuffle,
    SkipBack,
    SkipForward,
    Volume2,
    VolumeX,
    X,
} from "lucide-preact";
import {
    autoplay,
    currentId,
    currentLiked,
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
    queueOpen,
    repeatMode,
    seekTo,
    setAutoplay,
    setShuffle,
    setVolume,
    shuffleEnabled,
    cycleRepeat,
    toggleCurrentLike,
    togglePlay,
    toggleMute,
    position,
} from "../../common/player";
import { API } from "../../common/net/api";
import { playfulMotion, prefersReducedMotion, volume } from "../../common/prefs";
import { useCoverColour } from "../../common/dynamic-colour";
import { CoverArt } from "../Library/CoverArt";
import { LyricsPanel } from "../Lyrics/LyricsPanel";

import "./style.css";

function setLinkHref(uuid: string): string {
    return `/set/${uuid}`;
}

export function PlayerBar() {
    const track = nowPlaying.value;
    const coverSrc = track ? API.getTrackCoverUrl(String(currentId.value ?? track.id)) : "";
    useCoverColour(coverSrc);
    const [showLyrics, setShowLyrics] = useState(() => {
        const v = localStorage.getItem("mcmusic:lyricsOpen");
        return v === "true";
    });
    const [muted, setMuted] = useState(false);
    const showQueue = queueOpen;
    const [seekHover, setSeekHover] = useState<number | null>(null);
    const [seekDragging, setSeekDragging] = useState(false);
    const [volumeHover, setVolumeHover] = useState<number | null>(null);
    const [volumeDragging, setVolumeDragging] = useState(false);
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

    // A drag can end outside the thin slider tracks; always release it.
    useEffect(() => {
        if (!seekDragging && !volumeDragging) return;
        const stop = () => {
            setSeekDragging(false);
            setVolumeDragging(false);
        };
        window.addEventListener("mouseup", stop);
        return () => window.removeEventListener("mouseup", stop);
    }, [seekDragging, volumeDragging]);

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

    // Global keyboard controls — the full legacy shortcut set.
    useEffect(() => {
        function onKey(e: KeyboardEvent) {
            const target = e.target as HTMLElement | null;
            const editing = target instanceof HTMLInputElement ||
                target instanceof HTMLTextAreaElement ||
                target instanceof HTMLSelectElement ||
                !!target?.isContentEditable;

            if (e.key === "Escape") {
                if (editing) target?.blur?.();
                queueOpen.value = false;
                setShowLyrics(false);
                return;
            }
            if (editing) return;

            if (e.key === " ") { e.preventDefault(); togglePlay(); return; }
            if (e.key === "ArrowLeft") {
                e.preventDefault();
                if (e.shiftKey) playPrev();
                else seekTo(Math.max(0, position.value - 5));
                return;
            }
            if (e.key === "ArrowRight") {
                e.preventDefault();
                if (e.shiftKey) playNext();
                else seekTo(Math.min(duration.value, position.value + 5));
                return;
            }
            if (e.shiftKey && e.key === "ArrowUp") {
                e.preventDefault(); setVolume(Math.min(1, volume.value + 0.05)); return;
            }
            if (e.shiftKey && e.key === "ArrowDown") {
                e.preventDefault(); setVolume(Math.max(0, volume.value - 0.05)); return;
            }
            if (e.key === "/") {
                e.preventDefault();
                document.getElementById("global-search")?.focus();
                return;
            }
            const k = e.key.toLowerCase();
            if (k === "m") { toggleMute(); return; }
            if (k === "l") { void toggleCurrentLike(); return; }
            if (k === "q") { queueOpen.value = !queueOpen.value; return; }
        }
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [position.value, duration.value]);

    const playedPct = duration.value > 0 ? (position.value / duration.value) * 100 : 0;
    const isMutedEffective = muted || volume.value <= 0;
    const wavePlaying = isPlaying.value && playfulMotion.value && !prefersReducedMotion();

    function seekAt(clientX: number): number | null {
        const rect = seekRef.current?.getBoundingClientRect();
        if (!rect || rect.width <= 0) return null;
        const frac = (clientX - rect.left) / rect.width;
        return Math.max(0, Math.min(duration.value, frac * duration.value));
    }

    function volumeAt(clientX: number): number | null {
        const rect = volRef.current?.getBoundingClientRect();
        if (!rect || rect.width <= 0) return null;
        const frac = (clientX - rect.left) / rect.width;
        return Math.max(0, Math.min(1, frac));
    }

    function onSeekMove(clientX: number) {
        const t = seekAt(clientX);
        if (t == null) return;
        setSeekHover(t);
        if (seekDragging) seekTo(t);
    }

    function onVolumeMove(clientX: number) {
        const v = volumeAt(clientX);
        if (v == null) return;
        setVolumeHover(v);
        if (volumeDragging) setVolume(v);
    }

    function toggleMuteButton() {
        // A zero volume is silent even when audio.muted is false.
        if (volume.value <= 0) {
            setVolume(0.8);
            if (muted) { toggleMute(); setMuted(false); }
            return;
        }
        setMuted(!muted);
        toggleMute();
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
                        <CoverArt
                            class="art"
                            src={coverSrc}
                            name={track.title}
                            kind="track"
                            alt=""
                            onClick={() => { if (setUuid) window.location.href = setLinkHref(setUuid); }}
                        />
                    </div>

                    {/* Transport controls. */}
                    <Container horizontal centered_y class="transport">
                        <IconButton
                            title="Previous"
                            onClick={playPrev}
                        >
                            <SkipBack size={17} />
                        </IconButton>
                        <IconButton
                            title={isPlaying.value ? "Pause" : "Play"}
                            onClick={togglePlay}
                            class={isPlaying.value ? "play-pause playing" : "play-pause"}
                        >
                            {isPlaying.value ? <Pause size={19} /> : <Play size={19} />}
                        </IconButton>
                        <IconButton
                            title="Next"
                            onClick={() => playNext()}
                        >
                            <SkipForward size={17} />
                        </IconButton>
                        <IconButton
                            title={shuffleEnabled.value ? "Shuffle on" : "Shuffle off"}
                            class="control-shuffle"
                            variant={shuffleEnabled.value ? "accent-subtle" : "always-transparent"}
                            onClick={() => setShuffle(!shuffleEnabled.value)}
                        >
                            <Shuffle size={16} />
                        </IconButton>
                        <IconButton
                            title={repeatMode.value === "one" ? "Repeat one" : repeatMode.value === "all" ? "Repeat all" : "Repeat off"}
                            class="control-repeat"
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
                            <span class="play-error" role="status">{playError.value}</span>
                        )}
                    </Container>

                    {/* Seek bar with filled progress. */}
                    <div class="seek-wrap">
                        <div
                            class="seek-track"
                            ref={seekRef}
                            onMouseMove={(e) => onSeekMove(e.clientX)}
                            onMouseLeave={() => { setSeekHover(null); setSeekDragging(false); }}
                            onMouseDown={(e) => {
                                const t = seekAt(e.clientX);
                                if (t == null) return;
                                seekTo(t);
                                setSeekHover(t);
                                setSeekDragging(true);
                            }}
                            onMouseUp={() => setSeekDragging(false)}
                            role="slider"
                            aria-label="Seek"
                            aria-valuenow={position.value}
                            aria-valuemin={0}
                            aria-valuemax={duration.value}
                            tabIndex={-1}
                        >
                            <div class="seek-fill" style={{ width: `${playedPct}%` }}>
                                {wavePlaying && (
                                    <svg class="seek-wave" viewBox="0 0 24 12" preserveAspectRatio="none" aria-hidden="true">
                                        <path d="M0 6 Q6 1 12 6 T24 6" />
                                    </svg>
                                )}
                            </div>
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
                    <Container horizontal centered_y class="volume-wrap">
                        <IconButton
                            title={isMutedEffective ? "Unmute" : "Mute"}
                            onClick={toggleMuteButton}
                        >
                            {isMutedEffective ? <VolumeX size={16} /> : <Volume2 size={16} />}
                        </IconButton>
                        <div
                            class="volume-track"
                            ref={volRef}
                            onMouseMove={(e) => onVolumeMove(e.clientX)}
                            onMouseLeave={() => setVolumeHover(null)}
                            onMouseDown={(e) => {
                                const v = volumeAt(e.clientX);
                                if (v == null) return;
                                setVolume(v);
                                setVolumeHover(v);
                                setVolumeDragging(true);
                            }}
                            onMouseUp={() => setVolumeDragging(false)}
                        >
                            <div class="volume-fill" style={{ width: `${Math.max(0, volume.value) * 100}%` }} />
                            <div class="volume-thumb" style={{ left: `${Math.max(0, volume.value) * 100}%` }} />
                        </div>
                        {volumeHover != null && (
                            <Text dim class="volume-preview" content={`${Math.round(volumeHover * 100)}%`} />
                        )}
                    </Container>

                    {/* Like / queue / lyrics. */}
                    <Container horizontal centered_y class="player-actions">
                        <IconButton
                            title={currentLiked.value ? "Unlike" : "Like"}
                            variant={currentLiked.value ? "accent-subtle" : "always-transparent"}
                            onClick={() => void toggleCurrentLike()}
                        >
                            <Heart size={16} fill={currentLiked.value ? "currentColor" : "none"} />
                        </IconButton>
                        <IconButton
                            title={showQueue.value ? "Hide up next" : "Up next"}
                            variant={showQueue.value ? "accent-subtle" : "always-transparent"}
                            onClick={() => { queueOpen.value = !queueOpen.value; }}
                        >
                            <ListMusic size={16} />
                        </IconButton>
                        <IconButton
                            title={showLyrics ? "Hide lyrics" : "Lyrics"}
                            variant={showLyrics ? "accent-subtle" : "always-transparent"}
                            onClick={() => setShowLyrics(!showLyrics)}
                        >
                            <MicVocal size={16} />
                        </IconButton>
                    </Container>
                </Container>

                {showQueue.value && (
                    <Container class="queue-drawer">
                        <Container horizontal centered_y class="queue-head">
                            <Text class="queue-title" content="Up next" />
                            <Text dim content={` · ${queueTracks.length} track${queueTracks.length == 1 ? "" : "s"}`} />
                            <IconButton title="Close queue" onClick={() => { queueOpen.value = false; }}>
                                <X size={14} />
                            </IconButton>
                        </Container>
                        {queueTracks.length === 0 && (
                            <div class="queue-empty">Nothing queued — play an album to fill this up.</div>
                        )}
                        <div class="queue-list">
                            {queueTracks.map((t, i) => (
                                <button
                                    type="button"
                                    key={`${t.id}-${i}`}
                                    class={`queue-row${i === queueIndex.value ? " queue-row-active" : ""}`}
                                    onClick={() => playQueueIndex(i)}
                                >
                                    <Text dim content={i + 1} class="queue-num" />
                                    <span class="queue-info">
                                        <span class="queue-title-text">{t.title}</span>
                                        <span class="queue-artist-text">{t.artist}</span>
                                    </span>
                                    {i === queueIndex.value && <Text dim content={formatTime(position.value)} />}
                                </button>
                            ))}
                            <button
                                type="button"
                                class={`queue-row queue-autoplay${autoplay.value ? " queue-row-active" : ""}`}
                                title={autoplay.value ? "Autoplay on — similar tracks are added at the end" : "Autoplay off"}
                                onClick={() => setAutoplay(!autoplay.value)}
                            >
                                <Radio size={15} />
                                <span class="queue-info">
                                    <span class="queue-title-text">Autoplay</span>
                                    <span class="queue-artist-text">
                                        {autoplay.value ? "On — keep the music going" : "Off"}
                                    </span>
                                </span>
                            </button>
                        </div>
                    </Container>
                )}
            </FooterContainer>
        </>
    );
}
