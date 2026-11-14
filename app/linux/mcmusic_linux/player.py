"""Playback queue and audio output.

Audio is fetched through the same authenticated ``/api/tracks/<id>/stream``
endpoint the browser uses, cached locally, then handed to QtMultimedia. This
avoids putting a session cookie into a media URL and keeps the engine identical
across Wayland, X11, KDE and wlroots compositors.
"""
from __future__ import annotations

import os
import random
import time
from dataclasses import replace
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from .api import Api, Repo
from .models import Settings, Track

EXT_BY_TYPE = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/aac": ".aac",
    "audio/flac": ".flac",
    "audio/x-flac": ".flac",
    "audio/ogg": ".ogg",
    "audio/opus": ".opus",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/webm": ".webm",
}


def cache_dir() -> Path:
    root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    path = root / "mcmusic" / "audio"
    path.mkdir(parents=True, exist_ok=True)
    return path


class PlayerEngine(QObject):
    changed = Signal()          # current track / queue metadata changed
    tick = Signal()             # position or play state advanced
    error = Signal(str)
    loading_changed = Signal(bool)
    seeked = Signal(float)

    def __init__(self, repo: Repo, api: Api, runner, settings_fn: Callable[[], Settings],
                 parent: QObject | None = None):
        super().__init__(parent)
        self.repo = repo
        self.api = api
        self.runner = runner
        self.settings_fn = settings_fn
        self.cache = cache_dir()

        self.queue: list[Track] = []
        self.index = -1
        self.shuffle = False
        self.repeat = "off"          # off | all | one
        self.loading = False
        self.muted = False
        self._volume = 0.8
        self._duration = 0.0
        self._source_track = 0
        self._token = 0
        self._reported = False
        self._last_seek = 0.0

        self.media = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.media.setAudioOutput(self.audio)
        self.audio.setVolume(self._volume)

        self.media.playbackStateChanged.connect(self._on_state)
        self.media.mediaStatusChanged.connect(self._on_status)
        self.media.errorOccurred.connect(self._on_error)

        self._ticker = QTimer(self)
        self._ticker.setInterval(350)
        self._ticker.timeout.connect(self.tick.emit)
        self._ticker.start()

    # ── state ────────────────────────────────────────────────────────────
    @property
    def current(self) -> Optional[Track]:
        if 0 <= self.index < len(self.queue):
            return self.queue[self.index]
        return None

    @property
    def playing(self) -> bool:
        return self.media.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    @property
    def position(self) -> float:
        pos = self.media.position() / 1000.0
        return max(0.0, pos) if pos > 0 else 0.0

    @property
    def duration(self) -> float:
        dur = self.media.duration() / 1000.0
        if dur > 0:
            return dur
        t = self.current
        return self._duration or (t.duration if t else 0.0)

    @property
    def volume(self) -> float:
        return 0.0 if self.muted else self._volume

    # ── controls ─────────────────────────────────────────────────────────
    def play(self, tracks: list[Track], index: int = 0, shuffle_start: bool = False) -> None:
        if not tracks:
            return
        self.queue = list(tracks)
        self.index = min(max(0, index), len(tracks) - 1)
        if shuffle_start:
            self.shuffle = True
            self.index = random.randrange(len(self.queue))
        self._load()

    def _load(self) -> None:
        track = self.current
        if track is None:
            return
        self._token += 1
        token = self._token
        self._reported = False
        self._duration = track.duration
        self._source_track = 0
        self.media.stop()
        self._set_loading(True)
        self.changed.emit()

        cached = self._cached_file(track.id)
        if cached is not None:
            self._start(token, cached)
            return

        def job() -> Path:
            return self._fetch(track)

        self.runner.submit(
            job,
            ok=lambda path, tok=token: self._start(tok, path),
            error=lambda exc, tok=token: self._load_failed(tok, exc),
        )

    def _start(self, token: int, path: Path) -> None:
        if token != self._token:
            return
        self._source_track = self.current.id if self.current else 0
        self.media.setSource(QUrl.fromLocalFile(str(path)))
        self.media.play()
        self._set_loading(False)
        self.changed.emit()
        if self.settings_fn().prefetch:
            self._prefetch_next()

    def _load_failed(self, token: int, exc: Exception) -> None:
        if token != self._token:
            return
        self._set_loading(False)
        self.error.emit(str(exc) or "Could not load this track")
        self.changed.emit()

    def _cached_file(self, track_id: int) -> Optional[Path]:
        for p in self.cache.glob(f"{track_id}.*"):
            if p.suffix != ".part" and p.stat().st_size > 0:
                return p
        return None

    def _fetch(self, track: Track) -> Path:
        existing = self._cached_file(track.id)
        if existing is not None:
            return existing
        tmp = self.cache / f"{track.id}.audio"
        content_type = self.api.download(f"tracks/{track.id}/stream", tmp)
        ext = EXT_BY_TYPE.get(content_type.split(";")[0].strip().lower(), "")
        if not ext:
            # Fall back to sniffing the first bytes.
            head = tmp.read_bytes()[:12]
            if head.startswith(b"ID3") or head[:2] in (b"\xff\xfb", b"\xff\xf3"):
                ext = ".mp3"
            elif head[:4] == b"fLaC":
                ext = ".flac"
            elif head[:4] == b"OggS":
                ext = ".ogg"
            elif head[4:8] == b"ftyp":
                ext = ".m4a"
            elif head[:4] == b"RIFF":
                ext = ".wav"
            else:
                ext = ".mp3"
        final = self.cache / f"{track.id}{ext}"
        os.replace(tmp, final)
        return final

    def _prefetch_next(self) -> None:
        if not self.queue:
            return
        nxt = self.index + 1
        if nxt >= len(self.queue):
            nxt = 0
        if nxt == self.index or nxt >= len(self.queue):
            return
        track = self.queue[nxt]
        if self._cached_file(track.id) is not None:
            return

        def job() -> Path:
            return self._fetch(track)

        self.runner.submit(job, error=lambda _exc: None)

    def toggle(self) -> None:
        if not self.queue:
            return
        if self.playing:
            self.media.pause()
        elif self.media.source().isEmpty() or self._source_track != (self.current.id if self.current else 0):
            self._load()
        else:
            self.media.play()

    def pause(self) -> None:
        self.media.pause()

    def resume(self) -> None:
        if self.queue and not self.playing:
            self.toggle()

    def next(self, auto: bool = False) -> None:
        if not self.queue:
            return
        count = len(self.queue)
        if auto and self.repeat == "one":
            self.seek(0)
            self.media.play()
            return
        if self.shuffle and count > 1:
            choice = random.randrange(count - 1)
            self.index = choice + 1 if choice >= self.index else choice
        elif self.index + 1 < count:
            self.index += 1
        elif self.repeat == "all" or not auto:
            self.index = 0
        else:
            self.media.stop()
            self.changed.emit()
            return
        self._load()

    def prev(self) -> None:
        if not self.queue:
            return
        if self.position > 3.0:
            self.seek(0)
            return
        if self.shuffle and len(self.queue) > 1:
            self.index = random.randrange(len(self.queue))
        else:
            self.index = (self.index - 1) % len(self.queue)
        self._load()

    def seek(self, seconds: float) -> None:
        if not self.queue:
            return
        seconds = max(0.0, seconds)
        self.media.setPosition(int(seconds * 1000))
        self._last_seek = time.time()
        self.seeked.emit(seconds)
        self.tick.emit()

    def seek_fraction(self, fraction: float) -> None:
        fraction = min(1.0, max(0.0, fraction))
        self.seek(fraction * max(0.1, self.duration))

    def set_volume(self, value: float) -> None:
        self._volume = min(1.0, max(0.0, float(value)))
        self.muted = self._volume <= 0.001
        self.audio.setVolume(0.0 if self.muted else self._volume)

    def toggle_mute(self) -> None:
        self.muted = not self.muted
        self.audio.setVolume(0.0 if self.muted else self._volume)

    def toggle_shuffle(self) -> None:
        self.shuffle = not self.shuffle
        self.changed.emit()

    def cycle_repeat(self) -> None:
        self.repeat = {"off": "all", "all": "one", "one": "off"}[self.repeat]
        self.changed.emit()

    def jump(self, index: int) -> None:
        if 0 <= index < len(self.queue):
            self.index = index
            self._load()

    def add(self, track: Track, next: bool = False) -> None:
        if not self.queue:
            self.play([track], 0)
            return
        if next:
            self.queue.insert(self.index + 1, track)
        else:
            self.queue.append(track)
        self.changed.emit()

    def remove_at(self, at: int) -> None:
        if not (0 <= at < len(self.queue)):
            return
        was_current = at == self.index
        self.queue.pop(at)
        if at < self.index:
            self.index -= 1
        elif was_current:
            if not self.queue:
                self.index = -1
                self.media.stop()
            else:
                self.index = min(self.index, len(self.queue) - 1)
                self._load()
        self.changed.emit()

    def clear_upcoming(self) -> None:
        if self.index >= 0:
            self.queue = self.queue[: self.index + 1]
        else:
            self.queue = []
        self.changed.emit()

    def mark_liked(self, track_id: int, liked: bool) -> None:
        self.queue = [replace(t, liked=liked) if t.id == track_id else t for t in self.queue]
        self.changed.emit()

    def mark_explicit(self, track_id: int, explicit: bool) -> None:
        self.queue = [replace(t, explicit=explicit) if t.id == track_id else t for t in self.queue]
        self.changed.emit()

    def queue_ids(self) -> list[int]:
        return [t.id for t in self.queue]

    def clear(self) -> None:
        self._token += 1
        self.queue = []
        self.index = -1
        self._source_track = 0
        self.media.stop()
        self.media.setSource(QUrl())
        self.changed.emit()

    def shutdown(self) -> None:
        self._token += 1
        self.media.stop()
        self._ticker.stop()

    # ── media callbacks ─────────────────────────────────────────────────
    def _set_loading(self, value: bool) -> None:
        if self.loading != value:
            self.loading = value
            self.loading_changed.emit(value)

    def _on_state(self, _state) -> None:
        self.tick.emit()
        self.changed.emit()
        if self.playing and not self._reported and self.current:
            self._reported = True
            track = self.current

            def report() -> None:
                self.repo.report_play(track.id, False)

            QTimer.singleShot(2500, lambda: self.runner.submit(report, error=lambda _e: None))

    def _on_status(self, status) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            track = self.current
            if track:
                tid = track.id

                def report_done() -> None:
                    self.repo.report_play(tid, True)

                self.runner.submit(report_done, error=lambda _e: None)
            self.next(auto=True)
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self._set_loading(False)
            self.error.emit("This file could not be played")
        elif status in (QMediaPlayer.MediaStatus.LoadingMedia,
                        QMediaPlayer.MediaStatus.BufferingMedia):
            self._set_loading(True)
        elif status in (QMediaPlayer.MediaStatus.LoadedMedia,
                        QMediaPlayer.MediaStatus.BufferedMedia):
            self._set_loading(False)
            self.changed.emit()

    def _on_error(self, _error, message: str) -> None:
        self._set_loading(False)
        self.error.emit(message or "Audio backend error")
