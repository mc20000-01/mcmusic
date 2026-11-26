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

from .api import Api, Repo, SessionStore
from .models import Settings, Track
from .paths import audio_cache_dir

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
    path = audio_cache_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


class PlayerEngine(QObject):
    changed = Signal()          # current track / queue metadata changed
    tick = Signal()             # position or play state advanced
    error = Signal(str)
    loading_changed = Signal(bool)
    seeked = Signal(float)
    natural_end = Signal(int)   # current track ended at the queue tail

    def __init__(self, repo: Repo, api: Api, runner, settings_fn: Callable[[], Settings],
                 parent: QObject | None = None, store: SessionStore | None = None):
        super().__init__(parent)
        self.repo = repo
        self.api = api
        self.runner = runner
        self.settings_fn = settings_fn
        self.store = store
        self.cache = cache_dir()

        self.queue: list[Track] = []
        self.index = -1
        self.shuffle = False
        self.model_shuffle = False   # MDL ordered the queue; no random skips
        self.repeat = "off"          # off | all | one
        self.loading = False
        self.muted = False
        self._volume = 0.8
        self._duration = 0.0
        self._source_track = 0
        self._source_token = 0
        self._token = 0
        self._reported = False
        self._end_pending = False
        self._last_seek = 0.0
        self._last_snapshot = 0.0
        self._last_played_id = 0
        self._restore_position = 0.0
        self.changed.connect(self._snapshot_throttled)

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
        self._discard_previous_cache()
        self.queue = list(tracks)
        self.index = min(max(0, index), len(tracks) - 1)
        self.model_shuffle = False
        if shuffle_start:
            self.shuffle = True
            self.index = random.randrange(len(self.queue))
        self._restore_position = 0.0
        self._load()
        self.save_snapshot()

    def _load(self, autostart: bool = True) -> None:
        track = self.current
        if track is None:
            return
        self._discard_previous_cache()
        self._token += 1
        token = self._token
        self._reported = False
        self._end_pending = False
        self._duration = track.duration
        self._source_track = 0
        self.media.stop()
        self._set_loading(True)
        self.changed.emit()

        cached = self._cached_file(track.id)
        if cached is not None:
            self._start(token, cached, autostart)
            return

        def job() -> Path:
            return self._fetch(track)

        self.runner.submit(
            job,
            ok=lambda path, tok=token: self._start(tok, path, autostart),
            error=lambda exc, tok=token: self._load_failed(tok, exc),
        )

    def _start(self, token: int, path: Path, autostart: bool = True) -> None:
        if token != self._token:
            return
        self._source_track = self.current.id if self.current else 0
        self._source_token = token
        self.media.setSource(QUrl.fromLocalFile(str(path)))
        if autostart:
            self.media.play()
        else:
            self.media.pause()
            position = self._restore_position
            self._restore_position = 0.0
            if position > 0:
                QTimer.singleShot(400, lambda p=position, t=token: self._restore_seek(t, p))
        self._last_played_id = self._source_track
        self._set_loading(False)
        self.changed.emit()
        settings = self.settings_fn()
        if settings.prefetch and settings.offline_audio:
            self._prefetch_next()

    def _restore_seek(self, token: int, position: float) -> None:
        if token == self._token:
            self.media.setPosition(int(position * 1000))
            self.tick.emit()

    def _discard_previous_cache(self) -> None:
        """offline_audio off means 'stream cache': drop the previous file."""
        if self.settings_fn().offline_audio or not self._last_played_id:
            return
        if self._last_played_id == (self.current.id if self.current else 0):
            return
        for p in self.cache.glob(f"{self._last_played_id}.*"):
            if p.suffix != ".part":
                try:
                    p.unlink()
                except OSError:
                    pass
        self._last_played_id = 0

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

    def _report_skip(self) -> None:
        track = self.current
        if track is None or self.position < 3.0 or not self.playing:
            return
        self.runner.submit(
            lambda: self.repo.report_metric(track.id, "skip", self.position, self.duration),
            error=lambda _e: None,
        )

    def next(self, auto: bool = False) -> None:
        if not self.queue:
            return
        if not auto:
            self._report_skip()
        count = len(self.queue)
        if auto and self.repeat == "one":
            self.seek(0)
            self.media.play()
            return
        if self.shuffle and not self.model_shuffle and count > 1:
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
        self._report_skip()
        if self.position > 3.0:
            self.seek(0)
            return
        if self.shuffle and not self.model_shuffle and len(self.queue) > 1:
            self.index = random.randrange(len(self.queue))
        else:
            self.index = (self.index - 1) % len(self.queue)
        self._load()

    def seek(self, seconds: float) -> None:
        if not self.queue:
            return
        seconds = max(0.0, seconds)
        previous = self.position
        self.media.setPosition(int(seconds * 1000))
        if abs(seconds - previous) > 1.0 and self.current and self._source_token == self._token:
            tid = self.current.id
            self.runner.submit(
                lambda: self.repo.report_metric(tid, "seek", seconds, self.duration),
                error=lambda _e: None,
            )
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
        if not self.shuffle:
            self.model_shuffle = False
        self.changed.emit()

    def apply_model_order(self, ids: list[int]) -> bool:
        """Adopt an MDL queue order without reloading the current song."""
        if len(ids) < 2 or not self.current:
            return False
        by_id = {t.id: t for t in self.queue}
        ranked = [by_id[i] for i in ids if i in by_id]
        if len(ranked) < 2:
            return False
        seen = {t.id for t in ranked}
        ordered = ranked + [t for t in self.queue if t.id not in seen]
        index = next((i for i, t in enumerate(ordered) if t.id == self.current.id), 0)
        self.queue = ordered
        self.index = index
        self.model_shuffle = True
        self.save_snapshot()
        self.changed.emit()
        return True

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

    def move(self, from_index: int, to_index: int) -> bool:
        """Reorder upcoming tracks, keeping the current track at its position.

        Returns True when the queue actually changed so callers can restore
        focus on the moved row.
        """
        count = len(self.queue)
        if not (0 <= from_index < count and 0 <= to_index < count):
            return False
        if from_index == to_index or from_index == self.index or to_index <= self.index:
            return False
        track = self.queue.pop(from_index)
        self.queue.insert(to_index, track)
        self.changed.emit()
        self.save_snapshot()
        return True

    # ── queue snapshot ───────────────────────────────────────────────────
    def save_snapshot(self) -> None:
        if self.store is None:
            return
        self._last_snapshot = time.time()
        self.store.queue_snapshot = {
            "tracks": [
                {"id": t.id, "title": t.title, "artist": t.artist, "album": t.album,
                 "track_no": t.track_no, "genre": t.genre, "year": t.year,
                 "duration": t.duration, "liked": t.liked, "explicit": t.explicit,
                 "yt_id": t.yt_id, "yt_likes": t.yt_likes, "yt_views": t.yt_views,
                 "yt_channel": t.yt_channel, "yt_date": t.yt_date, "added": t.added}
                for t in self.queue[:200]
            ],
            "index": self.index,
            "shuffle": self.shuffle,
            "model_shuffle": self.model_shuffle,
            "repeat": self.repeat,
            "position": self.position if self.current else 0.0,
            "paused": not self.playing,
            "at": time.time(),
        }

    def _snapshot_throttled(self) -> None:
        if time.time() - self._last_snapshot > 4:
            self.save_snapshot()

    def restore_snapshot(self, valid_ids: set[int] | None = None) -> bool:
        """Restore a saved queue. Stale track ids and positions are dropped."""
        if self.store is None:
            return False
        snap = self.store.queue_snapshot
        rows = snap.get("tracks") if isinstance(snap, dict) else None
        if not isinstance(rows, list) or not rows:
            return False
        tracks: list[Track] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                track = Track.from_json(row)
            except (TypeError, ValueError):
                continue
            if track.id <= 0:
                continue
            if valid_ids is not None and track.id not in valid_ids:
                continue
            tracks.append(track)
        if not tracks:
            return False
        try:
            index = int(snap.get("index", 0))
        except (TypeError, ValueError):
            index = 0
        self.queue = tracks[:200]
        self.index = max(0, min(index, len(self.queue) - 1))
        self.shuffle = bool(snap.get("shuffle"))
        self.model_shuffle = bool(snap.get("model_shuffle"))
        self.repeat = str(snap.get("repeat") or "off")
        if self.repeat not in ("off", "all", "one"):
            self.repeat = "off"
        try:
            self._restore_position = float(snap.get("position", 0) or 0)
        except (TypeError, ValueError):
            self._restore_position = 0.0
        if snap.get("paused") is False and self._restore_position <= 0:
            self._restore_position = 0.0
        self._load(autostart=False)
        return True

    def clear(self) -> None:
        self._token += 1
        self.queue = []
        self.index = -1
        self._source_track = 0
        self._source_token = 0
        self._end_pending = False
        self._restore_position = 0.0
        self.media.stop()
        self.media.setSource(QUrl())
        if self.store is not None:
            self.store.queue_snapshot = {}
        self.changed.emit()

    def shutdown(self) -> None:
        if self.queue:
            self.save_snapshot()
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
                self.repo.report_metric(track.id, "play", self.position, self.duration)

            QTimer.singleShot(2500, lambda: self.runner.submit(report, error=lambda _e: None))

    def _on_status(self, status) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            track = self.current
            # Ignore statuses left over from a source that has already been
            # replaced by a manual skip or a new queue.
            if track is None or self._source_token != self._token:
                return
            if self._source_track != track.id:
                return
            if not self._end_pending:
                tid = track.id

                def report_done() -> None:
                    self.repo.report_play(tid, True)
                    self.repo.report_metric(tid, "complete", self.duration, self.duration)

                self.runner.submit(report_done, error=lambda _e: None)
            if self.repeat == "one":
                self.next(auto=True)
                return
            if self.index + 1 < len(self.queue):
                self.jump(self.index + 1)
                return
            if self.repeat == "all":
                self.jump(0)
                return
            if self._end_pending:
                return
            # Only a natural end of the last track, with repeat off, may ask
            # the shell to extend the queue. Manual Next never reaches here.
            self._end_pending = True
            self.media.stop()
            self.natural_end.emit(track.id)
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
