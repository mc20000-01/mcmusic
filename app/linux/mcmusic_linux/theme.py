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
    accent_fg: str
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
    # Painting code reads these; QSS uses palette-derived rgba() values below.
    def _tint(self, token: str, alpha: int) -> QColor:
        c = QColor(getattr(self, token))
        c.setAlpha(alpha)
        return c

    @property
    def glass(self) -> QColor:
        return self._tint("surface", 36)

    @property
    def glass_strong(self) -> QColor:
        return self._tint("surface2", 56)

    @property
    def glass_border(self) -> QColor:
        return self._tint("line2", 46)

    @property
    def glass_highlight(self) -> QColor:
        return self._tint("fg", 64)


# ── five palette families (shared by web, Android, iOS, macOS and Windows) ──
# Top half of the supplied swatch sheet gives the light variants; the bottom
# half gives the dark variants. Text/icons are dark on light and white on dark.
# A bare family id follows the current appearance; `family-light` / `family-dark`
# pins one half of the sheet.

def _variant(
    family: str,
    label: str,
    dark: bool,
    bg: str,
    bg2: str,
    surface: str,
    surface2: str,
    fg: str,
    dim: str,
    dim2: str,
    line: str,
    line2: str,
    accent: str,
    accent_fg: str = "#08060d",
) -> Palette:
    return Palette(
        name=f"{family}-{'dark' if dark else 'light'}",
        bg=bg, bg2=bg2, surface=surface, surface2=surface2,
        fg=fg, dim=dim, dim2=dim2, line=line, line2=line2,
        accent=accent, accent_fg=accent_fg, warn=accent,
        err="#ff6b72" if dark else "#b3261e",
        scrim=f"rgba({int(bg[1:3], 16)}, {int(bg[3:5], 16)}, {int(bg[5:7], 16)}, 0.78)",
        ink=bg2,
    )


VIOLET_LIGHT = _variant("violet", "Violet", False, "#f5f2ff", "#ede7ff", "#ffffff", "#f7f4ff",
                        "#08060d", "#473872", "#6a54aa", "#dacdff", "#cab8ff", "#9f7eff")
VIOLET_DARK = _variant("violet", "Violet", True, "#171721", "#222130", "#2a293c", "#444361",
                       "#ffffff", "#aaaab7", "#8b8a9d", "#35344b", "#605f78", "#9f7eff")
INDIGO_LIGHT = _variant("indigo", "Indigo", False, "#f2f4ff", "#e8ebff", "#ffffff", "#f5f6ff",
                        "#08060d", "#3b4172", "#5761aa", "#cfd5ff", "#bac3ff", "#8293ff")
INDIGO_DARK = _variant("indigo", "Indigo", True, "#12171f", "#1b212d", "#212838", "#36425b",
                       "#ffffff", "#a4a9b5", "#828999", "#2a3346", "#545e73", "#8293ff")
SKY_LIGHT = _variant("sky", "Sky", False, "#f1f8fe", "#e7f3fe", "#ffffff", "#f4f9fe",
                     "#08060d", "#385272", "#527ca9", "#cce5fe", "#b6dafe", "#7bbdfe")
SKY_DARK = _variant("sky", "Sky", True, "#182127", "#222f39", "#2a3a46", "#455f72",
                    "#ffffff", "#abb7bf", "#8b9ba7", "#354a58", "#607787", "#7bbdfe")
AQUA_LIGHT = _variant("aqua", "Aqua", False, "#f1fbfc", "#e7f9fa", "#ffffff", "#f4fcfd",
                      "#08060d", "#386168", "#53939a", "#cdf3f5", "#b6edf1", "#7ce0e6")
AQUA_DARK = _variant("aqua", "Aqua", True, "#15241c", "#1f3328", "#263f32", "#3e6751",
                     "#ffffff", "#a8bab0", "#87a093", "#30503f", "#5a7d6b", "#7ce0e6")
MINT_LIGHT = _variant("mint", "Mint", False, "#f1fff5", "#e7ffee", "#ffffff", "#f4fff7",
                      "#08060d", "#386e4c", "#52a76f", "#ccffdc", "#b6ffcc", "#7bffa4")
MINT_DARK = _variant("mint", "Mint", True, "#15241a", "#1f3425", "#26412e", "#3e694b",
                     "#ffffff", "#a8bbae", "#87a28f", "#30513a", "#5a7f66", "#7bffa4")

FAMILIES = {
    "violet": ("Violet", VIOLET_LIGHT, VIOLET_DARK),
    "indigo": ("Indigo", INDIGO_LIGHT, INDIGO_DARK),
    "sky": ("Sky", SKY_LIGHT, SKY_DARK),
    "aqua": ("Aqua", AQUA_LIGHT, AQUA_DARK),
    "mint": ("Mint", MINT_LIGHT, MINT_DARK),
}

PALETTES: dict[str, Palette] = {}
for _family, (_label, _light, _dark) in FAMILIES.items():
    PALETTES[_light.name] = _light
    PALETTES[_dark.name] = _dark

# Legacy saved values resolve to the nearest family.
ALIASES = {
    "dark": "violet-dark", "auto": "violet", "system": "violet",
    "light": "violet-light",
    "flufi": "violet-dark", "dusk": "violet-dark", "paper": "violet-light",
    "ink": "indigo-dark", "amoled": "indigo-dark",
    "midnight": "sky-dark", "tide": "aqua-dark",
    "forest": "mint-dark", "copper": "violet-dark", "mocha": "violet-dark",
    "rose": "violet-dark",
}

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
    return VIOLET_DARK if dark else VIOLET_LIGHT

ACCENTS = [
    ("#9f7eff", "violet"),
    ("#8293ff", "indigo"),
    ("#7bbdfe", "sky"),
    ("#7ce0e6", "aqua"),
    ("#7bffa4", "mint"),
]

# Mutable process-wide appearance state.
_ACTIVE = VIOLET_DARK
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
        color: {p.fg};
        selection-background-color: {p.accent};
        selection-color: {p.accent_fg};
    }}
    QLineEdit {{
        background: {_rgba(p.surface, 34)};
        border: 1px solid {_rgba(p.line2, 70)};
        border-radius: 10px;
        padding: 8px 12px;
        color: {p.fg};
        font-size: 13px;
    }}
    QLineEdit:focus {{ border-color: {_rgba(p.accent, 140)}; }}
    QLineEdit[echoMode="2"] {{ letter-spacing: 2px; }}
    QMenu {{
        background: {p.bg2};
        border: 1px solid {_rgba(p.line2, 70)};
        border-radius: 10px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 8px 28px 8px 12px;
        border-radius: 10px;
        color: {p.fg};
        font-size: 13px;
    }}
    QMenu::item:selected {{ background: {_rgba(p.surface2, 92)}; }}
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
        background: {_rgba(p.surface, 60)}; border: 1px solid {_rgba(p.line2, 70)};
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
    mode = mode_of(_THEME_NAME)
    p = resolve_theme(
        with_mode(name, mode),
        dark=system_dark() if mode == "auto" else mode == "dark",
    )
    return p.surface, p.accent
