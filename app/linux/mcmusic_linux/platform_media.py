"""Native Now Playing bridges for macOS and Windows.

Linux keeps its D-Bus/MPRIS2 implementation in :mod:`mcmusic_linux.mpris`.
Here we publish the same playback state to ``MPNowPlayingInfoCenter`` (macOS)
and the System Media Transport Controls (Windows) and forward their media-key
commands back into :class:`~mcmusic_linux.player.PlayerEngine`.

Both OS backends are optional. Importing this module never imports PyObjC or
winsdk, so the shared client stays installable on any platform without the
matching native packages; ``enabled`` reports whether a bridge came up.
"""
from __future__ import annotations

import sys
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, Qt, Signal

from .player import PlayerEngine


class MediaBridge(QObject):
    """Publishes playback metadata and relays OS media controls to the player."""

    command_requested = Signal(str, float)

    def __init__(self, player: PlayerEngine, parent: QObject | None = None):
        super().__init__(parent)
        self.player = player
        self.backend: Optional[Any] = None
        self.enabled = False
        self._last_metadata = ""
        self._last_state = ""
        self._last_position = -1.0
        self.command_requested.connect(self._command, Qt.ConnectionType.QueuedConnection)

        if sys.platform == "darwin":
            factory: Optional[Callable[[MediaBridge], Any]] = _mac_backend
        elif sys.platform == "win32":
            factory = _windows_backend
        else:
            factory = None
        if factory is not None:
            try:
                self.backend = factory(self)
                self.enabled = True
            except Exception:
                # A missing optional dependency must never break the desktop app.
                self.backend = None
        if self.enabled:
            player.changed.connect(self.publish)
            player.tick.connect(self.publish_timeline)
            player.seeked.connect(self.publish)
            self.publish()

    # ── commands ─────────────────────────────────────────────────────────
    def _command(self, action: str, arg: float = 0.0) -> None:
        player = self.player
        if action == "play":
            if not player.playing:
                player.toggle()
        elif action == "pause":
            if player.playing:
                player.toggle()
        elif action == "toggle":
            player.toggle()
        elif action == "next":
            player.next()
        elif action in ("prev", "previous"):
            player.prev()
        elif action == "stop":
            player.media.stop()
        elif action == "seek":
            player.seek(max(0.0, float(arg)))

    # ── state publication ────────────────────────────────────────────────
    def publish(self) -> None:
        if not self.enabled or self.backend is None:
            return
        track = self.player.current
        metadata = (
            (track.id, track.title, track.artist, track.album, int(track.duration))
            if track is not None else ()
        )
        state = "playing" if self.player.playing else ("paused" if track else "stopped")
        self._last_metadata = repr(metadata)
        self._last_state = state
        self._last_position = self.player.position
        try:
            self.backend.update(track, state, self.player.position,
                                self.player.duration, metadata_key=self._last_metadata,
                                state_key=state)
        except Exception:
            pass

    def publish_timeline(self) -> None:
        if not self.enabled or self.backend is None:
            return
        position = self.player.position
        state = "playing" if self.player.playing else ("paused" if self.player.current else "stopped")
        if abs(position - self._last_position) < 0.9 and state == self._last_state:
            return
        self._last_position = position
        self._last_state = state
        try:
            self.backend.timeline(position, self.player.duration, state)
        except Exception:
            pass

    def shutdown(self) -> None:
        if self.backend is None:
            return
        try:
            self.backend.close()
        except Exception:
            pass
        self.backend = None
        self.enabled = False


# ── macOS ────────────────────────────────────────────────────────────────────


def _mac_backend(bridge: MediaBridge) -> Any:
    from Foundation import NSMutableDictionary
    from MediaPlayer import (
        MPMediaItemPropertyAlbumTitle,
        MPMediaItemPropertyArtist,
        MPMediaItemPropertyPlaybackDuration,
        MPMediaItemPropertyTitle,
        MPMusicPlaybackStatePaused,
        MPMusicPlaybackStatePlaying,
        MPMusicPlaybackStateStopped,
        MPNowPlayingInfoCenter,
        MPNowPlayingInfoPropertyElapsedPlaybackTime,
        MPNowPlayingInfoPropertyPlaybackRate,
        MPRemoteCommandCenter,
    )

    class Backend:
        def __init__(self):
            self.info = MPNowPlayingInfoCenter.defaultCenter()
            self.center = MPRemoteCommandCenter.sharedCommandCenter()
            self.tokens: list[Any] = []
            commands = {
                "playCommand": "play",
                "pauseCommand": "pause",
                "togglePlayPauseCommand": "toggle",
                "nextTrackCommand": "next",
                "previousTrackCommand": "prev",
                "stopCommand": "stop",
                "changePlaybackPositionCommand": "seek",
            }
            for selector, action in commands.items():
                command = getattr(self.center, selector, None)
                if command is None:
                    continue
                command = command()
                if command is None:
                    continue
                # Remote commands are disabled until the app opts in.
                command.setEnabled_(True)

                def handler(event, action=action):
                    arg = 0.0
                    if action == "seek":
                        try:
                            arg = float(event.playbackPosition())
                        except Exception:
                            pass
                    bridge.command_requested.emit(action, arg)
                    return 0

                token = command.addTargetWithHandler_(handler)
                self.tokens.append((command, token))

        def update(self, track, state, position, duration, **_kwargs):
            info = NSMutableDictionary.dictionary()
            if track is not None:
                info[MPMediaItemPropertyTitle] = track.title or ""
                info[MPMediaItemPropertyArtist] = track.artist or ""
                if getattr(track, "album", ""):
                    info[MPMediaItemPropertyAlbumTitle] = track.album
                if duration > 0:
                    info[MPMediaItemPropertyPlaybackDuration] = float(duration)
                info[MPNowPlayingInfoPropertyElapsedPlaybackTime] = float(position)
                info[MPNowPlayingInfoPropertyPlaybackRate] = (
                    1.0 if state == "playing" else 0.0
                )
                self.info.setPlaybackState_(
                    MPMusicPlaybackStatePlaying if state == "playing"
                    else MPMusicPlaybackStatePaused
                )
            else:
                self.info.setPlaybackState_(MPMusicPlaybackStateStopped)
            self.info.setNowPlayingInfo_(info)

        def timeline(self, position, duration, state):
            current = dict(self.info.nowPlayingInfo() or {})
            current[MPNowPlayingInfoPropertyElapsedPlaybackTime] = float(position)
            current[MPNowPlayingInfoPropertyPlaybackRate] = 1.0 if state == "playing" else 0.0
            if duration > 0:
                current[MPMediaItemPropertyPlaybackDuration] = float(duration)
            self.info.setNowPlayingInfo_(current)

        def close(self):
            for command, token in self.tokens:
                try:
                    command.removeTarget_(token)
                except Exception:
                    pass
            self.tokens.clear()
            self.info.setNowPlayingInfo_(NSMutableDictionary.dictionary())
            self.info.setPlaybackState_(MPMusicPlaybackStateStopped)

    return Backend()


# ── Windows ──────────────────────────────────────────────────────────────────


def _windows_backend(bridge: MediaBridge) -> Any:
    from datetime import timedelta

    from winsdk.windows.media import (
        MediaPlaybackStatus,
        MediaPlaybackType,
        SystemMediaTransportControls,
        SystemMediaTransportControlsButton,
        SystemMediaTransportControlsTimelineProperties,
    )

    class Backend:
        def __init__(self):
            self.smtc = SystemMediaTransportControls.get_for_current_view()
            if self.smtc is None:
                raise RuntimeError("no SMTC for this app view")
            self.smtc.is_enabled = True
            self.smtc.is_play_enabled = True
            self.smtc.is_pause_enabled = True
            self.smtc.is_next_enabled = True
            self.smtc.is_previous_enabled = True
            self.smtc.is_stop_enabled = True
            self.smtc.add_button_pressed(self._button)
            self.smtc.add_playback_position_change_requested(self._seek)

        def _button(self, _sender, args):
            mapping = {
                SystemMediaTransportControlsButton.PLAY: "play",
                SystemMediaTransportControlsButton.PAUSE: "pause",
                SystemMediaTransportControlsButton.NEXT: "next",
                SystemMediaTransportControlsButton.PREVIOUS: "prev",
                SystemMediaTransportControlsButton.STOP: "stop",
            }
            action = mapping.get(getattr(args, "button", None))
            if action:
                bridge.command_requested.emit(action, 0.0)

        def _seek(self, _sender, args):
            try:
                seconds = args.requested_playback_position.total_seconds()
            except Exception:
                seconds = 0.0
            bridge.command_requested.emit("seek", float(seconds))

        def update(self, track, state, position, duration, **_kwargs):
            self.smtc.playback_status = {
                "playing": MediaPlaybackStatus.PLAYING,
                "paused": MediaPlaybackStatus.PAUSED,
                "stopped": MediaPlaybackStatus.STOPPED,
            }.get(state, MediaPlaybackStatus.STOPPED)
            updater = self.smtc.display_updater
            if updater is None:
                return
            updater.type = MediaPlaybackType.MUSIC
            if track is None:
                updater.clear_all()
            else:
                music = updater.music_properties
                if music is not None:
                    music.title = track.title or ""
                    music.artist = track.artist or ""
                    if getattr(track, "album", ""):
                        music.album_title = track.album
                self.timeline(position, duration, state)
            updater.update()

        def timeline(self, position, duration, state):
            props = SystemMediaTransportControlsTimelineProperties()
            props.start_time = timedelta(0)
            props.min_seek_time = timedelta(0)
            props.position = timedelta(seconds=max(0.0, float(position)))
            end = max(float(position), float(duration or 0))
            props.max_seek_time = timedelta(seconds=end)
            props.end_time = timedelta(seconds=end)
            self.smtc.update_timeline_properties(props)

        def close(self):
            self.smtc.is_enabled = False
            self.smtc.playback_status = MediaPlaybackStatus.STOPPED
            updater = self.smtc.display_updater
            if updater is not None:
                updater.clear_all()
                updater.update()

    return Backend()
