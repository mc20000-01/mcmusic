"""Authored 4.2.0 motion values and small Qt helpers.

Everything here reads ``design/tokens.json`` values mirrored as constants. The
local ``playfulMotion`` preference is stored by ``SessionStore`` under the
documented key and defaults on; a platform Reduce Motion setting always wins.
Desktop feedback is visual only: there are no haptics APIs in the Qt client.
"""
from __future__ import annotations

import math
import os
import subprocess
import sys
from functools import lru_cache
from typing import Any

from PySide6.QtCore import (
    QEasingCurve, QObject, QPropertyAnimation, QVariantAnimation,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtGui import QPainterPath

from . import design

PRESS_SCALE = 0.96
DAMPING = 0.7
MORPH_MS = 320
WAVE_HZ = 0.55
WAVE_PX = 3
SETTINGS_KEY = "playfulMotion"
DEFAULT_ENABLED = True

_STORE: Any = None

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def bind(store: Any) -> None:
    """Point motion at the session store so custom-painted widgets can read it."""
    global _STORE
    _STORE = store


def local_enabled(store: Any = None) -> bool:
    """Read the local switch without consulting the platform preference."""
    source = _STORE if store is None else store
    if source is None:
        return DEFAULT_ENABLED
    value = getattr(source, "playful_motion", DEFAULT_ENABLED)
    if isinstance(value, str):
        return value.casefold() in _TRUTHY
    return bool(value)


def _env_reduce() -> bool:
    for key in ("MC_MUSIC_REDUCED_MOTION", "REDUCED_MOTION"):
        value = os.environ.get(key, "")
        if value.casefold() in _TRUTHY:
            return True
    return False


def _qt_reduce() -> bool:
    app = QGuiApplication.instance()
    if app is None:
        return False
    hints = QGuiApplication.styleHints()
    for name in ("reducedMotion", "prefersReducedMotion"):
        attr = getattr(hints, name, None)
        if attr is None:
            continue
        try:
            return bool(attr() if callable(attr) else attr)
        except Exception:
            continue
    duration = getattr(hints, "animationDuration", None)
    if callable(duration):
        try:
            return duration() == 0
        except Exception:
            pass
    return False


def _command_reduce(command: list[str], off: str) -> bool:
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=1, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.stdout.strip().casefold() == off


@lru_cache(maxsize=1)
def platform_reduced_motion() -> bool:
    """Best-effort platform Reduce Motion lookup, cached for the process.

    Qt 6 does not expose a cross-platform Reduce Motion hint yet. The explicit
    ``MC_MUSIC_REDUCED_MOTION`` override is checked first, then a Qt hint when a
    newer Qt supplies one, then the platform's own setting. Every failure
    falls back to "motion allowed" so a missing utility cannot freeze the UI.
    """
    if _env_reduce() or _qt_reduce():
        return True
    if sys.platform == "darwin":
        return _command_reduce(
            ["defaults", "read", "com.apple.universalaccess", "reduceMotion"], "1",
        )
    if sys.platform == "win32":
        try:
            import ctypes
            flag = ctypes.c_bool(False)
            user32 = ctypes.windll.user32
            ok = user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(flag), 0)
            return bool(ok) and not flag.value
        except Exception:
            return False
    if sys.platform.startswith("linux"):
        return _command_reduce(
            ["gsettings", "get", "org.gnome.desktop.interface", "enable-animations"],
            "false",
        )
    return False


def reset_platform_cache() -> None:
    """Drop the cached platform preference (used by tests and settings reloads)."""
    platform_reduced_motion.cache_clear()


def enabled(store: Any = None) -> bool:
    """True only when the local switch is on and Reduce Motion is off."""
    return local_enabled(store) and not platform_reduced_motion()


def spring_curve() -> QEasingCurve:
    """Medium, gently damped spring-ish easing for short Qt transitions."""
    curve = QEasingCurve(QEasingCurve.Type.OutBack)
    curve.setOvershoot(0.35)
    curve.setPeriod(DAMPING)
    return curve


def animate(target: QObject, prop: str, end: Any,
            duration: int = MORPH_MS) -> QPropertyAnimation | None:
    """Animate an authored float/rect property, or return None when disabled.

    The caller owns the returned animation and must start it. Disabled motion
    callers should assign ``end`` directly instead.
    """
    if not enabled():
        return None
    anim = QPropertyAnimation(target, prop.encode("utf-8"))
    anim.setDuration(max(0, int(duration)))
    anim.setEasingCurve(spring_curve())
    anim.setEndValue(end)
    return anim


def tween(start: float, end: float, on_value, parent: QObject | None = None,
          duration: int = MORPH_MS) -> QVariantAnimation | None:
    """Tween a float through the shared spring curve, or set it outright.

    ``on_value`` receives each interpolated value. A parented animation stays
    alive for the duration; callers keep their own state in a field.
    """
    if not enabled():
        on_value(float(end))
        return None
    anim = QVariantAnimation(parent)
    anim.setStartValue(float(start))
    anim.setEndValue(float(end))
    anim.setDuration(max(0, int(duration)))
    anim.setEasingCurve(spring_curve())
    anim.valueChanged.connect(on_value)
    anim.start()
    return anim


def press_scale(store: Any = None) -> float:
    return PRESS_SCALE if enabled(store) else 1.0


def morph_radius(size: float, playing: bool, store: Any = None) -> float:
    """Pill when paused, squircle while playing, fixed squircle when disabled."""
    if not enabled(store) or playing:
        return float(design.Shape.lg)
    return float(size) / 2.0


def wave_y(x: float, width: float, playing: bool, phase: float,
           store: Any = None) -> float:
    """Vertical offset of the progress wave at ``x``, zero when flat."""
    if width <= 0 or not playing or not enabled(store):
        return 0.0
    unit = min(max(float(x) / float(width), 0.0), 1.0)
    envelope = math.sin(math.pi * unit)
    return WAVE_PX * envelope * math.sin(unit * math.pi * 4 + phase)


def wave_path(width: float, height: float, fraction: float, playing: bool,
              phase: float, store: Any = None) -> QPainterPath:
    """A flat or gently wavy filled progress line inside ``height``."""
    path = QPainterPath()
    if width <= 0 or height <= 0 or fraction <= 0:
        return path
    filled = min(max(float(fraction), 0.0), 1.0) * float(width)
    middle = float(height) / 2.0
    steps = max(2, int(filled / 4))
    for step in range(steps + 1):
        unit = step / steps
        x = filled * unit
        y = middle if not playing else middle + wave_y(
            x, filled, True, phase, store,
        )
        if step == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    return path
