"""Design tokens shared with the web client (ui/src/env.css).

Everything the native UI paints reads from these palettes, so the desktop app
keeps the same ink + violet identity as the browser and Android builds.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette


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
    accent_fg: str
    ok: str = "#1db954"
    warn: str = "#b888ff"
    err: str = "#ff6b72"
    scrim: str = "rgba(8, 6, 13, 0.78)"
    ink: str = "#08060d"

    def q(self, token: str) -> QColor:
        return QColor(getattr(self, token))

    @property
    def accent_soft(self) -> QColor:
        c = QColor(self.accent)
        c.setAlpha(36)
        return c

    # ── Liquid Glass tokens ─────────────────────────────────────────────
    # Painting code reads these; QSS uses the matching rgba literals below.
    @property
    def glass(self) -> QColor:
        c = QColor("#ffffff")
        c.setAlpha(36)
        return c

    @property
    def glass_strong(self) -> QColor:
        c = QColor("#ffffff")
        c.setAlpha(56)
        return c

    @property
    def glass_border(self) -> QColor:
        c = QColor("#ffffff")
        c.setAlpha(46)
        return c

    @property
    def glass_highlight(self) -> QColor:
        c = QColor("#ffffff")
        c.setAlpha(64)
        return c


# ── palettes (ui/src/env.css + Design.kt) ───────────────────────────────────

# DUSK mirrors the v3 web tokens exactly: one ink surface scale, one accent.
DUSK = Palette(
    name="dusk",
    bg="#08060d", bg2="#100c18", surface="#19122a", surface2="#241a38",
    fg="#ffffff", dim="#948aa6", dim2="#6a6178",
    line="#1f1830", line2="#2a2040",
    accent="#a06bff", accent_fg="#08060d",
    scrim="rgba(8, 6, 13, 0.78)", ink="#08060d",
)

PAPER = Palette(
    name="paper",
    bg="#f4f2f8", bg2="#ebe7f2", surface="#ffffff", surface2="#f8f6fb",
    fg="#08060d", dim="#6a6178", dim2="#948aa6",
    line="#d6cfe0", line2="#b8aecb",
    accent="#a06bff", accent_fg="#08060d",
    scrim="rgba(8, 6, 13, 0.36)", ink="#08060d",
)

INK = Palette(
    name="ink",
    bg="#050408", bg2="#0a0810", surface="#100c18", surface2="#181226",
    fg="#ffffff", dim="#948aa6", dim2="#6a6178",
    line="#1f1830", line2="#2a2040",
    accent="#a06bff", accent_fg="#08060d",
    scrim="rgba(0, 0, 0, 0.82)", ink="#000000",
)

TIDE = Palette(
    name="tide",
    bg="#070912", bg2="#0d1020", surface="#141830", surface2="#1c2240",
    fg="#ffffff", dim="#9aa0bc", dim2="#6f7591",
    line="#1e2440", line2="#2c3458",
    accent="#a06bff", accent_fg="#08060d",
    scrim="rgba(5, 7, 16, 0.78)", ink="#04050c",
)

FOREST = Palette(
    name="forest",
    bg="#06100c", bg2="#0a1a14", surface="#10251c", surface2="#182f25",
    fg="#ffffff", dim="#9cb7a8", dim2="#6f887b",
    line="#1a382c", line2="#274d3d",
    accent="#a06bff", accent_fg="#08060d",
    scrim="rgba(3, 12, 9, 0.78)", ink="#030906",
)

ROSE = Palette(
    name="rose",
    bg="#100810", bg2="#1a1020", surface="#241630", surface2="#30203f",
    fg="#ffffff", dim="#b09cba", dim2="#85738f",
    line="#2e2038", line2="#443052",
    accent="#a06bff", accent_fg="#08060d",
    scrim="rgba(14, 6, 14, 0.78)", ink="#0b050b",
)

PALETTES: dict[str, Palette] = {
    "dusk": DUSK, "paper": PAPER, "ink": INK, "tide": TIDE,
    "forest": FOREST, "rose": ROSE,
}

# Aliases used by the server / older clients.
ALIASES = {
    "dark": "dusk", "auto": "dusk", "light": "paper", "flufi": "dusk",
    "amoled": "ink", "midnight": "tide", "copper": "rose", "mocha": "rose",
}

THEME_ORDER = ["dusk", "paper", "ink", "tide", "forest", "rose"]

ACCENTS = [
    ("#a06bff", "violet"),
    ("#b888ff", "lilac"),
    ("#79d8a5", "forest"),
    ("#d97f9e", "rose"),
    ("#6fb3c4", "tide"),
    ("#cfc9da", "mist"),
]

# Mutable process-wide appearance state.
_ACTIVE = DUSK
_ACCENT_OVERRIDE = ""
_THEME_NAME = "dusk"


def _readable_on(hex_color: str) -> str:
    c = QColor(hex_color)
    lum = (0.299 * c.redF()) + (0.587 * c.greenF()) + (0.114 * c.blueF())
    return "#000000" if lum > 0.6 else "#ffffff"


def set_appearance(theme: str, accent: str | None) -> Palette:
    """Mirror of applySet(): palette lookup, then accent override."""
    global _ACTIVE, _ACCENT_OVERRIDE, _THEME_NAME
    key = ALIASES.get((theme or "").lower(), (theme or "").lower())
    base = PALETTES.get(key, DUSK)
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


def stylesheet(p: Palette | None = None) -> str:
    p = p or pal()
    return f"""
    QWidget {{
        color: {p.fg};
        selection-background-color: {p.accent};
        selection-color: {p.accent_fg};
    }}
    QLineEdit {{
        background: rgba(255, 255, 255, 0.10);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 10px;
        padding: 8px 12px;
        color: {p.fg};
        font-size: 13px;
    }}
    QLineEdit:focus {{ border-color: rgba(255, 255, 255, 0.32); }}
    QLineEdit[echoMode="2"] {{ letter-spacing: 2px; }}
    QMenu {{
        background: {p.bg2};
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 10px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 8px 28px 8px 12px;
        border-radius: 10px;
        color: {p.fg};
        font-size: 13px;
    }}
    QMenu::item:selected {{ background: rgba(255, 255, 255, 0.12); }}
    QMenu::item:disabled {{ color: {p.dim2}; }}
    QMenu::separator {{ height: 1px; background: {p.line}; margin: 4px 2px; }}
    QScrollBar:vertical {{
        background: transparent; width: 10px; margin: 2px 1px 2px 1px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.line2}; border-radius: 4px; min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {p.dim2}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0; background: none; border: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        background: transparent; height: 10px; margin: 1px 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p.line2}; border-radius: 4px; min-width: 30px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0; background: none; border: none;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    QToolTip {{
        background: {p.ink}; color: {p.fg};
        border: 1px solid {p.line2}; padding: 4px 7px;
        font-size: 11px;
    }}
    QDialog {{ background: {p.bg2}; }}
    QMessageBox {{ background: {p.bg2}; }}
    QMessageBox QLabel {{ color: {p.fg}; }}
    QMessageBox QPushButton {{
        background: rgba(255, 255, 255, 0.12); border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 10px; padding: 7px 15px; color: {p.fg};
    }}
    QMessageBox QPushButton:hover {{ background: {p.surface}; }}
    QColorDialog {{ background: {p.bg2}; }}
    QAbstractScrollArea {{ border: none; }}
    """


def qpalette(p: Palette | None = None) -> QPalette:
    """Native palette so stock widgets (menus, color dialog) follow the theme."""
    p = p or pal()
    out = QPalette()
    roles = {
        QPalette.ColorRole.Window: p.bg2,
        QPalette.ColorRole.WindowText: p.fg,
        QPalette.ColorRole.Base: p.bg,
        QPalette.ColorRole.AlternateBase: p.surface,
        QPalette.ColorRole.Text: p.fg,
        QPalette.ColorRole.Button: p.bg2,
        QPalette.ColorRole.ButtonText: p.fg,
        QPalette.ColorRole.Highlight: p.accent,
        QPalette.ColorRole.HighlightedText: p.accent_fg,
        QPalette.ColorRole.ToolTipBase: p.ink,
        QPalette.ColorRole.ToolTipText: p.fg,
        QPalette.ColorRole.PlaceholderText: p.dim2,
        QPalette.ColorRole.Link: p.accent,
        QPalette.ColorRole.Mid: p.line,
        QPalette.ColorRole.Dark: p.line2,
        QPalette.ColorRole.Light: p.surface2,
    }
    for role, color in roles.items():
        out.setColor(role, QColor(color))
    return out


def theme_preview(name: str) -> tuple[str, str]:
    """(surface, accent) pair used by the settings theme cards."""
    p = PALETTES.get(ALIASES.get(name, name), DUSK)
    return p.surface, p.accent
