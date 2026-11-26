"""Inline Lucide geometry — byte-for-byte the same paths as web/js/icons.js.

Rendered through QtSvg at paint time, so icons stay crisp on any scale factor
and need no icon font or network access. Unknown names fall back to a real icon
instead of an empty box, exactly like the web client.
"""
from __future__ import annotations

import re
from functools import lru_cache

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer

# ── appearance state ────────────────────────────────────────────────────────
# The same 1x / 1.5x / 2x preference as web and iOS. It is process-wide so
# custom-painted widgets pick it up on their next repaint without rebuilding
# the whole widget tree.
_STROKE_CHOICES = (1.0, 1.5, 2.0)
_ACTIVE_STROKE = 1.0
_ACTIVE_FILLED = False


def nearest_stroke(value) -> float:
    """Snap stored or hand-edited values onto the three allowed widths."""
    try:
        scale = float(value)
    except (TypeError, ValueError):
        return 1.0
    return min(_STROKE_CHOICES, key=lambda choice: abs(choice - scale))


def set_icon_style(stroke=1.0, filled=False) -> None:
    global _ACTIVE_STROKE, _ACTIVE_FILLED
    _ACTIVE_STROKE = nearest_stroke(stroke)
    _ACTIVE_FILLED = bool(filled)


def icon_style() -> tuple[float, bool]:
    return _ACTIVE_STROKE, _ACTIVE_FILLED


def stroke_width(scale: float, size: float) -> float:
    """Logical-pixel stroke for a Lucide icon drawn at ``size``.

    Lucide uses a 24-unit viewBox and a standard stroke of 2, so scale
    1/1.5/2 renders at 2/3/4 viewBox units (`size * scale / 12` pixels). The
    `size / 6` ceiling keeps 2x from crowding small icons; there is no pixel
    floor, so 1x stays at Lucide's default weight.
    """
    size = max(1.0, float(size))
    base = size * float(scale) / 12.0
    return min(base, size / 6.0)


def _viewbox_stroke(scale: float, size: float) -> float:
    """Convert the logical-pixel clamp into the renderer's 24-unit grid."""
    size = max(1.0, float(size))
    return stroke_width(scale, size) * 24.0 / size


# ── brand mark ──────────────────────────────────────────────────────────────
# The same mc line art as web/icon.svg, the Android launcher and this app's
# .desktop icon. Paths stay in the artwork's own coordinate space.
_MARK_OX, _MARK_OY = 233.8494, 173.57593
_MARK_W, _MARK_H = 10.06066, 12.84814
_MARK_D = [
    ("M241.7789,178.22582v4.34377", "round"),
    ("M243.66006,182.56958c0,0.31168 -0.42111,0.56435 -0.94058,0.56435c-0.51947,0 "
     "-0.94058,-0.25267 -0.94058,-0.56435c0,-0.31168 0.42111,-0.56435 0.94058,-0.56435"
     "c0.51947,0 0.94058,0.25267 0.94058,0.56435z", "butt"),
    ("M239.05942,178.22582v4.34377", "round"),
    ("M240.94058,182.56958c0,0.31168 -0.4211,0.56435 -0.94057,0.56435c-0.51947,0 "
     "-0.94058,-0.25267 -0.94058,-0.56435c0,-0.31168 0.42111,-0.56435 0.94058,-0.56435"
     "c0.51947,0 0.94057,0.25267 0.94057,0.56435z", "butt"),
    ("M236.33994,178.22582c0,-0.75097 0.60878,-1.35974 1.35974,-1.35974"
     "c0.75097,0 1.35974,0.60877 1.35974,1.35974", "butt"),
    ("M236.33994,178.22582v4.34377", "round"),
    ("M238.2211,182.56958c0,0.31168 -0.4211,0.56435 -0.94057,0.56435c-0.51947,0 "
     "-0.94058,-0.25267 -0.94058,-0.56435c0,-0.31168 0.42111,-0.56435 0.94058,-0.56435"
     "c0.51947,0 0.94057,0.25267 0.94057,0.56435z", "butt"),
    ("M239.05942,178.22582c0,-0.75097 0.60877,-1.35974 1.35974,-1.35974"
     "c0.75097,0 1.35974,0.60877 1.35974,1.35974", "butt"),
    ("M243.08703,186.17407c-4.96374,0 -8.98764,-2.76422 -8.98764,-6.17407"
     "c0,-3.40985 4.02389,-6.17407 8.98764,-6.17407", "butt"),
]


@lru_cache(maxsize=None)
def _mark_paths() -> tuple:
    """Parse the SVG subset (M/m, L/l, V/v, C/c, Z) into QPainterPaths."""
    paths = []
    for d, cap in _MARK_D:
        tokens = re.findall(r"[MLVCZmlvcz]|-?\d*\.?\d+", d)
        path = QPainterPath()
        cur = (0.0, 0.0)
        cmd = ""
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok.isalpha():
                cmd = tok
                i += 1
                continue
            if cmd in "Mm":
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == "m":
                    x, y = cur[0] + x, cur[1] + y
                path.moveTo(x, y)
                cur = (x, y)
                cmd = "L" if cmd == "M" else "l"
            elif cmd in "Ll":
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == "l":
                    x, y = cur[0] + x, cur[1] + y
                path.lineTo(x, y)
                cur = (x, y)
            elif cmd in "Vv":
                y = float(tokens[i])
                i += 1
                y = y if cmd == "V" else cur[1] + y
                path.lineTo(cur[0], y)
                cur = (cur[0], y)
            elif cmd in "Cc":
                vals = [float(v) for v in tokens[i:i + 6]]
                i += 6
                if cmd == "c":
                    vals = [v + cur[k % 2] for k, v in enumerate(vals)]
                path.cubicTo(*vals)
                cur = (vals[4], vals[5])
            elif cmd in "Zz":
                path.closeSubpath()
            else:
                break
        paths.append((path, cap))
    return tuple(paths)


def draw_mark(p: QPainter, rect: QRectF, color, stroke: float | None = None) -> None:
    """Paint the mc mark, centred and aspect-correct, inside *rect*."""
    s = rect.height() / _MARK_H
    x = rect.x() + (rect.width() - _MARK_W * s) / 2
    y = rect.y() + (rect.height() - _MARK_H * s) / 2
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.translate(x, y)
    p.scale(s, s)
    p.translate(-_MARK_OX, -_MARK_OY)
    width = 0.5 if stroke is None else stroke / s
    for path, cap in _mark_paths():
        pen = QPen(QColor(color))
        pen.setWidthF(width)
        pen.setCapStyle(
            Qt.PenCapStyle.RoundCap if cap == "round" else Qt.PenCapStyle.FlatCap
        )
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        pen.setMiterLimit(10)
        p.setPen(pen)
        p.drawPath(path)
    p.restore()
# BEGIN GENERATED ICONS
PATHS = {
    "album": "<circle cx=\"12\" cy=\"12\" r=\"10\"/><path d=\"M6 12c0-1.7.7-3.2 1.8-4.2\"/><circle cx=\"12\" cy=\"12\" r=\"2\"/><path d=\"M18 12c0 1.7-.7 3.2-1.8 4.2\"/>",
    "arrow-left": "<path d=\"m12 19-7-7 7-7\"/><path d=\"M19 12H5\"/>",
    "arrow-up-right": "<path d=\"M7 7h10v10\"/><path d=\"M7 17 17 7\"/>",
    "audio-lines": "<path d=\"M2 10v3\"/><path d=\"M6 6v11\"/><path d=\"M10 3v18\"/><path d=\"M14 8v7\"/><path d=\"M18 5v13\"/><path d=\"M22 10v3\"/>",
    "cast": "<path d=\"M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6\"/><path d=\"M2 12a9 9 0 0 1 8 8\"/><path d=\"M2 16a5 5 0 0 1 4 4\"/><path d=\"M2 20L2.01 20\"/>",
    "check": "<path d=\"M20 6 9 17l-5-5\"/>",
    "chevron-down": "<path d=\"m6 9 6 6 6-6\"/>",
    "chevron-left": "<path d=\"m15 18-6-6 6-6\"/>",
    "chevron-right": "<path d=\"m9 18 6-6-6-6\"/>",
    "chevron-up": "<path d=\"m18 15-6-6-6 6\"/>",
    "circle": "<circle cx=\"12\" cy=\"12\" r=\"10\"/>",
    "circle_help": "<circle cx=\"12\" cy=\"12\" r=\"10\"/><path d=\"M9 9.5a3 2.5 0 016 0c0 2-2 2-3 3.5\"/><path d=\"M12 17h.01\"/>",
    "circle-alert": "<circle cx=\"12\" cy=\"12\" r=\"10\"/><path d=\"M12 8L12 12\"/><path d=\"M12 16L12.01 16\"/>",
    "circle-check": "<circle cx=\"12\" cy=\"12\" r=\"10\"/><path d=\"m16 9-5.5 5.5L8 12\"/>",
    "circle-help": "<circle cx=\"12\" cy=\"12\" r=\"10\"/><path d=\"M9 9.5a3 2.5 0 016 0c0 2-2 2-3 3.5\"/><path d=\"M12 17h.01\"/>",
    "circle-x": "<circle cx=\"12\" cy=\"12\" r=\"10\"/><path d=\"m15 9-6 6\"/><path d=\"m9 9 6 6\"/>",
    "clock": "<circle cx=\"12\" cy=\"12\" r=\"10\"/><path d=\"M12 6v6l4 2\"/>",
    "cloud-download": "<path d=\"M12 13v8l-4-4\"/><path d=\"m12 21 4-4\"/><path d=\"M4.393 15.269A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.436 8.284\"/>",
    "coffee": "<path d=\"M10 2v2\"/><path d=\"M14 2v2\"/><path d=\"M16 8a1 1 0 0 1 1 1v8a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9a1 1 0 0 1 1-1h14a4 4 0 1 1 0 8h-1\"/><path d=\"M6 2v2\"/>",
    "compass": "<circle cx=\"12\" cy=\"12\" r=\"10\"/><path d=\"m16.24 7.76-1.804 5.411a2 2 0 0 1-1.265 1.265L7.76 16.24l1.804-5.411a2 2 0 0 1 1.265-1.265z\"/>",
    "cookie": "<path d=\"M11 17h.01\"/><path d=\"M11.496 2c.324-.016.558.292.529.615a4 4 0 004.235 4.368.713.713 0 01.758.757 4 4 0 004.366 4.237c.323-.03.63.204.614.527a10 10 0 01-2.915 6.566A1 1 0 114.93 4.918 10 10 0 0111.496 2\"/><path d=\"M12 12h.01\"/><path d=\"M16 16h.01\"/><path d=\"M16 3h.01\"/><path d=\"M21 4h.01\"/><path d=\"M21 8h.01\"/><path d=\"M7 14h.01\"/><path d=\"M9 8h.01\"/>",
    "disc-3": "<circle cx=\"12\" cy=\"12\" r=\"10\"/><path d=\"M6 12c0-1.7.7-3.2 1.8-4.2\"/><circle cx=\"12\" cy=\"12\" r=\"2\"/><path d=\"M18 12c0 1.7-.7 3.2-1.8 4.2\"/>",
    "download": "<path d=\"M12 15V3\"/><path d=\"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4\"/><path d=\"m7 10 5 5 5-5\"/>",
    "dumbbell": "<path d=\"M17.596 12.768a2 2 0 1 0 2.829-2.829l-1.768-1.767a2 2 0 0 0 2.828-2.829l-2.828-2.828a2 2 0 0 0-2.829 2.828l-1.767-1.768a2 2 0 1 0-2.829 2.829z\"/><path d=\"m2.5 21.5 1.4-1.4\"/><path d=\"m20.1 3.9 1.4-1.4\"/><path d=\"M5.343 21.485a2 2 0 1 0 2.829-2.828l1.767 1.768a2 2 0 1 0 2.829-2.829l-6.364-6.364a2 2 0 1 0-2.829 2.829l1.768 1.767a2 2 0 0 0-2.828 2.829z\"/><path d=\"m9.6 14.4 4.8-4.8\"/>",
    "ellipsis": "<circle cx=\"12\" cy=\"12\" r=\"1\"/><circle cx=\"19\" cy=\"12\" r=\"1\"/><circle cx=\"5\" cy=\"12\" r=\"1\"/>",
    "eye-off": "<path d=\"M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49\"/><path d=\"M14.084 14.158a3 3 0 0 1-4.242-4.242\"/><path d=\"M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143\"/><path d=\"m2 2 20 20\"/>",
    "film": "<rect x=\"3\" y=\"3\" width=\"18\" height=\"18\" rx=\"2\"/><path d=\"M7 3v18\"/><path d=\"M3 7.5h4\"/><path d=\"M3 12h18\"/><path d=\"M3 16.5h4\"/><path d=\"M17 3v18\"/><path d=\"M17 7.5h4\"/><path d=\"M17 16.5h4\"/>",
    "flame": "<path d=\"M12 3q1 4 4 6.5t3 5.5a1 1 0 0 1-14 0 5 5 0 0 1 1-3 1 1 0 0 0 5 0c0-2-1.5-3-1.5-5q0-2 2.5-4\"/>",
    "flower": "<circle cx=\"12\" cy=\"12\" r=\"3\"/><path d=\"M12 16.5A4.5 4.5 0 1 1 7.5 12 4.5 4.5 0 1 1 12 7.5a4.5 4.5 0 1 1 4.5 4.5 4.5 4.5 0 1 1-4.5 4.5\"/><path d=\"M12 7.5V9\"/><path d=\"M7.5 12H9\"/><path d=\"M16.5 12H15\"/><path d=\"M12 16.5V15\"/><path d=\"m8 8 1.88 1.88\"/><path d=\"M14.12 9.88 16 8\"/><path d=\"m8 16 1.88-1.88\"/><path d=\"M14.12 14.12 16 16\"/>",
    "folder-plus": "<path d=\"M12 10v6\"/><path d=\"M9 13h6\"/><path d=\"M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z\"/>",
    "grip-vertical": "<circle cx=\"9\" cy=\"12\" r=\"1\"/><circle cx=\"9\" cy=\"5\" r=\"1\"/><circle cx=\"9\" cy=\"19\" r=\"1\"/><circle cx=\"15\" cy=\"12\" r=\"1\"/><circle cx=\"15\" cy=\"5\" r=\"1\"/><circle cx=\"15\" cy=\"19\" r=\"1\"/>",
    "hard-drive": "<path d=\"M10 16h.01\"/><path d=\"M2.212 11.577a2 2 0 0 0-.212.896V18a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5.527a2 2 0 0 0-.212-.896L18.55 5.11A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z\"/><path d=\"M21.946 12.013H2.054\"/><path d=\"M6 16h.01\"/>",
    "headphones": "<path d=\"M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3\"/>",
    "heart": "<path d=\"M2 9.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5\"/>",
    "home": "<path d=\"M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8\"/><path d=\"M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z\"/>",
    "house": "<path d=\"M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8\"/><path d=\"M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z\"/>",
    "image": "<rect x=\"3\" y=\"3\" width=\"18\" height=\"18\" rx=\"2\"/><circle cx=\"9\" cy=\"9\" r=\"2\"/><path d=\"m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21\"/>",
    "inbox": "<path d=\"M22 12L16 12L14 15L10 15L8 12L2 12\"/><path d=\"M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z\"/>",
    "info": "<circle cx=\"12\" cy=\"12\" r=\"10\"/><path d=\"M12 16v-4\"/><path d=\"M12 8h.01\"/>",
    "key": "<path d=\"m2 21 9.6-9.6\"/><path d=\"m7.5 15.5 2.3 2.3a1 1 0 0 1 0 1.4l-2.1 2.1a1 1 0 0 1-1.4 0L4 19\"/><circle cx=\"15.5\" cy=\"7.5\" r=\"5.5\"/>",
    "library": "<path d=\"m16 6 4 14\"/><path d=\"M12 6v14\"/><path d=\"M8 8v12\"/><path d=\"M4 4v16\"/>",
    "link": "<path d=\"M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71\"/><path d=\"M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71\"/>",
    "list": "<path d=\"M3 5h.01\"/><path d=\"M3 12h.01\"/><path d=\"M3 19h.01\"/><path d=\"M8 5h13\"/><path d=\"M8 12h13\"/><path d=\"M8 19h13\"/>",
    "list-music": "<path d=\"M16 5H3\"/><path d=\"M11 12H3\"/><path d=\"M11 19H3\"/><path d=\"M21 16V5\"/><circle cx=\"18\" cy=\"16\" r=\"3\"/>",
    "list-plus": "<path d=\"M16 5H3\"/><path d=\"M11 12H3\"/><path d=\"M16 19H3\"/><path d=\"M18 9v6\"/><path d=\"M21 12h-6\"/>",
    "loader-circle": "<path d=\"M21 12a9 9 0 1 1-6.219-8.56\"/>",
    "lock": "<rect x=\"3\" y=\"11\" width=\"18\" height=\"11\" rx=\"2\"/><path d=\"M7 11V7a5 5 0 0 1 10 0v4\"/>",
    "log-in": "<path d=\"m10 17 5-5-5-5\"/><path d=\"M15 12H3\"/><path d=\"M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4\"/>",
    "log-out": "<path d=\"m16 17 5-5-5-5\"/><path d=\"M21 12H9\"/><path d=\"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4\"/>",
    "mail": "<path d=\"m22 7-8.991 5.727a2 2 0 0 1-2.009 0L2 7\"/><rect x=\"2\" y=\"4\" width=\"20\" height=\"16\" rx=\"2\"/>",
    "message-circle": "<path d=\"M2.992 16.342a2 2 0 0 1 .094 1.167l-1.065 3.29a1 1 0 0 0 1.236 1.168l3.413-.998a2 2 0 0 1 1.099.092 10 10 0 1 0-4.777-4.719\"/>",
    "mic-vocal": "<path d=\"m11 7.601-5.994 8.19a1 1 0 0 0 .1 1.298l.817.818a1 1 0 0 0 1.314.087L15.09 12\"/><path d=\"M16.5 21.174C15.5 20.5 14.372 20 13 20c-2.058 0-3.928 2.356-6 2-2.072-.356-2.775-3.369-1.5-4.5\"/><circle cx=\"16\" cy=\"7\" r=\"5\"/>",
    "monitor": "<rect x=\"2\" y=\"3\" width=\"20\" height=\"14\" rx=\"2\"/><path d=\"M8 21L16 21\"/><path d=\"M12 17L12 21\"/>",
    "moon": "<path d=\"M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401\"/>",
    "more-horizontal": "<circle cx=\"12\" cy=\"12\" r=\"1\"/><circle cx=\"19\" cy=\"12\" r=\"1\"/><circle cx=\"5\" cy=\"12\" r=\"1\"/>",
    "more-vertical": "<circle cx=\"12\" cy=\"12\" r=\"1\"/><circle cx=\"12\" cy=\"5\" r=\"1\"/><circle cx=\"12\" cy=\"19\" r=\"1\"/>",
    "music": "<path d=\"M21 16V3a1 1 0 0 0-1.28-.96l-10 2.917a1 1 0 0 0-.72.96V19\"/><circle cx=\"18\" cy=\"16\" r=\"3\"/><circle cx=\"6\" cy=\"19\" r=\"3\"/>",
    "music-note": "<path d=\"M21 16V3a1 1 0 0 0-1.28-.96l-10 2.917a1 1 0 0 0-.72.96V19\"/><circle cx=\"18\" cy=\"16\" r=\"3\"/><circle cx=\"6\" cy=\"19\" r=\"3\"/>",
    "palette": "<path d=\"M12 22a1 1 0 0 1 0-20 10 9 0 0 1 10 9 5 5 0 0 1-5 5h-2.25a1.75 1.75 0 0 0-1.4 2.8l.3.4a1.75 1.75 0 0 1-1.4 2.8z\"/><circle cx=\"13.5\" cy=\"6.5\" r=\"0.5\"/><circle cx=\"17.5\" cy=\"10.5\" r=\"0.5\"/><circle cx=\"6.5\" cy=\"12.5\" r=\"0.5\"/><circle cx=\"8.5\" cy=\"7.5\" r=\"0.5\"/>",
    "pause": "<rect x=\"14\" y=\"3\" width=\"5\" height=\"18\" rx=\"1\" fill=\"currentColor\" stroke=\"none\"/><rect x=\"5\" y=\"3\" width=\"5\" height=\"18\" rx=\"1\" fill=\"currentColor\" stroke=\"none\"/>",
    "pencil": "<path d=\"M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z\"/><path d=\"m15 5 4 4\"/>",
    "pentagon": "<path d=\"M10.83 2.38a2 2 0 0 1 2.34 0l8 5.74a2 2 0 0 1 .73 2.25l-3.04 9.26a2 2 0 0 1-1.9 1.37H7.04a2 2 0 0 1-1.9-1.37L2.1 10.37a2 2 0 0 1 .73-2.25z\"/>",
    "picture-in-picture-2": "<path d=\"M21 9V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v10c0 1.1.9 2 2 2h4\"/><rect x=\"12\" y=\"13\" width=\"10\" height=\"7\" rx=\"2\"/>",
    "pin": "<path d=\"M12 17v5\"/><path d=\"M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z\"/>",
    "play": "<path d=\"M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z\" fill=\"currentColor\" stroke=\"none\"/>",
    "plus": "<path d=\"M5 12h14\"/><path d=\"M12 5v14\"/>",
    "radio": "<path d=\"M16.247 7.761a6 6 0 0 1 0 8.478\"/><path d=\"M19.075 4.933a10 10 0 0 1 0 14.134\"/><path d=\"M4.925 19.067a10 10 0 0 1 0-14.134\"/><path d=\"M7.753 16.239a6 6 0 0 1 0-8.478\"/><circle cx=\"12\" cy=\"12\" r=\"2\"/>",
    "refresh-cw": "<path d=\"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8\"/><path d=\"M21 3v5h-5\"/><path d=\"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16\"/><path d=\"M8 16H3v5\"/>",
    "repeat": "<path d=\"m17 2 4 4-4 4\"/><path d=\"M3 11v-1a4 4 0 0 1 4-4h14\"/><path d=\"m7 22-4-4 4-4\"/><path d=\"M21 13v1a4 4 0 0 1-4 4H3\"/>",
    "repeat-1": "<path d=\"m17 2 4 4-4 4\"/><path d=\"M3 11v-1a4 4 0 0 1 4-4h14\"/><path d=\"m7 22-4-4 4-4\"/><path d=\"M21 13v1a4 4 0 0 1-4 4H3\"/><path d=\"M11 10h1v4\"/>",
    "search": "<path d=\"m21 21-4.34-4.34\"/><circle cx=\"11\" cy=\"11\" r=\"8\"/>",
    "server": "<rect x=\"2\" y=\"2\" width=\"20\" height=\"8\" rx=\"2\"/><rect x=\"2\" y=\"14\" width=\"20\" height=\"8\" rx=\"2\"/><path d=\"M6 6L6.01 6\"/><path d=\"M6 18L6.01 18\"/>",
    "settings": "<path d=\"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915\"/><circle cx=\"12\" cy=\"12\" r=\"3\"/>",
    "shield": "<path d=\"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z\"/>",
    "shield-alert": "<path d=\"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z\"/><path d=\"M12 8v4\"/><path d=\"M12 16h.01\"/>",
    "shield-check": "<path d=\"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z\"/><path d=\"m9 12 2 2 4-4\"/>",
    "shuffle": "<path d=\"m18 14 4 4-4 4\"/><path d=\"m18 2 4 4-4 4\"/><path d=\"M2 18h1.973a4 4 0 0 0 3.3-1.7l5.454-8.6a4 4 0 0 1 3.3-1.7H22\"/><path d=\"M2 6h1.972a4 4 0 0 1 3.6 2.2\"/><path d=\"M22 18h-6.041a4 4 0 0 1-3.3-1.8l-.359-.45\"/>",
    "skip-back": "<path d=\"M17.971 4.285A2 2 0 0 1 21 6v12a2 2 0 0 1-3.029 1.715l-9.997-5.998a2 2 0 0 1-.003-3.432z\" fill=\"currentColor\" stroke=\"none\"/><path d=\"M3 20V4\" fill=\"currentColor\" stroke=\"none\"/>",
    "skip-forward": "<path d=\"M21 4v16\" fill=\"currentColor\" stroke=\"none\"/><path d=\"M6.029 4.285A2 2 0 0 0 3 6v12a2 2 0 0 0 3.029 1.715l9.997-5.998a2 2 0 0 0 .003-3.432z\" fill=\"currentColor\" stroke=\"none\"/>",
    "smartphone": "<rect x=\"5\" y=\"2\" width=\"14\" height=\"20\" rx=\"2\"/><path d=\"M12 18h.01\"/>",
    "sparkles": "<path d=\"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z\"/><path d=\"M20 2v4\"/><path d=\"M22 4h-4\"/><circle cx=\"4\" cy=\"20\" r=\"2\"/>",
    "square-check": "<rect x=\"3\" y=\"3\" width=\"18\" height=\"18\" rx=\"2\"/><path d=\"m16 9-5.5 5.5L8 12\"/>",
    "squircle": "<path d=\"M12 3c7.2 0 9 1.8 9 9s-1.8 9-9 9-9-1.8-9-9 1.8-9 9-9\"/>",
    "star": "<path d=\"M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z\"/>",
    "text": "<path d=\"M12 4v16\"/><path d=\"M4 7V5a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v2\"/><path d=\"M9 20h6\"/>",
    "trash": "<path d=\"M10 11v6\"/><path d=\"M14 11v6\"/><path d=\"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6\"/><path d=\"M3 6h18\"/><path d=\"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2\"/>",
    "trash-2": "<path d=\"M10 11v6\"/><path d=\"M14 11v6\"/><path d=\"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6\"/><path d=\"M3 6h18\"/><path d=\"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2\"/>",
    "triangle-alert": "<path d=\"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3\"/><path d=\"M12 9v4\"/><path d=\"M12 17h.01\"/>",
    "tv-2": "<path d=\"M7 21h10\"/><rect x=\"2\" y=\"3\" width=\"20\" height=\"14\" rx=\"2\"/>",
    "unlink": "<path d=\"m18.84 12.25 1.72-1.71h-.02a5.004 5.004 0 0 0-.12-7.07 5.006 5.006 0 0 0-6.95 0l-1.72 1.71\"/><path d=\"m5.17 11.75-1.71 1.71a5.004 5.004 0 0 0 .12 7.07 5.006 5.006 0 0 0 6.95 0l1.71-1.71\"/><path d=\"M8 2L8 5\"/><path d=\"M2 8L5 8\"/><path d=\"M16 19L16 22\"/><path d=\"M19 16L22 16\"/>",
    "user": "<circle cx=\"12\" cy=\"8\" r=\"5\"/><path d=\"M20 21a8 8 0 0 0-16 0\"/>",
    "user-round": "<circle cx=\"12\" cy=\"8\" r=\"5\"/><path d=\"M20 21a8 8 0 0 0-16 0\"/>",
    "users": "<path d=\"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2\"/><path d=\"M16 3.128a4 4 0 0 1 0 7.744\"/><path d=\"M22 21v-2a4 4 0 0 0-3-3.87\"/><circle cx=\"9\" cy=\"7\" r=\"4\"/>",
    "volume-1": "<path d=\"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z\"/><path d=\"M16 9a5 5 0 0 1 0 6\"/>",
    "volume-2": "<path d=\"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z\"/><path d=\"M16 9a5 5 0 0 1 0 6\"/><path d=\"M19.364 18.364a9 9 0 0 0 0-12.728\"/>",
    "volume-x": "<path d=\"M11 4.702a.7.7 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.7.7 0 0 0 11 19.298z\"/><path d=\"m16.5 14.5 5-5\"/><path d=\"m16.5 9.5 5 5\"/>",
    "wifi": "<path d=\"M12 20h.01\"/><path d=\"M2 8.82a15 15 0 0 1 20 0\"/><path d=\"M5 12.859a10 10 0 0 1 14 0\"/><path d=\"M8.5 16.429a5 5 0 0 1 7 0\"/>",
    "wifi-off": "<path d=\"M12 20h.01\"/><path d=\"M8.5 16.429a5 5 0 0 1 7 0\"/><path d=\"M5 12.859a10 10 0 0 1 5.17-2.69\"/><path d=\"M19 12.859a10 10 0 0 0-2.007-1.523\"/><path d=\"M2 8.82a15 15 0 0 1 4.177-2.643\"/><path d=\"M22 8.82a15 15 0 0 0-11.288-3.764\"/><path d=\"m2 2 20 20\"/>",
    "x": "<path d=\"M18 6 6 18\"/><path d=\"m6 6 12 12\"/>",
    "zap": "<path d=\"M15.914 4a1.5 1.5 0 00-2.474-1.561l-9 9A1.5 1.5 0 005.5 14h4.002a.5.5 0 01.471.666L8.086 20a1.5 1.5 0 002.475 1.56l9-9A1.5 1.5 0 0018.5 10h-3.997a.5.5 0 01-.472-.667z\"/>",
}
# END GENERATED ICONS

FALLBACK_ICON = "circle-help"


_SHAPE_TAG = re.compile(r"<(rect|circle)\b([^>]*?)(/?)>")


def _body(name: str, color: str, shape_fill: bool) -> str:
    """Colour a glyph, optionally filling only its rect/circle primitives."""
    key = name if name in PATHS else FALLBACK_ICON
    body = PATHS[key].replace("currentColor", color)
    if not shape_fill:
        return body

    def fill_shape(match):
        tag, attrs, slash = match.group(1), match.group(2), match.group(3)
        # Explicitly filled primitives (play, pause, the dot menus) are already
        # correct; never override them with a competing stroke.
        if "fill=" in attrs:
            return match.group(0)
        return f'<{tag}{attrs} fill="{color}" stroke="none"{slash}>'

    return _SHAPE_TAG.sub(fill_shape, body)


def _build_svg(name: str, color: str, fill: bool, stroke: float,
               shape_fill: bool) -> str:
    """Pure SVG builder, shared by the renderer and the unit tests."""
    paint = color if fill else "none"
    line = "none" if fill else color
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'width="24" height="24" fill="{paint}" stroke="{line}" '
        f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">'
        f"{_body(name, color, shape_fill)}</svg>"
    )


@lru_cache(maxsize=512)
def _renderer(name: str, color: str, fill: bool, stroke: float,
              shape_fill: bool) -> QSvgRenderer:
    return QSvgRenderer(QByteArray(
        _build_svg(name, color, fill, stroke, shape_fill).encode("utf-8")
    ))


def draw_icon(painter: QPainter, name: str, rect: QRectF, color: str,
              stroke: float | None = None, fill: bool = False) -> None:
    """Render an icon into ``rect`` with the current painter.

    A ``None`` stroke derives the width from the widget's logical size and the
    active appearance setting. Pass a number only for artwork that deliberately
    owns its own width (the brand mark is handled separately).
    """
    scale, active_filled = icon_style()
    width = _viewbox_stroke(scale, max(rect.width(), rect.height())) \
        if stroke is None else float(stroke)
    r = _renderer(name, str(color), bool(fill), width, active_filled)
    if r.isValid():
        r.render(painter, QRectF(rect))


def pixmap(name: str, size: int, color: str, fill: bool = False,
           stroke: float | None = None, dpr: float = 2.0) -> QPixmap:
    px = max(1, int(round(size * dpr)))
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    # The painter works in device pixels here, so pass the width computed from
    # the logical icon size instead of letting draw_icon measure the pixmap.
    width = _viewbox_stroke(icon_style()[0], size) if stroke is None else stroke
    draw_icon(p, name, QRectF(0, 0, px, px), color, width, fill)
    p.end()
    pm.setDevicePixelRatio(dpr)
    return pm


def icon(name: str, color: str, size: int = 18, fill: bool = False) -> QIcon:
    out = QIcon()
    for s in (16, 20, 24, 32, 48, 64):
        out.addPixmap(pixmap(name, s, color, fill))
    return out


def image(name: str, size: int = 16, color: str = "#ffffff") -> str:
    """SVG markup, for .desktop/icon use and quick inspection."""
    key = name if name in PATHS else FALLBACK_ICON
    return PATHS[key].replace("currentColor", color)
