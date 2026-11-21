import { useState } from "preact/hooks";
import { Image, Container, FooterContainer, IconButton, Slider, Text } from "flufi-ui/components";
import { MicVocal, Pause, Play } from "lucide-preact";
import {
    currentId, duration, formatTime, isPlaying, nowPlaying, playError, position, seekTo, togglePlay
} from "../../common/player";
import { LyricsPanel } from "../Lyrics/LyricsPanel";

import "./style.css";

/**
 * Bottom player: artwork, transport, a flufi Slider for seeking and the
 * lyrics toggle. It renders nothing until a track is loaded.
 */
export function PlayerBar() {
    const track = nowPlaying.value;
    const [showLyrics, setShowLyrics] = useState(false);
    if (!track) return null;

    return (
        <>
            {showLyrics && <LyricsPanel trackId={track.id} onClose={() => setShowLyrics(false)} />}
            <FooterContainer other={{ id: "player-bar" }}>
                <Container horizontal centered_y class="player">
                    <Image
                        class="art"
                        src={`/api/tracks/${currentId.value ?? track.id}/cover`}
                        size={40}
                    />
                    <IconButton
                        title={isPlaying.value ? "Pause" : "Play"}
                        onClick={() => togglePlay()}
                    >
                        {isPlaying.value ? <Pause size={18} /> : <Play size={18} />}
                    </IconButton>
                    <Container vertical class="meta">
                        <Text class="title" content={track.title} />
                        <Text class="artist" dim content={track.artist} />
                        {playError.value && (
                            <Text class="play-error" role="status" content={playError.value} />
                        )}
                    </Container>
                    <Text class="time" dim content={formatTime(position.value)} />
                    <Slider
                        class="seek"
                        value={Math.min(position.value, duration.value)}
                        start={0}
                        end={Math.max(duration.value, 0.001)}
                        step={0.1}
                        onChange={seekTo}
                    />
                    <Text class="time" dim content={formatTime(duration.value)} />
                    <IconButton
                        title="Lyrics"
                        onClick={() => setShowLyrics(v => !v)}
                    >
                        <MicVocal size={17} />
                    </IconButton>
                </Container>
            </FooterContainer>
        </>
    )
}
