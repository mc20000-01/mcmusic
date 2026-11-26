"""Headless stand-ins for Qt Multimedia's audio backends.

CI runners and containers have no audio device, and constructing a real
``QAudioOutput`` there can segfault inside Qt's platform plugin. The stub is
opt-in via ``MC_MUSIC_QT_AUDIO_STUB=1``: production code still constructs the
real objects, while the widget suite can exercise the same window and player
logic without touching a sound card. It is not a blanket exception handler —
Python errors in the client still fail the tests normally.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QUrl, Signal


class FakeAudioOutput(QObject):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._volume = 1.0
        self._muted = False

    def setVolume(self, value: float) -> None:
        self._volume = float(value)

    def volume(self) -> float:
        return self._volume

    def setMuted(self, muted: bool) -> None:
        self._muted = bool(muted)

    def muted(self) -> bool:
        return self._muted


class FakeMediaPlayer(QObject):
    class PlaybackState:
        StoppedState = 0
        PlayingState = 1
        PausedState = 2

    class MediaStatus:
        NoMedia = 0
        LoadingMedia = 1
        LoadedMedia = 2
        StalledMedia = 3
        BufferingMedia = 4
        BufferedMedia = 5
        EndOfMedia = 6
        InvalidMedia = 7

    class Error:
        NoError = 0
        ResourceError = 1
        FormatError = 2
        NetworkError = 3
        AccessDeniedError = 4

    playbackStateChanged = Signal(object)
    mediaStatusChanged = Signal(object)
    errorOccurred = Signal(object, str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._state = self.PlaybackState.StoppedState
        self._source = QUrl()
        self._position = 0

    def setAudioOutput(self, _output) -> None:
        pass

    def playbackState(self):
        return self._state

    def mediaStatus(self):
        return self.MediaStatus.NoMedia

    def source(self) -> QUrl:
        return self._source

    def setSource(self, source: QUrl) -> None:
        self._source = QUrl(source)
        self._position = 0

    def position(self) -> int:
        return self._position

    def setPosition(self, value: int) -> None:
        self._position = max(0, int(value))

    def duration(self) -> int:
        return 0

    def play(self) -> None:
        self._state = self.PlaybackState.PlayingState
        self.playbackStateChanged.emit(self._state)

    def pause(self) -> None:
        self._state = self.PlaybackState.PausedState
        self.playbackStateChanged.emit(self._state)

    def stop(self) -> None:
        self._state = self.PlaybackState.StoppedState
        self.playbackStateChanged.emit(self._state)


def install() -> None:
    """Replace the audio classes inside the player module only."""
    from mcmusic_linux import player

    player.QAudioOutput = FakeAudioOutput
    player.QMediaPlayer = FakeMediaPlayer
