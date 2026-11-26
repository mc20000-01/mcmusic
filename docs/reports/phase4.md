# mcmusic 4.2.0 — Phase 4 report

Branch: `design-4.2.0`. Parent commit: `4d837c4` (Phase 3). This phase is the Qt desktop client only; no version bump or release action is included.

## What changed

- Added authored `design.py`, mirroring `design/tokens.json` for the 4/8/12/16/28/36 shape scale, pill, 20–28px covers, 28px cards, 36px hero corners, 48px touch targets, the 4px spacing grid and the Material 3 type scale. `placeholder_glyph()` intentionally mirrors the web `glyphIndex()` hash so the same name/kind picks the same Lucide cover glyph across clients.
- Added authored `motion.py`: medium 0.7-damped springs, a 0.96 press scale, a 320ms pill-to-squircle morph, a 0.55Hz wavy progress line and the `playfulMotion` switch (default on). A local QSettings value is combined with best-effort platform Reduce Motion detection (`MC_MUSIC_REDUCED_MOTION`, Qt hints, macOS, Windows and Linux); Reduce Motion wins. Desktop feedback is visual only because Qt has no haptics API.
- Added `SessionStore.playful_motion` in `api.py` as a QSettings-only key. No server settings key, schema or stored server payload changed. `app.py` binds the store to motion at startup and sets `design.font("body")` as the application default.
- Reworked `theme.py` stock-widget stylesheet and `QPalette` to flat M3 tonal roles: pill inputs/buttons with 48px minimum heights, 28px menu/card corners, tonal hover/selection surfaces and no alpha-blend elevations. The generated palette marker block, all five palette ids, displayed family names and stored aliases were left untouched.
- Reworked `widgets.py` primitives around the shared scale: `Txt` uses authored M3 type roles, `IconButton` and `McButton` have 48px hit targets and spring press feedback, nav/playlist buttons are tonal pills, `Switch`, `Segmented`, `StatusChip`, `Sheet`, fields and rows use 28px containers, and `Artwork` draws deterministic flat tonal Lucide placeholders while showing real artwork untouched. `SeekBar` is a flat line when paused or reduced-motion and a wavy filled line only while playing.
- Reworked `shell.py` rail, masthead, deck, queue and overlay on flat tonal surfaces with M3 labels and Lucide glyphs. The transport play button morphs between a paused pill and a playing squircle, both seek bars receive `set_playing()`, and cover placeholders are seeded from real track names. The legacy surface control still resolves stored settings but only renders flat tonal surfaces.
- Added a local `Playful motion` switch to `SettingsScreen` with copy explaining that Reduce Motion wins. Screens, status chips, theme swatches/cards and admin/download rows now use M3 roles, 48px controls and the M3 type scale; the legacy `material` value remains stored but introduces no glass, blur or backdrop effect.
- Updated `lyric_visualizer.py` to a flat tonal 28px panel with Bars / Wave / Rings modes, an M3 status pill and a repaint timer that only starts when motion is allowed. It remains a pure function of playback position and never creates or inspects extra audio objects.
- Kept feature truth: no Dolby/Spatial labels, fake Mix or Charts chips, fabricated lossless badge or invented explicit badge. `Start radio` still calls the real `/api/radio/<tid>` endpoint, and the desktop UI adds no new destination or remote data source.

## What was run

- `node scripts/gen-tokens.mjs --check && node scripts/gen-lucide.mjs --check` — pass; no token or icon source changed in this phase.
- `.venv/bin/python -m pytest tests/test_no_gradients.py tests/test_contrast.py tests/test_generated_fresh.py -q` — 3 passed; the no-allowlist flatness scan covers `app/linux` and no gradient, blur, glass or decorative shadow was introduced.
- `.venv/bin/python -m pytest tests -q` with the same Qt/widget/update exclusions CI uses — 95 passed, 1 skipped, 2 subtests passed.
- `QT_QPA_PLATFORM=offscreen MC_MUSIC_QT_AUDIO_STUB=1 .venv/bin/python -m pytest tests/test_qt_ui.py tests/test_qt_client.py tests/test_qt_icons.py tests/test_widgets.py tests/test_no_qt_shadowing.py tests/test_qt_selftest.py tests/test_updates.py -q` — 35 passed.
- `.venv/bin/python -m pyflakes app/linux src music_activity tools` — pass; `.venv/bin/python -m py_compile app/linux/mcmusic_linux/*.py` — pass.
- `bash tests/test_check_versions.sh` — 4 checks passed; `bash scripts/check-versions.sh` — all carriers still agree at 4.1.0; `bash tests/test_publish_release.sh` — 11 checks passed.
- `git diff --check` — pass; `bash -n scripts/*.sh tests/*.sh` — pass.
- Tool probe: `shellcheck` is not installed in this Linux workspace; CI installs it before the release-blocking shell gate. No shell script changed in this phase.
- CI is triggered by pushing this separate phase commit to `design-4.2.0`; no CI result is claimed in this pre-push report.

## What was not done and why

- No version bump or release publication: Phase 5 owns that, after this phase is CI-green.
- No web, Android or iOS redesign in this commit: those are Phases 1, 2 and 3. No shared token or generated icon source was changed here.
- No cover-derived dynamic colour on Qt: the written 4.2.0 contract keeps the desktop client on static family palettes; only web and Android derive from cover colour.
- No haptics: Qt exposes no cross-platform haptics API, so feedback here is the shared press spring and morph only.
- No device rendering, screenshot comparison or visual verification: no Qt desktop rendering target or mockup is available locally. CI covers compilation and the existing offscreen Qt suites; the written M3 Expressive contract is the only visual specification.
- No new remote network call, CDN font, tracker or analytics: the Qt client keeps its existing server API calls and locally resolved font families, and no effect asset was added.
- No generated blocks were hand-edited. Generated palettes stay inside `theme.py`'s marker block; it is reproduced below only as context in the authored file.
- No server settings, live database, branch sync, redeploy or secret rotation: the motion switch is a local QSettings value and those operations require explicit permission.
- No fake Mix/Radio/Chart, Dolby/Spatial label, fake lossless badge or fabricated explicit badge: the feature-truth audit and real endpoints remain unchanged.

## Full authored file contents

The files below are reproduced in full. Generated marker blocks are shown only as context in the authored files that contain them; no generated output was changed in this phase.

### `app/linux/mcmusic_linux/design.py`

```python
"""Authored 4.2.0 design values mirrored from ``design/tokens.json``.

Colours stay in the generated marker block of ``theme.py``; these constants are
the Qt half of the single-source token contract. Nothing here paints a
gradient, a blur or a decorative elevation: containers are flat tonal surfaces
with generous radii, and Lucide supplies every glyph.
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QFont

from . import theme


class Shape:
    """4/8/12/16/28/36 + pill, with the documented cover/card/touch rules."""

    xs = 4
    sm = 8
    md = 12
    lg = 16
    xl = 28
    xxl = 36
    pill = 999
    cover_min = 20
    cover_max = 28
    card = 28
    hero = 36
    touch = 48


SPACE_UNIT = 4


def space(units: int) -> int:
    """Return a value snapped to the authored 4px spacing grid."""
    return SPACE_UNIT * int(units)


@dataclass(frozen=True)
class TypeRole:
    size: int
    line: int
    weight: int


TYPE = {
    "display": TypeRole(36, 44, 700),
    "headline": TypeRole(28, 36, 700),
    "title": TypeRole(22, 28, 700),
    "body": TypeRole(16, 24, 400),
    "label": TypeRole(14, 20, 600),
}

_WEIGHTS = {
    400: QFont.Weight.Normal,
    500: QFont.Weight.Medium,
    600: QFont.Weight.DemiBold,
    700: QFont.Weight.Bold,
}

PLACEHOLDER_GLYPHS = ("circle", "squircle", "cookie", "flower", "pentagon")


def font(role: str = "body", *, size: int | None = None,
         weight: int | None = None) -> QFont:
    """Build an M3 type role from locally available families.

    Qt does not download fonts. Display roles use the display family picked by
    ``theme.families()``; everything else uses the UI family. Callers may
    override the size or weight for dense utility text without leaving the
    locally resolved family.
    """
    token = TYPE.get(role, TYPE["body"])
    family = theme.families()["display" if role in ("display", "headline") else "ui"]
    out = QFont(family)
    out.setPixelSize(int(size if size is not None else token.size))
    out.setWeight(_WEIGHTS.get(
        int(weight if weight is not None else token.weight),
        QFont.Weight.Normal,
    ))
    if role in ("display", "headline"):
        out.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, -0.4)
    return out


def placeholder_glyph(name: str, kind: str = "album") -> str:
    """Deterministic Lucide cover glyph, shared with the web placeholder."""
    text = str(name or "?")
    bucket = str(kind or "album")
    if bucket not in ("track", "artist", "album"):
        bucket = "album"
    value = len(bucket) * 17
    for char in text:
        value = (value * 31 + ord(char)) & 0xFFFFFFFF
    return PLACEHOLDER_GLYPHS[value % len(PLACEHOLDER_GLYPHS)]
```

### `app/linux/mcmusic_linux/motion.py`

```python
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
```

### `app/linux/mcmusic_linux/api.py`

```python
"""HTTP + session layer for the mcmusic server.

The server authenticates with the signed ``mcmusic_session`` cookie, exactly
like the browser and Android clients. Requests run off the GUI thread through a
small thread pool; results are delivered back on the Qt main thread.
"""
from __future__ import annotations

import json
import os
import platform
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlencode

import requests
from PySide6.QtCore import QObject, QSettings, Qt, Signal, Slot

from .models import (
    AdminStats,
    AdminUser,
    AlbumRef,
    ArtistRef,
    BuildInfo,
    DeviceRow,
    HomeData,
    ListeningUser,
    Me,
    PlaylistRef,
    RequestRow,
    SearchData,
    Section,
    Settings,
    Track,
)
from .paths import audio_cache_dir, settings_file
from .version import USER_AGENT

DEFAULT_SERVER = "http://127.0.0.1:8000"

# Only replay-safe writes go in the outbox. Toggles are kept separately so
# every tap survives a replay (mirrors the web client's REPLAYABLE list).
REPLAYABLE = [
    ("POST", re.compile(r"^like/\d+$"), True),
    ("POST", re.compile(r"^playlists/\d+/tracks$"), False),
    ("PATCH", re.compile(r"^playlists/\d+$"), False),
    ("DELETE", re.compile(r"^playlists/\d+$"), False),
    ("DELETE", re.compile(r"^playlists/\d+/tracks/\d+$"), False),
    ("PUT", re.compile(r"^settings$"), False),
]
CACHEABLE = [
    re.compile(r"^(me|settings|home|tracks|search|albums|album|artists|artist|likes|playlists|requests|devices|builds|version|ping)(/.*)?$"),
    re.compile(r"^tracks/\d+/(lyrics|sources)$"),
    re.compile(r"^public/(now/[^/]+|listening)$"),
    re.compile(r"^auth/(rotur|discord)/status$"),
]
CACHE_TTL = {
    "settings": 300, "home": 120, "tracks": 300, "albums": 600, "artists": 600,
    "likes": 120, "playlists": 120, "builds": 3600, "version": 3600,
    "devices": 60, "public/listening": 8, "requests": 30,
}


def _replay_rule(method: str, path: str):
    for verb, pattern, toggle in REPLAYABLE:
        if verb == method and pattern.match(path):
            return toggle
    return None


def _cache_ttl(path: str) -> int:
    head = path.split("/", 1)[0]
    return CACHE_TTL.get(head, 120)


class ApiError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status

    @property
    def offline(self) -> bool:
        """True for a transport failure, as opposed to an HTTP error."""
        return self.status == 0


# ── background runner ───────────────────────────────────────────────────────


class _Bridge(QObject):
    done = Signal(int, bool, object)


class Async(QObject):
    """Submit blocking work; callbacks run on the GUI thread."""

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="mcmusic-net")
        self._seq = 0
        self._lock = threading.Lock()
        self._callbacks: dict[int, tuple[Optional[Callable], Optional[Callable]]] = {}
        self._bridge = _Bridge(self)
        self._bridge.done.connect(self._finish, Qt.ConnectionType.QueuedConnection)

    def submit(self, fn: Callable[[], Any],
               ok: Optional[Callable[[Any], None]] = None,
               error: Optional[Callable[[Exception], None]] = None) -> int:
        with self._lock:
            self._seq += 1
            token = self._seq
            self._callbacks[token] = (ok, error)

        def work() -> None:
            try:
                value = fn()
            except Exception as exc:  # noqa: BLE001 - handed to the UI
                self._bridge.done.emit(token, False, exc)
            else:
                self._bridge.done.emit(token, True, value)

        try:
            self._pool.submit(work)
        except RuntimeError:
            self._callbacks.pop(token, None)
        return token

    @Slot(int, bool, object)
    def _finish(self, token: int, succeeded: bool, payload: object) -> None:
        with self._lock:
            pair = self._callbacks.pop(token, None)
        if not pair:
            return
        ok, error = pair
        if succeeded:
            if ok:
                ok(payload)
        elif error:
            error(payload if isinstance(payload, Exception) else Exception(str(payload)))

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)


# ── persistent client state ────────────────────────────────────────────────


class SessionStore:
    """QSettings-backed session cookie + local preferences."""

    def __init__(self) -> None:
        if sys.platform == "win32":
            # The Windows bundle keeps its settings beside the other per-user
            # app data instead of the registry, so roaming/profile cleanup and
            # the documented %APPDATA% location actually agree.
            path = settings_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            self._s = QSettings(str(path), QSettings.IniFormat)
        else:
            # Preserve the existing native QSettings location on Linux/macOS.
            self._s = QSettings("mcmusic", "mcmusic-desktop")

    # base url -------------------------------------------------------------
    @property
    def base_url(self) -> str:
        return str(self._s.value("base_url", DEFAULT_SERVER) or DEFAULT_SERVER)

    @base_url.setter
    def base_url(self, value: str) -> None:
        self._s.setValue("base_url", value)
        self._s.sync()

    # cookies --------------------------------------------------------------
    def load_cookies(self) -> dict[str, str]:
        raw = str(self._s.value("cookies", "") or "")
        if not raw:
            return {}
        try:
            data = json.loads(raw)
            return {str(k): str(v) for k, v in data.items() if v}
        except (ValueError, TypeError):
            return {}

    def save_cookies(self, cookies: dict[str, str]) -> None:
        self._s.setValue("cookies", json.dumps(cookies, separators=(",", ":")))
        self._s.sync()

    def clear_session(self) -> None:
        self._s.remove("cookies")
        self._s.remove("me")
        self._s.sync()

    # cached me ------------------------------------------------------------
    @property
    def cached_me(self) -> Optional[Me]:
        raw = str(self._s.value("me", "") or "")
        if not raw:
            return None
        try:
            return Me.from_json(json.loads(raw))
        except (ValueError, TypeError):
            return None

    @cached_me.setter
    def cached_me(self, me: Optional[Me]) -> None:
        if me is None:
            self._s.remove("me")
        else:
            self._s.setValue("me", json.dumps(me.to_json(), separators=(",", ":")))
        self._s.sync()

    # native app token (Rotur sign-in / device pairing) --------------------
    @property
    def device_token(self) -> str:
        return str(self._s.value("device_token", "") or "")

    @device_token.setter
    def device_token(self, value: str) -> None:
        if value:
            self._s.setValue("device_token", value)
        else:
            self._s.remove("device_token")
        self._s.sync()

    @property
    def pending_token(self) -> str:
        return str(self._s.value("pending_token", "") or "")

    @pending_token.setter
    def pending_token(self, value: str) -> None:
        if value:
            self._s.setValue("pending_token", value)
        else:
            self._s.remove("pending_token")
        self._s.sync()

    # derived listen-along invite link (never saved to server settings) ---
    @property
    def room_url(self) -> str:
        return str(self._s.value("room_url", "") or "")

    @room_url.setter
    def room_url(self, value: str) -> None:
        self._s.setValue("room_url", value)
        self._s.sync()

    # offline GET cache ----------------------------------------------------
    def _json_value(self, key: str, default: Any):
        raw = str(self._s.value(key, "") or "")
        if not raw:
            return default
        try:
            value = json.loads(raw)
            return value if isinstance(value, type(default)) else default
        except (ValueError, TypeError):
            return default

    def _set_json(self, key: str, value: Any) -> None:
        self._s.setValue(key, json.dumps(value, separators=(",", ":")))
        self._s.sync()

    def cache_get(self, key: str) -> Optional[dict]:
        entry = self._json_value("http_cache", {}).get(key)
        return entry if isinstance(entry, dict) and isinstance(entry.get("data"), dict) else None

    def cache_put(self, key: str, data: Any) -> None:
        if not isinstance(data, dict):
            return
        cache = self._json_value("http_cache", {})
        cache[key] = {"at": time.time(), "data": data}
        # A few hundred responses is plenty; keep the newest ones.
        if len(cache) > 400:
            for old in sorted(cache, key=lambda k: cache[k].get("at", 0))[:len(cache) - 400]:
                cache.pop(old, None)
        self._set_json("http_cache", cache)

    def cache_stats(self) -> tuple[int, int]:
        cache = self._json_value("http_cache", {})
        files = 0
        root = audio_cache_dir()
        if root.is_dir():
            files = sum(1 for p in root.iterdir() if p.is_file() and p.suffix != ".part")
        return len(cache), files

    def cache_clear(self, *, responses: bool = True, audio: bool = True) -> int:
        removed = 0
        if responses:
            removed += len(self._json_value("http_cache", {}))
            self._s.remove("http_cache")
        if audio:
            root = audio_cache_dir()
            if root.is_dir():
                for p in root.iterdir():
                    if p.is_file():
                        try:
                            p.unlink()
                            removed += 1
                        except OSError:
                            pass
        self._s.sync()
        return removed

    def cache_prune(self, max_age_days: int = 30, max_bytes: int = 2 * 1024**3) -> int:
        """Drop old audio files until the cache is under *max_bytes*."""
        root = audio_cache_dir()
        if not root.is_dir():
            return 0
        files = [p for p in root.iterdir() if p.is_file()]
        cutoff = time.time() - max(1, max_age_days) * 86400
        removed = 0
        for p in files:
            try:
                if p.stat().st_mtime < cutoff:
                    p.unlink()
                    removed += 1
            except OSError:
                pass
        total = sum(p.stat().st_size for p in files if p.exists())
        for p in sorted((p for p in files if p.exists()), key=lambda f: f.stat().st_mtime):
            if total <= max_bytes:
                break
            try:
                total -= p.stat().st_size
                p.unlink()
                removed += 1
            except OSError:
                pass
        return removed

    # offline write outbox -------------------------------------------------
    @property
    def outbox(self) -> list[dict]:
        return self._json_value("outbox", [])

    def outbox_add(self, method: str, path: str, body: Any = None) -> int:
        items = self.outbox
        toggle = _replay_rule(method, path)
        if not toggle:
            items = [i for i in items
                     if not (i.get("method") == method and i.get("path") == path
                             and json.dumps(i.get("body"), sort_keys=True)
                             == json.dumps(body, sort_keys=True))]
        items.append({"method": method, "path": path, "body": body, "at": time.time()})
        items = items[-200:]
        self._set_json("outbox", items)
        return len(items)

    def outbox_set(self, items: list[dict]) -> None:
        self._set_json("outbox", items)

    # queue / sleep timer snapshots ----------------------------------------
    @property
    def queue_snapshot(self) -> dict:
        snap = self._json_value("queue_snapshot", {})
        return snap if isinstance(snap, dict) else {}

    @queue_snapshot.setter
    def queue_snapshot(self, value: dict) -> None:
        self._set_json("queue_snapshot", value)

    @property
    def sleep_timer(self) -> dict:
        timer = self._json_value("sleep_timer", {})
        return timer if isinstance(timer, dict) else {}

    @sleep_timer.setter
    def sleep_timer(self, value: dict) -> None:
        if value:
            self._set_json("sleep_timer", value)
        else:
            self._s.remove("sleep_timer")
            self._s.sync()

    @property
    def reset_token(self) -> str:
        return str(self._s.value("reset_token", "") or "")

    @reset_token.setter
    def reset_token(self, value: str) -> None:
        if value:
            self._s.setValue("reset_token", value)
        else:
            self._s.remove("reset_token")
        self._s.sync()

    # appearance -----------------------------------------------------------
    @property
    def theme(self) -> str:
        return str(self._s.value("theme", "violet") or "violet")

    @theme.setter
    def theme(self, value: str) -> None:
        self._s.setValue("theme", value)

    @property
    def accent(self) -> str:
        return str(self._s.value("accent", "") or "")

    @accent.setter
    def accent(self, value: str) -> None:
        self._s.setValue("accent", value)

    @staticmethod
    def _icon_stroke(value) -> float:
        try:
            scale = float(value)
        except (TypeError, ValueError):
            return 1.0
        return min((1.0, 1.5, 2.0), key=lambda choice: abs(choice - scale))

    @property
    def icon_stroke(self) -> float:
        return self._icon_stroke(self._s.value("iconStroke", 1.0))

    @icon_stroke.setter
    def icon_stroke(self, value: float) -> None:
        self._s.setValue("iconStroke", self._icon_stroke(value))

    @property
    def icon_filled(self) -> bool:
        return bool(self._s.value("iconFilled", False))

    @icon_filled.setter
    def icon_filled(self, value: bool) -> None:
        self._s.setValue("iconFilled", bool(value))

    # Local 4.2.0 motion switch. It lives in QSettings only: server settings
    # have no `playfulMotion` key and the stored server payload is unchanged.
    @property
    def playful_motion(self) -> bool:
        value = self._s.value("playfulMotion", True)
        if isinstance(value, str):
            return value.casefold() in ("1", "true", "yes", "on")
        return bool(value)

    @playful_motion.setter
    def playful_motion(self, value: bool) -> None:
        self._s.setValue("playfulMotion", bool(value))
        self._s.sync()

    @property
    def volume(self) -> float:
        try:
            return float(self._s.value("volume", 0.8))
        except (TypeError, ValueError):
            return 0.8

    @volume.setter
    def volume(self, value: float) -> None:
        self._s.setValue("volume", round(float(value), 3))

    @property
    def device_hash(self) -> str:
        existing = str(self._s.value("device_hash", "") or "")
        if existing:
            return existing
        import hashlib
        seed = f"{platform.node()}-{os.path.expanduser('~')}-{platform.machine()}"
        value = hashlib.sha1(seed.encode("utf-8"), usedforsecurity=False).hexdigest()[:32]
        self._s.setValue("device_hash", value)
        return value

    def sync(self) -> None:
        self._s.sync()


# ── HTTP client ─────────────────────────────────────────────────────────────


class Api:
    def __init__(self, store: SessionStore):
        self.store = store
        self.cookies: dict[str, str] = store.load_cookies()
        self.token: str = store.device_token
        self._local = threading.local()
        self._flush_lock = threading.Lock()
        self.base_url = normalize(store.base_url)

    # transport ------------------------------------------------------------
    def _session(self) -> requests.Session:
        s = getattr(self._local, "session", None)
        system = "Darwin" if platform.system() == "Darwin" else (
            "Windows" if platform.system() == "Windows" else "Linux")
        if s is None:
            s = requests.Session()
            s.headers.update({
                "User-Agent": USER_AGENT.replace("Qt", f"{system}; Qt"),
                "Accept": "application/json",
            })
            self._local.session = s
        if self.token:
            s.headers["Authorization"] = f"Bearer {self.token}"
        else:
            s.headers.pop("Authorization", None)
        return s

    def set_token(self, token: str) -> None:
        """Adopt a native-client device token (Rotur sign-in / pairing)."""
        self.token = token.strip()
        self.store.device_token = self.token

    def clear_token(self) -> None:
        self.token = ""
        self.store.device_token = ""

    def set_base(self, raw: str) -> str:
        self.base_url = normalize(raw, self.base_url)
        self.store.base_url = self.base_url
        return self.base_url

    def url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/api/{path.lstrip('/')}"

    def web_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def cover_url(self, track_id: int | None) -> Optional[str]:
        return self.url(f"tracks/{track_id}/cover") if track_id else None

    def _cookie_header(self) -> str:
        return "; ".join(f"{k}={v}" for k, v in self.cookies.items())

    def _absorb_cookies(self, response: requests.Response) -> None:
        changed = False
        for cookie in response.cookies:
            if cookie.value:
                if self.cookies.get(cookie.name) != cookie.value:
                    self.cookies[cookie.name] = cookie.value
                    changed = True
            else:
                self.cookies.pop(cookie.name, None)
                changed = True
        if changed:
            self.store.save_cookies(self.cookies)

    def request(self, method: str, path: str, body: dict | None = None,
                params: dict | None = None, timeout: tuple[float, float] = (12, 40),
                raw: bool = False, headers: dict | None = None) -> Any:
        url = self.url(path)
        final_headers = dict(headers or {})
        if self.cookies:
            final_headers["Cookie"] = self._cookie_header()
        try:
            response = self._session().request(
                method, url, json=body, params=params, headers=final_headers,
                timeout=timeout, allow_redirects=True,
            )
        except requests.Timeout:
            raise ApiError("Server timed out") from None
        except requests.ConnectionError:
            raise ApiError("Can't reach the server") from None
        except requests.RequestException as exc:
            raise ApiError(str(exc) or "Network error") from None

        self._absorb_cookies(response)
        if response.status_code == 401:
            raise ApiError("login required", 401)
        if raw:
            if response.status_code >= 400:
                raise ApiError(f"HTTP {response.status_code}", response.status_code)
            return response.content, response.headers.get("Content-Type", "")

        text = response.text
        try:
            data = response.json() if text.strip() else {}
        except ValueError:
            data = {"error": text[:200] or f"HTTP {response.status_code}"}
        if response.status_code >= 400:
            message = ""
            if isinstance(data, dict):
                message = str(data.get("error") or data.get("message") or "")
            raise ApiError(message or f"HTTP {response.status_code}", response.status_code)
        return data

    @staticmethod
    def cache_key(path: str, params: dict | None) -> str:
        return path + ("?" + urlencode(sorted((params or {}).items())) if params else "")

    def get(self, path: str, params: dict | None = None) -> Any:
        """Read-through cache: use the network when possible, saved body otherwise."""
        key = self.cache_key(path, params)
        try:
            data = self.request("GET", path, params=params)
        except ApiError as exc:
            if not exc.offline or not any(p.match(path) for p in CACHEABLE):
                raise
            hit = self.store.cache_get(self.base_url + "|" + key)
            if hit is None:
                raise
            return hit["data"]
        if any(p.match(path) for p in CACHEABLE):
            self.store.cache_put(self.base_url + "|" + key, data)
        return data

    def write(self, method: str, path: str, body: dict | None = None) -> Any:
        """Queue replay-safe writes when the server cannot be reached."""
        try:
            return self.request(method, path, body=body)
        except ApiError as exc:
            if exc.offline and _replay_rule(method, path) is not None:
                pending = self.store.outbox_add(method, path, body)
                return {"queued": True, "pending": pending}
            raise

    def post(self, path: str, body: dict | None = None) -> Any:
        return self.write("POST", path, body)

    def put(self, path: str, body: dict | None = None) -> Any:
        return self.write("PUT", path, body)

    def patch(self, path: str, body: dict | None = None) -> Any:
        return self.write("PATCH", path, body)

    def delete(self, path: str) -> Any:
        return self.write("DELETE", path)

    def pending_writes(self) -> int:
        return len(self.store.outbox)

    def flush_outbox(self) -> tuple[int, int]:
        """Replay pending writes oldest-first. Returns (sent, still_pending)."""
        if not self._flush_lock.acquire(blocking=False):
            return 0, self.pending_writes()
        try:
            items = self.store.outbox
            sent = 0
            while items:
                item = items[0]
                try:
                    self.request(item["method"], item["path"], body=item.get("body"))
                except ApiError as exc:
                    if exc.status == 401 or exc.offline or exc.status >= 500 or exc.status == 429:
                        break
                    # A permanent 4xx (e.g. already deleted) is done; drop it.
                items = items[1:]
                self.store.outbox_set(items)
                sent += 1
            return sent, len(items)
        finally:
            self._flush_lock.release()

    def get_bytes(self, path: str) -> tuple[bytes, str]:
        return self.request("GET", path, raw=True)

    def download(self, path: str, dest: Path,
                 progress: Optional[Callable[[int, int], None]] = None,
                 cancel: Optional[Callable[[], bool]] = None) -> str:
        """Stream ``path`` to ``dest`` atomically; returns Content-Type."""
        url = self.url(path)
        headers = {"Cookie": self._cookie_header()} if self.cookies else {}
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        try:
            with self._session().get(url, headers=headers, stream=True,
                                     timeout=(12, 120)) as response:
                if response.status_code == 401:
                    raise ApiError("login required", 401)
                if response.status_code >= 400:
                    raise ApiError(f"HTTP {response.status_code}", response.status_code)
                self._absorb_cookies(response)
                total = int(response.headers.get("Content-Length") or 0)
                got = 0
                with open(tmp, "wb") as fh:
                    for chunk in response.iter_content(65536):
                        if cancel and cancel():
                            raise ApiError("cancelled")
                        if not chunk:
                            continue
                        fh.write(chunk)
                        got += len(chunk)
                        if progress:
                            progress(got, total)
                os.replace(tmp, dest)
                return response.headers.get("Content-Type", "")
        except requests.RequestException as exc:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise ApiError(str(exc) or "Download failed") from None
        except Exception:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise


def normalize(raw: str, fallback: str = DEFAULT_SERVER) -> str:
    value = (raw or "").strip()
    if not value:
        return fallback.rstrip("/")
    if not value.startswith(("http://", "https://")):
        value = "http://" + value
    value = value.rstrip("/")
    if value.endswith("/api"):
        value = value[:-4].rstrip("/")
    return value


# ── repository ──────────────────────────────────────────────────────────────


class Repo:
    """Endpoint map mirroring routes/*.py and the Android Repo class."""

    def __init__(self, api: Api):
        self.api = api

    # auth -----------------------------------------------------------------
    def me(self, force: bool = False) -> Me:
        """Current identity. Session checks must bypass the stale-if-error cache."""
        data = (self.api.request("GET", "me") if force else self.api.get("me"))
        return Me.from_json(data)

    def login(self, username: str, password: str) -> Me:
        return Me.from_json(self.api.post("login", {"username": username, "password": password}))

    def register(self, username: str, password: str, invite: str) -> Me:
        return Me.from_json(self.api.post("register", {
            "username": username, "password": password, "invite": invite,
        }))

    def logout(self) -> None:
        try:
            self.api.post("logout")
        except ApiError:
            pass

    def change_password(self, old: str, new: str) -> None:
        self.api.post("password", {"old": old, "new": new})

    def set_email(self, email: str) -> Me:
        return Me.from_json(self.api.post("auth/email", {"email": email}))

    def request_reset(self, email: str) -> dict:
        return self.api.post("auth/reset/request", {"email": email})

    def check_reset(self, token: str) -> None:
        self.api.post("auth/reset/check", {"token": token})

    def confirm_reset(self, token: str, password: str) -> None:
        self.api.post("auth/reset/confirm", {"token": token, "password": password})

    def verify_token(self, token: str) -> Me:
        """Verify a native device token without adopting it yet."""
        data = self.api.request(
            "GET", "me", timeout=(8, 12),
            headers={"Authorization": f"Bearer {token.strip()}"},
        )
        return Me.from_json(data)

    def adopt_token(self, token: str) -> Me:
        """Persist and start using a native device token, then verify it."""
        self.api.set_token(token)
        try:
            # Never accept a device token on the strength of a cached identity.
            return self.me(force=True)
        except ApiError:
            self.api.clear_token()
            raise

    def app_logout(self) -> None:
        if self.api.token:
            try:
                self.api.post("auth/app/logout")
            except ApiError:
                pass
            self.api.clear_token()

    # Rotur / Discord -------------------------------------------------------
    def rotur_status(self) -> dict:
        return self.api.get("auth/rotur/status")

    def unlink_rotur(self) -> None:
        self.api.post("auth/rotur/unlink")

    def rotur_authorize_url(self, device_hash: str = "") -> str:
        params = {"app": "1"}
        if device_hash:
            params["device_hash"] = device_hash
        return self.api.web_url("api/auth/rotur/authorize?" + urlencode(params))

    def rotur_activity(self, track_id: Optional[int], position: float,
                       playing: bool) -> None:
        self.api.post("auth/rotur/activity", {
            "track_id": track_id, "position": position, "playing": playing,
        })

    def discord_status(self) -> dict:
        return self.api.get("auth/discord/status")

    def discord_authorize_url(self) -> str:
        return self.api.web_url("api/auth/discord/authorize")

    def discord_unlink(self) -> None:
        self.api.post("auth/discord/unlink")

    def discord_activity(self, track_id: Optional[int], position: float,
                         playing: bool) -> None:
        self.api.post("auth/discord/activity", {
            "track_id": track_id, "position": position, "playing": playing,
        })

    # settings -------------------------------------------------------------
    def settings(self) -> Settings:
        return Settings.from_json(self.api.get("settings"))

    def save_settings(self, settings: Settings) -> None:
        self.api.put("settings", settings.to_json())

    # server metadata -------------------------------------------------------
    def ping(self) -> dict:
        return self.api.get("ping")

    def version(self) -> dict:
        return self.api.get("version")

    def builds(self) -> list[BuildInfo]:
        return BuildInfo.list_json(self.api.get("builds").get("builds"))

    def email_build(self, kind: str, email: str) -> dict:
        return self.api.post("builds/email", {"build": kind, "email": email})

    def build_url(self, path: str) -> str:
        return self.api.web_url(path.lstrip("/"))

    # library --------------------------------------------------------------
    def home(self) -> HomeData:
        o = self.api.get("home")
        sections = [
            Section(title=str(s.get("title", "")), tracks=Track.list_json(s.get("tracks")))
            for s in (o.get("sections") or []) if isinstance(s, dict)
        ]
        return HomeData(sections, AlbumRef.list_json(o.get("albums")))

    def tracks(self, query: str = "", limit: int = 2000) -> list[Track]:
        params: dict[str, Any] = {"limit": limit}
        if query:
            params["q"] = query
        return Track.list_json(self.api.get("tracks", params).get("tracks"))

    def find_track(self, track_id: int) -> Optional[Track]:
        """Resolve one track from the cached library list (no single-track GET)."""
        return next((t for t in self.tracks() if t.id == int(track_id)), None)

    def search(self, query: str) -> SearchData:
        o = self.api.get("search", {"q": query})
        return SearchData(
            Track.list_json(o.get("tracks")),
            AlbumRef.list_json(o.get("albums")),
            ArtistRef.list_json(o.get("artists")),
        )

    def albums(self) -> list[AlbumRef]:
        return AlbumRef.list_json(self.api.get("albums").get("albums"))

    def album(self, name: str) -> list[Track]:
        return Track.list_json(self.api.get("album", {"name": name}).get("tracks"))

    def artists(self) -> list[ArtistRef]:
        return ArtistRef.list_json(self.api.get("artists").get("artists"))

    def artist(self, name: str) -> list[Track]:
        return Track.list_json(self.api.get("artist", {"name": name}).get("tracks"))

    def lyrics(self, track_id: int) -> dict:
        """Lyrics for one track; the server looks them up on first listen."""
        return self.api.get(f"tracks/{int(track_id)}/lyrics")

    def track_sources(self, track_id: int) -> list[dict]:
        data = self.api.get(f"tracks/{int(track_id)}/sources")
        return [r for r in (data.get("sources") or []) if isinstance(r, dict)]

    def likes(self) -> list[Track]:
        return Track.list_json(self.api.get("likes").get("tracks"))

    def like(self, track_id: int):
        """Returns the new liked state, or a queued marker when offline."""
        data = self.api.post(f"like/{track_id}")
        if isinstance(data, dict) and data.get("queued"):
            return data
        return bool(data.get("liked"))

    def report_play(self, track_id: int, completed: bool) -> None:
        self.api.post("plays", {
            "track_id": track_id, "completed": completed, "client": "desktop",
        })

    def report_metric(
        self, track_id: int, event: str, position: float = 0.0, duration: float = 0.0,
    ) -> None:
        """Always-on listening events: admin insight and Faves ranking."""
        if event not in {"play", "skip", "complete", "seek"}:
            return
        self.api.post("metrics", {"events": [{
            "track_id": track_id, "event": event,
            "position": float(position), "duration": float(duration),
            "client": "desktop",
        }]})

    def set_explicit(self, track_id: int, explicit: bool) -> bool:
        return bool(self.api.patch(f"tracks/{track_id}", {"explicit": explicit}).get("explicit"))

    def radio(self, track_id: int) -> list[Track]:
        return Track.list_json(self.api.get(f"radio/{track_id}").get("tracks"))

    def model_rank(self, current: int, ids: list[int]) -> list[int]:
        """MDL queue order, empty until the 76% work-rate gate opens."""
        data = self.api.post("model/rank", {
            "current": int(current),
            "ids": [int(i) for i in ids][:500],
        })
        if not data.get("active"):
            return []
        return [int(i) for i in (data.get("ids") or [])]

    # playlists ------------------------------------------------------------
    def playlists(self) -> list[PlaylistRef]:
        return PlaylistRef.list_json(self.api.get("playlists").get("playlists"))

    def playlist(self, playlist_id: int) -> tuple[str, list[Track]]:
        o = self.api.get(f"playlists/{playlist_id}")
        return str(o.get("name") or "Playlist"), Track.list_json(o.get("tracks"))

    def create_playlist(self, name: str) -> int:
        return int(self.api.post("playlists", {"name": name}).get("id") or 0)

    def rename_playlist(self, playlist_id: int, name: str) -> None:
        self.api.patch(f"playlists/{playlist_id}", {"name": name})

    def delete_playlist(self, playlist_id: int) -> None:
        self.api.delete(f"playlists/{playlist_id}")

    def add_to_playlist(self, playlist_id: int, track_id: int) -> None:
        self.api.post(f"playlists/{playlist_id}/tracks", {"track_id": track_id})

    def remove_from_playlist(self, playlist_id: int, track_id: int) -> None:
        self.api.delete(f"playlists/{playlist_id}/tracks/{track_id}")

    # requests -------------------------------------------------------------
    def requests(self) -> tuple[bool, list[RequestRow]]:
        o = self.api.get("requests")
        rows = [RequestRow.from_json(r) for r in (o.get("requests") or []) if isinstance(r, dict)]
        return bool(o.get("is_admin")), rows

    def request_add(self, url: str) -> str:
        return str(self.api.post("requests", {"url": url}).get("status") or "")

    def request_act(self, request_id: int, action: str) -> None:
        self.api.post(f"requests/{request_id}/{action}")

    # admin ----------------------------------------------------------------
    def admin_stats(self) -> AdminStats:
        return AdminStats.from_json(self.api.get("admin/stats"))

    def admin_users(self) -> list[AdminUser]:
        return [AdminUser.from_json(u) for u in (self.api.get("admin/users").get("users") or [])]

    def admin_set_admin(self, user_id: int, is_admin: bool) -> None:
        self.api.post(f"admin/users/{user_id}/admin", {"is_admin": is_admin})

    def admin_scan(self) -> tuple[int, int]:
        o = self.api.post("admin/scan")
        return int(o.get("tracks") or 0), int(o.get("albums") or 0)

    # public listening ------------------------------------------------------
    def public_listening(self) -> tuple[list[ListeningUser], str]:
        data = self.api.get("public/listening")
        return ListeningUser.list_json(data.get("users")), str(data.get("base_url") or "")

    def public_now(self, username: str) -> dict:
        return self.api.get(f"public/now/{username}")

    # rooms -----------------------------------------------------------------
    def room_create(self) -> str:
        return str(self.api.post("rooms").get("code") or "")

    def room_state(self, code: str, track_id: int | None, pos: float,
                   playing: bool) -> None:
        self.api.post(f"rooms/{code}/state", {
            "track_id": track_id, "pos": pos, "playing": playing,
        })

    def room_get(self, code: str) -> dict:
        return self.api.get(f"rooms/{code}")

    def room_close(self, code: str) -> None:
        self.api.delete(f"rooms/{code}")

    # devices / playback registry ------------------------------------------
    def heartbeat(self, device_hash: str, name: str, track_id: int | None,
                  position: float, paused: bool) -> None:
        self.api.post("devices/heartbeat", {
            "device_hash": device_hash, "name": name, "track_id": track_id,
            "position": position, "paused": paused,
        })

    def devices(self) -> list[DeviceRow]:
        return DeviceRow.list_json(self.api.get("devices").get("devices"))

    def device_activate(self, device_id: int) -> None:
        self.api.post(f"devices/{int(device_id)}/activate")

    def device_rename(self, device_id: int, name: str) -> None:
        self.api.patch(f"devices/{int(device_id)}", {"name": name})

    def device_forget(self, device_id: int) -> None:
        self.api.delete(f"devices/{int(device_id)}")

    def devices_cleanup(self) -> None:
        self.api.post("devices/cleanup")

    def devices_clear(self) -> None:
        self.api.post("devices/clear")

    def devices_sync(self) -> dict:
        return self.api.get("devices/sync")

    def device_code(self) -> dict:
        return self.api.post("devices/code")

    def device_claim(self, code: str, name: str = "") -> dict:
        return self.api.post("devices/claim", {
            "code": code, "name": name, "device_hash": self.api.store.device_hash,
        })

    def device_tokens(self) -> list[dict]:
        data = self.api.get("devices/tokens")
        return [t for t in (data.get("tokens") or []) if isinstance(t, dict)]

    def device_token_revoke(self, token_id: int) -> None:
        self.api.post(f"devices/tokens/{int(token_id)}/revoke")

    def admin_devices(self) -> list[DeviceRow]:
        return DeviceRow.list_json(self.api.get("admin/devices").get("devices"))

    def publish_playback(self, track_id: int | None, position: float, duration: float,
                         playing: bool, queue: list[int], device: str = "") -> None:
        self.api.post("playback", {
            "track_id": track_id, "position": position, "duration": duration,
            "playing": playing, "queue": queue, "device": device or self.api.store.device_hash,
        })

    def playback(self, device: str = "") -> dict:
        return self.api.get("playback", {"device": device or self.api.store.device_hash})

    def playback_command(self, action: str, **arg) -> None:
        self.api.post("playback/command", {"action": action, **arg})

    def queue_snapshot(self) -> dict:
        return self.api.get("queue")

    # advanced request / admin ---------------------------------------------
    def admin_requests(self, limit: int = 200) -> list[RequestRow]:
        data = self.api.get("admin/requests", {"limit": limit})
        return [RequestRow.from_json(r) for r in (data.get("requests") or [])]

    def request_log(self, request_id: int) -> dict:
        return self.api.get(f"admin/requests/{int(request_id)}/log")

    def request_cancel(self, request_id: int) -> None:
        self.api.post(f"admin/requests/{int(request_id)}/cancel")

    def request_retry(self, request_id: int) -> None:
        self.api.post(f"admin/requests/{int(request_id)}/retry")

    def request_delete(self, request_id: int) -> None:
        self.api.delete(f"admin/requests/{int(request_id)}")

    def admin_delete_user(self, user_id: int) -> None:
        self.api.delete(f"admin/users/{int(user_id)}")

    def admin_invites(self) -> list[dict]:
        data = self.api.get("admin/invite-codes")
        return [r for r in (data.get("codes") or []) if isinstance(r, dict)]

    def admin_invite_create(self, uses: int = 1, hours: float = 0, note: str = "") -> dict:
        return self.api.post("admin/invite-codes", {
            "uses": uses, "hours": hours, "note": note,
        })

    def admin_invite_revoke(self, code_id: int) -> None:
        self.api.delete(f"admin/invite-codes/{int(code_id)}")

    def admin_rooms(self) -> list[dict]:
        data = self.api.get("admin/rooms")
        return [r for r in (data.get("rooms") or []) if isinstance(r, dict)]

    def admin_room_close(self, code: str) -> None:
        self.api.delete(f"admin/rooms/{code}")

    def admin_enrich_status(self) -> dict:
        return self.api.get("admin/enrich")

    def admin_enrich_start(self, force: bool = False) -> None:
        self.api.post("admin/enrich", {"force": force})

    def admin_lyrics_status(self) -> dict:
        return self.api.get("admin/lyrics")

    def admin_lyrics_start(self) -> None:
        self.api.post("admin/lyrics", {})

    def admin_channels(self) -> list[dict]:
        data = self.api.get("channels")
        return [r for r in (data.get("channels") or []) if isinstance(r, dict)]


def device_name() -> str:
    system = platform.system()
    try:
        host = platform.node() or system
    except Exception:
        host = system
    label = "macOS" if system == "Darwin" else (
        "Windows" if system == "Windows" else "Linux")
    return f"{host} · {label}"


def query(params: dict[str, Any]) -> str:
    return "?" + urlencode(params)
```

### `app/linux/mcmusic_linux/app.py`

```python
"""mcmusic desktop — native Qt 6 client for the mcmusic server."""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import design, motion, theme
from .api import Api, Async, Repo, SessionStore
from .art import ART
from .models import Settings
from .mpris import Mpris
from .player import PlayerEngine
from .platform_media import MediaBridge
from .shell import McWindow
from .version import VERSION

ASSETS = Path(__file__).with_name("assets")


def main(argv: list[str] | None = None) -> int:
    """Compatibility entry point; the GUI/TUI flag dispatch lives in .cli."""
    from .cli import main as cli_main
    return cli_main(argv)


def run_gui(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    # mcmusic://rotur?token=… / mcmusic-desktop://rotur?token=… from the browser.
    link_token = ""
    qt_args = [argv[0]] if argv else []
    for arg in argv[1:]:
        if arg.startswith(("mcmusic://", "mcmusic-desktop://")):
            parsed = urlparse(arg)
            values = parse_qs(parsed.query)
            link_token = (
                values.get("token", [""])[0]
                or values.get("access_token", [""])[0]
                or parsed.path.lstrip("/")
            )
        else:
            qt_args.append(arg)
    app = QApplication(qt_args)
    app.setApplicationName("mcmusic")
    app.setApplicationDisplayName("mcmusic")
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("mcmusic")
    app.setOrganizationDomain("mcmusic.dev")
    app.setDesktopFileName("mcmusic")
    # Fusion keeps metrics and control chrome identical on KDE, GNOME,
    # Hyprland and plain X11 sessions; all colours come from the palette below.
    app.setStyle("Fusion")

    icon_path = ASSETS / "mcmusic.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    store = SessionStore()
    if link_token:
        store.pending_token = link_token
    motion.bind(store)
    theme.set_appearance(store.theme, store.accent)
    app.setFont(design.font("body"))
    app.setStyleSheet(theme.stylesheet())
    app.setPalette(theme.qpalette())

    runner = Async()
    api = Api(store)
    api.set_base(store.base_url)
    repo = Repo(api)
    ART.bind(api, runner)

    holder: dict[str, object] = {"window": None}
    player = PlayerEngine(
        repo, api, runner,
        lambda: holder["window"].settings if holder["window"] is not None else Settings(),
        store=store,
    )
    player.set_volume(store.volume)

    window = McWindow(store, api, repo, runner, player)
    holder["window"] = window
    window.mpris = Mpris(player, window.close)  # type: ignore[attr-defined]
    window.media_bridge = MediaBridge(player, window)  # type: ignore[attr-defined]
    window.show()

    app.aboutToQuit.connect(window.media_bridge.shutdown)  # type: ignore[attr-defined]
    app.aboutToQuit.connect(player.shutdown)
    app.aboutToQuit.connect(runner.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
```

### `app/linux/mcmusic_linux/theme.py`

```python
"""Design tokens shared with the web client (ui/src/env.css).

Everything the native UI paints reads from these palettes, so the desktop app
keeps the same ink + violet identity as the browser and Android builds.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QPalette


@dataclass(frozen=True)
class Palette:
    name: str
    bg: str
    bg2: str
    surface: str
    surface2: str
    fg: str
    dim: str
    dim2: str
    line: str
    line2: str
    accent: str
    accent_text: str
    accent_fg: str
    # Generated Material 3 tonal roles (HCT from this family's accent seed).
    primary: str
    on_primary: str
    primary_container: str
    on_primary_container: str
    secondary: str
    on_secondary: str
    secondary_container: str
    on_secondary_container: str
    tertiary: str
    on_tertiary: str
    tertiary_container: str
    on_tertiary_container: str
    error: str
    on_error: str
    error_container: str
    on_error_container: str
    background: str
    on_background: str
    on_surface: str
    surface_variant: str
    on_surface_variant: str
    surface_container_lowest: str
    surface_container_low: str
    surface_container: str
    surface_container_high: str
    surface_container_highest: str
    outline: str
    outline_variant: str
    inverse_surface: str
    inverse_on_surface: str
    inverse_primary: str
    scrim_color: str
    shadow_color: str
    ok: str = "#1db954"
    warn: str = "#ffbf69"
    err: str = "#ff6b72"
    scrim: str = "rgba(23, 23, 33, 0.78)"
    ink: str = "#171721"

    def q(self, token: str) -> QColor:
        return QColor(getattr(self, token))

    @property
    def accent_soft(self) -> QColor:
        c = QColor(self.accent)
        c.setAlpha(36)
        return c

    # ── Material 3 surface tints ────────────────────────────────────────
    # QSS uses palette-derived rgba() values below.
    def _tint(self, token: str, alpha: int) -> QColor:
        c = QColor(getattr(self, token))
        c.setAlpha(alpha)
        return c


# BEGIN GENERATED PALETTES
def _variant(bg, bg2, surface, surface2, fg, dim, dim2, line, line2, accent, accentText, accent_fg,
             primary, on_primary, primary_container, on_primary_container, secondary, on_secondary, secondary_container, on_secondary_container, tertiary, on_tertiary, tertiary_container, on_tertiary_container, error, on_error, error_container, on_error_container, background, on_background, on_surface, surface_variant, on_surface_variant, surface_container_lowest, surface_container_low, surface_container, surface_container_high, surface_container_highest, outline, outline_variant, inverse_surface, inverse_on_surface, inverse_primary, scrim_color, shadow_color, dark, label):
    name = "%s-%s" % (label.lower(), "dark" if dark else "light")
    return Palette(
        name=name, bg=bg, bg2=bg2, surface=surface, surface2=surface2,
        fg=fg, dim=dim, dim2=dim2, line=line, line2=line2,
        accent=accent, accent_text=accentText, accent_fg=accent_fg, warn="#ffbf69",
        err="#ff6b72" if dark else "#b3261e",
        scrim="rgba(23, 23, 33, 0.78)", ink=bg2,
        primary=primary,
        on_primary=on_primary,
        primary_container=primary_container,
        on_primary_container=on_primary_container,
        secondary=secondary,
        on_secondary=on_secondary,
        secondary_container=secondary_container,
        on_secondary_container=on_secondary_container,
        tertiary=tertiary,
        on_tertiary=on_tertiary,
        tertiary_container=tertiary_container,
        on_tertiary_container=on_tertiary_container,
        error=error,
        on_error=on_error,
        error_container=error_container,
        on_error_container=on_error_container,
        background=background,
        on_background=on_background,
        on_surface=on_surface,
        surface_variant=surface_variant,
        on_surface_variant=on_surface_variant,
        surface_container_lowest=surface_container_lowest,
        surface_container_low=surface_container_low,
        surface_container=surface_container,
        surface_container_high=surface_container_high,
        surface_container_highest=surface_container_highest,
        outline=outline,
        outline_variant=outline_variant,
        inverse_surface=inverse_surface,
        inverse_on_surface=inverse_on_surface,
        inverse_primary=inverse_primary,
        scrim_color=scrim_color,
        shadow_color=shadow_color,
    )


violet_light = _variant(bg="#f5f2ff", bg2="#ede7ff", surface="#ffffff", surface2="#f7f4ff", fg="#08060d", dim="#473872", dim2="#6a54aa", line="#dacdff", line2="#cab8ff", accent="#9f7eff", accentText="#5b3f9e", accent_fg="#08060d", primary="#64558f", on_primary="#ffffff", primary_container="#e8ddff", on_primary_container="#4c3e76", secondary="#615b71", on_secondary="#ffffff", secondary_container="#e8def8", on_secondary_container="#494458", tertiary="#7d5261", on_tertiary="#ffffff", tertiary_container="#ffd9e3", on_tertiary_container="#633b49", error="#ba1a1a", on_error="#ffffff", error_container="#ffdad6", on_error_container="#93000a", background="#fffbff", on_background="#1d1927", on_surface="#1d1927", surface_variant="#e7dff3", on_surface_variant="#494454", surface_container_lowest="#fffbff", surface_container_low="#f8f1ff", surface_container="#f3eafe", surface_container_high="#ede5f9", surface_container_highest="#e7dff3", outline="#79757f", outline_variant="#878192", inverse_surface="#322e3d", inverse_on_surface="#f5eeff", inverse_primary="#cebdfe", scrim_color="#000000", shadow_color="#000000", dark=False, label="Violet")
violet_dark = _variant(bg="#171721", bg2="#222130", surface="#2a293c", surface2="#444361", fg="#ffffff", dim="#aaaab7", dim2="#8b8a9d", line="#35344b", line2="#605f78", accent="#9f7eff", accentText="#c6b2ff", accent_fg="#08060d", primary="#cebdfe", on_primary="#35275d", primary_container="#4c3e76", on_primary_container="#e8ddff", secondary="#cbc3dc", on_secondary="#332e41", secondary_container="#494458", on_secondary_container="#e8def8", tertiary="#efb8c9", on_tertiary="#492533", tertiary_container="#633b49", on_tertiary_container="#ffd9e3", error="#ffb4ab", on_error="#690005", error_container="#93000a", on_error_container="#ffdad6", background="#15111f", on_background="#f5eeff", on_surface="#f5eeff", surface_variant="#3b3746", on_surface_variant="#cbc3d6", surface_container_lowest="#0f0c19", surface_container_low="#1d1927", surface_container="#211e2b", surface_container_high="#2c2836", surface_container_highest="#373341", outline="#938f99", outline_variant="#878192", inverse_surface="#f5eeff", inverse_on_surface="#322e3d", inverse_primary="#64558f", scrim_color="#000000", shadow_color="#000000", dark=True, label="Violet")

indigo_light = _variant(bg="#f2f4ff", bg2="#e8ebff", surface="#ffffff", surface2="#f5f6ff", fg="#08060d", dim="#3b4172", dim2="#5761aa", line="#cfd5ff", line2="#bac3ff", accent="#8293ff", accentText="#4a56a8", accent_fg="#08060d", primary="#525a92", on_primary="#ffffff", primary_container="#dee0ff", on_primary_container="#3a4379", secondary="#5b5d72", on_secondary="#ffffff", secondary_container="#e0e1f9", on_secondary_container="#434559", tertiary="#77536d", on_tertiary="#ffffff", tertiary_container="#ffd7f1", on_tertiary_container="#5d3c54", error="#ba1a1a", on_error="#ffffff", error_container="#ffdad6", on_error_container="#93000a", background="#fffbff", on_background="#191b26", on_surface="#191b26", surface_variant="#e2e1f2", on_surface_variant="#454653", surface_container_lowest="#fffbff", surface_container_low="#f4f2ff", surface_container="#edecfd", surface_container_high="#e7e7f7", surface_container_highest="#e2e1f2", outline="#767680", outline_variant="#828391", inverse_surface="#2e303c", inverse_on_surface="#f0efff", inverse_primary="#bbc3ff", scrim_color="#000000", shadow_color="#000000", dark=False, label="Indigo")
indigo_dark = _variant(bg="#12171f", bg2="#1b212d", surface="#212838", surface2="#36425b", fg="#ffffff", dim="#a4a9b5", dim2="#828999", line="#2a3346", line2="#545e73", accent="#8293ff", accentText="#b4beff", accent_fg="#08060d", primary="#bbc3ff", on_primary="#232c61", primary_container="#3a4379", on_primary_container="#dee0ff", secondary="#c4c5dd", on_secondary="#2d2f42", secondary_container="#434559", on_secondary_container="#e0e1f9", tertiary="#e6bad7", on_tertiary="#45263d", tertiary_container="#5d3c54", on_tertiary_container="#ffd7f1", error="#ffb4ab", on_error="#690005", error_container="#93000a", on_error_container="#ffdad6", background="#11131e", on_background="#f0efff", on_surface="#f0efff", surface_variant="#373845", on_surface_variant="#c5c5d5", surface_container_lowest="#0c0d18", surface_container_low="#191b26", surface_container="#1d1f2b", surface_container_high="#282935", surface_container_highest="#333440", outline="#90909a", outline_variant="#828391", inverse_surface="#f0efff", inverse_on_surface="#2e303c", inverse_primary="#525a92", scrim_color="#000000", shadow_color="#000000", dark=True, label="Indigo")

sky_light = _variant(bg="#f1f8fe", bg2="#e7f3fe", surface="#ffffff", surface2="#f4f9fe", fg="#08060d", dim="#385272", dim2="#527ca9", line="#cce5fe", line2="#b6dafe", accent="#7bbdfe", accentText="#235f93", accent_fg="#08060d", primary="#32628d", on_primary="#ffffff", primary_container="#cfe5ff", on_primary_container="#134a74", secondary="#526070", on_secondary="#ffffff", secondary_container="#d6e4f7", on_secondary_container="#3a4857", tertiary="#695779", on_tertiary="#ffffff", tertiary_container="#f0dbff", on_tertiary_container="#514060", error="#ba1a1a", on_error="#ffffff", error_container="#ffdad6", on_error_container="#93000a", background="#fcfcff", on_background="#161c23", on_surface="#161c23", surface_variant="#dde3ed", on_surface_variant="#41474f", surface_container_lowest="#fcfcff", surface_container_low="#eef4fe", surface_container="#e9eef8", surface_container_high="#e3e8f2", surface_container_highest="#dde3ed", outline="#73777f", outline_variant="#7e848d", inverse_surface="#2b3138", inverse_on_surface="#ecf1fb", inverse_primary="#9dcbfc", scrim_color="#000000", shadow_color="#000000", dark=False, label="Sky")
sky_dark = _variant(bg="#182127", bg2="#222f39", surface="#2a3a46", surface2="#455f72", fg="#ffffff", dim="#abb7bf", dim2="#8b9ba7", line="#354a58", line2="#607787", accent="#7bbdfe", accentText="#a9d5ff", accent_fg="#08060d", primary="#9dcbfc", on_primary="#003355", primary_container="#134a74", on_primary_container="#cfe5ff", secondary="#bac8da", on_secondary="#243240", secondary_container="#3a4857", on_secondary_container="#d6e4f7", tertiary="#d4bee6", on_tertiary="#392a49", tertiary_container="#514060", on_tertiary_container="#f0dbff", error="#ffb4ab", on_error="#690005", error_container="#93000a", on_error_container="#ffdad6", background="#0e141b", on_background="#ecf1fb", on_surface="#ecf1fb", surface_variant="#343a41", on_surface_variant="#c1c7d0", surface_container_lowest="#090f15", surface_container_low="#161c23", surface_container="#1a2027", surface_container_high="#242a32", surface_container_highest="#2f353d", outline="#8c9199", outline_variant="#7e848d", inverse_surface="#ecf1fb", inverse_on_surface="#2b3138", inverse_primary="#32628d", scrim_color="#000000", shadow_color="#000000", dark=True, label="Sky")

aqua_light = _variant(bg="#f1fbfc", bg2="#e7f9fa", surface="#ffffff", surface2="#f4fcfd", fg="#08060d", dim="#386168", dim2="#53939a", line="#cdf3f5", line2="#b6edf1", accent="#7ce0e6", accentText="#126f77", accent_fg="#08060d", primary="#00696e", on_primary="#ffffff", primary_container="#9cf0f6", on_primary_container="#004f53", secondary="#4a6364", on_secondary="#ffffff", secondary_container="#cce8e9", on_secondary_container="#324b4c", tertiary="#4e5f7d", on_tertiary="#ffffff", tertiary_container="#d6e3ff", on_tertiary_container="#364764", error="#ba1a1a", on_error="#ffffff", error_container="#ffdad6", on_error_container="#93000a", background="#f4fefe", on_background="#141d1e", on_surface="#141d1e", surface_variant="#dae4e5", on_surface_variant="#3f4949", surface_container_lowest="#f4fefe", surface_container_low="#ebf6f6", surface_container="#e6f0f0", surface_container_high="#e0eaea", surface_container_highest="#dae4e5", outline="#6f7979", outline_variant="#7c8686", inverse_surface="#293233", inverse_on_surface="#e9f3f3", inverse_primary="#80d4d9", scrim_color="#000000", shadow_color="#000000", dark=False, label="Aqua")
aqua_dark = _variant(bg="#15241c", bg2="#1f3328", surface="#263f32", surface2="#3e6751", fg="#ffffff", dim="#a8bab0", dim2="#87a093", line="#30503f", line2="#5a7d6b", accent="#7ce0e6", accentText="#a6eff3", accent_fg="#08060d", primary="#80d4d9", on_primary="#003739", primary_container="#004f53", on_primary_container="#9cf0f6", secondary="#b1cccd", on_secondary="#1b3436", secondary_container="#324b4c", on_secondary_container="#cce8e9", tertiary="#b6c7e9", on_tertiary="#1f314c", tertiary_container="#364764", on_tertiary_container="#d6e3ff", error="#ffb4ab", on_error="#690005", error_container="#93000a", on_error_container="#ffdad6", background="#0c1516", on_background="#e9f3f3", on_surface="#e9f3f3", surface_variant="#313b3b", on_surface_variant="#bec8c9", surface_container_lowest="#071010", surface_container_low="#141d1e", surface_container="#182122", surface_container_high="#222c2c", surface_container_highest="#2d3637", outline="#899393", outline_variant="#7c8686", inverse_surface="#e9f3f3", inverse_on_surface="#293233", inverse_primary="#00696e", scrim_color="#000000", shadow_color="#000000", dark=True, label="Aqua")

mint_light = _variant(bg="#f1fff5", bg2="#e7ffee", surface="#ffffff", surface2="#f4fff7", fg="#08060d", dim="#386e4c", dim2="#52a76f", line="#ccffdc", line2="#b6ffcc", accent="#7bffa4", accentText="#216a43", accent_fg="#08060d", primary="#316a42", on_primary="#ffffff", primary_container="#b3f1bf", on_primary_container="#16512c", secondary="#506352", on_secondary="#ffffff", secondary_container="#d2e8d3", on_secondary_container="#394b3c", tertiary="#3a656e", on_tertiary="#ffffff", tertiary_container="#bdeaf5", on_tertiary_container="#204d56", error="#ba1a1a", on_error="#ffffff", error_container="#ffdad6", on_error_container="#93000a", background="#f5fff3", on_background="#121e14", on_surface="#121e14", surface_variant="#d7e7d6", on_surface_variant="#3c4a3e", surface_container_lowest="#f5fff3", surface_container_low="#e8f8e7", surface_container="#e3f2e1", surface_container_high="#ddecdc", surface_container_highest="#d7e7d6", outline="#717971", outline_variant="#798879", inverse_surface="#263428", inverse_on_surface="#e5f5e4", inverse_primary="#98d5a4", scrim_color="#000000", shadow_color="#000000", dark=False, label="Mint")
mint_dark = _variant(bg="#15241a", bg2="#1f3425", surface="#26412e", surface2="#3e694b", fg="#ffffff", dim="#a8bbae", dim2="#87a28f", line="#30513a", line2="#5a7f66", accent="#7bffa4", accentText="#a9ffc2", accent_fg="#08060d", primary="#98d5a4", on_primary="#00391a", primary_container="#16512c", on_primary_container="#b3f1bf", secondary="#b7ccb7", on_secondary="#223526", secondary_container="#394b3c", on_secondary_container="#d2e8d3", tertiary="#a2ced9", on_tertiary="#01363f", tertiary_container="#204d56", on_tertiary_container="#bdeaf5", error="#ffb4ab", on_error="#690005", error_container="#93000a", on_error_container="#ffdad6", background="#0a160d", on_background="#e5f5e4", on_surface="#e5f5e4", surface_variant="#2f3c31", on_surface_variant="#bbcbbb", surface_container_lowest="#051108", surface_container_low="#121e14", surface_container="#162218", surface_container_high="#202d22", surface_container_highest="#2b382d", outline="#8b938a", outline_variant="#798879", inverse_surface="#e5f5e4", inverse_on_surface="#263428", inverse_primary="#316a42", scrim_color="#000000", shadow_color="#000000", dark=True, label="Mint")

# Public uppercase aliases used by the runtime appearance state.
VIOLET_LIGHT = violet_light
VIOLET_DARK = violet_dark

FAMILIES = {
    "violet": ("Violet", violet_light, violet_dark),
    "indigo": ("Indigo", indigo_light, indigo_dark),
    "sky": ("Sky", sky_light, sky_dark),
    "aqua": ("Aqua", aqua_light, aqua_dark),
    "mint": ("Mint", mint_light, mint_dark),
}

PALETTES: dict[str, Palette] = {}
for _family, (_label, _light, _dark) in FAMILIES.items():
    PALETTES[_light.name] = _light
    PALETTES[_dark.name] = _dark

# Legacy saved values resolve to the nearest family.
ALIASES = {
    "": "violet",
    "auto": "violet",
    "system": "violet",
    "flufi": "violet-dark",
    "dark": "violet-dark",
    "dusk": "violet-dark",
    "paper": "violet-light",
    "light": "violet-light",
    "ink": "indigo-dark",
    "amoled": "indigo-dark",
    "midnight": "sky-dark",
    "tide": "aqua-dark",
    "forest": "mint-dark",
    "rose": "violet-dark",
    "copper": "violet-dark",
    "mocha": "violet-dark",
}
# END GENERATED PALETTES

THEME_ORDER = list(FAMILIES)


def family_label(name: str) -> str:
    key = family_of(name)
    return FAMILIES[key][0]


def family_of(name: str) -> str:
    key = (name or "").lower()
    key = ALIASES.get(key, key)
    for family in FAMILIES:
        if key == family or key.startswith(f"{family}-"):
            return family
    return "violet"


def mode_of(name: str) -> str:
    key = (name or "").lower()
    if not key or key == "auto":
        return "auto"
    key = ALIASES.get(key, key)
    if key.endswith("-light"):
        return "light"
    if key.endswith("-dark"):
        return "dark"
    return "auto"


def with_mode(name: str, mode: str) -> str:
    family = family_of(name)
    if mode == "auto":
        return family
    return f"{family}-{mode}"


def resolve_theme(name: str, dark: bool = True) -> Palette:
    """Family ids follow `dark`; explicit `-light`/`-dark` ids are exact."""
    key = (name or "").lower().strip()
    key = ALIASES.get(key, key)
    if key in PALETTES:
        return PALETTES[key]
    if key in FAMILIES:
        return FAMILIES[key][2 if dark else 1]
    return violet_dark if dark else violet_light

ACCENTS = [
    ("#9f7eff", "violet"),
    ("#8293ff", "indigo"),
    ("#7bbdfe", "sky"),
    ("#7ce0e6", "aqua"),
    ("#7bffa4", "mint"),
]

# Mutable process-wide appearance state.
_ACTIVE = violet_dark
_ACCENT_OVERRIDE = ""
_THEME_NAME = "violet"


def _readable_on(hex_color: str) -> str:
    c = QColor(hex_color)
    lum = (0.299 * c.redF()) + (0.587 * c.greenF()) + (0.114 * c.blueF())
    return "#000000" if lum > 0.6 else "#ffffff"


def system_dark() -> bool:
    """Best-effort system appearance for bare family ids."""
    try:
        scheme = QGuiApplication.styleHints().colorScheme()
        return scheme == Qt.ColorScheme.Dark
    except Exception:
        pass
    palette = QGuiApplication.palette() if QGuiApplication.instance() else QPalette()
    window = palette.color(QPalette.ColorRole.Window)
    lum = (0.299 * window.redF()) + (0.587 * window.greenF()) + (0.114 * window.blueF())
    return lum < 0.5


def set_appearance(theme: str, accent: str | None, dark: bool | None = None) -> Palette:
    """Mirror of applySet(): palette lookup, then accent override."""
    global _ACTIVE, _ACCENT_OVERRIDE, _THEME_NAME
    base = resolve_theme(theme, system_dark() if dark is None else dark)
    _THEME_NAME = base.name
    _ACCENT_OVERRIDE = accent or ""
    if accent and QColor(accent).isValid():
        base = replace(
            base,
            accent=accent.lower(),
            accent_fg=_readable_on(accent),
        )
    _ACTIVE = base
    return base


def pal() -> Palette:
    return _ACTIVE


def theme_name() -> str:
    return _THEME_NAME


def accent_override() -> str:
    return _ACCENT_OVERRIDE


# ── typography ──────────────────────────────────────────────────────────────

_FAMILIES: dict[str, str] = {}


def _pick(candidates: list[str], fallback: str) -> str:
    available = set(QFontDatabase.families())
    for name in candidates:
        if name in available:
            return name
    return fallback


def families() -> dict[str, str]:
    if not _FAMILIES:
        _FAMILIES["ui"] = _pick(
            ["Inter", "Adwaita Sans", "Cantarell", "Noto Sans", "DejaVu Sans"],
            "Sans Serif",
        )
        _FAMILIES["display"] = _pick(
            ["Inter", "SF Pro Display", "Adwaita Sans", "Cantarell", "Noto Sans",
             "DejaVu Sans"],
            "Sans Serif",
        )
        _FAMILIES["mono"] = _pick(
            ["JetBrains Mono", "Adwaita Mono", "Noto Sans Mono", "DejaVu Sans Mono",
             "Liberation Mono", "Consolas"],
            "Monospace",
        )
    return _FAMILIES


@lru_cache(maxsize=96)
def ui(size: float = 13, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    f = QFont(families()["ui"])
    f.setPixelSize(max(1, int(round(size))))
    f.setWeight(weight)
    return f


@lru_cache(maxsize=64)
def display(size: float = 30, weight: QFont.Weight = QFont.Weight.DemiBold) -> QFont:
    f = QFont(families()["display"])
    f.setPixelSize(max(1, int(round(size))))
    f.setWeight(weight)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, -0.4)
    return f


@lru_cache(maxsize=96)
def mono(size: float = 10, weight: QFont.Weight = QFont.Weight.Normal,
         spacing: float = 0.0) -> QFont:
    f = QFont(families()["mono"])
    f.setPixelSize(max(1, int(round(size))))
    f.setWeight(weight)
    if spacing:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
    return f


# ── widget stylesheet ───────────────────────────────────────────────────────


def _rgba(color: str, alpha: int) -> str:
    """QSS-safe rgba() from a palette token; alpha is 0–255."""
    c = QColor(color)
    if not c.isValid():
        return f"rgba(255, 255, 255, {alpha / 255:.2f})"
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha / 255:.2f})"


def stylesheet(p: Palette | None = None) -> str:
    p = p or pal()
    return f"""
    QWidget {{
        color: {p.on_surface};
        selection-background-color: {p.primary};
        selection-color: {p.on_primary};
        font-size: 16px;
    }}
    QLineEdit {{
        background: {p.surface_container};
        border: 1px solid {p.outline_variant};
        border-radius: 999px;
        min-height: 48px;
        padding: 10px 20px;
        color: {p.on_surface};
        font-size: 16px;
    }}
    QLineEdit:focus {{
        border-color: {p.primary};
        background: {p.surface_container_high};
    }}
    QLineEdit[echoMode="2"] {{ letter-spacing: 2px; }}
    QMenu {{
        background: {p.surface_container};
        border: 1px solid {p.outline_variant};
        border-radius: 28px;
        padding: 8px;
    }}
    QMenu::item {{
        padding: 12px 32px 12px 20px;
        border-radius: 16px;
        color: {p.on_surface};
        font-size: 14px;
    }}
    QMenu::item:selected {{ background: {p.primary_container}; color: {p.on_primary_container}; }}
    QMenu::item:disabled {{ color: {p.on_surface_variant}; }}
    QMenu::separator {{ height: 1px; background: {p.outline_variant}; margin: 4px 8px; }}
    QScrollBar:vertical {{
        background: transparent; width: 12px; margin: 2px 2px 2px 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.outline_variant}; border-radius: 999px; min-height: 36px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {p.primary}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0; background: none; border: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        background: transparent; height: 12px; margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p.outline_variant}; border-radius: 999px; min-width: 36px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0; background: none; border: none;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    QToolTip {{
        background: {p.inverse_surface}; color: {p.inverse_on_surface};
        border: 1px solid {p.outline_variant};
        border-radius: 12px; padding: 8px 12px;
        font-size: 14px;
    }}
    QDialog {{ background: {p.background}; }}
    QMessageBox {{ background: {p.background}; }}
    QMessageBox QLabel {{ color: {p.on_background}; }}
    QPushButton {{
        background: {p.surface_container_high};
        border: 1px solid {p.outline_variant};
        border-radius: 999px;
        min-height: 48px;
        padding: 12px 24px;
        color: {p.on_surface};
        font-size: 14px;
    }}
    QPushButton:hover {{ background: {p.primary_container}; color: {p.on_primary_container}; }}
    QMessageBox QPushButton:hover {{ background: {p.primary_container}; }}
    QColorDialog {{ background: {p.surface_container}; }}
    QAbstractScrollArea {{ border: none; }}
    """


def qpalette(p: Palette | None = None) -> QPalette:
    """Native palette so stock widgets (menus, color dialog) follow the theme."""
    p = p or pal()
    out = QPalette()
    roles = {
        QPalette.ColorRole.Window: p.background,
        QPalette.ColorRole.WindowText: p.on_surface,
        QPalette.ColorRole.Base: p.background,
        QPalette.ColorRole.AlternateBase: p.surface_container_low,
        QPalette.ColorRole.Text: p.on_surface,
        QPalette.ColorRole.Button: p.surface_container,
        QPalette.ColorRole.ButtonText: p.on_surface,
        QPalette.ColorRole.Highlight: p.primary,
        QPalette.ColorRole.HighlightedText: p.on_primary,
        QPalette.ColorRole.ToolTipBase: p.inverse_surface,
        QPalette.ColorRole.ToolTipText: p.inverse_on_surface,
        QPalette.ColorRole.PlaceholderText: p.on_surface_variant,
        QPalette.ColorRole.Link: p.primary,
        QPalette.ColorRole.Mid: p.outline_variant,
        QPalette.ColorRole.Dark: p.outline,
        QPalette.ColorRole.Light: p.surface_container_high,
    }
    for role, color in roles.items():
        out.setColor(role, QColor(color))
    return out


def theme_preview(name: str) -> tuple[str, str]:
    """(surface, accent) pair used by the settings theme cards."""
    mode = mode_of(_THEME_NAME)
    p = resolve_theme(
        with_mode(name, mode),
        dark=system_dark() if mode == "auto" else mode == "dark",
    )
    return p.surface_container, p.primary
```

### `app/linux/mcmusic_linux/widgets.py`

```python
"""Custom-painted widgets that carry the mcmusic 4.2.0 look natively.

Everything draws with QPainter from the generated palette and authored shape,
type and motion tokens: flat tonal containers, very round pills and cards,
Lucide glyphs and short springs. No HTML, no QWebEngine, no effects.
"""
from __future__ import annotations

import inspect
import math
from typing import Callable, Optional, Sequence

from PySide6.QtCore import QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from . import design, motion, theme
from .art import ART
from .icons import draw_icon
from .models import Track, fmt_time

STATE = {"covers": True, "density": "comfy"}


def set_covers(enabled: bool) -> None:
    STATE["covers"] = bool(enabled)


def set_density(value: str) -> None:
    STATE["density"] = "compact" if value == "compact" else "comfy"


def C(token: str, alpha: Optional[int] = None) -> QColor:
    color = QColor(getattr(theme.pal(), token))
    if alpha is not None:
        color.setAlpha(alpha)
    return color


def refresh_theme(root: QWidget) -> None:
    for widget in [root, *root.findChildren(QWidget)]:
        hook = getattr(widget, "refresh_theme", None)
        # Qt callables (signals, wrapper objects) can surface under Python
        # attribute names; only invoke hooks we actually declared as methods.
        if inspect.ismethod(hook) or inspect.isfunction(hook):
            hook()
        # Use the inherited QWidget implementation: a widget can legitimately
        # hold a field called `update` (for example a Download button), which
        # shadows the repaint method and made theme refresh crash at startup.
        if isinstance(widget, QWidget):
            QWidget.update(widget)
        else:
            widget.update()


def _fm(font: QFont, text: str) -> int:
    return QFontMetrics(font).horizontalAdvance(text)


def _elide(font: QFont, text: str, width: float) -> str:
    return QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideRight, max(8, int(width)))


# ── primitives ──────────────────────────────────────────────────────────────


class Rule(QWidget):
    def __init__(self, height: int = 1, token: str = "outline_variant", parent=None):
        super().__init__(parent)
        self._token = token
        self.setFixedHeight(height)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), C(self._token))


class Txt(QLabel):
    """Label in the shared M3 type scale, tinted by a generated palette role."""

    def __init__(self, text: str = "", *, size: float = 16, token: str = "on_surface",
                 family: str = "ui", weight: QFont.Weight = QFont.Weight.Normal,
                 spacing: float = 0.0, wrap: bool = False, selectable: bool = False,
                 align: Qt.AlignmentFlag | None = None, parent=None):
        super().__init__(text, parent)
        self._token = token
        role = "display" if family == "display" else "body"
        self._font = design.font(
            role, size=int(size), weight=int(weight) if int(weight) in (400, 500, 600, 700) else 400
        )
        if family == "mono" and spacing:
            self._font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
        self.setFont(self._font)
        self.setWordWrap(wrap)
        if align is not None:
            self.setAlignment(align)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse if selectable
            else Qt.TextInteractionFlag.NoTextInteraction
        )
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        self.setStyleSheet(f"color: {getattr(theme.pal(), self._token)}; background: transparent;")

    def set_token(self, token: str) -> None:
        self._token = token
        self.refresh_theme()


class Glyph(QWidget):
    def __init__(self, name: str, size: int = 16, token: str = "on_surface_variant",
                 fill: bool = False, stroke: float | None = None, parent=None):
        super().__init__(parent)
        self._name = name
        self._token = token
        self._fill = fill
        self._stroke = stroke
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        draw_icon(p, self._name, QRectF(self.rect()), getattr(theme.pal(), self._token),
                  self._stroke, self._fill)

    def set_icon(self, name: str) -> None:
        self._name = name
        self.update()


class IconButton(QAbstractButton):
    """Lucide button with a 48px hit target and the shared press spring."""

    def __init__(self, name: str, *, size: int = design.Shape.touch,
                 icon_size: float = 20, token: str = "on_surface_variant",
                 active_token: str = "primary", fill: bool = False,
                 tooltip: str = "", parent=None):
        super().__init__(parent)
        self._name = name
        self._icon_size = icon_size
        self._token = token
        self._active_token = active_token
        self._fill = fill
        self._active = False
        self._press = 0.0
        size = max(design.Shape.touch, int(size))
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.pressed.connect(lambda: self._animate_press(1.0))
        self.released.connect(lambda: self._animate_press(0.0))

    def _animate_press(self, end: float) -> None:
        motion.tween(self._press, end, self._set_press, self, duration=120)

    def _set_press(self, value) -> None:
        self._press = max(0.0, min(1.0, float(value)))
        self.update()

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self.update()

    def set_icon(self, name: str) -> None:
        if self._name != name:
            self._name = name
            self.update()

    def set_fill(self, fill: bool) -> None:
        self._fill = fill
        self.update()

    def paintEvent(self, _event) -> None:
        pal = theme.pal()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())
        scale = 1.0 - (1.0 - motion.PRESS_SCALE) * self._press
        center = rect.center()
        p.translate(center)
        p.scale(scale, scale)
        p.translate(-center)
        if self.underMouse() or self._active:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal.q("primary_container" if self._active else "secondary_container"))
            radius = rect.height() / 2.0
            p.drawRoundedRect(rect, radius, radius)
        color = getattr(pal, self._active_token if self._active else
                        ("on_surface" if self.underMouse() else self._token))
        side = min(float(self._icon_size), rect.width() - 16)
        icon_rect = QRectF(0, 0, side, side)
        icon_rect.moveCenter(center)
        draw_icon(p, self._name, icon_rect, color, fill=self._fill)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)


class McButton(QAbstractButton):
    """Friendly pill action with a 48px target and flat tonal fills."""

    def __init__(self, text: str, *, solid: bool = False, ghost: bool = False,
                 danger: bool = False, small: bool = False, icon: Optional[str] = None,
                 parent=None):
        super().__init__(parent)
        self._text = text
        self._symbol = icon
        self._solid = solid
        self._ghost = ghost
        self._danger = danger
        self._small = small
        self._font = design.font("label")
        self._press = 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(design.Shape.touch)
        self.setMinimumWidth(self.sizeHint().width())
        self.pressed.connect(lambda: self._animate_press(1.0))
        self.released.connect(lambda: self._animate_press(0.0))

    def _animate_press(self, end: float) -> None:
        motion.tween(self._press, end, self._set_press, self, duration=120)

    def _set_press(self, value) -> None:
        self._press = max(0.0, min(1.0, float(value)))
        self.update()

    def set_text(self, text: str) -> None:
        self._text = text
        self.setMinimumWidth(self.sizeHint().width())
        self.update()

    def sizeHint(self) -> QSize:
        width = _fm(self._font, self._text) + 40
        if self._symbol:
            width += 24
        return QSize(max(72, width), design.Shape.touch)

    def paintEvent(self, _event) -> None:
        pal = theme.pal()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        scale = 1.0 - (1.0 - motion.PRESS_SCALE) * self._press
        center = rect.center()
        p.translate(center)
        p.scale(scale, scale)
        p.translate(-center)
        radius = rect.height() / 2.0
        hover = self.underMouse()
        transparent = QColor(0, 0, 0, 0)
        if self._solid:
            bg, fg = pal.q("primary"), pal.q("on_primary")
            border = transparent
            if hover:
                bg = pal.q("primary").lighter(108)
        elif self._ghost:
            bg = pal.q("secondary_container") if hover else transparent
            border = transparent
            fg = pal.q("on_surface")
        elif self._danger:
            bg = pal.q("error_container")
            border = transparent
            fg = pal.q("on_error_container")
        else:
            bg = pal.q("secondary_container" if hover else "surface_container_high")
            border = pal.q("outline_variant")
            fg = pal.q("on_surface")
        if not self.isEnabled():
            fg = pal.q("on_surface_variant")
            bg = transparent
            border = pal.q("outline_variant")
        p.setPen(QPen(border, 1))
        p.setBrush(bg)
        p.drawRoundedRect(rect, radius, radius)

        icon_w = 20 if self._symbol else 0
        text_w = _fm(self._font, self._text)
        total = text_w + (icon_w + 8 if self._symbol else 0)
        x = center.x() - total / 2
        if self._symbol:
            icon_rect = QRectF(x, center.y() - 10, 20, 20)
            draw_icon(p, self._symbol, icon_rect, fg)
            x += icon_w + 8
        p.setFont(self._font)
        p.setPen(QPen(fg))
        p.drawText(QRectF(x, rect.top(), text_w + 4, rect.height()),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   self._text)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)


class NavButton(QAbstractButton):
    def __init__(self, text: str, icon: str, *, parent=None):
        super().__init__(parent)
        self._text = text
        self._icon = icon
        self._active = False
        self.setFixedHeight(design.Shape.touch)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._font = design.font("label")
        self.setFont(self._font)

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0, 1, 0, -1)
        if self._active or self.underMouse():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(C("primary_container" if self._active else "secondary_container"))
            radius = rect.height() / 2
            p.drawRoundedRect(rect, radius, radius)
        if self._active:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(C("primary"))
            p.drawRoundedRect(QRectF(4, 10, 4, self.height() - 20), 2, 2)
        draw_icon(p, self._icon, QRectF(14, (self.height() - 20) / 2, 20, 20),
                  C("primary" if self._active else "on_surface_variant"))
        p.setFont(self._font)
        p.setPen(QPen(C("on_primary_container" if self._active else "on_surface")))
        p.drawText(QRectF(44, 0, self.width() - 48, self.height()),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), self._text)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)


class PlaylistNavButton(QAbstractButton):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        self._active = False
        self.setFixedHeight(design.Shape.touch)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._font = design.font("label")
        self.setFont(self._font)

    def set_text(self, text: str) -> None:
        self._text = text
        self.update()

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0, 1, 0, -1)
        if self._active or self.underMouse():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(C("primary_container" if self._active else "secondary_container"))
            radius = rect.height() / 2
            p.drawRoundedRect(rect, radius, radius)
        p.setFont(self._font)
        p.setPen(QPen(C("on_primary_container" if self._active else "on_surface")))
        text = QFontMetrics(self._font).elidedText(
            self._text, Qt.TextElideMode.ElideRight, self.width() - 24
        )
        p.drawText(QRectF(12, 0, self.width() - 24, self.height()),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), text)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)


# ── artwork ────────────────────────────────────────────────────────────────


class Artwork(QWidget):
    """Flat tonal cover surface with deterministic Lucide placeholders.

    Real artwork is painted untouched. Missing artwork becomes a tonal tile
    using the same circle/squircle/cookie/flower/pentagon rotation as web and
    Android; there is no offset elevation treatment.
    """

    clicked = Signal()

    def __init__(self, size: int = 46, round_: bool = False, kind: str = "album",
                 name: str = "", parent=None):
        super().__init__(parent)
        self._size = size
        self._round = round_
        self._kind = kind
        self._name = name
        self._track_id: Optional[int] = None
        self._pixmap: Optional[QPixmap] = None
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        ART.loaded.connect(self._art_loaded)

    @property
    def kind(self) -> str:
        return self._kind

    def set_name(self, name: str) -> None:
        if self._name != name:
            self._name = name
            self.update()

    def set_cover(self, track_id: Optional[int], kind: Optional[str] = None,
                  name: Optional[str] = None) -> None:
        if kind:
            self._kind = kind
        if name:
            self._name = name
        if track_id == self._track_id:
            return
        self._track_id = track_id
        self._pixmap = ART.request(track_id) if STATE["covers"] else None
        self.update()

    def set_pixmap(self, pixmap: Optional[QPixmap]) -> None:
        self._pixmap = pixmap
        self.update()

    def _art_loaded(self, track_id: int) -> None:
        if track_id == self._track_id and STATE["covers"]:
            self._pixmap = ART.cached(track_id)
            self.update()

    def _radius(self) -> float:
        if self._size >= 200:
            return float(design.Shape.hero)
        if self._size >= 96:
            return float(design.Shape.card)
        if self._size >= 48:
            return float(design.Shape.cover_max)
        return min(self._size / 2.0, float(design.Shape.cover_min))

    def _path(self, rect: QRectF) -> QPainterPath:
        path = QPainterPath()
        if self._round:
            path.addEllipse(rect)
        else:
            radius = self._radius()
            path.addRoundedRect(rect, radius, radius)
        return path

    def paintEvent(self, _event) -> None:
        pal = theme.pal()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = self._path(rect)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(pal.q("primary_container"))
        p.drawPath(path)
        p.save()
        p.setClipPath(path)
        if self._pixmap is not None and not self._pixmap.isNull() and STATE["covers"]:
            pm = self._pixmap.scaled(
                int(rect.width()), int(rect.height()),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            src = QRect((pm.width() - rect.width()) / 2, (pm.height() - rect.height()) / 2,
                        rect.width(), rect.height())
            p.drawPixmap(rect, pm, QRectF(src))
        else:
            kind = self._kind if self._kind in ("track", "artist", "album") else "album"
            icon = design.placeholder_glyph(self._name or self._kind, kind)
            side = rect.width() * 0.42
            box = QRectF(0, 0, side, side)
            box.moveCenter(rect.center())
            draw_icon(p, icon, box, pal.q("on_primary_container"))
        p.restore()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(pal.q("outline_variant"), 1))
        p.drawPath(path)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


# ── track table ────────────────────────────────────────────────────────────


class TrackList(QWidget):
    """Virtualised track table: paints only the rows in the damage rect."""

    play_requested = Signal(int)
    like_requested = Signal(object)
    more_requested = Signal(object, int, object)

    def __init__(self, *, show_stats: bool = False, parent=None,
                 like_enabled: bool = True):
        super().__init__(parent)
        self.tracks: list[Track] = []
        self.current_id: Optional[int] = None
        self.show_stats = show_stats
        self.like_enabled = like_enabled
        self._hover = -1
        self._pressed = -1
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ART.loaded.connect(self._art_loaded)

    @property
    def compact(self) -> bool:
        return STATE["density"] == "compact"

    @property
    def row_height(self) -> int:
        return design.Shape.touch if self.compact else 56

    # data ---------------------------------------------------------------
    def set_tracks(self, tracks: Sequence[Track], current_id: Optional[int] = None,
                   show_stats: Optional[bool] = None) -> None:
        self.tracks = list(tracks)
        self.current_id = current_id
        if show_stats is not None:
            self.show_stats = show_stats
        self._hover = -1
        self._sync_height()
        self.update()

    def set_current(self, track_id: Optional[int]) -> None:
        if self.current_id != track_id:
            self.current_id = track_id
            self.update()

    def set_liked(self, track_id: int, liked: bool) -> None:
        from dataclasses import replace
        self.tracks = [replace(t, liked=liked) if t.id == track_id else t for t in self.tracks]
        self.update()

    def _sync_height(self) -> None:
        self.setFixedHeight(max(self.row_height, len(self.tracks) * self.row_height))

    def sizeHint(self) -> QSize:
        return QSize(720, max(self.row_height, len(self.tracks) * self.row_height))

    def minimumSizeHint(self) -> QSize:
        return QSize(320, max(self.row_height, len(self.tracks) * self.row_height))

    def refresh_theme(self) -> None:
        self._sync_height()
        self.update()

    def _art_loaded(self, track_id: int) -> None:
        for i, t in enumerate(self.tracks):
            if t.id == track_id:
                self.update(0, i * self.row_height, self.width(), self.row_height)
                break

    # geometry -----------------------------------------------------------
    def _metrics(self, index: int) -> dict[str, QRectF]:
        rh = self.row_height
        y = index * rh
        art = 32 if self.compact else 40
        x = 12.0 + 24 + 12
        art_rect = QRectF(x, y + (rh - art) / 2, art, art)
        x += art + 12
        right = self.width() - 12
        more = QRectF(right - design.Shape.touch, y + 4,
                      design.Shape.touch, design.Shape.touch)
        like = QRectF(more.left() - design.Shape.touch, y + 4,
                      design.Shape.touch, design.Shape.touch)
        right = like.left() - 8
        dur = QRectF(right - 40, y, 40, rh)
        right -= 46
        stats = None
        if self.show_stats:
            stats = QRectF(right - 50, y, 50, rh)
            right -= 56
        album = None
        if self.width() >= 780 and any(t.album for t in self.tracks[index:index + 1]):
            album_w = min(190.0, self.width() * 0.2)
            album = QRectF(right - album_w, y, album_w, rh)
            right -= album_w + 12
        title = QRectF(x, y + (rh - 40) / 2, max(40.0, right - x), 22)
        artist = QRectF(x, title.bottom() + 1, max(40.0, right - x), 20)
        return {
            "row": QRectF(0, y, self.width(), rh),
            "index": QRectF(8, y, 22, rh),
            "art": art_rect,
            "title": title,
            "artist": artist,
            "album": album,
            "stats": stats,
            "duration": dur,
            "like": like,
            "more": more,
        }

    # painting -----------------------------------------------------------
    def paintEvent(self, event) -> None:
        if not self.tracks:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        rh = self.row_height
        top = max(0, event.rect().top() // rh)
        bottom = min(len(self.tracks), event.rect().bottom() // rh + 2)
        num_font = design.font("label", size=12)
        title_font = design.font("label")
        title_font_c = design.font("label", weight=700)
        small_font = design.font("body", size=14)
        chip_font = design.font("label", size=12, weight=700)

        for i in range(top, bottom):
            track = self.tracks[i]
            m = self._metrics(i)
            row = m["row"]
            current = track.id == self.current_id
            hovered = i == self._hover
            if hovered or current:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(C("secondary_container" if hovered and not current
                             else "primary_container"))
                p.drawRoundedRect(row.adjusted(2, 1, 2, -1),
                                  design.Shape.card, design.Shape.card)

            p.setFont(num_font)
            p.setPen(QPen(C("primary" if current else "outline")))
            p.drawText(m["index"], int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                       f"{i + 1:02d}")

            self._paint_cover(p, track, m["art"])

            p.setFont(title_font_c if current else title_font)
            p.setPen(QPen(C("primary" if current else "on_surface")))
            chip_w = 0
            if track.explicit:
                chip_w = 15
            title_width = m["title"].width() - (chip_w + 4 if chip_w else 0)
            p.drawText(m["title"], int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                       _elide(title_font, track.title, title_width))
            if track.explicit:
                chip = QRectF(m["title"].x() + title_width + 4,
                              m["title"].center().y() - 7, 14, 14)
                p.setPen(QPen(C("on_surface_variant"), 1))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(chip, 2, 2)
                p.setFont(chip_font)
                p.setPen(QPen(C("on_surface_variant")))
                p.drawText(chip, int(Qt.AlignmentFlag.AlignCenter), "E")

            p.setFont(small_font)
            p.setPen(QPen(C("on_surface_variant")))
            p.drawText(m["artist"], int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                       _elide(small_font, track.artist, m["artist"].width()))

            if m["album"] is not None:
                p.setFont(small_font)
                p.setPen(QPen(C("on_surface_variant")))
                p.drawText(m["album"], int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                           _elide(small_font, track.album, m["album"].width()))
            if m["stats"] is not None:
                from .models import fmt_count
                p.setFont(small_font)
                p.setPen(QPen(C("on_surface_variant")))
                p.drawText(m["stats"], int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                           fmt_count(track.yt_likes))
            p.setFont(small_font)
            p.setPen(QPen(C("on_surface_variant")))
            p.drawText(m["duration"], int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                       fmt_time(track.duration))

            if self.like_enabled:
                heart = m["like"]
                box = QRectF(0, 0, 15, 15)
                box.moveCenter(heart.center())
                color = C("primary" if track.liked else ("on_surface" if hovered else "on_surface_variant"))
                draw_icon(p, "heart", box, color, fill=track.liked)
            more = m["more"]
            box = QRectF(0, 0, 15, 15)
            box.moveCenter(more.center())
            draw_icon(p, "more-vertical", box, C("on_surface" if hovered else "on_surface_variant"))

    def _paint_cover(self, p: QPainter, track: Track, rect: QRectF) -> None:
        path = QPainterPath()
        radius = design.Shape.cover_min if self.compact else design.Shape.cover_max
        path.addRoundedRect(rect, radius, radius)
        p.save()
        p.setClipPath(path)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("surface_container_high"))
        p.drawPath(path)
        pm = ART.request(track.id) if STATE["covers"] else None
        if pm is not None and not pm.isNull():
            scaled = pm.scaled(
                int(rect.width()), int(rect.height()),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            src = QRectF((scaled.width() - rect.width()) / 2, (scaled.height() - rect.height()) / 2,
                         rect.width(), rect.height())
            p.drawPixmap(rect, scaled, src)
        else:
            box = QRectF(0, 0, rect.width() * 0.5, rect.height() * 0.5)
            box.moveCenter(rect.center())
            draw_icon(p, design.placeholder_glyph(track.title, "track"), box,
                      C("on_primary_container"))
        p.restore()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(C("outline_variant"), 1))
        p.drawPath(path)

    # interaction --------------------------------------------------------
    def _row_at(self, y: float) -> int:
        if not self.tracks:
            return -1
        index = int(y // self.row_height)
        return index if 0 <= index < len(self.tracks) else -1

    def mousePressEvent(self, event) -> None:
        pos = event.position()
        index = self._row_at(pos.y())
        self._pressed = -1
        if index < 0:
            return
        m = self._metrics(index)
        if event.button() == Qt.MouseButton.RightButton:
            self.more_requested.emit(self.tracks[index], index,
                                     self.mapToGlobal(pos.toPoint()))
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self.like_enabled and m["like"].contains(pos):
            self.like_requested.emit(self.tracks[index])
            return
        if m["more"].contains(pos):
            self.more_requested.emit(self.tracks[index], index,
                                     self.mapToGlobal(pos.toPoint()))
            return
        self._pressed = index

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        index = self._row_at(event.position().y())
        if index >= 0 and index == self._pressed:
            m = self._metrics(index)
            pos = event.position()
            if not m["like"].contains(pos) and not m["more"].contains(pos):
                self.play_requested.emit(index)
        self._pressed = -1

    def mouseMoveEvent(self, event) -> None:
        index = self._row_at(event.position().y())
        if index != self._hover:
            self._hover = index
            self.update()

    def leaveEvent(self, event) -> None:
        self._hover = -1
        self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self._hover >= 0:
            self.play_requested.emit(self._hover)
        super().keyPressEvent(event)


# ── tiles, grids, shelves ──────────────────────────────────────────────────


class Tile(QAbstractButton):
    play_clicked = Signal()

    BASE = 158

    def __init__(self, title: str, subtitle: str = "", cover_id: Optional[int] = None,
                 *, round_: bool = False, kind: str = "album", payload=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.cover_id = cover_id
        self.round_ = round_
        self.kind = kind
        self.payload = payload
        self._width = self.BASE
        self._hover = False
        ART.loaded.connect(self._art_loaded)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.set_width(self.BASE)

    def set_width(self, width: int) -> None:
        self._width = max(120, int(width))
        self.setFixedSize(self._width, self._width + 58)

    def _art_rect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._width)

    def _play_rect(self) -> QRectF:
        art = self._art_rect()
        return QRectF(art.right() - 52, art.bottom() - 52,
                      design.Shape.touch, design.Shape.touch)

    def _art_loaded(self, track_id: int) -> None:
        if self.cover_id == track_id:
            self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        # Lists and tiles are unboxed; only the artwork carries the surface.
        art = self._art_rect()
        path = QPainterPath()
        if self.round_:
            path.addEllipse(art)
        else:
            radius = design.Shape.card if self._width >= 120 else design.Shape.cover_max
            path.addRoundedRect(art, radius, radius)
        p.save()
        p.setClipPath(path)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("surface_container_high"))
        p.drawPath(path)
        pm = ART.request(self.cover_id) if STATE["covers"] else None
        if pm is not None and not pm.isNull():
            scaled = pm.scaled(
                int(art.width()), int(art.height()),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            src = QRectF((scaled.width() - art.width()) / 2, (scaled.height() - art.height()) / 2,
                         art.width(), art.height())
            p.drawPixmap(art, scaled, src)
        else:
            kind = "artist" if self.round_ else self.kind
            icon = design.placeholder_glyph(self.title, kind)
            box = QRectF(0, 0, art.width() * 0.36, art.height() * 0.36)
            box.moveCenter(art.center())
            draw_icon(p, icon, box, C("on_primary_container"))
        p.restore()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(C("outline_variant"), 1))
        p.drawPath(path)

        if self._hover:
            play = self._play_rect()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(C("primary"))
            p.drawEllipse(play)
            box = QRectF(0, 0, 20, 20)
            box.moveCenter(play.center())
            draw_icon(p, "play", box, C("on_primary"))

        font_title = design.font("label")
        font_sub = design.font("body", size=14)
        text_align = (Qt.AlignmentFlag.AlignHCenter if self.round_
                      else Qt.AlignmentFlag.AlignLeft)
        title_rect = QRectF(10, art.bottom() + 8, self._width - 20, 18)
        sub_rect = QRectF(10, title_rect.bottom() + 1, self._width - 20, 14)
        p.setFont(font_title)
        p.setPen(QPen(C("on_surface")))
        p.drawText(title_rect, int(text_align | Qt.AlignmentFlag.AlignVCenter),
                   _elide(font_title, self.title, title_rect.width()))
        p.setFont(font_sub)
        p.setPen(QPen(C("on_surface_variant")))
        p.drawText(sub_rect, int(text_align | Qt.AlignmentFlag.AlignVCenter),
                   _elide(font_sub, self.subtitle, sub_rect.width()))

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._play_rect().contains(event.position()):
            self.play_clicked.emit()
            return
        super().mouseReleaseEvent(event)


class TileGrid(QWidget):
    opened = Signal(object)
    played = Signal(object)

    def __init__(self, *, gap: int = 14, tile_width: int = 158, parent=None):
        super().__init__(parent)
        self._gap = gap
        self._base = tile_width
        self._tiles: list[Tile] = []
        self._last_width = -1
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(gap)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    @property
    def tiles(self) -> list[Tile]:
        return self._tiles

    def set_items(self, items: Sequence[dict]) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._tiles = []
        for item in items:
            tile = Tile(
                item.get("title", ""), item.get("subtitle", ""), item.get("cover_id"),
                round_=bool(item.get("round")), kind=item.get("kind", "album"),
                payload=item.get("payload"),
            )
            tile.clicked.connect(lambda _=False, t=tile: self.opened.emit(t.payload))
            tile.play_clicked.connect(lambda t=tile: self.played.emit(t.payload))
            self._tiles.append(tile)
        self._last_width = -1
        self._relayout(force=True)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._relayout()

    def _relayout(self, force: bool = False) -> None:
        if not self._tiles:
            return
        width = self.width()
        if width <= 1:
            return
        cols = max(1, int((width + self._gap) // (self._base + self._gap)))
        tile_w = int((width - self._gap * (cols - 1)) / cols)
        if not force and width == self._last_width:
            return
        self._last_width = width
        while self._grid.count():
            self._grid.takeAt(0)
        for i, tile in enumerate(self._tiles):
            tile.set_width(tile_w)
            self._grid.addWidget(tile, i // cols, i % cols)
        for col in range(cols):
            self._grid.setColumnStretch(col, 0)
        self.updateGeometry()


class HScroll(QScrollArea):
    """Horizontal shelf with a thin scrollbar and wheel-to-scroll."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.viewport().setAutoFillBackground(False)
        self.setStyleSheet("background: transparent; border: none;")

    def wheelEvent(self, event) -> None:
        bar = self.horizontalScrollBar()
        bar.setValue(bar.value() - event.angleDelta().y())
        event.accept()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        inner = self.widget()
        if inner is not None:
            inner.setMinimumHeight(self.viewport().height())

    def refresh_theme(self) -> None:
        self.viewport().update()


class Shelf(QWidget):
    opened = Signal(object)
    played = Signal(object)

    def __init__(self, title: str, meta: str = "", *, tile_width: int = 158, parent=None):
        super().__init__(parent)
        self._tile_w = tile_width
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(10)
        self.title_label = Txt(title, size=18, family="display", token="on_surface")
        head.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignBottom)
        self.meta_label = Txt(meta.upper(), size=9, family="mono", token="on_surface_variant", spacing=1.1)
        head.addWidget(self.meta_label, 0, Qt.AlignmentFlag.AlignBottom)
        head.addStretch(1)
        self._actions = QHBoxLayout()
        self._actions.setSpacing(6)
        head.addLayout(self._actions)
        layout.addLayout(head)

        self.scroll_area = HScroll()
        self.inner = QWidget()
        self.inner.setStyleSheet("background: transparent;")
        self.row = QHBoxLayout(self.inner)
        self.row.setContentsMargins(0, 0, 0, 4)
        self.row.setSpacing(12)
        self.scroll_area.setWidget(self.inner)
        self.scroll_area.setFixedHeight(tile_width + 58 + 16)
        layout.addWidget(self.scroll_area)

    def add_action(self, widget: QWidget) -> None:
        self._actions.addWidget(widget)

    def set_items(self, items: Sequence[dict]) -> None:
        while self.row.count():
            item = self.row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for data in items:
            tile = Tile(
                data.get("title", ""), data.get("subtitle", ""), data.get("cover_id"),
                round_=bool(data.get("round")), kind=data.get("kind", "album"),
                payload=data.get("payload"),
            )
            tile.set_width(self._tile_w)
            tile.clicked.connect(lambda _=False, t=tile: self.opened.emit(t.payload))
            tile.play_clicked.connect(lambda t=tile: self.played.emit(t.payload))
            self.row.addWidget(tile)
        self.row.addStretch(1)

    def set_meta(self, meta: str) -> None:
        self.meta_label.setText(meta.upper())


# ── page furniture ─────────────────────────────────────────────────────────


class PageHead(QWidget):
    def __init__(self, title: str, kicker: str = "", meta: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        if kicker:
            self.kicker = Txt(kicker.upper(), size=10, family="mono", token="primary", spacing=1.8)
            layout.addWidget(self.kicker)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        self.title_label = Txt(title, size=30, family="display", token="on_surface")
        row.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignBottom)
        if meta:
            self.meta_label = Txt(meta.upper(), size=9, family="mono", token="on_surface_variant", spacing=1.2)
            row.addWidget(self.meta_label, 0, Qt.AlignmentFlag.AlignBottom)
        row.addStretch(1)
        self.action_row = QHBoxLayout()
        self.action_row.setSpacing(8)
        row.addLayout(self.action_row)
        layout.addLayout(row)
        layout.addSpacing(10)
        layout.addWidget(Rule())

    def add_action(self, widget: QWidget) -> None:
        self.action_row.addWidget(widget)


class Hero(QWidget):
    def __init__(self, kicker: str, title: str, subs: Sequence[str] = (),
                 cover_id: Optional[int] = None, *, round_: bool = False, parent=None):
        super().__init__(parent)
        self._round = round_
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.setMaximumHeight(300)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 20)
        outer.setSpacing(0)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(26)
        row.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.art = Artwork(190, round_, "artist" if round_ else "album", name=title)
        self.art.set_cover(cover_id, name=title)
        row.addWidget(self.art, 0, Qt.AlignmentFlag.AlignBottom)

        info = QVBoxLayout()
        info.setContentsMargins(0, 0, 0, 2)
        info.setSpacing(7)
        info.addStretch(1)
        self.kicker = Txt(kicker.upper(), size=14, token="primary",
                          weight=QFont.Weight.Bold)
        info.addWidget(self.kicker)
        self.title_label = Txt(title, size=36, family="display", token="on_surface", wrap=True)
        info.addWidget(self.title_label)
        self.sub_label = Txt("  ·  ".join([s for s in subs if s]), size=16,
                             token="on_surface_variant", wrap=True)
        info.addWidget(self.sub_label)
        self.action_row = QHBoxLayout()
        self.action_row.setContentsMargins(0, 6, 0, 0)
        self.action_row.setSpacing(8)
        info.addLayout(self.action_row)
        row.addLayout(info, 1)
        outer.addLayout(row)
        outer.addSpacing(16)
        outer.addWidget(Rule())

    def add_action(self, widget: QWidget) -> None:
        self.action_row.addWidget(widget)

    def paintEvent(self, _event) -> None:
        pal = theme.pal()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(pal.q("surface_container_low"))
        rect = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        p.drawRoundedRect(rect, design.Shape.hero, design.Shape.hero)


class EmptyState(QWidget):
    def __init__(self, title: str, hint: str = "", *, icon: str = "music",
                 action: Optional[tuple[str, Callable[[], None]]] = None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 48, 20, 48)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        glyph = Glyph(icon, 32, "primary")
        layout.addWidget(glyph, 0, Qt.AlignmentFlag.AlignHCenter)
        title_label = Txt(title, size=28, family="display", token="on_surface",
                          align=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)
        if hint:
            hint_label = Txt(hint, size=16, token="on_surface_variant", wrap=True,
                             align=Qt.AlignmentFlag.AlignHCenter)
            hint_label.setMaximumWidth(420)
            layout.addWidget(hint_label, 0, Qt.AlignmentFlag.AlignHCenter)
        if action:
            label, callback = action
            button = McButton(label, small=True)
            button.clicked.connect(callback)
            layout.addSpacing(4)
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)
        self.setMinimumHeight(200)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(C("outline_variant"), 1))
        p.setBrush(C("surface_container_low"))
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.drawRoundedRect(rect, design.Shape.card, design.Shape.card)


class Panel(QWidget):
    def __init__(self, title: Optional[str] = None, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        if title:
            head = Txt(title.upper(), size=14, token="primary",
                       weight=QFont.Weight.Bold)
            head.setContentsMargins(20, 16, 20, 12)
            outer.addWidget(head)
            outer.addWidget(Rule())
        self.body = QWidget()
        self.body.setStyleSheet("background: transparent;")
        self.rows = QVBoxLayout(self.body)
        self.rows.setContentsMargins(0, 0, 0, 0)
        self.rows.setSpacing(0)
        outer.addWidget(self.body)

    def add_row(self, title: str, subtitle: str = "", trailing: Optional[QWidget] = None,
                last: bool = False) -> "SettingRow":
        row = SettingRow(title, subtitle, trailing, last)
        self.rows.addWidget(row)
        return row

    def add_widget(self, widget: QWidget) -> None:
        self.rows.addWidget(widget)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(C("outline_variant"), 1))
        p.setBrush(C("surface_container"))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5),
                          design.Shape.card, design.Shape.card)


class SettingRow(QWidget):
    def __init__(self, title: str, subtitle: str = "", trailing: Optional[QWidget] = None,
                 last: bool = False, parent=None):
        super().__init__(parent)
        self._last = last
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(16)
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(2)
        self.title_label = Txt(title, size=16, token="on_surface")
        text.addWidget(self.title_label)
        self.subtitle_label = None
        if subtitle:
            self.subtitle_label = Txt(subtitle, size=14, token="on_surface_variant", wrap=True)
            text.addWidget(self.subtitle_label)
        layout.addLayout(text, 1)
        if trailing is not None:
            layout.addWidget(trailing, 0, Qt.AlignmentFlag.AlignVCenter)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        if not self._last:
            p.fillRect(QRect(20, self.height() - 1, self.width() - 20, 1),
                       C("outline_variant"))


class StatCard(QWidget):
    """Flat tonal card for admin counters."""

    def __init__(self, value: str, label: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)
        self.value_label = Txt(value, size=28, family="display", token="on_surface")
        layout.addWidget(self.value_label)
        layout.addWidget(Txt(label.upper(), size=14, token="on_surface_variant"))
        self.setMinimumWidth(112)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("primary_container"))
        p.drawRoundedRect(rect, design.Shape.card, design.Shape.card)


# ── controls ───────────────────────────────────────────────────────────────


class SeekBar(QWidget):
    """Flat progress line that waves only while playback is active."""

    seeked = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._position = 0.0
        self._duration = 0.0
        self._phase = 0.0
        self._playing = False
        self._drag: Optional[float] = None
        self._hover = False
        self.setFixedHeight(design.Shape.touch)
        self.setMinimumWidth(90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_values(self, position: float, duration: float) -> None:
        self._position = max(0.0, position or 0)
        self._duration = max(0.0, duration or 0)
        self._phase = self._position * motion.WAVE_HZ * math.tau
        self.update()

    def set_playing(self, playing: bool) -> None:
        if self._playing != bool(playing):
            self._playing = bool(playing)
            self.update()

    def fraction(self) -> float:
        if self._drag is not None:
            return self._drag
        if self._duration <= 0:
            return 0.0
        return min(1.0, max(0.0, self._position / self._duration))

    def _apply(self, event) -> None:
        width = max(1, self.width() - 16)
        frac = (event.position().x() - 8) / width
        self._drag = min(1.0, max(0.0, frac))
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag = 0.0
            self._apply(event)

    def mouseMoveEvent(self, event) -> None:
        self._hover = True
        if self._drag is not None:
            self._apply(event)
        else:
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag is not None:
            frac = self._drag
            self._drag = None
            self.seeked.emit(frac)
            self.update()

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        left = 8.0
        width = max(1.0, self.width() - 16.0)
        cy = self.height() / 2
        frac = self.fraction()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("outline_variant"))
        p.drawRoundedRect(QRectF(left, cy - 3, width, 6), 3, 3)
        if frac > 0:
            p.setBrush(C("primary"))
            if self._playing and not self._drag:
                path = motion.wave_path(width, 6, frac, True, self._phase)
                path.translate(left, cy - 3)
                p.drawPath(path)
            else:
                p.drawRoundedRect(QRectF(left, cy - 3, width * frac, 6), 3, 3)
        if self._hover or self._drag is not None:
            p.setBrush(C("on_primary"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(left + width * frac, cy), 8, 8)


class VolumeControl(QWidget):
    changed = Signal(float)
    mute_clicked = Signal()

    def __init__(self, level: float = 0.8, parent=None):
        super().__init__(parent)
        self._level = level
        self._muted = False
        self._hover = False
        self._drag = False
        self.setFixedSize(140, design.Shape.touch)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_level(self, value: float, muted: bool = False) -> None:
        self._level = min(1.0, max(0.0, float(value)))
        self._muted = muted
        self.update()

    def _groove(self) -> QRectF:
        return QRectF(32, self.height() / 2 - 3, self.width() - 40, 6)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if event.position().x() < 24:
            self.mute_clicked.emit()
            return
        self._drag = True
        self._set_from(event.position().x())

    def mouseMoveEvent(self, event) -> None:
        self._hover = True
        if self._drag:
            self._set_from(event.position().x())
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        self._drag = False
        self.update()

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def _set_from(self, x: float) -> None:
        groove = self._groove()
        value = (x - groove.x()) / max(1.0, groove.width())
        value = min(1.0, max(0.0, value))
        self._level = value
        self._muted = value <= 0.001
        self.changed.emit(value)
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        icon = "volume-x"
        if not self._muted and self._level > 0.01:
            icon = "volume-1" if self._level < 0.5 else "volume-2"
        draw_icon(p, icon, QRectF(6, (self.height() - 20) / 2, 20, 20),
                  C("on_surface_variant" if not self._hover else "on_surface"))
        groove = self._groove()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("outline_variant"))
        p.drawRoundedRect(groove, 3, 3)
        frac = 0.0 if self._muted else self._level
        if frac > 0:
            p.setBrush(C("primary"))
            p.drawRoundedRect(QRectF(groove.x(), groove.y(), groove.width() * frac,
                                     groove.height()), 3, 3)
        if self._hover or self._drag:
            p.setBrush(C("on_primary"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(groove.x() + groove.width() * frac,
                                  groove.center().y()), 7, 7)


class Switch(QAbstractButton):
    """44px visual track inside a 48px hit target."""

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(design.Shape.touch, design.Shape.touch)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggled.connect(lambda _=False: self.update())

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("primary" if self.isChecked() else "outline_variant"))
        p.drawRoundedRect(QRectF(2, 14, 44, 20), 10, 10)
        p.setBrush(C("on_primary" if self.isChecked() else "on_surface"))
        x = 26 if self.isChecked() else 6
        p.drawEllipse(QRectF(x, 16, 16, 16))


class Segmented(QWidget):
    changed = Signal(str)

    def __init__(self, options: Sequence[tuple[str, str]], selected: str = "", parent=None):
        super().__init__(parent)
        self._options = list(options)
        self._selected = selected or (self._options[0][0] if self._options else "")
        self._font = design.font("label")
        self.setFixedHeight(design.Shape.touch)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(self.sizeHint().width())

    @property
    def selected(self) -> str:
        return self._selected

    def set_selected(self, key: str) -> None:
        if key != self._selected:
            self._selected = key
            self.update()

    def _segment_rects(self) -> list[tuple[str, str, QRectF]]:
        out = []
        x = 2.0
        for key, label in self._options:
            w = _fm(self._font, label.upper()) + 24
            out.append((key, label, QRectF(x, 2, w, self.height() - 4)))
            x += w + 2
        return out

    def sizeHint(self) -> QSize:
        return QSize(int(sum(r.width() for _, _, r in self._segment_rects()) + 6),
                     design.Shape.touch)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("surface_container_high"))
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        p.setFont(self._font)
        for key, label, rect in self._segment_rects():
            on = key == self._selected
            if on:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(C("primary"))
                p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
            p.setPen(QPen(C("on_primary" if on else "on_surface_variant")))
            p.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), label.upper())

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        for key, _label, rect in self._segment_rects():
            if rect.contains(event.position()):
                if key != self._selected:
                    self._selected = key
                    self.update()
                    self.changed.emit(key)
                return


class StatusChip(QWidget):
    """Flat tonal status pill."""

    def __init__(self, text: str, token: str = "on_surface_variant", parent=None):
        super().__init__(parent)
        self._text = text.upper()
        self._token = token
        self._font = design.font("label", size=12)
        self.setFixedHeight(28)
        self.setMinimumWidth(self.sizeHint().width())

    def sizeHint(self) -> QSize:
        return QSize(_fm(self._font, self._text) + 24, 28)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("secondary_container"))
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        p.setFont(self._font)
        p.setPen(QPen(C(self._token)))
        p.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), self._text)


class Spinner(QWidget):
    def __init__(self, size: int = 18, parent=None):
        super().__init__(parent)
        self._angle = 0
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._step)
        if motion.enabled():
            self._timer.start()

    def _step(self) -> None:
        self._angle = (self._angle + 9) % 360
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        p.setPen(QPen(C("outline_variant"), 2))
        p.drawArc(rect, 0, 5760)
        p.setPen(QPen(C("primary"), 2))
        p.drawArc(rect, -self._angle * 16, 120 * 16)


# ── fields ─────────────────────────────────────────────────────────────────


class SearchField(QWidget):
    text_changed = Signal(str)
    submitted = Signal(str)

    def __init__(self, placeholder: str = "Search songs, albums, artists", parent=None):
        super().__init__(parent)
        self.setFixedHeight(design.Shape.touch)
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 4, 0)
        layout.setSpacing(10)
        self.icon_glyph = Glyph("search", 22, "on_surface_variant")
        layout.addWidget(self.icon_glyph)
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setFrame(False)
        self.line_edit.setStyleSheet(
            "QLineEdit{background:transparent;border:none;padding:0;color:inherit;}"
            "QLineEdit:focus{border:none;}"
        )
        self.line_edit.setClearButtonEnabled(False)
        self.line_edit.textChanged.connect(self._changed)
        self.line_edit.returnPressed.connect(lambda: self.submitted.emit(self.line_edit.text()))
        self.line_edit.installEventFilter(self)
        layout.addWidget(self.line_edit, 1)
        self.clear_button = IconButton("x", size=design.Shape.touch, icon_size=20,
                                       tooltip="Clear search")
        self.clear_button.clicked.connect(self._clear)
        self.clear_button.setVisible(False)
        layout.addWidget(self.clear_button)
        self._focused = False

    def text(self) -> str:
        return self.line_edit.text()

    def set_text(self, text: str) -> None:
        if self.line_edit.text() != text:
            self.line_edit.setText(text)

    def focus(self) -> None:
        self.line_edit.setFocus()
        self.line_edit.selectAll()

    def _clear(self) -> None:
        self.line_edit.clear()
        self.focus()

    def _changed(self, text: str) -> None:
        self.clear_button.setVisible(bool(text))
        self.text_changed.emit(text)

    def eventFilter(self, obj, event) -> bool:
        if obj is self.line_edit:
            if event.type() == event.Type.FocusIn:
                self._focused = True
                self.update()
            elif event.type() == event.Type.FocusOut:
                self._focused = False
                self.update()
        return super().eventFilter(obj, event)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(C("primary" if self._focused else "outline_variant"), 1))
        p.setBrush(C("surface_container_high"))
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        p.end()
        super().paintEvent(_event)

    def refresh_theme(self) -> None:
        self.update()


class LabeledField(QWidget):
    def __init__(self, label: str, placeholder: str = "", *, password: bool = False,
                 leading: Optional[str] = None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(Txt(label.upper(), size=14, token="primary",
                             weight=QFont.Weight.Bold))
        row = QWidget()
        row.setFixedHeight(design.Shape.touch)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(18, 0, 18, 0)
        row_layout.setSpacing(10)
        if leading:
            row_layout.addWidget(Glyph(leading, 20, "on_surface_variant"))
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setFrame(False)
        self.line_edit.setStyleSheet("QLineEdit{background:transparent;border:none;padding:0;}")
        if password:
            self.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        row_layout.addWidget(self.line_edit, 1)
        layout.addWidget(row)

    def text(self) -> str:
        return self.line_edit.text()

    def set_text(self, text: str) -> None:
        self.line_edit.setText(text)


class FieldFrame(QWidget):
    """Pill field frame; keyboard input is a transparent QLineEdit."""

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(C("outline_variant"), 1))
        p.setBrush(C("surface_container"))
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)


# ── dialogs and overlays ───────────────────────────────────────────────────


class Sheet(QDialog):
    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setModal(True)
        self._title = title

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        self.card = QWidget()
        self.card.setObjectName("sheetCard")
        self.card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        outer.addWidget(self.card)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        head = QWidget()
        head_layout = QHBoxLayout(head)
        head_layout.setContentsMargins(24, 16, 12, 12)
        head_layout.setSpacing(12)
        head_layout.addWidget(Txt(title, size=22, family="display", token="on_surface"), 1)
        close = IconButton("x", size=design.Shape.touch, icon_size=20, tooltip="Close")
        close.clicked.connect(self.reject)
        head_layout.addWidget(close)
        card_layout.addWidget(head)
        card_layout.addWidget(Rule())
        body = QWidget()
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(24, 16, 24, 24)
        self.body.setSpacing(10)
        card_layout.addWidget(body)
        self.setFixedWidth(470)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        p = theme.pal()
        self.card.setStyleSheet(
            f"QWidget#sheetCard{{background:{p.surface_container};"
            f"border:1px solid {p.outline_variant};"
            f"border-radius:{design.Shape.card}px;}}"
        )

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.adjustSize()
        host = self.parentWidget()
        if host is not None:
            center = host.window().frameGeometry().center()
            self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)


def _dialog_buttons(layout: QVBoxLayout, sheet: Sheet, confirm: str, *, danger: bool,
                    on_confirm: Callable[[], None]) -> None:
    row = QHBoxLayout()
    row.setSpacing(8)
    row.addStretch(1)
    cancel = McButton("Cancel", ghost=True)
    cancel.clicked.connect(sheet.reject)
    row.addWidget(cancel)
    ok = McButton(confirm, solid=True, danger=danger)
    ok.clicked.connect(on_confirm)
    row.addWidget(ok)
    layout.addSpacing(4)
    layout.addLayout(row)


def prompt(parent, title: str, label: str, *, placeholder: str = "", initial: str = "",
           confirm: str = "Save") -> Optional[str]:
    sheet = Sheet(parent, title)
    field = LabeledField(label, placeholder)
    field.set_text(initial)
    sheet.body.addWidget(field)
    result: dict[str, Optional[str]] = {"value": None}

    def accept() -> None:
        result["value"] = field.text().strip()
        sheet.accept()

    _dialog_buttons(sheet.body, sheet, confirm, danger=False, on_confirm=accept)
    field.line_edit.returnPressed.connect(accept)
    field.line_edit.setFocus()
    sheet.exec()
    return result["value"] or None


def confirm(parent, title: str, message: str, *, confirm_label: str = "Delete",
            danger: bool = True) -> bool:
    sheet = Sheet(parent, title)
    sheet.body.addWidget(Txt(message, size=13, token="on_surface_variant", wrap=True))
    answer = {"ok": False}

    def accept() -> None:
        answer["ok"] = True
        sheet.accept()

    _dialog_buttons(sheet.body, sheet, confirm_label, danger=danger, on_confirm=accept)
    sheet.exec()
    return answer["ok"]


def message(parent, title: str, text: str) -> None:
    sheet = Sheet(parent, title)
    sheet.body.addWidget(Txt(text, size=13, token="on_surface_variant", wrap=True))
    row = QHBoxLayout()
    row.addStretch(1)
    ok = McButton("OK", solid=True)
    ok.clicked.connect(sheet.accept)
    row.addWidget(ok)
    sheet.body.addLayout(row)
    sheet.exec()


class Toast(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self._message = ""
        self._font = design.font("body", size=14, weight=500)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text: str, msec: int = 2800) -> None:
        self._message = text
        self._timer.start(msec)
        fm = QFontMetrics(self._font)
        width = min(int(fm.horizontalAdvance(text)) + 28, max(200, self.parent().width() - 48))
        self.setFixedSize(width, design.Shape.touch)
        self._reposition()
        self.show()
        self.raise_()

    def _reposition(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        x = (parent.width() - self.width()) // 2
        y = parent.height() - 150
        self.move(max(12, x), max(12, y))

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("inverse_surface"))
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        p.setFont(self._font)
        p.setPen(QPen(C("inverse_on_surface")))
        p.drawText(QRectF(20, 0, self.width() - 40, self.height()),
                   int(Qt.AlignmentFlag.AlignCenter),
                   QFontMetrics(self._font).elidedText(
                       self._message, Qt.TextElideMode.ElideRight, self.width() - 28))
```

### `app/linux/mcmusic_linux/shell.py`

```python
"""The native window: rail, masthead, content stack, deck and overlays."""
from __future__ import annotations

import time
from dataclasses import replace
from typing import Any, Callable, Optional, Sequence

from shiboken6 import isValid
from PySide6.QtCore import (
    QPoint, QRectF, QSize, Qt, QTimer, QUrl, QMimeData,
)
from PySide6.QtGui import (
    QDesktopServices,
    QDrag,
    QFont,
    QGuiApplication,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPen,
    QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import design, icons, motion, theme, widgets
from .api import Api, ApiError, Async, Repo, SessionStore, device_name
from .art import ART
from .icons import draw_icon
from .lyric_visualizer import LyricVisualizer
from .login import LoginPage, SplashPage
from .models import (
    BuildInfo, Me, PlaylistRef, Settings, Track, fmt_count, fmt_time,
)
from .player import PlayerEngine
from .screens import (
    AdminScreen,
    CollectionScreen,
    DevicesScreen,
    DownloadsScreen,
    HomeScreen,
    LibraryScreen,
    LikesScreen,
    ListeningScreen,
    PlaylistScreen,
    PlaylistsScreen,
    RequestsScreen,
    SearchScreen,
    SettingsScreen,
    Screen,
)
from . import updates
from .version import VERSION
from .widgets import (
    Artwork,
    Glyph,
    IconButton,
    McButton,
    PlaylistNavButton,
    NavButton,
    Rule,
    SearchField,
    SeekBar,
    Sheet,
    Txt,
    VolumeControl,
    prompt,
)


def _elide(text: str, width: int, font: QFont) -> str:
    from PySide6.QtGui import QFontMetrics
    return QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideRight, max(10, width))


def _rounded(rect: QRectF, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(rect, float(radius), float(radius))
    return path


class Mark(QWidget):
    def __init__(self, size: int = 26, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        icons.draw_mark(p, QRectF(self.rect()), theme.pal().q("primary"))


class OnlineDot(QWidget):
    def __init__(self, size: int = 5, parent=None):
        super().__init__(parent)
        self._online = True
        self.setFixedSize(size, size)

    def set_online(self, online: bool) -> None:
        self._online = online
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.pal().q("primary" if self._online else "error"))
        p.drawEllipse(QRectF(self.rect()))


class UserButton(QAbstractButton):
    def __init__(self, username: str = "", parent=None):
        super().__init__(parent)
        self._name = username
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(design.Shape.touch)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_user(self, username: str) -> None:
        self._name = username
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:
        font = design.font("label")
        width = 48 + (QFontMetricsWidth(font, self._name) + 12 if self._name else 0)
        return QSize(max(design.Shape.touch, width), design.Shape.touch)

    def paintEvent(self, _event) -> None:
        from PySide6.QtGui import QFontMetrics
        pal = theme.pal()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if self.underMouse():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal.q("secondary_container"))
            radius = self.height() / 2.0
            p.drawRoundedRect(QRectF(self.rect()), radius, radius)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(pal.q("primary"))
        p.drawEllipse(QRectF(6, 8, 32, 32))
        p.setFont(design.font("label"))
        p.setPen(QPen(pal.q("on_primary")))
        p.drawText(QRectF(6, 8, 32, 32), int(Qt.AlignmentFlag.AlignCenter),
                   (self._name[:1] or "?").upper())
        if self._name:
            font = design.font("label")
            p.setFont(font)
            p.setPen(QPen(pal.q("on_surface")))
            text = QFontMetrics(font).elidedText(
                self._name, Qt.TextElideMode.ElideRight, self.width() - 52
            )
            p.drawText(QRectF(44, 0, self.width() - 46, self.height()),
                       int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), text)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)


def QFontMetricsWidth(font: QFont, text: str) -> int:
    from PySide6.QtGui import QFontMetrics
    return QFontMetrics(font).horizontalAdvance(text)


class PlayButton(QAbstractButton):
    """Pill-to-squircle transport button with the shared press treatment."""

    def __init__(self, size: int = design.Shape.touch + 10, parent=None):
        super().__init__(parent)
        self._size = size
        self._playing = False
        self._morph = 0.0
        self._press = 0.0
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pressed.connect(lambda: self._animate_press(1.0))
        self.released.connect(lambda: self._animate_press(0.0))

    def _animate_press(self, end: float) -> None:
        motion.tween(self._press, end, self._set_press, self, duration=120)

    def _set_morph(self, value) -> None:
        self._morph = max(0.0, min(1.0, float(value)))
        self.update()

    def _set_press(self, value) -> None:
        self._press = max(0.0, min(1.0, float(value)))
        self.update()

    def set_playing(self, playing: bool) -> None:
        if self._playing != playing:
            self._playing = playing
            motion.tween(self._morph, 1.0 if playing else 0.0,
                         self._set_morph, self)

    def paintEvent(self, _event) -> None:
        pal = theme.pal()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())
        scale = 1.0 - (1.0 - motion.PRESS_SCALE) * self._press
        center = rect.center()
        p.translate(center)
        p.scale(scale, scale)
        p.translate(-center)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(pal.q("primary"))
        radius = (1.0 - self._morph) * (self._size / 2.0) \
            + self._morph * design.Shape.lg
        p.drawRoundedRect(rect, radius, radius)
        icon = "pause" if self._playing else "play"
        side = self._size * 0.42
        box = QRectF(0, 0, side, side)
        box.moveCenter(center)
        if icon == "play":
            box.translate(1, 0)
        draw_icon(p, icon, box, pal.q("on_primary"))


class Rail(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__()
        self.shell = window
        self._nav: dict[str, NavButton] = {}
        self._pl_buttons: list[PlaylistNavButton] = []
        self._online = OnlineDot(5)
        self._net_label = Txt("ONLINE", size=14, token="primary", weight=QFont.Weight.Bold)
        self.setFixedWidth(252)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 14)
        layout.setSpacing(0)

        brand = QWidget()
        brand_line = QHBoxLayout(brand)
        brand_line.setContentsMargins(10, 0, 10, 16)
        brand_line.setSpacing(9)
        brand_line.addWidget(Mark(26))
        brand_line.addWidget(Txt("mcmusic", size=20, family="display", token="on_surface"))
        brand_line.addStretch(1)
        brand_line.addWidget(Txt("LINUX", size=14, token="primary", weight=QFont.Weight.Bold))
        layout.addWidget(brand)

        for key, label, icon in (
            ("home", "Home", "home"),
            ("search", "Search", "search"),
            ("library", "Library", "library"),
        ):
            layout.addWidget(self._nav_button(key, label, icon))

        layout.addWidget(self._rule(12, 10, 12, 10))
        layout.addWidget(self._label("YOUR LISTS"))
        for key, label, icon in (
            ("likes", "Liked", "heart"),
            ("playlists", "Playlists", "list-music"),
            ("requests", "Requests", "download"),
            ("downloads", "Downloads", "cloud-download"),
        ):
            layout.addWidget(self._nav_button(key, label, icon))

        layout.addWidget(self._rule(12, 10, 12, 10))
        layout.addWidget(self._label("SERVER"))
        for key, label, icon in (
            ("devices", "Devices", "smartphone"),
            ("listening", "Listening", "users"),
        ):
            layout.addWidget(self._nav_button(key, label, icon))

        layout.addWidget(self._rule(12, 10, 12, 10))
        pl_head = QWidget()
        pl_line = QHBoxLayout(pl_head)
        pl_line.setContentsMargins(10, 0, 6, 6)
        pl_line.setSpacing(4)
        pl_line.addWidget(Txt("PLAYLISTS", size=14, token="primary", weight=QFont.Weight.Bold))
        pl_line.addStretch(1)
        new_pl = IconButton("plus", size=20, icon_size=12, tooltip="New playlist")
        new_pl.clicked.connect(window.create_playlist)
        pl_line.addWidget(new_pl)
        layout.addWidget(pl_head)

        self.pl_scroll = QScrollArea()
        self.pl_scroll.setWidgetResizable(True)
        self.pl_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.pl_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pl_scroll.viewport().setAutoFillBackground(False)
        self.pl_scroll.setStyleSheet("background: transparent; border: none;")
        self.pl_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pl_inner = QWidget()
        self.pl_inner.setStyleSheet("background: transparent;")
        self.pl_layout = QVBoxLayout(self.pl_inner)
        self.pl_layout.setContentsMargins(0, 0, 0, 0)
        self.pl_layout.setSpacing(1)
        self.pl_layout.addStretch(1)
        self.pl_scroll.setWidget(self.pl_inner)
        layout.addWidget(self.pl_scroll, 1)

        self._settings_nav = self._nav_button("settings", "Settings", "settings")
        layout.addWidget(self._settings_nav)
        self._admin_nav = self._nav_button("admin", "Admin", "users")
        self._admin_nav.setVisible(False)
        layout.addWidget(self._admin_nav)

        layout.addWidget(self._rule(8, 10, 8, 10))
        foot = QWidget()
        foot_line = QVBoxLayout(foot)
        foot_line.setContentsMargins(6, 8, 6, 2)
        foot_line.setSpacing(6)
        self.user_button = UserButton()
        self.user_button.clicked.connect(lambda: window.navigate(("settings",)))
        foot_line.addWidget(self.user_button)
        net = QWidget()
        net_line = QHBoxLayout(net)
        net_line.setContentsMargins(4, 0, 0, 0)
        net_line.setSpacing(6)
        net_line.addWidget(self._online)
        net_line.addWidget(self._net_label)
        net_line.addStretch(1)
        foot_line.addWidget(net)
        layout.addWidget(foot)

    def _nav_button(self, key: str, label: str, icon: str) -> NavButton:
        button = NavButton(label, icon)
        button.clicked.connect(lambda _=False, k=key: self.shell.navigate((k,)))
        self._nav[key] = button
        return button

    def _label(self, text: str) -> Txt:
        label = Txt(text.upper(), size=14, token="primary", weight=QFont.Weight.Bold)
        label.setContentsMargins(10, 0, 10, 6)
        return label

    def _rule(self, top: int, left: int, bottom: int, right: int) -> QWidget:
        wrap = QWidget()
        line = QVBoxLayout(wrap)
        line.setContentsMargins(left, top, right, bottom)
        line.addWidget(Rule())
        return wrap

    def set_active(self, route: tuple) -> None:
        kind = route[0] if route else "home"
        active_key = {
            "album": "library", "artist": "library", "playlist": "playlists",
            "home": "home", "search": "search", "library": "library", "likes": "likes",
            "playlists": "playlists", "requests": "requests", "downloads": "downloads",
            "devices": "devices", "listening": "listening", "settings": "settings",
            "admin": "admin",
        }.get(kind, "")
        for key, button in self._nav.items():
            button.set_active(key == active_key)
        playlist_id = route[1] if kind == "playlist" and len(route) > 1 else None
        for button, pid in self._pl_buttons:
            button.set_active(pid == playlist_id)

    def set_user(self, me: Optional[Me]) -> None:
        self.user_button.set_user(me.username if me else "")
        self._admin_nav.setVisible(bool(me and me.is_admin))

    def set_online(self, online: bool) -> None:
        self._online.set_online(online)
        self._net_label.setText("ONLINE" if online else "OFFLINE")

    def set_playlists(self, playlists: Sequence[PlaylistRef], active_id: Optional[int]) -> None:
        while self.pl_layout.count():
            item = self.pl_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self._pl_buttons = []
        for playlist in playlists[:200]:
            button = PlaylistNavButton(playlist.name)
            button.set_active(playlist.id == active_id)
            button.clicked.connect(
                lambda _=False, pid=playlist.id: self.shell.navigate(("playlist", pid))
            )
            self.pl_layout.addWidget(button)
            self._pl_buttons.append((button, playlist.id))
        self.pl_layout.addStretch(1)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        palette = theme.pal()
        card = QRectF(self.rect()).adjusted(8, 12, -8, -12)
        p.setPen(QPen(palette.q("outline_variant"), 1))
        p.setBrush(palette.q("surface_container_low"))
        p.drawRoundedRect(card, design.Shape.card, design.Shape.card)


class TopBar(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__()
        self.setFixedHeight(58)
        line = QHBoxLayout(self)
        line.setContentsMargins(26, 0, 26, 0)
        line.setSpacing(10)
        self.back = IconButton("chevron-left", size=28, tooltip="Back")
        self.back.clicked.connect(window.back)
        self.back.setVisible(False)
        line.addWidget(self.back)
        self.search = SearchField()
        self.search.setMaximumWidth(460)
        self.search.text_changed.connect(window.on_search_text)
        self.search.submitted.connect(window.on_search_submit)
        line.addWidget(self.search, 2)
        line.addStretch(1)
        queue = IconButton("list-music", size=32, tooltip="Queue")
        queue.clicked.connect(window.toggle_queue)
        line.addWidget(queue)
        self.user = UserButton()
        self.user.clicked.connect(lambda: window.navigate(("settings",)))
        line.addWidget(self.user)

    def paintEvent(self, _event) -> None:
        # The shell background shows through; no attached masthead bar.
        pass


class Deck(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__()
        self.setFixedHeight(104)
        grid = QGridLayout(self)
        grid.setContentsMargins(26, 8, 26, 10)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(3)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 1)

        left = QWidget()
        left_line = QHBoxLayout(left)
        left_line.setContentsMargins(0, 0, 0, 0)
        left_line.setSpacing(11)
        self.art = Artwork(52, kind="track")
        self.art.clicked.connect(window.show_now_playing)
        left_line.addWidget(self.art)
        meta = QVBoxLayout()
        meta.setContentsMargins(0, 0, 0, 0)
        meta.setSpacing(1)
        self.title = Txt("Nothing playing right now", size=16, token="on_surface",
                         weight=QFont.Weight.Bold)
        self.title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.artist = Txt("Pick a song from your library", size=14, token="on_surface_variant")
        self.artist.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        meta.addWidget(self.title)
        meta.addWidget(self.artist)
        left_line.addLayout(meta, 1)
        self.like = IconButton("heart", size=30, tooltip="Like")
        self.like.clicked.connect(window.like_current)
        left_line.addWidget(self.like)
        grid.addWidget(left, 0, 0)

        center = QWidget()
        center_line = QVBoxLayout(center)
        center_line.setContentsMargins(0, 0, 0, 0)
        center_line.setSpacing(2)
        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(2)
        controls.addStretch(1)
        self.shuffle = IconButton("shuffle", size=28, icon_size=15, tooltip="Shuffle")
        self.shuffle.clicked.connect(window.toggle_shuffle)
        controls.addWidget(self.shuffle)
        prev = IconButton("skip-back", size=28, icon_size=16, token="on_surface", tooltip="Previous")
        prev.clicked.connect(window.player.prev)
        controls.addWidget(prev)
        self.play = PlayButton()
        self.play.clicked.connect(window.player.toggle)
        controls.addWidget(self.play)
        nxt = IconButton("skip-forward", size=28, icon_size=16, token="on_surface", tooltip="Next")
        nxt.clicked.connect(window.player.next)
        controls.addWidget(nxt)
        self.repeat = IconButton("repeat", size=28, icon_size=15, tooltip="Repeat")
        self.repeat.clicked.connect(window.player.cycle_repeat)
        controls.addWidget(self.repeat)
        controls.addStretch(1)
        center_line.addLayout(controls)

        progress = QHBoxLayout()
        progress.setContentsMargins(0, 0, 0, 0)
        progress.setSpacing(9)
        self.pos_label = Txt("0:00", size=14, token="on_surface_variant",
                       align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.pos_label.setFixedWidth(36)
        progress.addWidget(self.pos_label)
        self.seek = SeekBar()
        self.seek.seeked.connect(window.player.seek_fraction)
        progress.addWidget(self.seek, 1)
        self.dur = Txt("0:00", size=14, token="on_surface_variant")
        self.dur.setFixedWidth(36)
        progress.addWidget(self.dur)
        center_line.addLayout(progress)
        grid.addWidget(center, 0, 1)

        right = QWidget()
        right_line = QHBoxLayout(right)
        right_line.setContentsMargins(0, 0, 0, 0)
        right_line.setSpacing(4)
        right_line.addStretch(1)
        expand = IconButton("tv-2", size=30, tooltip="Now playing")
        expand.clicked.connect(window.show_now_playing)
        right_line.addWidget(expand)
        queue = IconButton("list-music", size=30, tooltip="Queue")
        queue.clicked.connect(window.toggle_queue)
        right_line.addWidget(queue)
        self.volume = VolumeControl()
        self.volume.changed.connect(window.set_volume)
        self.volume.mute_clicked.connect(window.player.toggle_mute)
        right_line.addWidget(self.volume)
        grid.addWidget(right, 0, 2)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        palette = theme.pal()
        card = QRectF(self.rect()).adjusted(12, 2, -12, -8)
        p.setPen(QPen(palette.q("outline_variant"), 1))
        p.setBrush(palette.q("surface_container"))
        p.drawRoundedRect(card, design.Shape.card, design.Shape.card)


QUEUE_MIME = "application/x-mcmusic-queue-index"


class QueueRow(QWidget):
    def __init__(self, window: "McWindow", track: Track, index: int,
                 *, current: bool = False, removable: bool = True,
                 reorder: bool = False, parent=None):
        super().__init__(parent)
        self.shell = window
        self.track = track
        self.index = index
        self.current = current
        self._hover = False
        self._reorder = bool(reorder and not current)
        self._drag_start: Optional[QPoint] = None
        self._dragging = False
        self._drop_target = False
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if self._reorder:
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setAcceptDrops(True)
            self.setToolTip("Drag to reorder, or use Up/Down when focused")
        line = QHBoxLayout(self)
        line.setContentsMargins(6, 5, 6, 5)
        line.setSpacing(10)
        art = Artwork(34, kind="track")
        art.set_cover(track.id, name=track.title)
        art.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        line.addWidget(art)
        meta = QVBoxLayout()
        meta.setContentsMargins(0, 0, 0, 0)
        meta.setSpacing(1)
        title = Txt(track.title, size=14, token="primary" if current else "on_surface",
                    weight=QFont.Weight.DemiBold)
        title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        meta.addWidget(title)
        artist = Txt(track.artist, size=14, token="on_surface_variant")
        artist.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        meta.addWidget(artist)
        line.addLayout(meta, 1)
        if self._reorder:
            up = IconButton("chevron-up", size=26, icon_size=13, tooltip="Move up")
            up.setEnabled(index > window.player.index + 1)
            up.clicked.connect(lambda: self._shift(-1))
            line.addWidget(up)
            down = IconButton("chevron-down", size=26, icon_size=13, tooltip="Move down")
            down.setEnabled(index + 1 < len(window.player.queue))
            down.clicked.connect(lambda: self._shift(1))
            line.addWidget(down)
        if removable and not current:
            remove = IconButton("x", size=26, icon_size=13, tooltip="Remove from queue")
            remove.clicked.connect(lambda: window.player.remove_at(index))
            line.addWidget(remove)

    def _shift(self, delta: int) -> None:
        target = self.index + delta
        if self.shell.player.move(self.index, target):
            self.shell.drawer.focus_index(target)

    @staticmethod
    def _mime_index(event) -> Optional[int]:
        if event.mimeData().hasFormat(QUEUE_MIME):
            raw = bytes(event.mimeData().data(QUEUE_MIME)).decode("utf-8", "replace")
        elif event.mimeData().hasText():
            raw = event.mimeData().text()
        else:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def _can_drop(self, event) -> bool:
        source = self._mime_index(event)
        player = self.shell.player
        return (source is not None and self._reorder
                and source > player.index and self.index > player.index
                and source != self.index)

    def mousePressEvent(self, event) -> None:
        if self._reorder and event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (self._reorder and self._drag_start is not None
                and (event.position().toPoint() - self._drag_start).manhattanLength()
                >= QApplication.startDragDistance()):
            self._dragging = True
            mime = QMimeData()
            mime.setData(QUEUE_MIME, str(self.index).encode("ascii"))
            mime.setText(str(self.index))
            drag = QDrag(self)
            drag.setMimeData(mime)
            drag.setPixmap(self.grab())
            drag.setHotSpot(self._drag_start)
            drag.exec(Qt.DropAction.MoveAction)
            self._drag_start = None
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        dragged = self._dragging
        self._drag_start = None
        self._dragging = False
        if not dragged and event.button() == Qt.MouseButton.LeftButton:
            self.shell.player.jump(self.index)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if not self._reorder:
            super().keyPressEvent(event)
            return
        if event.key() == Qt.Key.Key_Up:
            self._shift(-1)
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            self._shift(1)
            event.accept()
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.shell.player.remove_at(self.index)
            event.accept()
        elif event.key() == Qt.Key.Key_Return:
            self.shell.player.jump(self.index)
            event.accept()
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, event) -> None:
        if self._can_drop(event):
            self._drop_target = True
            self.update()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if self._can_drop(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, _event) -> None:
        self._drop_target = False
        self.update()

    def dropEvent(self, event) -> None:
        source = self._mime_index(event)
        self._drop_target = False
        self.update()
        if source is None or not self._reorder:
            event.ignore()
            return
        target = self.index
        if self.shell.player.move(source, target):
            self.shell.drawer.focus_index(target)
            event.acceptProposedAction()
        else:
            event.ignore()

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event) -> None:
        palette = theme.pal()
        if self._hover or self.hasFocus() or self._drop_target:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            if self._hover or self.hasFocus():
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(palette.q("secondary_container"))
                p.drawRoundedRect(QRectF(self.rect()).adjusted(0, 1, 0, -1),
                                  design.Shape.lg, design.Shape.lg)
            if self._drop_target:
                p.setPen(QPen(palette.q("primary"), 2))
                p.drawLine(QPoint(2, 1), QPoint(self.width() - 2, 1))


class Scrim(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__(window.shell)
        self.shell = window
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.hide()

    def paintEvent(self, _event) -> None:
        color = theme.pal().q("scrim_color")
        color.setAlpha(135)
        QPainter(self).fillRect(self.rect(), color)

    def mouseReleaseEvent(self, event) -> None:
        self.shell.close_overlays()
        super().mouseReleaseEvent(event)


class QueueDrawer(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__(window.shell)
        self.shell = window
        self.setFixedWidth(390)
        self.hide()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        head = QWidget()
        head_line = QHBoxLayout(head)
        head_line.setContentsMargins(16, 16, 12, 12)
        head_line.addWidget(Txt("Queue", size=18, family="display", token="on_surface"))
        head_line.addStretch(1)
        close = IconButton("x", size=28, icon_size=15, tooltip="Close queue")
        close.clicked.connect(window.close_overlays)
        head_line.addWidget(close)
        outer.addWidget(head)
        outer.addWidget(Rule())
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.viewport().setAutoFillBackground(False)
        self.inner = QWidget()
        self.inner.setStyleSheet("background: transparent;")
        self.body = QVBoxLayout(self.inner)
        self.body.setContentsMargins(12, 10, 12, 24)
        self.body.setSpacing(2)
        self._rows: dict[int, QueueRow] = {}
        self.scroll_area.setWidget(self.inner)
        outer.addWidget(self.scroll_area, 1)

    def focus_index(self, index: int) -> None:
        row = self._rows.get(index)
        if row is not None and isValid(row):
            row.setFocus(Qt.FocusReason.OtherFocusReason)

    def refresh(self) -> None:
        self._rows.clear()
        while self.body.count():
            item = self.body.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        player = self.shell.player
        current = player.current
        if current is None:
            self.body.addWidget(Txt("Queue is empty", size=16, token="on_surface_variant"))
            self.body.addStretch(1)
            return
        label = Txt("NOW PLAYING", size=14, token="primary", weight=QFont.Weight.Bold)
        label.setContentsMargins(6, 8, 6, 4)
        self.body.addWidget(label)
        current_row = QueueRow(self.shell, current, player.index, current=True,
                               removable=False)
        self._rows[player.index] = current_row
        self.body.addWidget(current_row)
        upcoming = [(i, t) for i, t in enumerate(player.queue) if i > player.index]
        head = QWidget()
        head_line = QHBoxLayout(head)
        head_line.setContentsMargins(6, 16, 4, 6)
        head_line.addWidget(Txt(f"Next up ({len(upcoming)})", size=14,
                                token="primary", weight=QFont.Weight.Bold))
        head_line.addStretch(1)
        if upcoming:
            clear = McButton("Clear next", small=True, ghost=True)
            clear.clicked.connect(player.clear_upcoming)
            head_line.addWidget(clear)
        self.body.addWidget(head)
        for index, track in upcoming[:80]:
            row = QueueRow(self.shell, track, index, reorder=True)
            self._rows[index] = row
            self.body.addWidget(row)
        if not upcoming:
            self.body.addWidget(Txt("Nothing queued", size=16,
                                    token="on_surface_variant"))
        else:
            hint = Txt("Drag to reorder or focus a row and press Up/Down", size=14,
                       token="on_surface_variant")
            hint.setContentsMargins(6, 8, 6, 0)
            self.body.addWidget(hint)
        self.body.addStretch(1)

    def paintEvent(self, _event) -> None:
        pal = theme.pal()
        p = QPainter(self)
        p.fillRect(self.rect(), pal.q("surface_container_low"))
        p.fillRect(0, 0, 1, self.height(), pal.q("outline_variant"))


class PickRow(QAbstractButton):
    def __init__(self, playlist: PlaylistRef, parent=None):
        super().__init__(parent)
        self.playlist = playlist
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        pal = theme.pal()
        if self.underMouse():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal.q("secondary_container"))
            p.drawRoundedRect(QRectF(self.rect()).adjusted(0, 1, 0, -1),
                              design.Shape.lg, design.Shape.lg)
        box = QRectF(6, (self.height() - 44) / 2, 44, 44)
        path = QRectF(box)
        pm = ART.request(self.playlist.cover_id)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(pal.q("primary_container"))
        p.drawRoundedRect(path, design.Shape.cover_min, design.Shape.cover_min)
        if pm is not None and not pm.isNull():
            p.save()
            p.setClipPath(_rounded(path, design.Shape.cover_min))
            scaled = pm.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                               Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap(box.toRect(), scaled)
            p.restore()
        else:
            draw_icon(p, design.placeholder_glyph(self.playlist.name),
                      box.adjusted(11, 11, -11, -11), pal.q("on_primary_container"))
        font = design.font("label")
        p.setFont(font)
        p.setPen(QPen(pal.q("on_surface")))
        p.drawText(QRectF(60, 6, self.width() - 70, 22),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   _elide(self.playlist.name, self.width() - 70, font))
        p.setFont(design.font("label"))
        p.setPen(QPen(pal.q("on_surface_variant")))
        p.drawText(QRectF(60, 28, self.width() - 70, 20),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   f"{self.playlist.n} tracks")


class NowPlayingOverlay(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__(window.shell)
        self.shell = window
        self._up_next_key: tuple = ()
        self.hide()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.viewport().setAutoFillBackground(False)
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        body = QVBoxLayout(inner)
        body.setContentsMargins(28, 16, 28, 28)
        body.setSpacing(0)

        header = QHBoxLayout()
        close = IconButton("chevron-down", size=32, tooltip="Close player")
        close.clicked.connect(window.close_overlays)
        header.addWidget(close)
        header.addStretch(1)
        header.addWidget(Txt("NOW PLAYING", size=14, token="primary",
                             weight=QFont.Weight.DemiBold))
        header.addStretch(1)
        self.more = IconButton("more-vertical", size=32, tooltip="Track options")
        self.more.clicked.connect(self._more)
        header.addWidget(self.more)
        body.addLayout(header)
        body.addSpacing(10)

        art_row = QHBoxLayout()
        art_row.addStretch(1)
        self.art = Artwork(300, kind="track")
        art_row.addWidget(self.art)
        art_row.addStretch(1)
        body.addLayout(art_row)
        body.addSpacing(20)

        self.title = Txt("Nothing playing right now", size=28, family="display",
                         token="on_surface", weight=QFont.Weight.Bold, wrap=True,
                         align=Qt.AlignmentFlag.AlignHCenter)
        body.addWidget(self.title)
        body.addSpacing(4)
        self.artist = Txt("", size=14, token="on_surface_variant",
                          align=Qt.AlignmentFlag.AlignHCenter)
        body.addWidget(self.artist)
        body.addSpacing(18)

        seek_wrap = QWidget()
        seek_line = QHBoxLayout(seek_wrap)
        seek_line.setContentsMargins(0, 0, 0, 0)
        seek_line.setSpacing(9)
        self.pos_label = Txt("0:00", size=14, token="on_surface_variant")
        self.pos_label.setFixedWidth(38)
        seek_line.addWidget(self.pos_label)
        self.seek = SeekBar()
        self.seek.seeked.connect(window.player.seek_fraction)
        seek_line.addWidget(self.seek, 1)
        self.dur = Txt("0:00", size=14, token="on_surface_variant",
                       align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.dur.setFixedWidth(38)
        seek_line.addWidget(self.dur)
        wrap = QHBoxLayout()
        wrap.addStretch(1)
        seek_wrap.setMaximumWidth(560)
        wrap.addWidget(seek_wrap, 3)
        wrap.addStretch(1)
        body.addLayout(wrap)
        body.addSpacing(16)

        controls = QHBoxLayout()
        controls.addStretch(1)
        self.shuffle = IconButton("shuffle", size=40, icon_size=18, tooltip="Shuffle")
        self.shuffle.clicked.connect(window.toggle_shuffle)
        controls.addWidget(self.shuffle)
        prev = IconButton("skip-back", size=44, icon_size=20, token="on_surface")
        prev.clicked.connect(window.player.prev)
        controls.addWidget(prev)
        self.play = PlayButton()
        self.play.clicked.connect(window.player.toggle)
        controls.addWidget(self.play)
        nxt = IconButton("skip-forward", size=44, icon_size=20, token="on_surface")
        nxt.clicked.connect(window.player.next)
        controls.addWidget(nxt)
        self.repeat = IconButton("repeat", size=40, icon_size=18, tooltip="Repeat")
        self.repeat.clicked.connect(window.player.cycle_repeat)
        controls.addWidget(self.repeat)
        controls.addStretch(1)
        body.addLayout(controls)
        body.addSpacing(10)

        secondary = QHBoxLayout()
        secondary.addStretch(1)
        self.like = IconButton("heart", size=40, tooltip="Like")
        self.like.clicked.connect(window.like_current)
        secondary.addWidget(self.like)
        lyrics = McButton("Lyrics", small=True, ghost=True, icon="text")
        lyrics.clicked.connect(window.show_lyrics)
        secondary.addWidget(lyrics)
        self.sleep_button = McButton("Sleep", small=True, ghost=True, icon="clock")
        self.sleep_button.clicked.connect(
            lambda _=False, b=self.sleep_button: window.show_sleep_menu(b)
        )
        secondary.addWidget(self.sleep_button)
        queue = McButton("Queue", small=True, ghost=True, icon="list-music")
        queue.clicked.connect(window.toggle_queue)
        secondary.addWidget(queue)
        add = IconButton("folder-plus", size=40, tooltip="Add to playlist")
        add.clicked.connect(lambda: window.add_current_to_playlist())
        secondary.addWidget(add)
        secondary.addStretch(1)
        body.addLayout(secondary)
        body.addSpacing(18)

        body.addWidget(Rule())
        body.addSpacing(14)
        self.up_next_label = Txt("UP NEXT", size=14, token="primary",
                                 weight=QFont.Weight.DemiBold)
        body.addWidget(self.up_next_label)
        body.addSpacing(6)
        self.up_next = QVBoxLayout()
        self.up_next.setContentsMargins(0, 0, 0, 0)
        self.up_next.setSpacing(1)
        body.addLayout(self.up_next)
        body.addStretch(1)

        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def _more(self) -> None:
        track = self.shell.player.current
        if track is not None:
            self.shell.open_track_menu(track, self.shell.player.index,
                                        self.mapToGlobal(QPoint(self.width() - 44, 48)))

    def refresh(self) -> None:
        player = self.shell.player
        track = player.current
        if track is None:
            self.title.setText("Nothing playing right now")
            self.artist.setText("Pick a song from your library")
            self.art.set_cover(None)
            self.more.setEnabled(False)
            self.like.setVisible(False)
        else:
            self.art.set_cover(track.id, name=track.title)
            self.title.setText(track.title)
            parts = [track.artist]
            if track.album:
                parts.append(track.album)
            self.artist.setText("  ·  ".join(p for p in parts if p))
            self.more.setEnabled(True)
            self.like.setVisible(True)
            self.like.set_active(track.liked)
            self.like.set_fill(track.liked)
        self.play.set_playing(player.playing)
        self.seek.set_playing(player.playing)
        self.shuffle.set_active(player.shuffle)
        name = "repeat-1" if player.repeat == "one" else "repeat"
        self.repeat.set_icon(name)
        self.repeat.set_active(player.repeat != "off")
        self.pos_label.setText(fmt_time(player.position))
        self.dur.setText(fmt_time(player.duration))
        self.seek.set_values(player.position, player.duration)
        timer = self.shell.store.sleep_timer
        try:
            left = max(0, int((float(timer.get("ends_at", 0)) - time.time()) / 60))
        except (TypeError, ValueError):
            left = 0
        self.sleep_button.set_text(f"Sleep {left}m" if left else "Sleep")

        key = tuple((i, t.id) for i, t in enumerate(player.queue) if i > player.index)[:8]
        if key != self._up_next_key:
            self._up_next_key = key
            while self.up_next.count():
                item = self.up_next.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()
            upcoming = [(i, t) for i, t in enumerate(player.queue) if i > player.index][:8]
            for index, queued in upcoming:
                self.up_next.addWidget(QueueRow(self.shell, queued, index))
            if not upcoming:
                self.up_next.addWidget(Txt("Nothing queued", size=16,
                                           token="on_surface_variant"))

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), theme.pal().q("surface_container_lowest"))


class StatusStrip(QWidget):
    """A quiet, persistent line for offline/pending/update notices."""

    def __init__(self, window: "McWindow"):
        super().__init__()
        self.shell = window
        self._online = True
        self._pending = 0
        self._notice = ""
        self.setFixedHeight(0)
        line = QHBoxLayout(self)
        line.setContentsMargins(30, 0, 26, 0)
        line.setSpacing(8)
        self.icon_glyph = Glyph("check", 16, "primary")
        line.addWidget(self.icon_glyph)
        self.label = Txt("", size=14, token="on_surface_variant")
        line.addWidget(self.label, 1)
        self.sync = McButton("Sync now", small=True, ghost=True, icon="refresh-cw")
        self.sync.clicked.connect(window.sync_outbox)
        self.sync.setVisible(False)
        line.addWidget(self.sync)
        self.update_button = McButton("Open page", small=True, ghost=True, icon="download")
        self.update_button.setToolTip("Open the public download page in your browser")
        self.update_button.clicked.connect(window.open_update)
        self.update_button.setVisible(False)
        line.addWidget(self.update_button)

    def set_state(self, *, online: bool, pending: int = 0, notice: str = "",
                  has_update: bool = False) -> None:
        self._online = online
        self._pending = max(0, int(pending or 0))
        self._notice = notice or ""
        if not online:
            text = "OFFLINE — using saved session"
            self.icon_glyph.set_icon("wifi-off")
        elif self._pending:
            text = f"{self._pending} pending change" + ("s" if self._pending != 1 else "") + " — will sync"
            self.icon_glyph.set_icon("refresh-cw")
        elif self._notice:
            text = self._notice
            self.icon_glyph.set_icon("arrow-up-right")
        else:
            text = ""
            self.icon_glyph.set_icon("check")
        self.label.setText(text)
        self.setVisible(bool(text))
        self.setFixedHeight(56 if text else 0)
        self.sync.setVisible(online and self._pending > 0)
        self.update_button.setVisible(online and has_update)

    def paintEvent(self, _event) -> None:
        if not self.height():
            return
        pal = theme.pal()
        p = QPainter(self)
        p.fillRect(self.rect(), pal.q("surface_container"))
        p.fillRect(0, self.height() - 1, self.width(), 1, pal.q("outline_variant"))


class ShellPage(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__()
        self.shell = window

    def paintEvent(self, _event) -> None:
        QPainter(self).fillRect(self.rect(), theme.pal().q("background"))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.shell.position_overlays()


class McWindow(QMainWindow):
    def __init__(self, store: SessionStore, api: Api, repo: Repo, runner: Async,
                 player: PlayerEngine):
        super().__init__()
        motion.bind(store)
        self.store = store
        self.api = api
        self.repo = repo
        self.runner = runner
        self.player = player
        self.me: Optional[Me] = store.cached_me
        self.settings = Settings(theme=store.theme, accent=store.accent,
                                 volume=store.volume)
        self.route: tuple = ("home",)
        self.back_stack: list[tuple] = []
        self.current_screen: Optional[Screen] = None
        self.playlists: list[PlaylistRef] = []
        self._offline = False
        self._activity_sig = ""
        self._activity_at = 0.0
        self._last_remote_command = 0
        self._update: Optional[BuildInfo] = None
        self._update_url = ""
        self._notice = ""
        self._radio_busy = False

        self.setWindowTitle("mcmusic")
        self.resize(1280, 830)
        self.setMinimumSize(940, 620)

        self._search = ""
        self._device_timer = QTimer(self)
        self._device_timer.setInterval(30_000)
        self._device_timer.timeout.connect(self._heartbeat)
        self._publish_timer = QTimer(self)
        self._publish_timer.setInterval(10_000)
        self._publish_timer.timeout.connect(self._publish_playback)
        self._retry_timer = QTimer(self)
        self._retry_timer.setInterval(15_000)
        self._retry_timer.timeout.connect(self._retry_connection)
        self._remote_timer = QTimer(self)
        self._remote_timer.setInterval(3_000)
        self._remote_timer.timeout.connect(self._poll_remote)
        self._sleep_timer = QTimer(self)
        self._sleep_timer.setInterval(1_000)
        self._sleep_timer.timeout.connect(self._check_sleep_timer)

        self._build_pages()
        self._build_shortcuts()

        widgets.set_covers(self.settings.covers)
        widgets.set_density(self.settings.density)

        self.player.changed.connect(self._refresh_playback)
        self.player.tick.connect(self._refresh_progress)
        self.player.error.connect(self.toast)
        self.player.natural_end.connect(self._autoplay_radio)
        self.player.loading_changed.connect(lambda _busy: self._refresh_playback())
        self.player.changed.connect(self._update_window_title)
        self.player.changed.connect(self._publish_activity)

        self.apply_settings(self.settings, persist=False)
        try:
            QGuiApplication.styleHints().colorSchemeChanged.connect(
                self._system_appearance_changed
            )
        except (AttributeError, RuntimeError, TypeError):
            pass

        if self.me is not None and (self.api.cookies or self.api.token):
            self.stack.setCurrentWidget(self.splash)
            self.run(lambda: self.repo.me(force=True), self.after_login,
                     self._restore_failed)
        elif self.store.pending_token:
            # A mcmusic://oauth?token=… deep link arrived before any session.
            self.stack.setCurrentWidget(self.splash)
            self.run(self._restore_token_session, self.after_login,
                     self._token_restore_failed)
        else:
            self.show_login()

    def _restore_token_session(self) -> Me:
        token = self.store.pending_token
        me = self.repo.adopt_token(token)
        self.store.pending_token = ""
        self.store.reset_token = ""
        return me

    def _token_restore_failed(self, exc: Exception) -> None:
        offline = isinstance(exc, ApiError) and exc.offline
        if not offline:
            self.store.pending_token = ""
        self.show_login()
        if isValid(self) and hasattr(self, "login_page"):
            self.login_page._show_error(
                "Saved sign-in will be retried when the server is reachable"
                if offline else (str(exc) or "That sign-in link could not be used")
            )

    # ── construction ────────────────────────────────────────────────────
    def paintEvent(self, _event) -> None:
        """A flat background sits behind every screen."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), theme.pal().q("background"))

    def _build_pages(self) -> None:
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.splash = SplashPage()
        self.stack.addWidget(self.splash)

        self.shell = ShellPage(self)
        root = QHBoxLayout(self.shell)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.rail = Rail(self)
        root.addWidget(self.rail)

        main = QWidget()
        main.setStyleSheet("background: transparent;")
        main_line = QVBoxLayout(main)
        main_line.setContentsMargins(0, 0, 0, 0)
        main_line.setSpacing(0)
        self.topbar = TopBar(self)
        main_line.addWidget(self.topbar)
        self.status_strip = StatusStrip(self)
        main_line.addWidget(self.status_strip)
        self.content_host = QWidget()
        self.content_host.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_host)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        main_line.addWidget(self.content_host, 1)
        self.deck = Deck(self)
        main_line.addWidget(self.deck)
        root.addWidget(main, 1)
        self.stack.addWidget(self.shell)

        self.scrim = Scrim(self)

        self.drawer = QueueDrawer(self)
        self.overlay = NowPlayingOverlay(self)

        self.toast_widget = widgets.Toast(self)

    def _text_focused(self) -> bool:
        focused = QApplication.focusWidget()
        return isinstance(focused, (QLineEdit, QTextEdit, QPlainTextEdit))

    def _build_shortcuts(self) -> None:
        # Keep the old direct keys alongside the Ctrl bindings. Every shortcut
        # that could collide with typing is guarded so fields stay editable.
        shortcuts = [
            ("Ctrl+F", lambda: self.topbar.search.focus(), False),
            ("Ctrl+Space", self.player.toggle, True),
            ("Ctrl+Left", self.player.prev, True),
            ("Ctrl+Right", self.player.next, True),
            ("Ctrl+M", self.player.toggle_mute, True),
            ("Ctrl+Up", lambda: self.set_volume(self.player.volume + 0.05), True),
            ("Ctrl+Down", lambda: self.set_volume(self.player.volume - 0.05), True),
            ("Alt+Left", self.back, False),
            ("Escape", self.close_overlays, False),
            ("Space", self.player.toggle, True),
            ("Shift+Left", self.player.prev, True),
            ("Shift+Right", self.player.next, True),
            ("Up", lambda: self.set_volume(self.player.volume + 0.05), True),
            ("Down", lambda: self.set_volume(self.player.volume - 0.05), True),
            ("/", lambda: self.topbar.search.focus(), True),
            ("m", self.player.toggle_mute, True),
            ("l", self.like_current, True),
            ("q", self.toggle_queue, True),
            (QKeySequence(Qt.Key.Key_MediaPlay), self.player.toggle, True),
            (QKeySequence(Qt.Key.Key_MediaPause), self.player.pause, True),
            (QKeySequence(Qt.Key.Key_MediaNext), self.player.next, True),
            (QKeySequence(Qt.Key.Key_MediaPrevious), self.player.prev, True),
        ]
        self._shortcuts = []
        for keys, callback, guard in shortcuts:
            shortcut = QShortcut(QKeySequence(keys), self)
            shortcut.activated.connect(
                (lambda cb=callback, guarded=guard: self._run_shortcut(cb, guarded))
            )
            self._shortcuts.append(shortcut)

    def _run_shortcut(self, callback: Callable[[], None], guarded: bool) -> None:
        if guarded and self._text_focused():
            return
        callback()

    # ── session ─────────────────────────────────────────────────────────
    def show_login(self) -> None:
        self._device_timer.stop()
        self._publish_timer.stop()
        self._retry_timer.stop()
        self._remote_timer.stop()
        self._sleep_timer.stop()
        self._set_online(False, pending=self.api.pending_writes())
        if hasattr(self, "login_page") and self.login_page is not None:
            self.stack.removeWidget(self.login_page)
            self.login_page.deleteLater()
        self.login_page = LoginPage(self)
        self.login_page.succeeded.connect(self.after_login)
        self.stack.addWidget(self.login_page)
        self.stack.setCurrentWidget(self.login_page)
        self.login_page.username.line_edit.setFocus()

    def after_login(self, me: Me) -> None:
        self.me = me
        self.store.cached_me = me
        self._offline = False
        self.rail.set_user(me)
        self.topbar.user.set_user(me.username)
        self.stack.setCurrentWidget(self.shell)
        self.back_stack = []
        self._set_online(True, pending=self.api.pending_writes())
        self._load_settings()
        self.refresh_playlists()
        self.navigate(("home",), push=False)
        self._restore_queue()
        self._device_timer.start()
        self._publish_timer.start()
        self._retry_timer.stop()
        self._remote_timer.start()
        self._sleep_timer.start()
        self.sync_outbox(quiet=True)
        self._verify_pending_token()
        self._check_updates()
        self.position_overlays()
        self.player.changed.emit()

    def _restore_failed(self, exc: Exception) -> None:
        if not isValid(self):
            return
        if isinstance(exc, ApiError) and exc.status == 401:
            self.toast("Session expired — please sign in again")
            self.sign_out()
            return
        if self.me is None:
            self.show_login()
            return
        # Transport error or 5xx: keep the cached identity and session alive.
        self._resume_offline(str(exc))

    def _resume_offline(self, reason: str = "") -> None:
        if self.me is None or not isValid(self):
            return
        self._offline = True
        self.rail.set_user(self.me)
        self.topbar.user.set_user(self.me.username)
        self.stack.setCurrentWidget(self.shell)
        self.back_stack = []
        self._set_online(False, pending=self.api.pending_writes())
        self.apply_settings(
            Settings.from_json({**self.settings.to_json(),
                                "theme": self.store.theme,
                                "accent": self.store.accent,
                                "iconStroke": self.store.icon_stroke,
                                "iconFilled": self.store.icon_filled,
                                "volume": self.store.volume}),
            persist=False,
        )
        if not isinstance(self.current_screen, Screen):
            self.navigate(("home",), push=False)
        self._restore_queue()
        self._device_timer.stop()
        self._publish_timer.stop()
        self._remote_timer.stop()
        self._retry_timer.start()
        self._sleep_timer.start()
        if reason:
            self.toast("Offline — using saved session")

    def _retry_connection(self) -> None:
        if self.me is None or not self._offline:
            self._retry_timer.stop()
            return
        self.run(lambda: self.repo.me(force=True), self._retry_ok,
                 self._restore_failed)

    def _retry_ok(self, me: Me) -> None:
        self.toast("Back online")
        self.after_login(me)

    def _set_online(self, online: bool, *, pending: int = 0,
                    notice: Optional[str] = None) -> None:
        if notice is not None:
            self._notice = notice
        self.rail.set_online(online)
        self.status_strip.set_state(
            online=online,
            pending=pending if online else self.api.pending_writes(),
            notice=self._notice if online else "",
            has_update=bool(self._update_url),
        )

    def open_update(self) -> None:
        """Open the public download page; never fetch or launch a build here."""
        if not self._update_url:
            self.toast("No update is available for this platform")
            return
        QDesktopServices.openUrl(QUrl(self._update_url))

    def sign_out(self) -> None:
        def job() -> None:
            self.repo.logout()
            self.repo.app_logout()

        self.run(job, lambda _: None, lambda _exc: None)
        self.me = None
        self._offline = False
        self.store.clear_session()
        self.store.reset_token = ""
        self.api.cookies.clear()
        self.store.save_cookies({})
        self.ART_clear()
        self.player.clear()
        self.playlists = []
        self.rail.set_playlists([], None)
        self.rail.set_user(None)
        self.topbar.user.set_user("")
        self.topbar.search.set_text("")
        self._search = ""
        self.current_screen = None
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.stack.setCurrentWidget(self.login_page or self.splash)
        self.show_login()
        self.toast("Signed out")

    def ART_clear(self) -> None:
        ART.clear()
        self.update()

    def change_server(self, url: str) -> None:
        try:
            self.api.set_base(url)
        except Exception:
            self.toast("That server address is not valid")
            return
        self.api.cookies.clear()
        self.store.save_cookies({})
        ART.clear()

        def ok(me: Me) -> None:
            self.toast(f"Connected to {self.api.base_url}")
            self.after_login(me)

        def fail(exc: Exception) -> None:
            self.toast(str(exc) or "Can't reach that server")
            self.sign_out()

        self.run(lambda: self.repo.me(force=True), ok, fail)

    def _load_settings(self) -> None:
        local = Settings(theme=self.store.theme, accent=self.store.accent,
                         iconStroke=self.store.icon_stroke,
                         iconFilled=self.store.icon_filled,
                         volume=self.store.volume, room_url=self.store.room_url)
        self.apply_settings(local, persist=False)
        self.run(self.repo.settings, self._settings_loaded, lambda _exc: None)

    def _settings_loaded(self, remote: Settings) -> None:
        if remote.room_url:
            self.store.room_url = remote.room_url
        else:
            remote = replace(remote, room_url=self.store.room_url)
        self.apply_settings(remote, persist=False)

    # ── appearance ──────────────────────────────────────────────────────
    def _system_appearance_changed(self, *_args) -> None:
        """Bare family ids repaint when the OS switches light/dark."""
        if getattr(self, "settings", None) is not None:
            self.apply_settings(self.settings, persist=False)

    def apply_settings(self, settings: Settings, persist: bool = True) -> None:
        self.settings = settings
        theme.set_appearance(settings.theme, settings.accent)
        icons.set_icon_style(settings.iconStroke, settings.iconFilled)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.stylesheet())
            app.setPalette(theme.qpalette())
        widgets.set_covers(settings.covers)
        widgets.set_density(settings.density)
        self.store.theme = settings.theme
        self.store.accent = settings.accent
        self.store.icon_stroke = settings.iconStroke
        self.store.icon_filled = settings.iconFilled
        if settings.remember_volume:
            self.store.volume = settings.volume
            self.player.set_volume(settings.volume)
        widgets.refresh_theme(self)
        if self.current_screen is not None:
            self.current_screen.apply_settings(settings)
        self._refresh_deck()
        self._refresh_progress()
        if persist:
            def save() -> int:
                self.repo.save_settings(settings)
                return self.api.pending_writes()

            self.run(save, lambda pending: self._set_online(
                not self._offline, pending=pending), lambda _exc: None)

    def set_volume(self, value: float) -> None:
        value = min(1.0, max(0.0, value))
        self.player.set_volume(value)
        self.store.volume = value
        if self.settings.remember_volume:
            self.settings = replace(self.settings, volume=value)
        self.deck.volume.set_level(value, self.player.muted)
        self._refresh_deck()

    def toast(self, text: str) -> None:
        if not isValid(self):
            return
        self.toast_widget.show_message(str(text))
        self.toast_widget.raise_()

    # ── routing ─────────────────────────────────────────────────────────
    def navigate(self, route: tuple, push: bool = True) -> None:
        route = tuple(route)
        if push and route != self.route:
            self.back_stack.append(self.route)
        self.route = route
        self._show_route()

    def back(self) -> None:
        if self.back_stack:
            self.route = self.back_stack.pop()
            self._show_route()
            return
        if self.route != ("home",):
            self.route = ("home",)
            self._show_route()

    def _show_route(self) -> None:
        screen = self._make_screen(self.route)
        if self.current_screen is not None:
            self.content_layout.removeWidget(self.current_screen)
            self.current_screen.setParent(None)
            self.current_screen.deleteLater()
        self.current_screen = screen
        self.content_layout.addWidget(screen)
        self.rail.set_active(self.route)
        self.topbar.back.setVisible(bool(self.back_stack))
        screen.apply_settings(self.settings)

    def _make_screen(self, route: tuple) -> Screen:
        kind = route[0] if route else "home"
        if kind == "search":
            return SearchScreen(self, self.topbar.search.text())
        if kind == "library":
            tab = route[1] if len(route) > 1 else "songs"
            return LibraryScreen(self, tab)
        if kind == "album" and len(route) > 1:
            return CollectionScreen(self, route[1], "album")
        if kind == "artist" and len(route) > 1:
            return CollectionScreen(self, route[1], "artist")
        if kind == "likes":
            return LikesScreen(self)
        if kind == "playlists":
            return PlaylistsScreen(self)
        if kind == "playlist" and len(route) > 1:
            return PlaylistScreen(self, route[1])
        if kind == "requests":
            return RequestsScreen(self)
        if kind == "downloads":
            return DownloadsScreen(self)
        if kind == "devices":
            return DevicesScreen(self)
        if kind == "listening":
            return ListeningScreen(self)
        if kind == "settings":
            return SettingsScreen(self)
        if kind == "admin":
            return AdminScreen(self) if (self.me and self.me.is_admin) else HomeScreen(self)
        return HomeScreen(self)

    def on_search_text(self, text: str) -> None:
        self._search = text
        if not text.strip():
            if self.route[0] == "search" and self.current_screen is not None:
                self.current_screen.set_query("")
            return
        if self.route[0] != "search":
            self.navigate(("search",), push=True)
        elif self.current_screen is not None:
            self.current_screen.set_query(text)

    def on_search_submit(self, text: str) -> None:
        self.on_search_text(text)

    def refresh_playlists(self) -> None:
        self.run(self.repo.playlists, self._playlists_loaded, lambda _exc: None)

    def _playlists_loaded(self, playlists: list[PlaylistRef]) -> None:
        self.playlists = playlists
        active = self.route[1] if self.route[0] == "playlist" and len(self.route) > 1 else None
        self.rail.set_playlists(playlists, active)

    # ── playback ────────────────────────────────────────────────────────
    def _playable(self, tracks: Sequence[Track]) -> list[Track]:
        if self.settings.hide_explicit:
            return [t for t in tracks if not t.explicit]
        return list(tracks)

    def play_tracks(self, tracks: Sequence[Track], index: int = 0) -> None:
        playable = self._playable(tracks)
        if not playable:
            self.toast("Nothing to play")
            return
        target = tracks[index] if 0 <= index < len(tracks) else None
        at = 0
        if target is not None:
            at = next((i for i, t in enumerate(playable) if t.id == target.id), 0)
        self.player.play(playable, at)

    def shuffle_tracks(self, tracks: Sequence[Track]) -> None:
        playable = self._playable(tracks)
        if not playable:
            self.toast("Nothing to play")
            return
        self.player.play(playable, 0, shuffle_start=True)

    def play_album(self, name: str) -> None:
        self.run(lambda: self.repo.album(name),
                 lambda tracks: self.play_tracks(tracks, 0))

    def play_artist(self, name: str) -> None:
        self.run(lambda: self.repo.artist(name),
                 lambda tracks: self.play_tracks(tracks, 0))

    def play_playlist(self, playlist_id: int) -> None:
        self.run(lambda: self.repo.playlist(playlist_id),
                 lambda result: self.play_tracks(result[1], 0))

    def queue_next(self, track: Track) -> None:
        if not self.player.queue:
            self.play_tracks([track], 0)
            return
        self.player.add(track, next=True)
        self.toast("Playing next")

    def queue_add(self, track: Track) -> None:
        if not self.player.queue:
            self.play_tracks([track], 0)
            return
        self.player.add(track)
        self.toast("Added to queue")

    def start_radio(self, track: Track) -> None:
        def ok(rest: list[Track]) -> None:
            self.player.play([track] + rest, 0)
            self.toast("Radio started")

        self.run(lambda: self.repo.radio(track.id), ok)

    def _autoplay_radio(self, seed_id: int) -> None:
        """Refill from radio after the last track ends naturally (repeat off)."""
        seed = self.player.current
        if (seed is None or seed.id != seed_id or self._radio_busy
                or not self.settings.autoplay or self.player.repeat != "off"):
            return
        if self.player.index != len(self.player.queue) - 1:
            return
        self._radio_busy = True

        def ok(rest: list[Track]) -> None:
            self._radio_busy = False
            current = self.player.current
            if (current is None or current.id != seed_id or self.player.playing
                    or not self.settings.autoplay or self.player.repeat != "off"
                    or self.player.index != len(self.player.queue) - 1):
                return
            have = {t.id for t in self.player.queue}
            additions: list[Track] = []
            for track in rest:
                if track.id <= 0 or track.id in have:
                    continue
                have.add(track.id)
                additions.append(track)
                if len(additions) == 5:
                    break
            if not additions:
                return
            first_new = len(self.player.queue)
            self.player.queue.extend(additions)
            self.player.jump(first_new)

        def fail(_exc: Exception) -> None:
            self._radio_busy = False

        self.run(lambda: self.repo.radio(seed_id), ok, fail)

    def like_current(self) -> None:
        track = self.player.current
        if track is not None:
            self.toggle_like(track)

    def toggle_like(self, track: Track) -> None:
        def ok(result) -> None:
            if isinstance(result, dict) and result.get("queued"):
                self._like_done(track.id, not track.liked, "Saved offline — will sync")
                self._set_online(False)
            else:
                self._like_done(track.id, bool(result))

        self.run(lambda: self.repo.like(track.id), ok)

    def _like_done(self, track_id: int, liked: bool,
                   message: Optional[str] = None) -> None:
        self.player.mark_liked(track_id, liked)
        if self.current_screen is not None:
            self.current_screen.apply_like(track_id, liked)
        self.toast(message or ("Liked" if liked else "Removed from liked"))
        self._refresh_deck()

    def toggle_shuffle(self) -> None:
        self.player.toggle_shuffle()
        self._refresh_deck()
        if not self.player.shuffle:
            return
        current = self.player.current
        if current is None or len(self.player.queue) < 2:
            return

        def ok(ranked: list[int]) -> None:
            # Ignore a late answer if the user toggled shuffle off meanwhile.
            now = self.player.current
            if (not self.player.shuffle or now is None or now.id != current.id
                    or not self.player.apply_model_order(ranked)):
                return
            self._refresh_deck()

        self.run(lambda: self.repo.model_rank(current.id, self.player.queue_ids()),
                 ok, lambda _e: None)

    def toggle_explicit(self, track: Track) -> None:
        self.run(lambda: self.repo.set_explicit(track.id, not track.explicit),
                 lambda value: (self.player.mark_explicit(track.id, value),
                                self.toast("Updated"), self._refresh_deck()))

    def make_track_list(self, tracks: Sequence[Track], screen: Screen,
                        playlist_id: Optional[int] = None):
        track_list = widgets.TrackList(show_stats=self.settings.yt_stats)
        current = self.player.current
        track_list.set_tracks(tracks, current.id if current else None)
        track_list.play_requested.connect(lambda index: self.play_tracks(tracks, index))
        track_list.like_requested.connect(self.toggle_like)
        track_list.more_requested.connect(
            lambda track, index, pos: self.open_track_menu(track, index, pos, playlist_id)
        )
        return track_list

    # ── deck / overlays ─────────────────────────────────────────────────
    def _refresh_deck(self) -> None:
        if not hasattr(self, "deck"):
            return
        player = self.player
        track = player.current
        if track is None:
            self.deck.title.setText("Nothing playing right now")
            self.deck.artist.setText("Pick a song from your library")
            self.deck.like.setVisible(False)
            self.deck.art.set_cover(None)
        else:
            self.deck.title.setText(track.title)
            self.deck.artist.setText(
                "  ·  ".join(x for x in (track.artist, track.album) if x)
            )
            self.deck.like.setVisible(True)
            self.deck.like.set_active(track.liked)
            self.deck.like.set_fill(track.liked)
            self.deck.art.set_cover(track.id, name=track.title)
        self.deck.play.set_playing(player.playing)
        self.deck.seek.set_playing(player.playing)
        self.deck.shuffle.set_active(player.shuffle)
        self.deck.repeat.set_icon("repeat-1" if player.repeat == "one" else "repeat")
        self.deck.repeat.set_active(player.repeat != "off")
        self.deck.volume.set_level(player.volume, player.muted)
        self.deck.seek.set_values(player.position, player.duration)
        self.deck.pos_label.setText(fmt_time(player.position))
        self.deck.dur.setText(fmt_time(player.duration))

    def _refresh_progress(self) -> None:
        if not hasattr(self, "deck"):
            return
        player = self.player
        self.deck.seek.set_values(player.position, player.duration)
        self.deck.seek.set_playing(player.playing)
        self.deck.pos_label.setText(fmt_time(player.position))
        self.deck.dur.setText(fmt_time(player.duration))
        self.deck.play.set_playing(player.playing)
        if self.overlay.isVisible():
            self.overlay.pos_label.setText(fmt_time(player.position))
            self.overlay.dur.setText(fmt_time(player.duration))
            self.overlay.seek.set_values(player.position, player.duration)
            self.overlay.seek.set_playing(player.playing)
            self.overlay.play.set_playing(player.playing)
        self._publish_activity()

    def _refresh_playback(self) -> None:
        self._refresh_deck()
        self._refresh_progress()
        if self.overlay.isVisible():
            self.overlay.refresh()
        if self.drawer.isVisible():
            self.drawer.refresh()
        self.rail.set_active(self.route)

    def _update_window_title(self) -> None:
        track = self.player.current
        if track is None:
            self.setWindowTitle("mcmusic")
        else:
            self.setWindowTitle(f"mcmusic — {track.title} · {track.artist}")

    def show_now_playing(self) -> None:
        self.drawer.hide()
        self.scrim.setVisible(False)
        self.overlay.setGeometry(self.shell.rect())
        self.overlay.refresh()
        self.overlay.show()
        self.overlay.raise_()
        self.toast_widget.raise_()

    def toggle_queue(self) -> None:
        if self.drawer.isVisible():
            self.close_overlays()
            return
        if self.me is None:
            return
        self.overlay.hide()
        self.position_overlays()
        self.drawer.refresh()
        self.scrim.setVisible(True)
        self.scrim.raise_()
        self.drawer.show()
        self.drawer.raise_()
        self.toast_widget.raise_()

    def close_overlays(self) -> None:
        self.drawer.hide()
        self.scrim.setVisible(False)
        self.overlay.hide()

    def position_overlays(self) -> None:
        if not hasattr(self, "scrim"):
            return
        self.scrim.setGeometry(self.shell.rect())
        self.drawer.setGeometry(self.shell.width() - 390, 0, 390, self.shell.height())
        self.overlay.setGeometry(self.shell.rect())
        if getattr(self, "toast_widget", None) is not None and self.toast_widget.isVisible():
            self.toast_widget._reposition()

    # ── menus and dialogs ───────────────────────────────────────────────
    def _menu_icon(self, name: str, token: str = "on_surface_variant"):
        return icons.icon(name, getattr(theme.pal(), token), 16)

    def open_track_menu(self, track: Track, index: int = 0, pos=None,
                        playlist_id: Optional[int] = None) -> None:
        menu = QMenu(self)

        def add(icon_name: str, label: str, callback: Callable[[], None],
                *, token: str = "on_surface_variant", shortcut: str = "") -> None:
            action = menu.addAction(self._menu_icon(icon_name, token), label)
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)

        add("play", "Play now", lambda: self.play_tracks([track], 0))
        add("list-music", "Play next", lambda: self.queue_next(track))
        add("plus", "Add to queue", lambda: self.queue_add(track))
        add("folder-plus", "Add to playlist…",
            lambda: self._add_to_playlist_dialog(track))
        add("radio", "Start radio", lambda: self.start_radio(track))
        menu.addSeparator()
        if track.album:
            add("disc-3", "Go to album",
                lambda: self.navigate(("album", track.album)))
        if track.artist:
            add("users", "Go to artist",
                lambda: self.navigate(("artist", track.artist)))
        menu.addSeparator()
        add("heart", "Remove from liked" if track.liked else "Like",
            lambda: self.toggle_like(track),
            token="primary" if track.liked else "on_surface_variant")
        add("info", "Track info", lambda: self._track_info(track))
        if playlist_id is not None:
            menu.addSeparator()
            add("trash-2", "Remove from playlist",
                lambda: self._remove_from_playlist(playlist_id, track), token="error")
        if self.me and self.me.is_admin:
            menu.addSeparator()
            add("triangle-alert",
                "Mark as clean" if track.explicit else "Mark as explicit",
                lambda: self.toggle_explicit(track))
        if pos is not None:
            menu.exec(pos)
        else:
            menu.exec(self.cursor().pos())

    def _remove_from_playlist(self, playlist_id: int, track: Track) -> None:
        def ok(_) -> None:
            self.toast("Removed from playlist")
            if (self.route[0] == "playlist" and len(self.route) > 1
                    and self.route[1] == playlist_id and self.current_screen is not None):
                self.current_screen.load()
            self.refresh_playlists()

        self.run(lambda: self.repo.remove_from_playlist(playlist_id, track.id), ok)

    def _track_info(self, track: Track) -> None:
        sheet = Sheet(self, "Track info")
        head = QHBoxLayout()
        head.setSpacing(12)
        art = Artwork(64, kind="track")
        art.set_cover(track.id, name=track.title)
        head.addWidget(art)
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(3)
        text.addWidget(Txt(track.title, size=16, token="on_surface",
                           weight=QFont.Weight.Bold))
        text.addWidget(Txt(" · ".join(x for x in (track.artist, track.album) if x),
                           size=14, token="on_surface_variant"))
        head.addLayout(text, 1)
        sheet.body.addLayout(head)
        sheet.body.addSpacing(10)

        rows = [
            ("Length", fmt_time(track.duration)),
            ("Track", str(track.track_no) if track.track_no else "—"),
            ("Year", track.year or "—"),
            ("Genre", track.genre or "—"),
            ("Explicit", "Yes" if track.explicit else "No"),
        ]
        if track.yt_channel:
            rows.append(("Channel", track.yt_channel))
        if track.yt_likes is not None:
            rows.append(("YT likes", fmt_count(track.yt_likes)))
        if track.yt_views is not None:
            rows.append(("YT views", fmt_count(track.yt_views)))
        if track.yt_date:
            rows.append(("Uploaded", track.yt_date))
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(7)
        for i, (key, value) in enumerate(rows):
            grid.addWidget(Txt(key.upper(), size=14, token="primary",
                               weight=QFont.Weight.Bold), i, 0)
            grid.addWidget(Txt(value, size=16, token="on_surface"), i, 1)
        grid.setColumnStretch(1, 1)
        sheet.body.addLayout(grid)

        sheet.body.addSpacing(10)
        sheet.body.addWidget(Txt("SOURCES", size=14, token="primary",
                                 weight=QFont.Weight.Bold))
        sources = Txt("Reading source metadata…", size=16,
                      token="on_surface_variant", wrap=True)
        sheet.body.addWidget(sources)

        def sources_ok(rows: list[dict]) -> None:
            if not isValid(sources):
                return
            if not rows:
                sources.setText("No source metadata recorded")
                return
            lines = []
            for row in rows[:10]:
                name = str(row.get("source") or row.get("kind") or "source")
                detail = row.get("url") or row.get("title") or row.get("id") or ""
                lines.append(f"{name}: {detail}")
            sources.setText("\n".join(lines))

        self.run(lambda: self.repo.track_sources(track.id), sources_ok,
                 error=lambda _e: sources.setText("Sources unavailable offline"))
        if track.yt_id:
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices
            sheet.body.addSpacing(8)
            open_yt = McButton("Open on YouTube", small=True, icon="arrow-up-right")
            open_yt.clicked.connect(lambda: QDesktopServices.openUrl(
                QUrl(f"https://www.youtube.com/watch?v={track.yt_id}")))
            sheet.body.addWidget(open_yt, 0, Qt.AlignmentFlag.AlignLeft)
        sheet.exec()

    def _add_to_playlist_dialog(self, track: Track) -> None:
        sheet = Sheet(self, "Add to playlist")
        list_host = QWidget()
        listing = QVBoxLayout(list_host)
        listing.setContentsMargins(0, 0, 0, 0)
        listing.setSpacing(1)
        sheet.body.addWidget(list_host)
        hint = Txt("No playlists yet — name one below.", size=16,
                   token="on_surface_variant")
        hint.setVisible(False)
        sheet.body.addWidget(hint)

        def add_to(playlist: PlaylistRef) -> None:
            def ok(_) -> None:
                sheet.accept()
                self.toast("Added to playlist")
                self.refresh_playlists()

            self.run(lambda: self.repo.add_to_playlist(playlist.id, track.id), ok)

        for playlist in self.playlists:
            pick = PickRow(playlist)
            pick.clicked.connect(lambda _=False, p=playlist: add_to(p))
            listing.addWidget(pick)
        if not self.playlists:
            hint.setVisible(True)

        sheet.body.addSpacing(12)
        row = QHBoxLayout()
        row.setSpacing(8)
        name = QLineEdit()
        name.setPlaceholderText("New playlist name")
        name.setFixedHeight(34)
        row.addWidget(name, 1)
        create = McButton("Create", small=True)

        def create_and_add() -> None:
            value = name.text().strip()
            if not value:
                return
            create.setEnabled(False)

            def job() -> int:
                pid = self.repo.create_playlist(value)
                self.repo.add_to_playlist(pid, track.id)
                return pid

            def ok(_pid: int) -> None:
                sheet.accept()
                self.toast("Added to playlist")
                self.refresh_playlists()

            def fail(exc: Exception) -> None:
                create.setEnabled(True)
                self.toast(str(exc) or "Could not create playlist")

            self.run(job, ok, fail)

        create.clicked.connect(create_and_add)
        name.returnPressed.connect(create_and_add)
        row.addWidget(create)
        sheet.body.addLayout(row)
        name.setFocus()
        sheet.exec()

    def create_playlist(self) -> None:
        name = prompt(self, "New playlist", "Name", placeholder="Late night drives",
                      confirm="Create")
        if not name:
            return

        def ok(_pid: int) -> None:
            self.toast("Playlist created")
            self.refresh_playlists()
            if self.route[0] == "playlists" and self.current_screen is not None:
                self.current_screen.load()

        self.run(lambda: self.repo.create_playlist(name), ok)

    def add_current_to_playlist(self) -> None:
        track = self.player.current
        if track is not None:
            self._add_to_playlist_dialog(track)

    def show_lyrics(self) -> None:
        track = self.player.current
        if track is None:
            self.toast("Play a track to see its lyrics")
            return
        sheet = Sheet(self, "Lyrics")
        sheet.body.addWidget(Txt(f"{track.title} — {track.artist}", size=16,
                                 token="on_surface_variant", wrap=True))
        visualizer = LyricVisualizer(self.player, sheet)
        sheet.body.addWidget(visualizer)
        view = QTextEdit()
        view.setReadOnly(True)
        view.setPlaceholderText("No lyrics have been found for this track yet.")
        sheet.body.addWidget(view, 1)
        sheet.resize(560, 520)

        def ok(data: dict) -> None:
            if not isValid(view):
                return
            text = str(data.get("lyrics") or data.get("text") or "")
            source = str(data.get("source") or "")
            view.setPlainText(text or "No lyrics have been found for this track yet.")
            if source and hasattr(sheet, "setWindowTitle"):
                sheet.setWindowTitle("Lyrics · " + source)

        self.run(lambda: self.repo.lyrics(track.id), ok,
                 error=lambda _e: view.setPlaceholderText("Lyrics are unavailable offline"))
        sheet.finished.connect(lambda _result=0: visualizer.stop())
        sheet.exec()

    def show_sleep_menu(self, button: QWidget) -> None:
        menu = QMenu(self)
        for label, minutes in (
            ("Off", 0), ("5 minutes", 5), ("15 minutes", 15),
            ("30 minutes", 30), ("45 minutes", 45), ("60 minutes", 60),
        ):
            action = menu.addAction(label)
            action.triggered.connect(
                lambda _=False, m=minutes: self.set_sleep_timer(m)
            )
        menu.exec(button.mapToGlobal(QPoint(0, button.height())))

    def set_sleep_timer(self, minutes: int) -> None:
        if minutes <= 0:
            self.store.sleep_timer = {}
            self.toast("Sleep timer off")
        else:
            self.store.sleep_timer = {
                "ends_at": time.time() + minutes * 60, "minutes": minutes,
            }
            self.toast(f"Sleep timer set for {minutes} minutes")
        if hasattr(self, "overlay"):
            self.overlay.refresh()

    def _check_sleep_timer(self) -> None:
        timer = self.store.sleep_timer
        if not timer:
            return
        try:
            ends = float(timer.get("ends_at", 0))
        except (TypeError, ValueError):
            self.store.sleep_timer = {}
            return
        if time.time() < ends:
            return
        self.store.sleep_timer = {}
        if self.player.playing:
            self.player.pause()
            self.toast("Sleep timer finished")
        if hasattr(self, "overlay"):
            self.overlay.refresh()

    def sync_outbox(self, quiet: bool = False) -> None:
        def job() -> tuple[int, int]:
            return self.api.flush_outbox()

        def ok(result: tuple[int, int]) -> None:
            sent, pending = result
            self._set_online(not self._offline, pending=pending)
            if sent and not quiet:
                self.toast(f"Synced {sent} offline change" + ("" if sent == 1 else "s"))

        def fail(exc: Exception) -> None:
            if isinstance(exc, ApiError) and exc.status == 401:
                self.sign_out()
            else:
                self._set_online(False)

        self.run(job, ok, fail)

    def _restore_queue(self) -> None:
        def ok(tracks: list[Track]) -> None:
            ids = {t.id for t in tracks}
            if self.player.restore_snapshot(ids):
                self._refresh_playback()

        def fail(_exc: Exception) -> None:
            if self.player.restore_snapshot():
                self._refresh_playback()

        self.run(self.repo.tracks, ok, fail)

    def _verify_pending_token(self) -> None:
        token = self.store.pending_token
        if not token:
            return

        def job() -> Me:
            self.repo.verify_token(token)
            return self.repo.adopt_token(token)

        def ok(me: Me) -> None:
            self.store.pending_token = ""
            self.toast("Rotur sign-in restored")

        def fail(exc: Exception) -> None:
            if isinstance(exc, ApiError) and exc.status == 401:
                self.store.pending_token = ""
            elif not (isinstance(exc, ApiError) and exc.offline):
                self.toast("Saved Rotur sign-in could not be verified")

        self.run(job, ok, fail)

    def _check_updates(self, done: Optional[Callable[[Optional[BuildInfo]], None]] = None
                       ) -> None:
        def job() -> list:
            return self.repo.builds()

        def ok(builds: list) -> None:
            found = updates.find_update(builds, VERSION)
            self._update = found
            self._update_url = updates.download_page(self.api.base_url) if found else ""
            notice = f"Update available · {found.label} {found.version}" if found else ""
            self._set_online(not self._offline, pending=self.api.pending_writes(),
                             notice=notice)
            if done:
                done(found)

        def fail(exc: Exception) -> None:
            if done:
                done(None)
            self.toast(f"Update check failed: {exc}")

        self.run(job, ok, fail)

    def _publish_activity(self) -> None:
        settings = self.settings
        track = self.player.current
        playing = self.player.playing
        bucket = int(self.player.position // 5)
        if not (settings.rotur_activity or settings.discord_activity):
            if self._activity_sig == "off":
                return
            self._activity_sig = "off"
            sig = (None, False, 0)
        else:
            sig = (track.id if track else None, playing, bucket)
            if sig == self._activity_sig:
                return
            now = time.time()
            if now - self._activity_at < 5:
                return
            self._activity_at = now
            self._activity_sig = sig

        track_id = sig[0] if settings.rotur_activity or settings.discord_activity else None
        position = self.player.position if sig[1] else 0.0
        is_playing = bool(sig[1]) if settings.rotur_activity or settings.discord_activity else False

        def job() -> None:
            if settings.rotur_activity or not is_playing:
                try:
                    self.repo.rotur_activity(track_id, position, is_playing)
                except ApiError:
                    pass
            if settings.discord_activity or not is_playing:
                try:
                    self.repo.discord_activity(track_id, position, is_playing)
                except ApiError:
                    pass

        self.run(job, lambda _: None, lambda _exc: None)

    def _clear_activity(self, *, sync: bool = False) -> None:
        self._activity_sig = ""
        if sync:
            for send in (self.repo.rotur_activity, self.repo.discord_activity):
                try:
                    send(None, 0.0, False)
                except Exception:
                    pass
        else:
            self.run(lambda: self.repo.rotur_activity(None, 0.0, False),
                     lambda _: None, lambda _exc: None)
            self.run(lambda: self.repo.discord_activity(None, 0.0, False),
                     lambda _: None, lambda _exc: None)

    def _poll_remote(self) -> None:
        if self.me is None:
            return
        self.run(self.repo.playback, self._apply_remote, lambda _exc: None)

    def _apply_remote(self, data: dict) -> None:
        if not isinstance(data, dict):
            return
        for command in data.get("commands") or []:
            if not isinstance(command, dict):
                continue
            try:
                cid = int(command.get("id") or 0)
            except (TypeError, ValueError):
                cid = 0
            if cid and cid <= self._last_remote_command:
                continue
            if cid:
                self._last_remote_command = cid
            action = str(command.get("action") or "")
            arg = command.get("arg") if isinstance(command.get("arg"), dict) else {}
            if action == "play":
                if not self.player.playing:
                    self.player.toggle()
            elif action == "pause":
                if self.player.playing:
                    self.player.pause()
            elif action == "toggle":
                self.player.toggle()
            elif action in ("next", "skip"):
                self.player.next()
            elif action == "prev":
                self.player.prev()
            elif action == "seek":
                try:
                    self.player.seek(float(arg.get("position") or 0))
                except (TypeError, ValueError):
                    pass
            elif action == "remove":
                try:
                    self.player.remove_at(int(arg.get("index") or 0))
                except (TypeError, ValueError):
                    pass
            elif action in ("enqueue", "play_track"):
                raw = arg.get("track")
                if isinstance(raw, dict):
                    track = Track.from_json(raw)
                    if action == "enqueue":
                        self.player.add(track)
                    else:
                        self.player.play([track], 0)
                    continue
                try:
                    tid = int(arg.get("track_id") or 0)
                except (TypeError, ValueError):
                    tid = 0
                if not tid:
                    continue

                def ok(track: Optional[Track], replace_queue=action == "play_track") -> None:
                    if track is None:
                        return
                    if replace_queue:
                        self.player.play([track], 0)
                    else:
                        self.player.add(track)

                self.run(lambda t=tid: self.repo.find_track(t), ok)

    # ── background sync ─────────────────────────────────────────────────
    def _heartbeat(self) -> None:
        if self.me is None:
            return
        track = self.player.current
        self.run(
            lambda: self.repo.heartbeat(
                self.store.device_hash, device_name(),
                track.id if track else None, self.player.position,
                not self.player.playing,
            ),
            lambda _: self._set_online(True, pending=self.api.pending_writes()),
            lambda _exc: self._set_online(False),
        )

    def _publish_playback(self) -> None:
        if self.me is None or not self.player.queue:
            return
        track = self.player.current
        self.run(
            lambda: self.repo.publish_playback(
                track.id if track else None, self.player.position,
                self.player.duration, self.player.playing, self.player.queue_ids(),
                self.store.device_hash,
            ),
            lambda _: self._set_online(True, pending=self.api.pending_writes()),
            lambda _exc: self._set_online(False),
        )

    def run(self, fn: Callable[[], Any], ok: Optional[Callable[[Any], None]] = None,
            error: Optional[Callable[[Exception], None]] = None) -> None:
        def safe_ok(value: Any) -> None:
            if isValid(self) and ok is not None:
                ok(value)

        def safe_error(exc: Exception) -> None:
            if not isValid(self):
                return
            if error is not None:
                error(exc)
            else:
                self.toast(str(exc) or "Something went wrong")

        self.runner.submit(fn, safe_ok, safe_error)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.position_overlays()

    def closeEvent(self, event) -> None:
        self._clear_activity(sync=True)
        try:
            self.api.flush_outbox()
        except Exception:
            pass
        self.player.shutdown()
        self.runner.shutdown()
        super().closeEvent(event)
```

### `app/linux/mcmusic_linux/screens.py`

```python
"""All routed views: home, search, library, collections, likes, playlists,
requests, settings and the admin console.

Screens are plain QScrollAreas that reload from the API when shown. Data loads
on the worker pool; widgets are built on the GUI thread only.
"""
from __future__ import annotations

import time
from dataclasses import replace
from typing import Any, Callable, Optional, Sequence

from shiboken6 import isValid
from PySide6.QtCore import QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import (
    QColor, QDesktopServices, QGuiApplication, QPainter, QPen,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QColorDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import design, motion, theme
from .models import (
    BuildInfo,
    DeviceRow,
    ListeningUser,
    AdminStats,
    AdminUser,
    AlbumRef,
    ArtistRef,
    HomeData,
    PlaylistRef,
    RequestRow,
    SearchData,
    Settings,
    Track,
    fmt_bytes,
    fmt_time,
    fmt_total,
    fmt_uptime,
)
from .widgets import (
    EmptyState,
    Glyph,
    Hero,
    IconButton,
    LabeledField,
    McButton,
    PageHead,
    Panel,
    Segmented,
    Shelf,
    Spinner,
    StatCard,
    Sheet,
    StatusChip,
    Switch,
    TileGrid,
    Txt,
    confirm,
    prompt,
)
from .version import VERSION

STATUS_TOKEN = {
    "done": "primary",
    "failed": "error",
    "rejected": "error",
    "cancelled": "error",
    "running": "primary",
    "approved": "primary",
    "pending": "on_surface_variant",
}


class Screen(QScrollArea):
    """Scrollable page with a centred, max-width content column."""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.shell = window
        self.track_list = None
        self._loading_row: Optional[QWidget] = None
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.viewport().setAutoFillBackground(False)
        self.setStyleSheet("QScrollArea{background:transparent;border:none;}"
                           "QScrollArea>QWidget>QWidget{background:transparent;}")

        host = QWidget()
        host.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(host)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch(1)
        self.body = QWidget()
        self.body.setMaximumWidth(1180)
        self.body.setStyleSheet("background: transparent;")
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(26, 22, 26, 40)
        self.body_layout.setSpacing(0)
        self.body_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        row.addWidget(self.body, 100)
        row.addStretch(1)
        outer.addLayout(row)
        self.setWidget(host)

    # layout helpers -----------------------------------------------------
    def add(self, widget: QWidget, spacing: int = 0) -> QWidget:
        self.body_layout.addWidget(widget)
        if spacing:
            self.body_layout.addSpacing(spacing)
        return widget

    def space(self, height: int) -> None:
        self.body_layout.addSpacing(height)

    def clear(self) -> None:
        while self.body_layout.count():
            item = self.body_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self.track_list = None
        self._loading_row = None

    def reset_scroll(self) -> None:
        self.verticalScrollBar().setValue(0)

    # async --------------------------------------------------------------
    def run(self, fn: Callable[[], Any],
            ok: Callable[[Any], None],
            error: Optional[Callable[[Exception], None]] = None) -> None:
        def safe_ok(value) -> None:
            if not isValid(self):
                return
            try:
                ok(value)
            except RuntimeError:
                return

        def safe_error(exc: Exception) -> None:
            if not isValid(self):
                return
            self.shell.toast(str(exc) or "Something went wrong")
            if error:
                error(exc)

        self.shell.run(fn, safe_ok, safe_error)

    def loading(self, text: str = "Loading…") -> None:
        row = QWidget()
        line = QHBoxLayout(row)
        line.setContentsMargins(0, 40, 0, 40)
        line.setSpacing(10)
        line.addStretch(1)
        line.addWidget(Spinner(18))
        line.addWidget(Txt(text, size=16, token="on_surface_variant"))
        line.addStretch(1)
        self._loading_row = row
        self.add(row)

    def stop_loading(self) -> None:
        if self._loading_row is None:
            return
        self.body_layout.removeWidget(self._loading_row)
        self._loading_row.setParent(None)
        self._loading_row.deleteLater()
        self._loading_row = None

    def load(self) -> None:
        pass

    # hooks --------------------------------------------------------------
    def apply_like(self, track_id: int, liked: bool) -> None:
        if self.track_list is not None:
            self.track_list.set_liked(track_id, liked)

    def apply_settings(self, settings: Settings) -> None:
        pass

    def refresh_theme(self) -> None:
        self.viewport().update()


# ── shared bits ────────────────────────────────────────────────────────────


def section_head(title: str, meta: str = "", actions: Sequence[QWidget] = ()) -> QWidget:
    widget = QWidget()
    line = QHBoxLayout(widget)
    line.setContentsMargins(0, 0, 0, 12)
    line.setSpacing(10)
    line.addWidget(Txt(title, size=22, family="display", token="on_surface"), 0,
                   Qt.AlignmentFlag.AlignBottom)
    if meta:
        line.addWidget(Txt(meta.upper(), size=14, family="mono", token="on_surface_variant", spacing=1.2),
                       0, Qt.AlignmentFlag.AlignBottom)
    line.addStretch(1)
    for action in actions:
        line.addWidget(action)
    return widget


def _album_items(albums: Sequence[AlbumRef]) -> list[dict]:
    return [
        {
            "title": a.album,
            "subtitle": " · ".join(x for x in [a.artist, f"{a.n} tracks"] if x),
            "cover_id": a.cover_id,
            "kind": "album",
            "payload": a,
        }
        for a in albums
    ]


def _artist_items(artists: Sequence[ArtistRef]) -> list[dict]:
    return [
        {
            "title": a.artist,
            "subtitle": f"{a.n} tracks · {a.albums} albums",
            "cover_id": a.cover_id,
            "round": True,
            "kind": "artist",
            "payload": a,
        }
        for a in artists
    ]


def _playlist_items(playlists: Sequence[PlaylistRef]) -> list[dict]:
    return [
        {
            "title": p.name,
            "subtitle": f"{p.n} tracks",
            "cover_id": p.cover_id,
            "kind": "playlist",
            "payload": p,
        }
        for p in playlists
    ]


# ── home ───────────────────────────────────────────────────────────────────


class HomeScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        self.loading("Warming up the shelves…")
        self.run(self.shell.repo.home, self._render)

    def _render(self, home: HomeData) -> None:
        self.clear()
        hour = time.localtime().tm_hour
        greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
        head = PageHead("Home", greeting, f"{len(home.sections)} shelves")
        self.add(head, 16)

        if home.albums:
            shelf = Shelf("Fresh pressings", f"{len(home.albums)} albums")
            shelf.set_items(_album_items(home.albums))
            shelf.opened.connect(lambda a: self.shell.navigate(("album", a.album)))
            shelf.played.connect(lambda a: self.shell.play_album(a.album))
            browse = McButton("All albums", small=True, ghost=True)
            browse.clicked.connect(lambda: self.shell.navigate(("library", "albums")))
            shelf.add_action(browse)
            self.add(shelf, 10)

        for section in home.sections:
            if not section.tracks:
                continue
            shelf = Shelf(section.title, f"{len(section.tracks)} tracks")
            play_all = McButton("Play all", small=True, solid=True, icon="play")
            play_all.clicked.connect(
                lambda _=False, tracks=section.tracks: self.shell.play_tracks(tracks, 0)
            )
            shelf.add_action(play_all)
            shelf.set_items([
                {
                    "title": t.title,
                    "subtitle": t.artist,
                    "cover_id": t.id,
                    "kind": "track",
                    "payload": (section.tracks, i),
                }
                for i, t in enumerate(section.tracks)
            ])
            shelf.opened.connect(
                lambda payload: self.shell.play_tracks(payload[0], payload[1])
            )
            shelf.played.connect(
                lambda payload: self.shell.play_tracks(payload[0], payload[1])
            )
            self.add(shelf, 10)

        if not home.sections and not home.albums:
            self.add(EmptyState(
                "Your library is waiting for its first song",
                "Ask an admin to scan the music folder, or add something yourself from Requests.",
                icon="disc-3",
                action=("Add music", lambda: self.shell.navigate(("requests",))),
            ))
        self.reset_scroll()


# ── search ─────────────────────────────────────────────────────────────────


class SearchScreen(Screen):
    def __init__(self, window, query: str = "", parent=None):
        super().__init__(window, parent)
        self._query = query
        self._token = 0
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(260)
        self._debounce.timeout.connect(self._search)

        self.head = PageHead("Search", "Find something to play", "")
        self.add(self.head, 16)
        self.results = QWidget()
        self.rlayout = QVBoxLayout(self.results)
        self.rlayout.setContentsMargins(0, 0, 0, 0)
        self.rlayout.setSpacing(0)
        self.add(self.results)

        if query.strip():
            self._debounce.start(10)
        else:
            self._render_empty()

    def set_query(self, query: str) -> None:
        self._query = query
        self._debounce.start()

    def _search(self) -> None:
        query = self._query.strip()
        self._token += 1
        token = self._token
        if not query:
            self._render_empty()
            return
        self._render_loading(query)
        self.run(
            lambda: self.shell.repo.search(query),
            lambda data: self._render(query, data, token),
        )

    def _clear_results(self) -> None:
        while self.rlayout.count():
            item = self.rlayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self.track_list = None

    def _render_loading(self, query: str) -> None:
        self._clear_results()
        self.head.title_label.setText("Search")
        row = QWidget()
        line = QHBoxLayout(row)
        line.setContentsMargins(0, 30, 0, 30)
        line.setSpacing(10)
        line.addWidget(Spinner(18))
        line.addWidget(Txt(f'Searching for “{query}”…', size=16, token="on_surface_variant"))
        line.addStretch(1)
        self.rlayout.addWidget(row)

    def _render_empty(self) -> None:
        self._clear_results()
        self.head.title_label.setText("Search")
        self.rlayout.addWidget(EmptyState(
            "Search your library",
            "Songs, albums and artists — start typing in the field above.",
            icon="search",
        ))

    def _render(self, query: str, data: SearchData, token: int) -> None:
        if token != self._token or query != self._query.strip():
            return
        self._clear_results()
        self.head.title_label.setText(f"“{query}”")
        total = len(data.tracks) + len(data.albums) + len(data.artists)
        if not total:
            self.rlayout.addWidget(EmptyState(
                "Nothing matched",
                "Try a different spelling or browse the library.",
                icon="search",
                action=("Browse library", lambda: self.shell.navigate(("library",))),
            ))
            return

        if data.tracks:
            self.rlayout.addWidget(section_head("Songs", f"{len(data.tracks)} results"))
            tl = self.shell.make_track_list(data.tracks, self)
            tl.setParent(self.results)
            self.rlayout.addWidget(tl)
            self.track_list = tl
            self.rlayout.addSpacing(22)

        if data.albums:
            self.rlayout.addWidget(section_head("Albums", f"{len(data.albums)} results"))
            grid = TileGrid()
            grid.set_items(_album_items(data.albums))
            grid.opened.connect(lambda a: self.shell.navigate(("album", a.album)))
            grid.played.connect(lambda a: self.shell.play_album(a.album))
            self.rlayout.addWidget(grid)
            self.rlayout.addSpacing(22)

        if data.artists:
            self.rlayout.addWidget(section_head("Artists", f"{len(data.artists)} results"))
            grid = TileGrid()
            grid.set_items(_artist_items(data.artists))
            grid.opened.connect(lambda a: self.shell.navigate(("artist", a.artist)))
            grid.played.connect(lambda a: self.shell.play_artist(a.artist))
            self.rlayout.addWidget(grid)


# ── library ────────────────────────────────────────────────────────────────


class LibraryScreen(Screen):
    def __init__(self, window, tab: str = "songs", parent=None):
        super().__init__(window, parent)
        self.tab = tab if tab in ("songs", "albums", "artists", "playlists") else "songs"
        self.tracks: list[Track] = []
        head = PageHead("Library", "Everything on the server", "")
        self.seg = Segmented(
            [("songs", "Songs"), ("albums", "Albums"), ("artists", "Artists"),
             ("playlists", "Playlists")], self.tab
        )
        self.seg.changed.connect(self._switch)
        head.add_action(self.seg)
        self.add(head, 16)
        self.content = QWidget()
        self.clayout = QVBoxLayout(self.content)
        self.clayout.setContentsMargins(0, 0, 0, 0)
        self.clayout.setSpacing(0)
        self.add(self.content)
        self.load()

    def _switch(self, tab: str) -> None:
        self.tab = tab
        self.load()

    def _clear_content(self) -> None:
        while self.clayout.count():
            item = self.clayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self.track_list = None

    def load(self) -> None:
        self._clear_content()
        self.loading()
        if self.tab == "songs":
            self.run(self.shell.repo.tracks, self._render_songs)
        elif self.tab == "albums":
            self.run(self.shell.repo.albums, self._render_albums)
        elif self.tab == "artists":
            self.run(self.shell.repo.artists, self._render_artists)
        else:
            self.run(self.shell.repo.playlists, self._render_playlists)

    def _render_playlists(self, playlists: list[PlaylistRef]) -> None:
        self._clear_content()
        if not playlists:
            self.clayout.addWidget(EmptyState(
                "No playlists yet",
                "Faves and Likes appear here automatically once you listen and like tracks.",
                icon="list-music",
            ))
            return
        grid = TileGrid()
        grid.set_items(_playlist_items(playlists))
        grid.opened.connect(lambda p: self.shell.navigate(("playlist", p.id)))
        grid.played.connect(lambda p: self.shell.play_playlist(p.id))
        self.clayout.addWidget(grid)

    def _render_songs(self, tracks: list[Track]) -> None:
        self._clear_content()
        self.tracks = tracks
        if not tracks:
            self.clayout.addWidget(EmptyState(
                "No songs yet", "Add music to the server and rescan.",
                icon="music",
            ))
            return
        self.clayout.addWidget(section_head("Songs", f"{len(tracks)} tracks"))
        tl = self.shell.make_track_list(tracks, self)
        tl.setParent(self.content)
        self.clayout.addWidget(tl)
        self.track_list = tl

    def _render_albums(self, albums: list[AlbumRef]) -> None:
        self._clear_content()
        if not albums:
            self.clayout.addWidget(EmptyState("No albums yet", icon="disc-3"))
            return
        self.clayout.addWidget(section_head("Albums", f"{len(albums)} albums"))
        grid = TileGrid()
        grid.set_items(_album_items(albums))
        grid.opened.connect(lambda a: self.shell.navigate(("album", a.album)))
        grid.played.connect(lambda a: self.shell.play_album(a.album))
        self.clayout.addWidget(grid)

    def _render_artists(self, artists: list[ArtistRef]) -> None:
        self._clear_content()
        if not artists:
            self.clayout.addWidget(EmptyState("No artists yet", icon="users"))
            return
        self.clayout.addWidget(section_head("Artists", f"{len(artists)} artists"))
        grid = TileGrid()
        grid.set_items(_artist_items(artists))
        grid.opened.connect(lambda a: self.shell.navigate(("artist", a.artist)))
        grid.played.connect(lambda a: self.shell.play_artist(a.artist))
        self.clayout.addWidget(grid)


# ── album / artist ─────────────────────────────────────────────────────────


class CollectionScreen(Screen):
    def __init__(self, window, name: str, kind: str = "album", parent=None):
        super().__init__(window, parent)
        self.name = name
        self.kind = kind
        self.tracks: list[Track] = []
        self.load()

    def load(self) -> None:
        self.clear()
        self.loading()
        if self.kind == "artist":
            self.run(lambda: self.shell.repo.artist(self.name), self._render)
        else:
            self.run(lambda: self.shell.repo.album(self.name), self._render)

    def _render(self, tracks: list[Track]) -> None:
        self.clear()
        self.tracks = tracks
        if not tracks:
            self.add(PageHead("Artist" if self.kind == "artist" else "Album",
                              "", ""), 16)
            self.add(EmptyState(
                "Nothing here", "This release has no tracks on the server.",
                icon="disc-3",
                action=("Back to library", lambda: self.shell.navigate(("library",))),
            ))
            return
        cover = tracks[0].id
        total = sum(t.duration for t in tracks)
        subs = [
            tracks[0].artist if self.kind == "album" else "",
            f"{len(tracks)} tracks",
            fmt_total(total),
        ]
        hero = Hero(
            "Artist" if self.kind == "artist" else "Album",
            self.name,
            [s for s in subs if s],
            cover,
            round_=self.kind == "artist",
        )
        play = McButton("Play", solid=True, icon="play")
        play.clicked.connect(lambda: self.shell.play_tracks(tracks, 0))
        hero.add_action(play)
        shuffle = McButton("Shuffle", icon="shuffle")
        shuffle.clicked.connect(lambda: self.shell.shuffle_tracks(tracks))
        hero.add_action(shuffle)
        radio = McButton("Radio", ghost=True, icon="radio")
        radio.clicked.connect(lambda: self.shell.start_radio(tracks[0]))
        hero.add_action(radio)
        self.add(hero, 10)
        tl = self.shell.make_track_list(tracks, self)
        tl.setParent(self.body)
        self.add(tl)
        self.track_list = tl


# ── likes ──────────────────────────────────────────────────────────────────


class LikesScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        self.loading()
        self.run(self.shell.repo.likes, self._render)

    def _render(self, tracks: list[Track]) -> None:
        self.clear()
        if not tracks:
            self.add(PageHead("Liked songs", "Saved by you", ""), 16)
            self.add(EmptyState(
                "No liked songs yet",
                "Tap the heart on any track and it will show up here.",
                icon="heart",
                action=("Browse library", lambda: self.shell.navigate(("library",))),
            ))
            return
        hero = Hero(
            "Collection", "Liked songs",
            [f"{len(tracks)} tracks", fmt_total(sum(t.duration for t in tracks))],
            tracks[0].id,
        )
        play = McButton("Play", solid=True, icon="play")
        play.clicked.connect(lambda: self.shell.play_tracks(tracks, 0))
        hero.add_action(play)
        shuffle = McButton("Shuffle", icon="shuffle")
        shuffle.clicked.connect(lambda: self.shell.shuffle_tracks(tracks))
        hero.add_action(shuffle)
        self.add(hero, 10)
        tl = self.shell.make_track_list(tracks, self)
        tl.setParent(self.body)
        self.add(tl)
        self.track_list = tl


# ── playlists ──────────────────────────────────────────────────────────────


class PlaylistsScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        head = PageHead("Playlists", "Your collections", "")
        new = McButton("New playlist", solid=True, icon="plus")
        new.clicked.connect(self.shell.create_playlist)
        head.add_action(new)
        self.add(head, 16)
        self.loading()
        self.run(self.shell.repo.playlists, self._render)

    def _render(self, playlists: list[PlaylistRef]) -> None:
        self.clear()
        head = PageHead("Playlists", "Your collections", f"{len(playlists)} lists")
        new = McButton("New playlist", solid=True, icon="plus")
        new.clicked.connect(self.shell.create_playlist)
        head.add_action(new)
        self.add(head, 16)
        if not playlists:
            self.add(EmptyState(
                "No playlists yet",
                "Group tracks into a playlist — it syncs with the web and mobile apps.",
                icon="list-music",
                action=("Create playlist", self.shell.create_playlist),
            ))
            return
        grid = TileGrid()
        grid.set_items(_playlist_items(playlists))
        grid.opened.connect(lambda p: self.shell.navigate(("playlist", p.id)))
        grid.played.connect(lambda p: self.shell.play_playlist(p.id))
        self.add(grid)


class PlaylistScreen(Screen):
    def __init__(self, window, playlist_id: int, parent=None):
        super().__init__(window, parent)
        self.playlist_id = playlist_id
        self.playlist_name = ""
        self.tracks: list[Track] = []
        self.load()

    def load(self) -> None:
        self.clear()
        self.loading()
        self.run(lambda: self.shell.repo.playlist(self.playlist_id), self._render)

    def _render(self, result: tuple[str, list[Track]]) -> None:
        name, tracks = result
        self.playlist_name = name
        self.tracks = tracks
        self.clear()
        hero = Hero(
            "Playlist", name,
            [f"{len(tracks)} tracks", fmt_total(sum(t.duration for t in tracks))],
            tracks[0].id if tracks else None,
        )
        if tracks:
            play = McButton("Play", solid=True, icon="play")
            play.clicked.connect(lambda: self.shell.play_tracks(tracks, 0))
            hero.add_action(play)
            shuffle = McButton("Shuffle", icon="shuffle")
            shuffle.clicked.connect(lambda: self.shell.shuffle_tracks(tracks))
            hero.add_action(shuffle)
        rename = McButton("Rename", ghost=True)
        rename.clicked.connect(self._rename)
        hero.add_action(rename)
        delete = McButton("Delete", ghost=True, danger=True, icon="trash-2")
        delete.clicked.connect(self._delete)
        hero.add_action(delete)
        self.add(hero, 10)

        if not tracks:
            self.add(EmptyState(
                "This playlist is empty",
                "Add tracks from any song menu — “Add to playlist…”.",
                icon="list-music",
            ))
            return
        tl = self.shell.make_track_list(tracks, self, playlist_id=self.playlist_id)
        tl.setParent(self.body)
        self.add(tl)
        self.track_list = tl

    def _rename(self) -> None:
        name = prompt(self, "Rename playlist", "Name", initial=self.playlist_name,
                      confirm="Rename")
        if not name:
            return
        self.run(lambda: self.shell.repo.rename_playlist(self.playlist_id, name),
                 lambda _: (self.shell.refresh_playlists(), self.shell.toast("Renamed"),
                            self.load()))

    def _delete(self) -> None:
        if not confirm(self, "Delete playlist",
                       f"“{self.playlist_name}” will be removed. Tracks stay in the library.",
                       confirm_label="Delete"):
            return

        def job():
            self.shell.repo.delete_playlist(self.playlist_id)

        def ok(_):
            self.shell.refresh_playlists()
            self.shell.toast("Playlist deleted")
            self.shell.navigate(("playlists",), push=False)

        self.run(job, ok)


# ── requests ───────────────────────────────────────────────────────────────


class RequestLine(QWidget):
    def __init__(self, row: RequestRow, is_admin: bool, last: bool,
                 on_action: Callable[[int, str], None],
                 on_log: Callable[[RequestRow], None], parent=None):
        super().__init__(parent)
        self._last = last
        line = QHBoxLayout(self)
        line.setContentsMargins(16, 10, 16, 10)
        line.setSpacing(12)
        line.addWidget(Glyph("download", 15, "dim2"))
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(2)
        url = Txt(row.url, size=14, family="mono", token="on_surface", wrap=True)
        url.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        text.addWidget(url)
        when = time.strftime("%d %b %H:%M", time.localtime(row.created)) if row.created else ""
        who = f"@{row.username}" if row.username else "you"
        text.addWidget(Txt(f"#{row.id} · {who} · {when}", size=14, family="mono",
                           token="on_surface_variant"))
        line.addLayout(text, 1)
        line.addWidget(StatusChip(row.status or "queued",
                                  STATUS_TOKEN.get(row.status,
                                                   "on_surface_variant")), 0,
                       Qt.AlignmentFlag.AlignVCenter)
        if is_admin and row.status in ("pending", "failed"):
            approve = McButton("Approve", small=True, solid=True)
            approve.clicked.connect(lambda: on_action(row.id, "approve"))
            line.addWidget(approve)
            reject = McButton("Reject", small=True, ghost=True, danger=True)
            reject.clicked.connect(lambda: on_action(row.id, "reject"))
            line.addWidget(reject)
        elif row.status == "running":
            line.addWidget(Spinner(14))
        if is_admin:
            if row.status in ("pending", "running"):
                cancel = IconButton("x", size=26, icon_size=14, tooltip="Cancel request")
                cancel.clicked.connect(lambda: on_action(row.id, "cancel"))
                line.addWidget(cancel)
            if row.status in ("failed", "rejected", "cancelled"):
                retry = IconButton("refresh-cw", size=26, icon_size=14,
                                   tooltip="Retry request")
                retry.clicked.connect(lambda: on_action(row.id, "retry"))
                line.addWidget(retry)
            delete = IconButton("trash-2", size=26, icon_size=14, tooltip="Delete request")
            delete.clicked.connect(lambda: on_action(row.id, "delete"))
            line.addWidget(delete)
        log = IconButton("info", size=26, icon_size=16, tooltip="View log")
        log.clicked.connect(lambda: on_log(row))
        line.addWidget(log)

    def paintEvent(self, _event) -> None:
        if not self._last:
            p = QPainter(self)
            p.fillRect(16, self.height() - 1, self.width() - 16, 1, theme.pal().q("outline_variant"))


class RequestsScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        head = PageHead("Requests", "Download queue", "")
        self.add(head, 16)

        add_row = QWidget()
        line = QHBoxLayout(add_row)
        line.setContentsMargins(0, 0, 0, 16)
        line.setSpacing(8)
        self.url = QLineEdit()
        self.url.setPlaceholderText("Paste an https YouTube / YouTube Music link")
        self.url.setFixedHeight(36)
        self.url.returnPressed.connect(self._add)
        line.addWidget(self.url, 1)
        button = McButton("Request", solid=True, icon="download")
        button.clicked.connect(self._add)
        line.addWidget(button)
        self.add(add_row)

        self.list_host = QWidget()
        self.llayout = QVBoxLayout(self.list_host)
        self.llayout.setContentsMargins(0, 0, 0, 0)
        self.llayout.setSpacing(0)
        self.add(self.list_host)
        self.loading()
        self.run(
            self.shell.repo.requests,
            lambda result: self._render(result[0], result[1]),
        )

    def _clear_list(self) -> None:
        while self.llayout.count():
            item = self.llayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _render(self, is_admin: bool, rows: list[RequestRow]) -> None:
        self.stop_loading()
        self._clear_list()
        if not rows:
            self.llayout.addWidget(EmptyState(
                "No requests yet",
                "Paste a link above to add music to the server.",
                icon="download",
            ))
            return
        panel = Panel("Recent requests")
        for i, row in enumerate(rows):
            panel.add_widget(RequestLine(row, is_admin, i == len(rows) - 1,
                                         self._act, self._log))
        self.llayout.addWidget(panel)

    def _add(self) -> None:
        url = self.url.text().strip()
        if not url.startswith("http"):
            self.shell.toast("Paste an https YouTube link")
            return
        self.run(lambda: self.shell.repo.request_add(url), self._added)

    def _added(self, status: str) -> None:
        self.url.clear()
        self.shell.toast("Sent for approval" if status == "pending" else "Download queued")
        self.load()

    def _act(self, request_id: int, action: str) -> None:
        def job():
            if action == "cancel":
                self.shell.repo.request_cancel(request_id)
            elif action == "retry":
                self.shell.repo.request_retry(request_id)
            elif action == "delete":
                self.shell.repo.request_delete(request_id)
            else:
                self.shell.repo.request_act(request_id, action)

        self.run(job, lambda _: self.load())

    def _log(self, row: RequestRow) -> None:
        sheet = Sheet(self, f"Request #{row.id}")
        view = QTextEdit()
        view.setReadOnly(True)
        view.setPlainText(row.log or "No log recorded yet.")
        sheet.body.addWidget(view, 1)

        def ok(data: dict) -> None:
            if not isValid(view):
                return
            text = ""
            if isinstance(data, dict):
                text = str(data.get("log") or data.get("text") or "")
            view.setPlainText(text or row.log or "No log recorded yet.")

        self.run(lambda: self.shell.repo.request_log(row.id), ok,
                 error=lambda _e: None)
        sheet.exec()


# ── settings ───────────────────────────────────────────────────────────────


class ThemeCard(QAbstractButton):
    def __init__(self, name: str, label: str, selected: bool = False, parent=None):
        super().__init__(parent)
        self.name = name
        self.label = label
        self._selected = selected
        self.setFixedSize(96, 72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_selected(self, selected: bool) -> None:
        if self._selected != selected:
            self._selected = selected
            self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        surface, accent = theme.theme_preview(self.name)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        pal = theme.pal()
        p.setPen(QPen(pal.q("primary") if self._selected else
                      pal.q("outline_variant"), 2 if self._selected else 1))
        p.setBrush(pal.q("surface_container_lowest"))
        p.drawRoundedRect(rect, 16, 16)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(surface))
        p.drawRoundedRect(QRectF(rect.x() + 2, rect.y() + 2,
                                 rect.width() - 4, 42), 14, 14)
        p.setBrush(QColor(accent))
        p.drawRoundedRect(QRectF(rect.x() + 12, rect.y() + 32, 20, 6), 3, 3)
        p.setFont(design.font("label", size=12))
        p.setPen(QPen(pal.q("on_surface_variant")))
        p.drawText(QRectF(rect.x(), rect.y() + 44, rect.width(), rect.height() - 46),
                   int(Qt.AlignmentFlag.AlignCenter), self.label.upper())


class Swatch(QAbstractButton):
    def __init__(self, color: str, selected: bool = False, parent=None):
        super().__init__(parent)
        self.color = color
        self._selected = selected
        self.setFixedSize(48, 48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(color)

    def set_selected(self, selected: bool) -> None:
        if self._selected != selected:
            self._selected = selected
            self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(theme.pal().q("outline_variant"), 1))
        p.setBrush(QColor(self.color))
        p.drawEllipse(QRectF(10, 10, 28, 28))
        if self._selected:
            p.setPen(QPen(theme.pal().q("primary"), 3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(5, 5, 38, 38))


class SettingsScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self._theme_cards: list[ThemeCard] = []
        self._swatches: list[Swatch] = []
        self._mode: Optional[Segmented] = None
        self._density: Optional[Segmented] = None
        self._material: Optional[Segmented] = None
        self._stroke: Optional[Segmented] = None
        self._filled: Optional[Switch] = None
        self._motion: Optional[Switch] = None
        self._covers: Optional[Switch] = None
        self._rotur_layout: Optional[QHBoxLayout] = None
        self._rotur_row = None
        self._discord_layout: Optional[QHBoxLayout] = None
        self._discord_row = None
        self._builds_host: Optional[QWidget] = None
        self._server_row = None
        self._update_row = None
        self._update_button: Optional[McButton] = None
        self._pending_row = None
        self.load()

    def load(self) -> None:
        self.clear()
        settings = self.shell.settings
        user = self.shell.me
        head = PageHead("Settings", "Preferences",
                        user.username if user else "")
        self.add(head, 16)
        self._theme_cards = []
        self._swatches = []

        # appearance -----------------------------------------------------
        panel = Panel("Appearance")
        themes_row = QWidget()
        line = QHBoxLayout(themes_row)
        line.setContentsMargins(16, 14, 16, 12)
        line.setSpacing(8)
        for name in theme.THEME_ORDER:
            card = ThemeCard(name, theme.family_label(name),
                             theme.family_of(settings.theme) == name)
            card.clicked.connect(lambda _=False, n=name: self._pick_theme(n))
            self._theme_cards.append(card)
            line.addWidget(card)
        line.addStretch(1)
        panel.add_widget(themes_row)

        self._mode = Segmented(
            [("auto", "System"), ("light", "Light"), ("dark", "Dark")],
            theme.mode_of(settings.theme),
        )
        self._mode.changed.connect(self._set_mode)
        panel.add_row("Mode", "Top half light, bottom half dark", self._mode)

        accents = QWidget()
        aline = QHBoxLayout(accents)
        aline.setContentsMargins(0, 0, 0, 0)
        aline.setSpacing(8)
        current = QColor(settings.accent).name().lower()
        for color, _label in theme.ACCENTS:
            swatch = Swatch(color, color.lower() == current)
            swatch.clicked.connect(lambda _=False, c=color: self._pick_accent(c))
            self._swatches.append(swatch)
            aline.addWidget(swatch)
        custom = McButton("Custom", small=True, ghost=True)
        custom.clicked.connect(self._pick_custom_accent)
        aline.addWidget(custom)
        aline.addStretch(1)
        panel.add_row("Accent", "Buttons, progress and highlights", accents)
        self._stroke = Segmented(
            [("1", "1x"), ("1.5", "1.5x"), ("2", "2x")],
            f"{settings.iconStroke:g}",
        )
        self._stroke.changed.connect(
            lambda value: self._set(iconStroke=float(value))
        )
        panel.add_row("Icon width", "Lucide outline weight", self._stroke)
        self._filled = Switch(settings.iconFilled)
        self._filled.toggled.connect(lambda value: self._set(iconFilled=value))
        panel.add_row("Filled icons", "Fill circles and squares only", self._filled)
        self._density = Segmented([("comfy", "Comfy"), ("compact", "Compact")],
                                  settings.density)
        self._density.changed.connect(lambda value: self._set(density=value))
        panel.add_row("Density", "Row height in track lists", self._density)
        self._material = Segmented(
            [("plane", "Plane"), ("solid", "Solid")],
            settings.material,
        )
        self._material.changed.connect(lambda value: self._set(material=value))
        panel.add_row("Surface", "Background treatment shared with the web player",
                      self._material)
        self._motion = Switch(motion.local_enabled(self.shell.store))
        self._motion.toggled.connect(self._set_motion)
        panel.add_row("Playful motion", "Springs and bounces; Reduce Motion wins",
                      self._motion)
        self._covers = Switch(settings.covers)
        self._covers.toggled.connect(lambda value: self._set(covers=value))
        panel.add_row("Cover art", "Show embedded artwork", self._covers, last=True)
        self.add(panel, 16)

        # playback -------------------------------------------------------
        panel = Panel("Playback")
        options = [
            ("autoplay", "Autoplay", "Continue to the next track automatically", settings.autoplay),
            ("hide_explicit", "Hide explicit tracks", "Skip explicit tracks in queues", settings.hide_explicit),
            ("yt_stats", "YouTube stats", "Show like counts in track lists", settings.yt_stats),
            ("remember_volume", "Remember volume", "Restore the last volume on start", settings.remember_volume),
            ("prefetch", "Prefetch next track", "Cache the next track in the background", settings.prefetch),
            ("offline_audio", "Stream cache", "Keep played audio on disk for offline replay", settings.offline_audio),
        ]
        for index, (key, title, subtitle, value) in enumerate(options):
            toggle = Switch(value)
            toggle.toggled.connect(lambda checked, k=key: self._set(**{k: checked}))
            panel.add_row(title, subtitle, toggle, last=index == len(options) - 1)
        self.add(panel, 16)

        # privacy / activity ----------------------------------------------
        panel = Panel("Privacy & activity")
        options = [
            ("private", "Private listening", "Hide what you play from other listeners", settings.private),
            ("rotur_activity", "RoturLink activity", "Publish your current track to RoturLink", settings.rotur_activity),
            ("discord_activity", "Discord activity", "Show your current track in Discord", settings.discord_activity),
            ("show_room_url", "Show room link", "Expose your listen-along invite link in Settings", settings.show_room_url),
        ]
        for index, (key, title, subtitle, value) in enumerate(options):
            toggle = Switch(value)
            toggle.toggled.connect(lambda checked, k=key: self._set(**{k: checked}))
            panel.add_row(title, subtitle, toggle, last=index == len(options) - 1)
        self.add(panel, 16)

        # account --------------------------------------------------------
        panel = Panel("Account")
        panel.add_row("Username", "Signed in to this server",
                      Txt(user.username if user else "", size=16, token="on_surface_variant"))

        server_row = QWidget()
        sline = QHBoxLayout(server_row)
        sline.setContentsMargins(0, 0, 0, 0)
        sline.setSpacing(8)
        sline.addWidget(Txt(self.shell.api.base_url, size=14, family="mono",
                            token="on_surface_variant", wrap=True))
        change = McButton("Change", small=True, ghost=True)
        change.clicked.connect(self._change_server)
        sline.addWidget(change)
        self._server_row = panel.add_row("Server", "Where the library lives", server_row)

        email = McButton("Change", small=True, ghost=True)
        email.clicked.connect(self._change_email)
        panel.add_row("Email", user.email or "No email on this account", email)

        password = McButton("Change password", small=True)
        password.clicked.connect(self._change_password)
        panel.add_row("Password", "Update your local account password", password)

        room_trailing = QWidget()
        rline = QHBoxLayout(room_trailing)
        rline.setContentsMargins(0, 0, 0, 0)
        rline.setSpacing(6)
        copy_room = McButton("Copy", small=True, ghost=True)
        copy_room.clicked.connect(self._copy_room_url)
        open_room = McButton("Open", small=True, ghost=True, icon="arrow-up-right")
        open_room.clicked.connect(self._open_room_url)
        rline.addWidget(copy_room)
        rline.addWidget(open_room)
        self._room_row = panel.add_row(
            "Room link", "Invite others to listen along", room_trailing
        )

        self._rotur_trailing = QWidget()
        self._rotur_layout = QHBoxLayout(self._rotur_trailing)
        self._rotur_layout.setContentsMargins(0, 0, 0, 0)
        self._rotur_layout.setSpacing(8)
        self._rotur_trailing.setMinimumWidth(120)
        self._rotur_row = panel.add_row("RoturLink", "Checking…", self._rotur_trailing)

        self._discord_trailing = QWidget()
        self._discord_layout = QHBoxLayout(self._discord_trailing)
        self._discord_layout.setContentsMargins(0, 0, 0, 0)
        self._discord_layout.setSpacing(8)
        self._discord_trailing.setMinimumWidth(120)
        self._discord_row = panel.add_row("Discord", "Checking…", self._discord_trailing)

        if user and user.is_admin:
            admin = McButton("Open admin", small=True, ghost=True, icon="users")
            admin.clicked.connect(lambda: self.shell.navigate(("admin",)))
            panel.add_row("Admin", "Manage users, requests and scans", admin)
        signout = McButton("Sign out", small=True, danger=True, icon="log-out")
        signout.clicked.connect(self.shell.sign_out)
        panel.add_row("Session", "Sign out of this desktop", signout, last=True)
        self.add(panel, 16)

        # server metadata / builds ---------------------------------------
        panel = Panel("Updates & builds")
        panel.add_row("Client version", VERSION,
                      Txt("Running now", size=14, token="on_surface_variant"))
        self._server_version_row = panel.add_row(
            "Server version", "Checking…", Txt("", size=14, family="mono", token="on_surface_variant")
        )
        update_actions = QWidget()
        update_line = QHBoxLayout(update_actions)
        update_line.setContentsMargins(0, 0, 0, 0)
        update_line.setSpacing(6)
        self._update_button = McButton("Open page", small=True, ghost=True, icon="download")
        self._update_button.setToolTip("Open the public download page in your browser")
        self._update_button.clicked.connect(
            lambda _=False: self.shell.open_update()
        )
        self._update_button.setVisible(False)
        check = McButton("Check", small=True, ghost=True, icon="refresh-cw")
        check.clicked.connect(self._check_for_updates)
        update_line.addWidget(self._update_button)
        update_line.addWidget(check)
        self._update_row = panel.add_row(
            "App update", f"Current version {VERSION}", update_actions
        )
        self._render_update(self.shell._update)

        self._builds_host = QWidget()
        build_line = QVBoxLayout(self._builds_host)
        build_line.setContentsMargins(0, 0, 0, 0)
        build_line.setSpacing(0)
        panel.add_widget(self._builds_host)
        guide = McButton("Self-hosting guide", small=True, ghost=True,
                         icon="arrow-up-right")
        guide.clicked.connect(self._open_selfhost)
        panel.add_row("Run your own", "Docs for hosting a private server", guide,
                      last=True)
        self.add(panel, 16)

        # offline state / cache ------------------------------------------
        panel = Panel("Offline & cache")
        self._pending_label = Txt("0 pending changes", size=14, token="on_surface_variant")
        sync = McButton("Sync now", small=True, ghost=True, icon="refresh-cw")
        sync.clicked.connect(self.shell.sync_outbox)
        self._pending_row = panel.add_row("Offline writes",
                                         "Queued until the server is reachable", sync)
        self._cache_label = Txt("", size=14, token="on_surface_variant")
        panel.add_row("Cache", "Saved replies and streamed audio", self._cache_label)
        downloads = McButton("Manage", small=True, ghost=True,
                             icon="arrow-up-right")
        downloads.clicked.connect(lambda: self.shell.navigate(("downloads",)))
        panel.add_row("Downloads", "Inspect, prune or clear cached files", downloads,
                      last=True)
        self.add(panel, 16)

        about = Txt(
            f"mcmusic desktop {VERSION} · native Qt 6 client. Same server API, "
            "palette and icons as the web player and Android app.",
            size=14, token="on_surface_variant", wrap=True,
        )
        self.add(about)

        self.refresh_sync_state()
        self.run(self.shell.repo.rotur_status, self._render_rotur,
                 error=lambda _e: self._render_rotur({}))
        self.run(self.shell.repo.discord_status, self._render_discord,
                 error=lambda _e: self._render_discord({}))
        self.run(self.shell.repo.version, self._render_version,
                 error=lambda _e: None)
        self.run(self.shell.repo.builds, self._render_builds,
                 error=lambda _e: None)

    # helpers ------------------------------------------------------------
    def _set(self, **changes) -> None:
        self.shell.apply_settings(replace(self.shell.settings, **changes))

    def _set_motion(self, enabled: bool) -> None:
        self.shell.store.playful_motion = bool(enabled)
        motion.reset_platform_cache()

    def _pick_theme(self, name: str) -> None:
        family = theme.family_of(name)
        mode = theme.mode_of(self.shell.settings.theme)
        self.shell.apply_settings(
            replace(self.shell.settings, theme=theme.with_mode(family, mode))
        )

    def _set_mode(self, mode: str) -> None:
        self.shell.apply_settings(
            replace(self.shell.settings,
                    theme=theme.with_mode(self.shell.settings.theme, mode))
        )

    def _pick_accent(self, color: str) -> None:
        self.shell.apply_settings(replace(self.shell.settings, accent=color))

    def _pick_custom_accent(self) -> None:
        initial = QColor(self.shell.settings.accent)
        chosen = QColorDialog.getColor(initial, self, "Accent colour")
        if chosen.isValid():
            self._pick_accent(chosen.name())

    def _change_server(self) -> None:
        url = prompt(self, "Change server", "Server URL",
                     initial=self.shell.api.base_url, placeholder="http://host:8000",
                     confirm="Connect")
        if url:
            self.shell.change_server(url)

    def _change_password(self) -> None:
        from .widgets import Sheet

        sheet = Sheet(self, "Change password")
        old = LabeledField("Current password", "••••••••", password=True)
        new = LabeledField("New password", "at least 6 characters", password=True)
        sheet.body.addWidget(old)
        sheet.body.addWidget(new)
        error = Txt("", size=14, token="error", wrap=True)
        error.setVisible(False)
        sheet.body.addWidget(error)

        row = QHBoxLayout()
        row.addStretch(1)
        cancel = McButton("Cancel", ghost=True)
        cancel.clicked.connect(sheet.reject)
        row.addWidget(cancel)
        save = McButton("Save", solid=True)
        row.addWidget(save)
        sheet.body.addLayout(row)

        def submit() -> None:
            if len(new.text()) < 6:
                error.setText("New password must be 6+ characters")
                error.setVisible(True)
                return
            save.setEnabled(False)

            def job():
                self.shell.repo.change_password(old.text(), new.text())

            def ok(_):
                sheet.accept()
                self.shell.toast("Password changed")

            def fail(exc: Exception) -> None:
                save.setEnabled(True)
                error.setText(str(exc))
                error.setVisible(True)

            self.shell.run(job, ok, fail)

        save.clicked.connect(submit)
        new.line_edit.returnPressed.connect(submit)
        old.line_edit.setFocus()
        sheet.exec()

    def _change_email(self) -> None:
        current = self.shell.me.email if self.shell.me else ""
        email = prompt(self, "Account email", "Email address", initial=current or "",
                       placeholder="you@example.com", confirm="Save")
        if not email:
            return
        self.run(lambda: self.shell.repo.set_email(email),
                 lambda me: (self.shell.after_login(me), self.load(),
                             self.shell.toast("Email updated")))

    def _room_url(self) -> str:
        base = self.shell.settings.room_url or self.shell.store.room_url
        if not base:
            return ""
        user = self.shell.me
        code = (user.rotur_user_id or user.rotur_id if user else "") or ""
        return base.rstrip("/") + ("#room=" + code[:8] if code else "")

    def _copy_room_url(self) -> None:
        url = self._room_url()
        if not url:
            self.shell.toast("No room link is available yet")
            return
        QGuiApplication.clipboard().setText(url)
        self.shell.toast("Room link copied")

    def _open_room_url(self) -> None:
        url = self._room_url()
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _render_rotur(self, status: dict) -> None:
        while self._rotur_layout.count():
            item = self._rotur_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not isinstance(status, dict):
            status = {}
        configured = bool(status.get("configured"))
        linked = bool(status.get("linked"))
        if not configured:
            self._rotur_trailing.setVisible(False)
            if self._rotur_row.subtitle_label is not None:
                self._rotur_row.subtitle_label.setText(
                    "RoturLink is not configured on this server"
                )
            return
        self._rotur_trailing.setVisible(True)
        if self._rotur_row.subtitle_label is not None:
            self._rotur_row.subtitle_label.setText(
                f"Linked as {status.get('rotur_id')}" if linked else
                "Not linked — sign in through RoturLink"
            )
        if linked:
            unlink = McButton("Unlink", small=True, ghost=True, danger=True)
            unlink.clicked.connect(self._unlink)
            self._rotur_layout.addWidget(unlink)
        else:
            open_link = McButton("Open", small=True, ghost=True, icon="link")
            open_link.clicked.connect(self._open_rotur)
            self._rotur_layout.addWidget(open_link)

    def _unlink(self) -> None:
        self.run(self.shell.repo.unlink_rotur, lambda _: self.load())

    def _open_rotur(self) -> None:
        QDesktopServices.openUrl(QUrl(self.shell.repo.rotur_authorize_url(
            self.shell.store.device_hash
        )))

    def _render_discord(self, status: dict) -> None:
        while self._discord_layout.count():
            item = self._discord_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not isinstance(status, dict):
            status = {}
        configured = bool(status.get("configured"))
        linked = bool(status.get("linked"))
        if not configured:
            self._discord_trailing.setVisible(False)
            if self._discord_row.subtitle_label is not None:
                self._discord_row.subtitle_label.setText(
                    "Discord linking is not configured on this server"
                )
            return
        self._discord_trailing.setVisible(True)
        if self._discord_row.subtitle_label is not None:
            self._discord_row.subtitle_label.setText(
                f"Linked as {status.get('username') or status.get('discord_id')}"
                if linked else "Not linked — connect a Discord account"
            )
        if linked:
            unlink = McButton("Unlink", small=True, ghost=True, danger=True)
            unlink.clicked.connect(self._unlink_discord)
            self._discord_layout.addWidget(unlink)
        else:
            link = McButton("Connect", small=True, ghost=True, icon="link")
            link.clicked.connect(self._open_discord)
            self._discord_layout.addWidget(link)

    def _unlink_discord(self) -> None:
        self.run(self.shell.repo.discord_unlink, lambda _: self.load())

    def _open_discord(self) -> None:
        QDesktopServices.openUrl(QUrl(self.shell.repo.discord_authorize_url()))

    def _check_for_updates(self) -> None:
        def render(build: Optional[BuildInfo]) -> None:
            self._render_update(build)
            if build is None and self.shell._update is None:
                self.shell.toast("No update is available for this platform")

        if self._update_button is not None:
            self._update_button.setVisible(False)
        self.shell._check_updates(render)

    def _render_update(self, build: Optional[BuildInfo]) -> None:
        if self._update_row is None or not isValid(self._update_row):
            return
        if build and build.available and build.version:
            subtitle = f"{build.version} available — open the download page"
        else:
            subtitle = f"Up to date ({VERSION})"
        if self._update_row.subtitle_label is not None:
            self._update_row.subtitle_label.setText(subtitle)
        if self._update_button is not None:
            self._update_button.setVisible(bool(build and build.available))

    def _render_version(self, data: dict) -> None:
        if not self._server_row or not isinstance(data, dict):
            return
        build = str(data.get("build") or "")[:12]
        label = f"build {build}" if build else "reachable"
        if self._server_version_row.subtitle_label is not None:
            self._server_version_row.subtitle_label.setText(label)
        trailing = self._server_version_row.layout().itemAt(1)
        if trailing is not None and trailing.widget() is not None:
            trailing.widget().setText(str(data.get("shell") or VERSION))

    def _render_builds(self, builds: list[BuildInfo]) -> None:
        host = self._builds_host
        if host is None or not isValid(host):
            return
        layout = host.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        shown = [b for b in builds if b.available][:12]
        if not shown:
            layout.addWidget(Txt("No builds are published yet.", size=14,
                                 token="on_surface_variant", wrap=True))
            return
        panel = Panel("Available builds")
        for index, build in enumerate(shown):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            line.setSpacing(6)
            download = McButton("Download", small=True, ghost=True, icon="download")
            download.clicked.connect(lambda _=False, b=build: QDesktopServices.openUrl(
                QUrl(self.shell.repo.build_url(b.url))))
            email = McButton("Email", small=True, ghost=True)
            email.clicked.connect(lambda _=False, b=build: self._email_build(b))
            line.addWidget(download)
            line.addWidget(email)
            subtitle = " · ".join(x for x in [build.version, fmt_bytes(build.bytes),
                                              build.built] if x)
            panel.add_row(build.label, subtitle or build.note, trailing,
                          last=index == len(shown) - 1)
        layout.addWidget(panel)

    def _email_build(self, build: BuildInfo) -> None:
        email = prompt(self, "Email build", "Email address",
                       placeholder="you@example.com", confirm="Send")
        if not email:
            return
        self.run(lambda: self.shell.repo.email_build(build.kind, email),
                 lambda _: self.shell.toast(f"{build.label} link sent"))

    def _open_selfhost(self) -> None:
        QDesktopServices.openUrl(QUrl(
            "https://github.com/mc20000-01/mcmusic/blob/main/docs/selfhost.md"
        ))

    def refresh_sync_state(self) -> None:
        pending = self.shell.api.pending_writes()
        if self._pending_label is not None and isValid(self._pending_label):
            self._pending_label.setText(
                f"{pending} pending change" + ("" if pending == 1 else "s")
            )
        if self._cache_label is not None and isValid(self._cache_label):
            responses, audio = self.shell.store.cache_stats()
            self._cache_label.setText(f"{responses} replies · {audio} audio files")

    def apply_settings(self, settings: Settings) -> None:
        for card in self._theme_cards:
            card.set_selected(theme.family_of(settings.theme) == card.name)
        if self._mode is not None:
            self._mode.set_selected(theme.mode_of(settings.theme))
        current = QColor(settings.accent).name().lower()
        for swatch in self._swatches:
            swatch.set_selected(swatch.color.lower() == current)
        if self._density is not None:
            self._density.set_selected(settings.density)
        if self._material is not None:
            self._material.set_selected(settings.material)
        if self._stroke is not None:
            self._stroke.set_selected(f"{settings.iconStroke:g}")
        if self._filled is not None:
            self._filled.setChecked(settings.iconFilled)
        if self._motion is not None:
            self._motion.setChecked(motion.local_enabled(self.shell.store))
        if self._covers is not None:
            self._covers.setChecked(settings.covers)
        if self._room_row is not None:
            self._room_row.setVisible(bool(settings.show_room_url and self._room_url()))
        self.refresh_sync_state()


# ── admin ──────────────────────────────────────────────────────────────────


class AdminScreen(Screen):
    """Sectioned server console matching the web/Android admin tools."""

    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    @staticmethod
    def _clear(widget: QWidget) -> None:
        layout = widget.layout()
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            child = item.widget()
            if child is not None:
                child.setParent(None)
                child.deleteLater()

    @staticmethod
    def _host(title: str) -> tuple[QWidget, QVBoxLayout, QWidget]:
        """A permanent panel wrapper with a replaceable body layout."""
        host = QWidget()
        outer = QVBoxLayout(host)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        panel = Panel(title)
        outer.addWidget(panel)
        body = QWidget()
        line = QVBoxLayout(body)
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(0)
        panel.add_widget(body)
        return host, line, body

    def load(self) -> None:
        self.clear()
        head = PageHead("Admin", "Server console", "")
        refresh = McButton("Refresh", small=True, ghost=True, icon="refresh-cw")
        refresh.clicked.connect(self.load)
        head.add_action(refresh)
        scan = McButton("Rescan library", small=True, ghost=True)
        scan.clicked.connect(self._rescan)
        head.add_action(scan)
        self.add(head, 16)
        self.loading("Reading server stats…")

        self._stats_host = QWidget()
        self.add(self._stats_host, 16)
        self._users_host, self._users_line, self._users_body = self._host("Users")
        self.add(self._users_host, 16)
        self._invites_host, self._invites_line, self._invites_body = self._host(
            "Invite codes"
        )
        invite = McButton("New code", small=True, ghost=True, icon="plus")
        invite.clicked.connect(self._create_invite)
        head.add_action(invite)
        self.add(self._invites_host, 16)
        self._requests_host, self._requests_line, self._requests_body = self._host(
            "Download requests"
        )
        self.add(self._requests_host, 16)
        self._devices_host, self._devices_line, self._devices_body = self._host(
            "Connected devices"
        )
        self.add(self._devices_host, 16)
        self._channels_host, self._channels_line, self._channels_body = self._host(
            "Control channels"
        )
        self.add(self._channels_host, 16)
        self._rooms_host, self._rooms_line, self._rooms_body = self._host(
            "Listening rooms"
        )
        self.add(self._rooms_host, 16)
        self._jobs_host, self._jobs_line, self._jobs_body = self._host("Library jobs")
        self.add(self._jobs_host, 16)

        self.run(self.shell.repo.admin_stats, self._render_stats)
        self.run(self.shell.repo.admin_users, self._render_users)
        self.run(self.shell.repo.admin_invites, self._render_invites)
        self.run(self.shell.repo.admin_requests, self._render_requests)
        self.run(self.shell.repo.admin_devices, self._render_devices)
        self.run(self.shell.repo.admin_channels, self._render_channels)
        self.run(self.shell.repo.admin_rooms, self._render_rooms)
        self.run(self.shell.repo.admin_enrich_status, self._render_enrich)
        self.run(self.shell.repo.admin_lyrics_status, self._render_lyrics)

    def _done(self) -> None:
        self.stop_loading()

    def _render_stats(self, stats: AdminStats) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._stats_host)
        grid = QGridLayout(self._stats_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)
        cards = [
            (str(stats.users), "users"), (str(stats.admins), "admins"),
            (str(stats.tracks), "tracks"), (str(stats.albums), "albums"),
            (str(stats.playlists), "playlists"), (str(stats.plays), "plays"),
            (str(stats.queue), "queue"), (str(stats.rooms), "rooms"),
            (fmt_bytes(stats.music_bytes), "music"),
            (fmt_bytes(stats.disk_free), "disk free"),
            (fmt_uptime(stats.uptime), "uptime"),
        ]
        columns = max(2, min(6, self.width() // 190))
        for i, (value, label) in enumerate(cards):
            grid.addWidget(StatCard(value, label), i // columns, i % columns)

    def _render_users(self, users: list[AdminUser]) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._users_body)
        for i, user in enumerate(users):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            line.setSpacing(8)
            if user.is_admin:
                line.addWidget(StatusChip("admin", "accent"))
            button = McButton("Revoke" if user.is_admin else "Make admin",
                              small=True, ghost=True, danger=user.is_admin)
            button.clicked.connect(lambda _=False, u=user: self._toggle_admin(u))
            delete = IconButton("trash-2", size=26, icon_size=16,
                                tooltip="Delete user")
            delete.clicked.connect(lambda _=False, u=user: self._delete_user(u))
            line.addWidget(button)
            line.addWidget(delete)
            subtitle = (f"{user.plays} plays · {user.likes} likes · "
                        f"{user.playlists} playlists · {user.requests} requests")
            self._users_line.addWidget(self._row_widget(
                user.username, subtitle, trailing, i == len(users) - 1))
        if not users:
            self._users_line.addWidget(self._row_widget(
                "No users", "Nobody has signed in yet", None, True))

    @staticmethod
    def _row_widget(title: str, subtitle: str, trailing: Optional[QWidget],
                    last: bool) -> QWidget:
        host = QWidget()
        line = QHBoxLayout(host)
        line.setContentsMargins(16, 12, 16, 12)
        line.setSpacing(16)
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.addWidget(Txt(title, size=16, token="on_surface"))
        if subtitle:
            text.addWidget(Txt(subtitle, size=14, token="on_surface_variant", wrap=True))
        line.addLayout(text, 1)
        if trailing is not None:
            line.addWidget(trailing, 0, Qt.AlignmentFlag.AlignVCenter)
        if not last:
            host.setProperty("mcRow", True)
        return host

    def _toggle_admin(self, user: AdminUser) -> None:
        self.run(
            lambda: self.shell.repo.admin_set_admin(user.id, not user.is_admin),
            lambda _: (self.shell.toast(
                "Admin removed" if user.is_admin else "Admin granted"), self.load()),
        )

    def _delete_user(self, user: AdminUser) -> None:
        if not confirm(self, "Delete user",
                       f"Permanently delete @{user.username} and their library?",
                       confirm_label="Delete"):
            return
        self.run(lambda: self.shell.repo.admin_delete_user(user.id),
                 lambda _: (self.shell.toast("User deleted"), self.load()))

    def _rescan(self) -> None:
        self.run(
            self.shell.repo.admin_scan,
            lambda result: self.shell.toast(f"{result[0]} tracks · {result[1]} albums"),
        )

    def _create_invite(self) -> None:
        note = prompt(self, "New invite code", "Note (optional)",
                      placeholder="For a friend", confirm="Create")
        if note is None:
            return
        self.run(lambda: self.shell.repo.admin_invite_create(1, 0, note),
                 lambda data: (QGuiApplication.clipboard().setText(str(data.get("code", ""))),
                               self.shell.toast("Invite code copied"), self.load()))

    def _render_invites(self, codes: list[dict]) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._invites_body)
        for i, code in enumerate(codes[:50]):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            copy = McButton("Copy", small=True, ghost=True)
            copy.clicked.connect(lambda _=False, c=code: QGuiApplication.clipboard().setText(
                str(c.get("code", ""))))
            revoke = IconButton("x", size=26, icon_size=14, tooltip="Revoke code")
            revoke.setEnabled(not code.get("expired") and not code.get("exhausted"))
            revoke.clicked.connect(lambda _=False, c=code: self.run(
                lambda: self.shell.repo.admin_invite_revoke(int(c.get("id") or 0)),
                lambda _: self.load()))
            line.addWidget(copy)
            line.addWidget(revoke)
            state = "expired" if code.get("expired") else (
                "used up" if code.get("exhausted") else "active")
            subtitle = (f"{code.get('uses', 0)}/{code.get('max_uses', 0)} uses · "
                        f"{code.get('note') or state}")
            self._invites_line.addWidget(self._row_widget(
                str(code.get("code", "")), subtitle, trailing, i == min(len(codes), 50) - 1))
        if not codes:
            self._invites_line.addWidget(self._row_widget(
                "No invite codes", "Create one to invite a friend", None, True))

    def _render_requests(self, rows: list[RequestRow]) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._requests_body)
        open_requests = McButton("Open queue", small=True, ghost=True,
                                 icon="arrow-up-right")
        open_requests.clicked.connect(lambda: self.shell.navigate(("requests",)))
        self._requests_line.addWidget(self._row_widget(
            f"{len(rows)} requests", "Approve, cancel, retry and read logs",
            open_requests, True))

    def _render_devices(self, devices: list[DeviceRow]) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._devices_body)
        open_devices = McButton("Open devices", small=True, ghost=True,
                                icon="arrow-up-right")
        open_devices.clicked.connect(lambda: self.shell.navigate(("devices",)))
        self._devices_line.addWidget(self._row_widget(
            f"{len(devices)} devices", "Rename, activate and revoke app passwords",
            open_devices, True))

    def _render_channels(self, channels: list[dict]) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._channels_body)
        for i, channel in enumerate(channels[:50]):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            unbind = McButton("Unbind", small=True, ghost=True, danger=True)
            unbind.clicked.connect(lambda _=False, c=channel: self.run(
                lambda: self.shell.api.delete(f"channels/{int(c.get('id') or 0)}"),
                lambda _: self.load()))
            line.addWidget(unbind)
            subtitle = (f"{channel.get('platform', 'chat')} · "
                        f"{channel.get('channel_id', '')}")
            self._channels_line.addWidget(self._row_widget(
                str(channel.get("name") or channel.get("id") or "channel"),
                subtitle, trailing, i == min(len(channels), 50) - 1))
        if not channels:
            self._channels_line.addWidget(self._row_widget(
                "No control channels", "Bot channels appear here when bound", None, True))

    def _render_rooms(self, rooms: list[dict]) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._rooms_body)
        for i, room in enumerate(rooms[:40]):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            close = McButton("Close", small=True, ghost=True, danger=True)
            close.clicked.connect(lambda _=False, r=room: self.run(
                lambda: self.shell.repo.admin_room_close(str(r.get("code", ""))),
                lambda _: self.load()))
            line.addWidget(close)
            track = room.get("track") or {}
            subtitle = (f"@{room.get('host', '?')} · "
                        f"{(track.get('title') if isinstance(track, dict) else '') or 'idle'}")
            self._rooms_line.addWidget(self._row_widget(
                str(room.get("code", "")), subtitle, trailing,
                i == min(len(rooms), 40) - 1))
        if not rooms:
            self._rooms_line.addWidget(self._row_widget(
                "No open rooms", "Listen-along rooms appear here", None, True))

    def _render_enrich(self, status: dict) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._jobs_body)
        status = status if isinstance(status, dict) else {}
        row = QWidget()
        line = QHBoxLayout(row)
        line.setContentsMargins(16, 12, 16, 12)
        line.setSpacing(8)
        line.addWidget(Txt(
            f"YouTube metadata: {status.get('linked', 0)}/{status.get('total', 0)} linked · "
            f"{status.get('fetched', 0)} fetched", size=14, token="on_surface_variant", wrap=True), 1)
        start = McButton("Refresh stats", small=True, ghost=True)
        start.clicked.connect(lambda: self.run(self.shell.repo.admin_enrich_start,
                                               lambda _: self.load()))
        force = McButton("Re-fetch all", small=True, ghost=True, danger=True)
        force.clicked.connect(lambda: self.run(
            lambda: self.shell.repo.admin_enrich_start(force=True),
            lambda _: (self.shell.toast("Metadata refresh queued"), self.load())))
        lyric = McButton("Fetch lyrics", small=True, ghost=True)
        lyric.clicked.connect(lambda: self.run(self.shell.repo.admin_lyrics_start,
                                               lambda _: (self.shell.toast(
                                                   "Lyrics fetch queued"), self.load())))
        for button in (start, force, lyric):
            line.addWidget(button)
        self._jobs_line.addWidget(row)

    def _render_lyrics(self, status: dict) -> None:
        if not isValid(self):
            return
        status = status if isinstance(status, dict) else {}
        row = QWidget()
        line = QHBoxLayout(row)
        line.setContentsMargins(16, 4, 16, 12)
        line.addWidget(Txt("Lyrics: " + ", ".join(
            f"{k}={v}" for k, v in list(status.items())[:4]
        ) or "no status", size=14, token="on_surface_variant", wrap=True))
        self._jobs_line.addWidget(row)


# ── downloads / cache ────────────────────────────────────────────────────────


class DownloadsScreen(Screen):
    """The local audio cache: files, bytes, pruning and removal."""

    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        from .player import cache_dir
        self._dir = cache_dir()
        head = PageHead("Downloads", "Server imports and local audio", "")
        seg = Segmented([("requests", "Requests"), ("device", "Your downloads")],
                        getattr(self, "tab", "device"))
        seg.changed.connect(self._switch)
        head.add_action(seg)
        refresh = McButton("Refresh", small=True, ghost=True, icon="refresh-cw")
        refresh.clicked.connect(self.load)
        head.add_action(refresh)
        self.add(head, 12)
        self.tab = getattr(self, "tab", "device")
        if self.tab == "requests":
            panel = Panel("Requests")
            open_requests = McButton("Open requests", small=True, ghost=True,
                                     icon="arrow-up-right")
            open_requests.clicked.connect(lambda: self.shell.navigate(("requests",)))
            panel.add_row(
                "Server imports", "YouTube and direct links are approved on the server",
                open_requests, last=True,
            )
            self.add(panel, 16)
            self.add(Txt("Approved imports appear in the library; saved tracks show up under "
                         "“Your downloads” on this device.", size=14, token="on_surface_variant", wrap=True))
            return

        from datetime import datetime
        files = []
        for p in sorted(self._dir.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True):
            if not p.is_file() or p.suffix == ".part":
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            files.append((p, st))
        total = sum(st.st_size for _, st in files)
        responses, _ = self.shell.store.cache_stats()

        panel = Panel("Storage")
        panel.add_row("Audio files", f"{len(files)} files · {fmt_bytes(total)}",
                      Txt("on this device", size=14, token="on_surface_variant"))
        panel.add_row("API responses", f"{responses} cached replies",
                      Txt("offline reads", size=14, token="on_surface_variant"))
        actions = QWidget()
        line = QHBoxLayout(actions)
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(6)
        prune = McButton("Prune old", small=True, ghost=True)
        prune.clicked.connect(self._prune)
        line.addWidget(prune)
        clear = McButton("Clear cache", small=True, danger=True, icon="trash-2")
        clear.clicked.connect(self._clear)
        line.addWidget(clear)
        folder = McButton("Open folder", small=True, ghost=True, icon="arrow-up-right")
        folder.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(self._dir))))
        line.addWidget(folder)
        panel.add_row("Maintenance", "Old files and oversized caches can be removed", actions,
                      last=True)
        self.add(panel, 16)

        panel = Panel("Cached tracks")
        if not files:
            panel.add_row("Nothing cached yet", "Tracks you play are kept here",
                          last=True)
        for index, (path, st) in enumerate(files[:200]):
            trailing = QWidget()
            row_line = QHBoxLayout(trailing)
            row_line.setContentsMargins(0, 0, 0, 0)
            row_line.setSpacing(6)
            row_line.addWidget(Txt(fmt_bytes(st.st_size), size=14, family="mono", token="on_surface_variant"))
            play = McButton("Play", small=True, ghost=True, icon="play")
            play.clicked.connect(lambda _=False, p=path: self._play_cached(p))
            row_line.addWidget(play)
            remove = IconButton("trash-2", size=26, icon_size=16, tooltip="Remove file")
            remove.clicked.connect(lambda _=False, p=path: self._remove(p))
            row_line.addWidget(remove)
            when = datetime.fromtimestamp(st.st_mtime).strftime("%d %b %Y")
            panel.add_row(path.stem, fmt_bytes(st.st_size) + " · " + when,
                          trailing, last=index == min(len(files), 200) - 1)
        self.add(panel, 16)
        self.add(Txt("Downloads are the same stream cache the player uses. Turning off "
                     "“Stream cache” in Settings discards files after playback.",
                     size=14, token="on_surface_variant", wrap=True))

    def _switch(self, tab: str) -> None:
        self.tab = tab
        self.load()

    def _play_cached(self, path) -> None:
        # Reuse the normal engine so MPRIS, activity and queue state stay in sync.
        try:
            track_id = int(path.stem.split(".")[0])
        except ValueError:
            return
        if track_id in (t.id for t in self.shell.player.queue):
            self.shell.player.jump(next(i for i, t in enumerate(self.shell.player.queue)
                                         if t.id == track_id))
            return
        self.run(
            lambda: self.shell.repo.find_track(track_id),
            lambda track: (
                self.shell.player.play([track], 0) if track is not None
                else self.shell.toast("Track details are not cached — open it from your library")
            ),
            lambda _exc: self.shell.toast("Track details are not cached — open it from your library"),
        )

    def _remove(self, path) -> None:
        try:
            path.unlink()
            self.shell.toast("Cache file removed")
        except OSError as exc:
            self.shell.toast(str(exc))
        self.load()

    def _prune(self) -> None:
        removed = self.shell.store.cache_prune()
        self.shell.toast(f"Pruned {removed} files")
        self.load()

    def _clear(self) -> None:
        if not confirm(self, "Clear cache",
                       "Remove cached audio and offline API replies? You will need a "
                       "connection to play those tracks again.", confirm_label="Clear"):
            return
        removed = self.shell.store.cache_clear()
        self.shell.toast(f"Cleared {removed} cached items")
        self.load()


# ── devices ──────────────────────────────────────────────────────────────────


class DevicesScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        head = PageHead("Devices", "Your signed-in players", "")
        refresh = McButton("Refresh", small=True, ghost=True, icon="refresh-cw")
        refresh.clicked.connect(self.load)
        head.add_action(refresh)
        pair = McButton("Pair device", small=True, icon="link")
        pair.clicked.connect(self._pair)
        head.add_action(pair)
        self.add(head, 12)
        self.loading("Reading devices…")
        self.run(self.shell.repo.devices, self._render_devices,
                 error=lambda _e: self.stop_loading())
        self.run(self.shell.repo.device_tokens, self._render_tokens,
                 error=lambda _e: None)

    def _render_devices(self, devices: list[DeviceRow]) -> None:
        self.stop_loading()
        panel = Panel("Registered devices")
        for index, device in enumerate(devices):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            line.setSpacing(6)
            if device.active:
                line.addWidget(StatusChip("active", "accent"))
            if not device.active:
                activate = McButton("Activate", small=True, ghost=True)
                activate.clicked.connect(lambda _=False, d=device: self._act(
                    lambda: self.shell.repo.device_activate(d.id), "Device activated"))
                line.addWidget(activate)
            rename = McButton("Rename", small=True, ghost=True)
            rename.clicked.connect(lambda _=False, d=device: self._rename(d))
            line.addWidget(rename)
            forget = IconButton("trash-2", size=26, icon_size=16, tooltip="Forget device")
            forget.clicked.connect(lambda _=False, d=device: self._forget(d))
            line.addWidget(forget)
            subtitle = (device.track_title or "No track") + (
                " — " + device.track_artist if device.track_artist else "")
            panel.add_row(device.name or device.device_hash[:12], subtitle, trailing,
                          last=index == len(devices) - 1)
        if not devices:
            panel.add_row("No devices yet", "Play something to register this app", last=True)
        self.add(panel, 16)

        panel = Panel("Maintenance")
        cleanup = McButton("Remove stale devices", small=True, ghost=True)
        cleanup.clicked.connect(lambda: self._act(
            self.shell.repo.devices_cleanup, "Stale devices removed"))
        panel.add_row("Cleanup", "Drop devices unseen for 30 days", cleanup)
        clear = McButton("Forget all devices", small=True, danger=True)
        clear.clicked.connect(self._clear_all)
        panel.add_row("Reset", "Remove every device for this account", clear, last=True)
        self.add(panel, 16)
        self.reset_scroll()

    def _render_tokens(self, tokens: list[dict]) -> None:
        panel = Panel("App passwords")
        for index, token in enumerate(tokens[:50]):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            revoke = McButton("Revoke", small=True, danger=True)
            token_id = token.get("id", token.get("device_id", 0))
            revoke.clicked.connect(lambda _=False, tid=token_id: self._act(
                lambda: self.shell.repo.device_token_revoke(int(tid)), "Token revoked"))
            line.addWidget(revoke)
            label = str(token.get("name") or token.get("prefix") or token.get("id") or "token")
            panel.add_row(label, "Long-lived native client credential", trailing,
                          last=index == min(len(tokens), 50) - 1)
        if not tokens:
            panel.add_row("No app passwords", "Pair a device to create one", last=True)
        self.add(panel, 16)

    def _act(self, fn, success: str) -> None:
        self.run(fn, lambda _: (self.shell.toast(success), self.load()))

    def _rename(self, device: DeviceRow) -> None:
        name = prompt(self, "Rename device", "Name", initial=device.name,
                      placeholder="Living room speaker", confirm="Rename")
        if name:
            self._act(lambda: self.shell.repo.device_rename(device.id, name),
                      "Device renamed")

    def _forget(self, device: DeviceRow) -> None:
        if confirm(self, "Forget device", f"Remove {device.name or 'this device'}?",
                   confirm_label="Forget"):
            self._act(lambda: self.shell.repo.device_forget(device.id), "Device forgotten")

    def _clear_all(self) -> None:
        if confirm(self, "Forget all devices", "Every device for this account will be "
                   "signed out. This app will re-register on its next heartbeat.",
                   confirm_label="Forget all"):
            self._act(self.shell.repo.devices_clear, "Devices cleared")

    def _pair(self) -> None:
        sheet = Sheet(self, "Pair a device")
        code_label = Txt("Asking the server for a code…", size=16, token="on_surface_variant", wrap=True)
        sheet.body.addWidget(code_label)
        hint = Txt("", size=14, token="on_surface_variant", wrap=True)
        sheet.body.addWidget(hint)

        def ok(data: dict) -> None:
            if not isinstance(data, dict):
                return
            code = str(data.get("code") or "")
            code_label.setText(code or "No code returned")
            hint.setText(str(data.get("hint") or ""))

        self.run(self.shell.repo.device_code, ok,
                 error=lambda e: code_label.setText(str(e)))

        enter = McButton("I have a code", small=True)
        sheet.body.addWidget(enter, 0, Qt.AlignmentFlag.AlignLeft)

        def claim() -> None:
            value = prompt(self, "Pair device", "One-time code", placeholder="XXXX-XXXX",
                           confirm="Sign in")
            if not value:
                return
            enter.setEnabled(False)

            def done(data: dict) -> None:
                token = str(data.get("token") or "")
                if not token:
                    self.shell.toast("That code could not be used")
                    enter.setEnabled(True)
                    return
                self.shell.api.set_token(token)
                me = self.shell.repo.me()
                sheet.accept()
                self.shell.after_login(me)
                self.shell.toast("Device paired")

            self.run(lambda: self.shell.repo.device_claim(value, "mcmusic desktop"),
                     done, error=lambda _e: enter.setEnabled(True))

        enter.clicked.connect(claim)
        sheet.exec()


# ── public listening ─────────────────────────────────────────────────────────


class ListeningScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        head = PageHead("Listening", "What your server is playing", "")
        refresh = McButton("Refresh", small=True, ghost=True, icon="refresh-cw")
        refresh.clicked.connect(self.load)
        head.add_action(refresh)
        self.add(head, 12)
        self.loading("Checking who is online…")
        self.run(self.shell.repo.public_listening,
                 lambda value: self._render(value[0], value[1]),
                 error=lambda _e: self.stop_loading())

    def _render(self, users: list[ListeningUser], base: str) -> None:
        self.stop_loading()
        panel = Panel("Recently active")
        for index, user in enumerate(users[:60]):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            line.addWidget(StatusChip("listening" if user.listening else "paused",
                                      "accent" if user.listening else "dim"))
            profile = McButton("Profile", small=True, ghost=True, icon="arrow-up-right")
            profile.clicked.connect(lambda _=False, u=user: self._profile(u.username))
            line.addWidget(profile)
            if user.track:
                sub = f"{user.track.title} · {user.track.artist}"
                if user.listening and user.track.duration:
                    sub += f" · {fmt_time(user.position)}/{fmt_time(user.track.duration)}"
            else:
                sub = "Nothing playing"
            panel.add_row(user.username, sub, trailing, last=index == min(len(users), 60) - 1)
        if not users:
            panel.add_row("Nobody listening right now",
                          "Devices appear here while they are active", last=True)
        self.add(panel, 16)
        if base:
            self.add(Txt("Public profiles: " + base + "/u/username",
                         size=14, family="mono", token="on_surface_variant", wrap=True))
        self.reset_scroll()

    def _profile(self, username: str) -> None:
        sheet = Sheet(self, "Profile")
        label = Txt("Loading " + username + "…", size=16, token="on_surface_variant", wrap=True)
        sheet.body.addWidget(label)
        open_web = McButton("Open profile", small=True, ghost=True, icon="arrow-up-right")
        open_web.setEnabled(False)
        sheet.body.addWidget(open_web, 0, Qt.AlignmentFlag.AlignLeft)

        def ok(data: dict) -> None:
            if not isinstance(data, dict):
                return
            track = data.get("track") or {}
            if isinstance(track, dict):
                label.setText(
                    f"{data.get('username', username)}\n"
                    f"{track.get('title', '')} — {track.get('artist', '')}\n"
                    f"{fmt_time(float(data.get('position') or 0))}"
                )
            else:
                label.setText(str(data.get("username") or username))
            url = str(data.get("profile_url") or "")
            if url:
                open_web.setEnabled(True)
                open_web.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

        self.run(lambda: self.shell.repo.public_now(username), ok,
                 error=lambda e: label.setText(str(e)))
        sheet.exec()
```

### `app/linux/mcmusic_linux/lyric_visualizer.py`

```python
"""A compact lyric-sheet visualizer for the Qt desktop client.

Pure PySide6. The animation is a deterministic function of the player's
reported ``position``; ``playing`` only decides whether repaints are needed.
No QtMultimedia objects are created or inspected beyond those two properties,
so opening the lyrics sheet never touches the local audio backend.

Colours come from the active palette, so macOS/Windows follow the same five
swatch-derived families as the web, Android and iOS clients.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QBrush, QColor, QFontMetrics, QPainter, QPainterPath, QPen,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from . import design, motion, theme


class LyricVisualizer(QWidget):
    """Small Bars / Wave / Rings panel driven by playback position."""

    MODES: tuple[str, ...] = ("Bars", "Wave", "Rings")

    def __init__(self, player, parent=None):
        super().__init__(parent)
        self._player = player
        self._mode = 0
        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Visualizer: Bars — click to cycle (Bars / Wave / Rings)")
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._on_timeout)

    # ── public API ───────────────────────────────────────────────────────
    @property
    def mode(self) -> str:
        return self.MODES[self._mode]

    def cycle_mode(self) -> str:
        self._mode = (self._mode + 1) % len(self.MODES)
        self.setToolTip(f"Visualizer: {self.mode} — click to cycle")
        self.update()
        return self.mode

    def stop(self) -> None:
        self._timer.stop()

    # ── player state (read-only) ─────────────────────────────────────────
    def _position(self) -> float:
        try:
            value = float(self._player.position)
        except (AttributeError, TypeError, ValueError):
            return 0.0
        return value if math.isfinite(value) and value > 0 else 0.0

    def _playing(self) -> bool:
        try:
            return bool(self._player.playing)
        except (AttributeError, TypeError, ValueError):
            return False

    def _on_timeout(self) -> None:
        # Position freezes with the media, so a paused track needs no redraws.
        if self._playing():
            self.update()

    # ── lifecycle ────────────────────────────────────────────────────────
    def showEvent(self, event) -> None:
        super().showEvent(event)
        if motion.enabled():
            self._timer.start()

    def hideEvent(self, event) -> None:
        self.stop()
        super().hideEvent(event)

    def closeEvent(self, event) -> None:
        self.stop()
        super().closeEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.cycle_mode()
            event.accept()
            return
        super().mousePressEvent(event)

    # ── painting ─────────────────────────────────────────────────────────
    def paintEvent(self, _event) -> None:
        palette = theme.pal()
        accent = QColor(palette.primary)
        line = QColor(palette.outline_variant)

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(palette.surface_container_low))
        p.drawRoundedRect(rect, design.Shape.card, design.Shape.card)

        t = self._position()
        if self._mode == 0:
            self._draw_bars(p, rect, t, accent, line)
        elif self._mode == 1:
            self._draw_wave(p, rect, t, accent)
        else:
            self._draw_rings(p, rect, t, accent)
        self._draw_chip(p, rect, palette)

    @staticmethod
    def _inner(rect: QRectF) -> QRectF:
        # Extra headroom keeps the mode chip clear of the animation.
        return rect.adjusted(12, 26, -12, 12)

    def _draw_bars(self, p: QPainter, rect: QRectF, t: float,
                   accent: QColor, line: QColor) -> None:
        inner = self._inner(rect)
        if inner.isEmpty():
            return
        count = 26
        gap = 3.0
        bar_w = max(1.5, (inner.width() - gap * (count - 1)) / count)
        base = inner.bottom()
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(count):
            a = math.sin(t * 2.17 + i * 0.53)
            b = math.sin(t * 0.91 - i * 0.29 + 1.1)
            c = math.sin(t * 3.31 + i * 0.11 + 2.4)
            energy = min(1.0, max(0.08, 0.42 + 0.28 * a + 0.18 * b + 0.10 * c))
            h = energy * inner.height() * 0.94
            x = inner.left() + i * (bar_w + gap)
            color = QColor(accent)
            color.setAlphaF(0.35 + 0.6 * energy)
            p.setBrush(color)
            p.drawRoundedRect(QRectF(x, base - h, bar_w, h), bar_w / 2, bar_w / 2)
        baseline = QColor(line)
        baseline.setAlpha(70)
        p.setPen(QPen(baseline, 1))
        p.drawLine(QPointF(inner.left(), base + 1), QPointF(inner.right(), base + 1))

    def _draw_wave(self, p: QPainter, rect: QRectF, t: float,
                   accent: QColor) -> None:
        inner = self._inner(rect)
        if inner.isEmpty():
            return
        mid = inner.center().y()
        amp = inner.height() * 0.32
        steps = max(32, int(inner.width() / 4))

        def wave(u: float, phase: float) -> float:
            return (
                0.60 * math.sin(u * math.tau * 2.0 + t * 2.0 + phase)
                + 0.28 * math.sin(u * math.tau * 5.0 - t * 1.3 + phase * 0.5)
                + 0.12 * math.sin(u * math.tau * 9.0 + t * 0.7 - phase)
            )

        p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        for phase, alpha, width in ((0.0, 205, 2.2), (1.35, 78, 1.4)):
            path = QPainterPath()
            for step in range(steps + 1):
                u = step / steps
                x = inner.left() + inner.width() * u
                y = mid + amp * wave(u, phase)
                if step == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            color = QColor(accent)
            color.setAlpha(alpha)
            p.setPen(QPen(color, width))
            p.drawPath(path)

    def _draw_rings(self, p: QPainter, rect: QRectF, t: float,
                    accent: QColor) -> None:
        inner = self._inner(rect)
        if inner.isEmpty():
            return
        center = QPointF(inner.center().x(), inner.center().y())
        pulse = 0.5 + 0.5 * math.sin(t * 1.7)
        base = min(inner.width(), inner.height()) * (0.22 + 0.06 * pulse)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for ring in range(4):
            radius = base * (1.0 + ring * 0.62)
            color = QColor(accent)
            color.setAlphaF(0.30 * (1.0 - ring / 4.0) * (0.65 + 0.35 * pulse))
            p.setPen(QPen(color, 1.5))
            p.drawEllipse(center, radius, radius)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(accent)
        dot = 3.5 + 2.0 * pulse
        p.drawEllipse(center, dot, dot)

    def _draw_chip(self, p: QPainter, rect: QRectF, palette) -> None:
        label = f"{self.mode.upper()} >"
        font = design.font("label", size=12)
        p.setFont(font)
        width = QFontMetrics(font).horizontalAdvance(label) + 24
        chip = QRectF(rect.right() - 12 - width, rect.top() + 8, width, 28)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(palette.primary_container))
        p.drawRoundedRect(chip, chip.height() / 2, chip.height() / 2)
        p.setPen(QPen(QColor(palette.on_primary_container)))
        p.drawText(chip, int(Qt.AlignmentFlag.AlignCenter), label)
```
