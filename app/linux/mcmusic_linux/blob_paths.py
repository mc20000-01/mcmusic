"""Read the generated 100x100 blob paths into paint-ready Qt paths.

Only the absolute SVG subset emitted by the token generator is supported:
``M H V C Q A L Z``. Arcs are converted to short cubic runs with the SVG
centre-parameterisation, so a path keeps its geometry at any target rect.
"""
from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPainterPath, QTransform

from .blobs import BLOB_PATHS

_SIZE = 100.0
_NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
_TOKEN = re.compile(r"[MHVCLQAZ]|" + _NUMBER)

__all__ = ["blob_path", "blob_id_for"]


def _take(tokens: list[str], index: int, count: int) -> tuple[list[float], int]:
    if index + count > len(tokens):
        raise ValueError("truncated blob path")
    return [float(value) for value in tokens[index:index + count]], index + count


def _arc_cubics(start: QPointF, args: list[float]) -> list[tuple[QPointF, ...]]:
    """Turn one SVG arc into (control1, control2, end) cubic segments."""
    rx, ry, rotation, large, sweep, end_x, end_y = args
    x1, y1 = start.x(), start.y()
    if rx == 0 or ry == 0 or (x1 == end_x and y1 == end_y):
        return []

    phi = math.radians(rotation % 180.0)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)
    half_x, half_y = (x1 - end_x) / 2.0, (y1 - end_y) / 2.0
    x1p = cos_phi * half_x + sin_phi * half_y
    y1p = -sin_phi * half_x + cos_phi * half_y
    rx, ry = abs(rx), abs(ry)
    scale = math.sqrt((x1p / rx) ** 2 + (y1p / ry) ** 2)
    if scale > 1.0:
        rx, ry = rx * scale, ry * scale

    sign = -1.0 if bool(large) == bool(sweep) else 1.0
    numerator = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    denominator = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    coef = sign * math.sqrt(max(0.0, numerator / denominator)) if denominator else 0.0
    cxp = coef * rx * y1p / ry
    cyp = -coef * ry * x1p / rx
    cx = cos_phi * cxp - sin_phi * cyp + (x1 + end_x) / 2.0
    cy = sin_phi * cxp + cos_phi * cyp + (y1 + end_y) / 2.0

    def vector(x: float, y: float) -> tuple[float, float]:
        return ((x - cxp) / rx, (y - cyp) / ry)

    ux, uy = vector(x1p, y1p)
    vx, vy = vector(-x1p, -y1p)
    theta = math.atan2(uy, ux)
    delta = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
    if not sweep and delta > 0:
        delta -= math.tau
    elif sweep and delta < 0:
        delta += math.tau

    def point(t: float) -> QPointF:
        c, s = math.cos(t), math.sin(t)
        return QPointF(cx + cos_phi * rx * c - sin_phi * ry * s,
                       cy + sin_phi * rx * c + cos_phi * ry * s)

    def tangent(t: float) -> QPointF:
        c, s = math.cos(t), math.sin(t)
        return QPointF(-cos_phi * rx * s - sin_phi * ry * c,
                       -sin_phi * rx * s + cos_phi * ry * c)

    steps = max(1, math.ceil(abs(delta) / (math.pi / 2.0)))
    out = []
    for step in range(steps):
        t1 = theta + delta * step / steps
        t2 = theta + delta * (step + 1) / steps
        p1, p2 = point(t1), point(t2)
        alpha = (4.0 / 3.0) * math.tan((t2 - t1) / 4.0)
        d1, d2 = tangent(t1), tangent(t2)
        out.append((p1 + d1 * alpha, p2 - d2 * alpha, p2))
    return out


@lru_cache(maxsize=None)
def _normalized(blob_id: str) -> QPainterPath:
    tokens = _TOKEN.findall(BLOB_PATHS[blob_id])
    path = QPainterPath()
    current = QPointF()
    command = ""
    index = 0
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
            if command == "Z":
                path.closeSubpath()
                continue
        if not command:
            raise ValueError("blob path has no command")
        if command == "M":
            values, index = _take(tokens, index, 2)
            current = QPointF(*values)
            path.moveTo(current)
            command = "L"
        elif command == "L":
            values, index = _take(tokens, index, 2)
            current = QPointF(*values)
            path.lineTo(current)
        elif command == "H":
            values, index = _take(tokens, index, 1)
            current.setX(values[0])
            path.lineTo(current)
        elif command == "V":
            values, index = _take(tokens, index, 1)
            current.setY(values[0])
            path.lineTo(current)
        elif command == "C":
            values, index = _take(tokens, index, 6)
            path.cubicTo(QPointF(values[0], values[1]), QPointF(values[2], values[3]),
                         QPointF(values[4], values[5]))
            current = QPointF(values[4], values[5])
        elif command == "Q":
            values, index = _take(tokens, index, 4)
            path.quadTo(QPointF(values[0], values[1]), QPointF(values[2], values[3]))
            current = QPointF(values[2], values[3])
        elif command == "A":
            values, index = _take(tokens, index, 7)
            for control1, control2, end in _arc_cubics(current, values):
                path.cubicTo(control1, control2, end)
            current = QPointF(values[5], values[6])
        else:
            raise ValueError(f"unsupported blob path command: {command}")
    return path


@lru_cache(maxsize=512)
def blob_id_for(name: str) -> str:
    """Map a name onto a generated blob id, stably across processes."""
    digest = hashlib.sha256(str(name or "").encode("utf-8")).hexdigest()
    ids = tuple(BLOB_PATHS)
    return ids[int(digest[:8], 16) % len(ids)]


def blob_path(id: str, rect: QRectF) -> QPainterPath:
    """Return the named blob fitted to ``rect`` (a copy callers may mutate)."""
    blob_id = id if id in BLOB_PATHS else blob_id_for(id)
    transform = QTransform(
        rect.width() / _SIZE, 0.0, 0.0, rect.height() / _SIZE,
        rect.x(), rect.y(),
    )
    return QPainterPath(_normalized(blob_id)) * transform
