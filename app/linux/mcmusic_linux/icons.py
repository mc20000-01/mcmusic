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
PATHS = {
    # playback
    "play": '<path d="M7 4.5v15l12-7.5z" fill="currentColor" stroke="none"/>',
    "pause": '<rect x="7" y="4" width="3.5" height="16" rx="1" fill="currentColor" stroke="none"/>'
             '<rect x="13.5" y="4" width="3.5" height="16" rx="1" fill="currentColor" stroke="none"/>',
    "skip-forward": '<path d="M5 4l10 8-10 8z" fill="currentColor" stroke="none"/>'
                    '<path d="M18 4v16"/>',
    "skip-back": '<path d="M19 4L9 12l10 8z" fill="currentColor" stroke="none"/>'
                 '<path d="M6 4v16"/>',
    "shuffle": '<path d="M16 3h5v5"/><path d="M4 20L21 3"/><path d="M21 16v5h-5"/>'
               '<path d="M15 15l6 6"/><path d="M4 4l5 5"/>',
    "repeat": '<path d="M17 2l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/>'
              '<path d="M7 22l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>',
    "repeat-1": '<path d="M17 2l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/>'
                '<path d="M7 22l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>'
                '<path d="M11 10h2v5"/>',
    "volume-2": '<path d="M11 5L6 9H2v6h4l5 4z"/>'
                '<path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M18.5 5.5a9 9 0 0 1 0 13"/>',
    "volume-1": '<path d="M11 5L6 9H2v6h4l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/>',
    "volume-x": '<path d="M11 5L6 9H2v6h4l5 4z"/><path d="M22 9l-6 6"/><path d="M16 9l6 6"/>',
    # navigation
    "home": '<path d="M3 10.5L12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.3-4.3"/>',
    "library": '<path d="M4 4h5v16H4z"/><path d="M11 4h5v16h-5z"/>'
               '<path d="M18 5l3 1-3 14-3-1z"/>',
    "disc-3": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2.5"/>',
    "album": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2.5"/>',
    "music": '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/>'
             '<circle cx="18" cy="16" r="3"/>',
    "radio": '<rect x="3" y="9" width="18" height="11" rx="2"/><path d="M3 9l16-5"/>'
             '<path d="M7 14h.01"/><path d="M11 14h.01"/><path d="M15 14h.01"/>',
    "settings": '<circle cx="12" cy="12" r="3"/>'
                '<path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1'
                'M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
             '<circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/>'
             '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    # actions
    "list-music": '<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6h.01M3 12h.01M3 18h.01"/>',
    "text": '<path d="M4 6h16"/><path d="M4 12h10"/><path d="M4 18h16"/>',
    "tv-2": '<rect x="3" y="5" width="18" height="12" rx="1.5"/><path d="M7 21h10"/>'
            '<path d="M12 17v4"/>',
    "heart": '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 1 0-7.8 7.8'
             'l8.8 8.8 8.8-8.8a5.5 5.5 0 0 0 0-7.8z"/>',
    "download": '<path d="M12 3v12"/><path d="M7 11l5 5 5-5"/><path d="M4 21h16"/>',
    "cloud-download": '<path d="M12 12v7"/><path d="M9 16l3 3 3-3"/>'
                      '<path d="M6.5 19a4.5 4.5 0 0 1-.4-9A6 6 0 0 1 18 9.6a3.5 3.5 0 0 1 .5 7"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "check": '<path d="M20 6L9 17l-5-5"/>',
    "chevron-left": '<path d="M15 5l-7 7 7 7"/>',
    "chevron-right": '<path d="M9 5l7 7-7 7"/>',
    "chevron-down": '<path d="M5 9l7 7 7-7"/>',
    "chevron-up": '<path d="M5 15l7-7 7 7"/>',
    "grip-vertical": '<circle cx="9" cy="5" r="1.3" fill="currentColor" stroke="none"/>'
                     '<circle cx="15" cy="5" r="1.3" fill="currentColor" stroke="none"/>'
                     '<circle cx="9" cy="12" r="1.3" fill="currentColor" stroke="none"/>'
                     '<circle cx="15" cy="12" r="1.3" fill="currentColor" stroke="none"/>'
                     '<circle cx="9" cy="19" r="1.3" fill="currentColor" stroke="none"/>'
                     '<circle cx="15" cy="19" r="1.3" fill="currentColor" stroke="none"/>',
    "more-vertical": '<circle cx="12" cy="5" r="1.4" fill="currentColor" stroke="none"/>'
                     '<circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/>'
                     '<circle cx="12" cy="19" r="1.4" fill="currentColor" stroke="none"/>',
    "more-horizontal": '<circle cx="5" cy="12" r="1.4" fill="currentColor" stroke="none"/>'
                       '<circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/>'
                       '<circle cx="19" cy="12" r="1.4" fill="currentColor" stroke="none"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/>',
    "log-out": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
               '<path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
    "link": '<path d="M10.5 13.5a4.5 4.5 0 0 0 6.4 0l2.6-2.6a4.5 4.5 0 1 0-6.4-6.4'
            'l-1.3 1.3"/><path d="M13.5 10.5a4.5 4.5 0 0 0-6.4 0l-2.6 2.6a4.5 4.5 0 1 0 '
            '6.4 6.4l1.3-1.3"/>',
    "unlink": '<path d="M15 7l3-3a4 4 0 0 1 6 6l-3 3"/>'
              '<path d="M9 17l-3 3a4 4 0 0 1-6-6l3-3"/>'
              '<path d="M8 2v3M2 8h3M16 22v-3M22 16h-3"/>',
    "arrow-up-right": '<path d="M7 17L17 7"/><path d="M8 7h9v9"/>',
    "arrow-left": '<path d="M19 12H5"/><path d="M11 18l-6-6 6-6"/>',
    "refresh-cw": '<path d="M21 12a9 9 0 0 1-9 9 9 9 0 0 1-8-4"/>'
                  '<path d="M3 12a9 9 0 0 1 9-9 9 9 0 0 1 8 4"/>'
                  '<path d="M3 3v5h5"/><path d="M21 21v-5h-5"/>',
    "wifi-off": '<path d="M2 2l20 20"/><path d="M8.5 16.5a5 5 0 0 1 7 0"/>'
                '<path d="M2 8.8a16 16 0 0 1 4-2.6"/><path d="M22 8.8a16 16 0 0 0-6-3.1"/>'
                '<path d="M5 12.5a11 11 0 0 1 3-1.7"/><path d="M19 12.5a11 11 0 0 0-3-1.7"/>'
                '<path d="M12 20h.01"/>',
    "trash-2": '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/>'
               '<path d="M10 11v5M14 11v5"/>',
    "folder-plus": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5'
                   'a2 2 0 0 1-2-2z"/><path d="M12 11v5M9.5 13.5h5"/>',
    "pin": '<path d="M12 17v5"/><path d="M9 3h6l-1 6 4 4H6l4-4z"/>',
    "triangle-alert": '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L14.7 3.9'
                      'a2 2 0 0 0-3.4 0z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 16v-5"/><path d="M12 8h.01"/>',
    "circle-help": '<circle cx="12" cy="12" r="9"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 2.5-3 4"/>'
                   '<path d="M12 17h.01"/>',
    "circle": '<circle cx="12" cy="12" r="9"/>',
    "cast": '<path d="M2 20h.01"/><path d="M2 16a4 4 0 0 1 4 4"/><path d="M2 12a8 8 0 0 1 8 8"/>'
            '<path d="M2 8a12 12 0 0 1 12 12"/><rect x="2" y="3" width="20" height="14" rx="2"/>',
    "smartphone": '<rect x="6" y="2" width="12" height="20" rx="2.5"/><path d="M11 18h2"/>',
    "square-check": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 12l3 3 5-6"/>',
    "sparkles": '<path d="M12 3l1.7 4.3L18 9l-4.3 1.7L12 15l-1.7-4.3L6 9l4.3-1.7z"/>'
                '<path d="M18 15l.9 2.1L21 18l-2.1.9L18 21l-.9-2.1L15 18l2.1-.9z"/>',
}

FALLBACK_ICON = "circle-help"


@lru_cache(maxsize=512)
def _renderer(name: str, color: str, fill: bool, stroke: float) -> QSvgRenderer:
    key = name if name in PATHS else FALLBACK_ICON
    body = PATHS[key].replace("currentColor", color)
    paint = color if fill else "none"
    line = "none" if fill else color
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'width="24" height="24" fill="{paint}" stroke="{line}" '
        f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">'
        f"{body}</svg>"
    )
    return QSvgRenderer(QByteArray(svg.encode("utf-8")))


def draw_icon(painter: QPainter, name: str, rect: QRectF, color: str,
              stroke: float = 1.8, fill: bool = False) -> None:
    """Render an icon into ``rect`` with the current painter."""
    r = _renderer(name, str(color), fill, float(stroke))
    if r.isValid():
        r.render(painter, QRectF(rect))


def pixmap(name: str, size: int, color: str, fill: bool = False,
           stroke: float = 1.8, dpr: float = 2.0) -> QPixmap:
    px = max(1, int(round(size * dpr)))
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    draw_icon(p, name, QRectF(0, 0, px, px), color, stroke, fill)
    p.end()
    pm.setDevicePixelRatio(dpr)
    return pm


def icon(name: str, color: str, size: int = 18, fill: bool = False) -> QIcon:
    out = QIcon()
    for s in (16, 20, 24, 32, 48, 64):
        out.addPixmap(pixmap(name, s, color, fill, 1.8, 2.0))
    return out


def image(name: str, size: int = 16, color: str = "#ffffff") -> str:
    """SVG markup, for .desktop/icon use and quick inspection."""
    key = name if name in PATHS else FALLBACK_ICON
    return PATHS[key].replace("currentColor", color)
