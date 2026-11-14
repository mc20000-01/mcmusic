"""Design tokens shared with the web client (web/css/variables.css).

Everything the native UI paints reads from these palettes, so the desktop app
keeps the same warm-ink + brass identity as the browser and Android builds.
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
    ok: str = "#7fa86a"
    warn: str = "#d9b13d"
    err: str = "#c9603f"
    scrim: str = "rgba(10, 8, 6, 0.72)"
    ink: str = "#0d0b09"

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


# ── palettes (variables.css + Theme.kt) ─────────────────────────────────────

DUSK = Palette(
    name="dusk",
    bg="#14110d", bg2="#1b1712", surface="#221d17", surface2="#2b241c",
    fg="#f3ebdd", dim="#a4957f", dim2="#786b58",
    line="#332b22", line2="#4a3f31",
    accent="#d98a3d", accent_fg="#1a130a",
    ok="#7fa86a", warn="#d9b13d", err="#c9603f",
    scrim="rgba(10, 8, 6, 0.72)", ink="#0d0b09",
)

PAPER = Palette(
    name="paper",
    bg="#f4efe4", bg2="#ece4d5", surface="#fbf7ee", surface2="#efe7d8",
    fg="#241d14", dim="#6d6151", dim2="#8d8069",
    line="#dcd1bd", line2="#bfb098",
    accent="#b4531f", accent_fg="#fff8ef",
    ok="#5c8a4a", warn="#a97f1f", err="#b04a2c",
    scrim="rgba(40, 32, 20, 0.34)", ink="#1b1610",
)

INK = Palette(
    name="ink",
    bg="#050505", bg2="#0b0b0c", surface="#121214", surface2="#191a1d",
    fg="#f5f5f5", dim="#8f8f96", dim2="#64646b",
    line="#212126", line2="#34343b",
    accent="#d7d7de", accent_fg="#0a0a0a",
    ok="#7fa86a", warn="#d9b13d", err="#c9603f",
    scrim="rgba(0, 0, 0, 0.77)", ink="#000000",
)

TIDE = Palette(
    name="tide",
    bg="#0e161a", bg2="#131e23", surface="#18262c", surface2="#1f3038",
    fg="#e4eef1", dim="#8ba3ab", dim2="#647e87",
    line="#23363d", line2="#33505a",
    accent="#6fb3c4", accent_fg="#06171c",
    ok="#7fa86a", warn="#d9b13d", err="#c9603f",
    scrim="rgba(6, 15, 19, 0.77)", ink="#070d10",
)

COPPER = Palette(
    name="copper",
    bg="#1a0f0d", bg2="#221412", surface="#2b1a16", surface2="#37211c",
    fg="#f6e7df", dim="#b2928a", dim2="#856a63",
    line="#3a241f", line2="#553229",
    accent="#e08a5f", accent_fg="#1c0d08",
    ok="#7fa86a", warn="#d9b13d", err="#c9603f",
    scrim="rgba(18, 8, 7, 0.8)", ink="#0d0706",
)

PALETTES: dict[str, Palette] = {
    "dusk": DUSK, "paper": PAPER, "ink": INK, "tide": TIDE, "copper": COPPER,
}

# Aliases used by the server / older clients.
ALIASES = {
    "dark": "dusk", "auto": "dusk", "light": "paper",
    "amoled": "ink", "midnight": "tide", "mocha": "copper", "rose": "copper",
}

THEME_ORDER = ["dusk", "paper", "ink", "tide", "copper"]

ACCENTS = [
    ("#d98a3d", "brass"),
    ("#c9603f", "ember"),
    ("#7fa86a", "moss"),
    ("#6fb3c4", "tide"),
    ("#a78bbf", "plum"),
    ("#d97f9e", "rose"),
    ("#c8b48a", "sand"),
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
        border-radius: 12px;
        padding: 8px 12px;
        color: {p.fg};
        font-size: 13px;
    }}
    QLineEdit:focus {{ border-color: rgba(255, 255, 255, 0.32); }}
    QLineEdit[echoMode="2"] {{ letter-spacing: 2px; }}
    QMenu {{
        background: {p.bg2};
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 16px;
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
        border-radius: 999px; padding: 7px 15px; color: {p.fg};
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
