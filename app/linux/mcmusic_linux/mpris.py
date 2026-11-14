"""MPRIS2 media controls (KDE Plasma, GNOME shell, playerctl, Waybar…).

Optional and fully defensive: without a session bus the app simply runs without
media-control integration.

PySide6 does not expose ``Q_CLASSINFO``, so a ``QDBusAbstractAdaptor`` cannot
declare the MPRIS interface names. Instead the service is a
``QDBusVirtualObject`` that answers the small, fixed MPRIS surface directly.
"""
from __future__ import annotations

import time
from typing import Any, Callable

from PySide6.QtCore import QObject
from PySide6.QtDBus import (
    QDBusConnection,
    QDBusMessage,
    QDBusVariant,
    QDBusVirtualObject,
)

try:  # not exported by every PySide6 build
    from PySide6.QtDBus import QDBusObjectPath  # type: ignore
except Exception:  # pragma: no cover
    QDBusObjectPath = None  # type: ignore

SERVICE = "org.mpris.MediaPlayer2.mcmusic"
PATH = "/org/mpris/MediaPlayer2"
ROOT = "org.mpris.MediaPlayer2"
PLAYER = "org.mpris.MediaPlayer2.Player"
PROPS = "org.freedesktop.DBus.Properties"

INTROSPECT = f"""<!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
<node>
  <interface name="org.freedesktop.DBus.Introspectable">
    <method name="Introspect">
      <arg name="xml_data" type="s" direction="out"/>
    </method>
  </interface>
  <interface name="{PROPS}">
    <method name="Get">
      <arg name="interface_name" type="s" direction="in"/>
      <arg name="property_name" type="s" direction="in"/>
      <arg name="value" type="v" direction="out"/>
    </method>
    <method name="GetAll">
      <arg name="interface_name" type="s" direction="in"/>
      <arg name="properties" type="a{{sv}}" direction="out"/>
    </method>
    <method name="Set">
      <arg name="interface_name" type="s" direction="in"/>
      <arg name="property_name" type="s" direction="in"/>
      <arg name="value" type="v" direction="in"/>
    </method>
    <signal name="PropertiesChanged">
      <arg name="interface_name" type="s"/>
      <arg name="changed_properties" type="a{{sv}}"/>
      <arg name="invalidated_properties" type="as"/>
    </signal>
  </interface>
  <interface name="{ROOT}">
    <method name="Raise"/>
    <method name="Quit"/>
    <property name="CanQuit" type="b" access="read"/>
    <property name="CanRaise" type="b" access="read"/>
    <property name="HasTrackList" type="b" access="read"/>
    <property name="Identity" type="s" access="read"/>
    <property name="DesktopEntry" type="s" access="read"/>
    <property name="SupportedUriSchemes" type="as" access="read"/>
    <property name="SupportedMimeTypes" type="as" access="read"/>
  </interface>
  <interface name="{PLAYER}">
    <method name="Next"/>
    <method name="Previous"/>
    <method name="Pause"/>
    <method name="Play"/>
    <method name="PlayPause"/>
    <method name="Stop"/>
    <method name="Seek">
      <arg name="Offset" type="x" direction="in"/>
    </method>
    <method name="SetPosition">
      <arg name="TrackId" type="o" direction="in"/>
      <arg name="Position" type="x" direction="in"/>
    </method>
    <method name="OpenUri">
      <arg name="Uri" type="s" direction="in"/>
    </method>
    <signal name="Seeked">
      <arg name="Position" type="x"/>
    </signal>
    <property name="PlaybackStatus" type="s" access="read"/>
    <property name="LoopStatus" type="s" access="readwrite"/>
    <property name="Rate" type="d" access="read"/>
    <property name="Shuffle" type="b" access="readwrite"/>
    <property name="Metadata" type="a{{sv}}" access="read"/>
    <property name="Volume" type="d" access="readwrite"/>
    <property name="Position" type="x" access="read"/>
    <property name="MinimumRate" type="d" access="read"/>
    <property name="MaximumRate" type="d" access="read"/>
    <property name="CanGoNext" type="b" access="read"/>
    <property name="CanGoPrevious" type="b" access="read"/>
    <property name="CanPlay" type="b" access="read"/>
    <property name="CanPause" type="b" access="read"/>
    <property name="CanSeek" type="b" access="read"/>
    <property name="CanControl" type="b" access="read"/>
  </interface>
</node>
"""


def _unwrap(value: Any) -> Any:
    return value.variant() if isinstance(value, QDBusVariant) else value


class _Service(QDBusVirtualObject):
    def __init__(self, engine, quit_cb: Callable[[], None]):
        super().__init__()
        self.engine = engine
        self._quit = quit_cb

    # ── QDBusVirtualObject ───────────────────────────────────────────────
    def introspect(self, _path: str) -> str:
        return INTROSPECT

    def handleMessage(self, message: QDBusMessage, connection: QDBusConnection) -> bool:
        iface = message.interface() or ""
        member = message.member() or ""
        args = list(message.arguments())
        try:
            if iface == "org.freedesktop.DBus.Introspectable" and member == "Introspect":
                connection.send(message.createReply([INTROSPECT]))
                return True
            if iface == PROPS:
                self._properties(message, connection, member, args)
                return True
            if iface == ROOT:
                if member == "Quit":
                    self._quit()
                elif member != "Raise":
                    return False
                connection.send(message.createReply())
                return True
            if iface == PLAYER:
                self._player(message, connection, member, args)
                return True
            return False
        except Exception as exc:  # never let a bad client kill the app
            connection.send(message.createErrorReply(
                "org.freedesktop.DBus.Error.Failed", f"mcmusic: {exc}"))
            return True

    # ── properties ───────────────────────────────────────────────────────
    def _all(self, iface: str) -> dict[str, Any] | None:
        engine = self.engine
        if iface == ROOT:
            return {
                "CanQuit": True,
                "CanRaise": True,
                "HasTrackList": False,
                "Identity": "mcmusic",
                "DesktopEntry": "mcmusic",
                "SupportedUriSchemes": [],
                "SupportedMimeTypes": [],
            }
        if iface != PLAYER:
            return None
        track = getattr(engine, "current", None)
        status = "Playing" if getattr(engine, "playing", False) else (
            "Paused" if track is not None else "Stopped")
        return {
            "PlaybackStatus": status,
            "LoopStatus": {"off": "None", "all": "Playlist", "one": "Track"}.get(
                getattr(engine, "repeat", "off"), "None"),
            "Rate": 1.0,
            "Shuffle": bool(getattr(engine, "shuffle", False)),
            "Metadata": self._metadata(),
            "Volume": float(getattr(engine, "volume", 0.0)),
            "Position": int(getattr(engine, "position", 0.0) * 1_000_000),
            "MinimumRate": 1.0,
            "MaximumRate": 1.0,
            "CanGoNext": bool(getattr(engine, "queue", [])),
            "CanGoPrevious": bool(getattr(engine, "queue", [])),
            "CanPlay": bool(getattr(engine, "queue", [])),
            "CanPause": bool(getattr(engine, "queue", [])),
            "CanSeek": bool(getattr(engine, "queue", [])),
            "CanControl": True,
        }

    def _metadata(self) -> dict[str, Any]:
        track = getattr(self.engine, "current", None)
        if track is None:
            return {}
        length = int((getattr(self.engine, "duration", 0.0) or track.duration) * 1_000_000)
        track_id: Any = f"/org/mcmusic/track/{track.id}"
        if QDBusObjectPath is not None:
            try:
                track_id = QDBusObjectPath(track_id)
            except Exception:
                pass
        return {
            "mpris:trackid": track_id,
            "mpris:length": length,
            "xesam:title": track.title,
            "xesam:artist": [track.artist],
            "xesam:album": track.album,
            "xesam:genre": [track.genre] if track.genre else [],
            "xesam:contentCreated": track.year,
        }

    def _properties(self, message, connection, member: str, args: list[Any]) -> None:
        def fail(name: str, text: str) -> None:
            connection.send(message.createErrorReply(
                f"org.freedesktop.DBus.Error.{name}", text))

        if member == "Get":
            iface, prop = str(args[0]), str(args[1])
            props = self._all(iface)
            if props is None:
                fail("InvalidArgs", f"Unknown interface {iface}")
                return
            if prop not in props:
                fail("UnknownProperty", f"Unknown property {prop}")
                return
            connection.send(message.createReply(QDBusVariant(props[prop])))
            return
        if member == "GetAll":
            iface = str(args[0])
            props = self._all(iface)
            if props is None:
                fail("InvalidArgs", f"Unknown interface {iface}")
                return
            connection.send(message.createReply(props))
            return
        if member == "Set":
            iface, prop = str(args[0]), str(args[1])
            value = _unwrap(args[2] if len(args) > 2 else None)
            if iface != PLAYER or prop not in ("LoopStatus", "Shuffle", "Volume"):
                fail("PropertyReadOnly", f"{prop} is read-only")
                return
            engine = self.engine
            if prop == "LoopStatus":
                engine.repeat = {"None": "off", "Playlist": "all", "Track": "one"}.get(
                    str(value), "off")
            elif prop == "Shuffle":
                engine.shuffle = bool(value)
            else:
                try:
                    engine.set_volume(float(value))
                except Exception:
                    pass
            self._emit_changed({prop: value})
            connection.send(message.createReply())
            return
        if member == "PropertiesChanged":
            return
        fail("UnknownMethod", member)

    # ── player methods ───────────────────────────────────────────────────
    def _player(self, message, connection, member: str, args: list[Any]) -> None:
        engine = self.engine
        if member == "Next":
            engine.next()
        elif member == "Previous":
            engine.prev()
        elif member == "Pause":
            engine.pause()
        elif member == "Play":
            engine.resume()
        elif member == "PlayPause":
            engine.toggle()
        elif member == "Stop":
            engine.pause()
            engine.seek(0.0)
        elif member == "Seek" and args:
            engine.seek(float(engine.position) + int(_unwrap(args[0])) / 1_000_000)
        elif member == "SetPosition" and len(args) > 1:
            engine.seek(int(_unwrap(args[1])) / 1_000_000)
        elif member == "OpenUri":
            pass
        else:
            connection.send(message.createErrorReply(
                "org.freedesktop.DBus.Error.UnknownMethod", f"Unknown method {member}"))
            return
        connection.send(message.createReply())

    # ── signals ──────────────────────────────────────────────────────────
    def _emit_changed(self, changed: dict[str, Any]) -> None:
        bus = self._bus
        if bus is None:
            return
        msg = QDBusMessage.createSignal(PATH, PROPS, "PropertiesChanged")
        msg.setArguments([PLAYER, changed, []])
        bus.send(msg)

    _bus: QDBusConnection | None = None


class Mpris(QObject):
    """Registers the MPRIS service; silently no-ops without a session bus."""

    def __init__(self, engine, quit_callback, parent: QObject | None = None):
        super().__init__(parent)
        self.engine = engine
        self.available = False
        try:
            self.bus = QDBusConnection.sessionBus()
        except Exception:
            self.bus = None
        if self.bus is None or not self.bus.isConnected():
            return
        try:
            self._service = _Service(engine, quit_callback)
            self._service._bus = self.bus
            if not self.bus.registerService(SERVICE):
                return
            options = QDBusConnection.VirtualObjectRegisterOption.SingleNode
            if not self.bus.registerVirtualObject(PATH, self._service, options):
                self.bus.unregisterService(SERVICE)
                return
            engine.changed.connect(self.notify)
            engine.seeked.connect(self._seeked)
            self.available = True
        except Exception:
            self.available = False

    def notify(self) -> None:
        if not self.available:
            return
        try:
            self._service._emit_changed(self._service._all(PLAYER) or {})
        except Exception:
            pass

    def _seeked(self, position: float) -> None:
        if not self.available:
            return
        try:
            msg = QDBusMessage.createSignal(PATH, PLAYER, "Seeked")
            msg.setArguments([int(position * 1_000_000)])
            self.bus.send(msg)
        except Exception:
            pass
