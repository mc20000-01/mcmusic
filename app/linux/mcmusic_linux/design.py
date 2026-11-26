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
