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
        color: {p.fg};
        selection-background-color: {p.accent};
        selection-color: {p.accent_fg};
    }}
    QLineEdit {{
        background: {_rgba(p.surface2, 64)};
        border: 1px solid {_rgba(p.line2, 90)};
        border-radius: 18px;
        padding: 9px 14px;
        color: {p.fg};
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border-color: {_rgba(p.accent, 170)};
        background: {_rgba(p.surface2, 82)};
    }}
    QLineEdit[echoMode="2"] {{ letter-spacing: 2px; }}
    QMenu {{
        background: {p.bg2};
        border: 1px solid {_rgba(p.line2, 90)};
        border-radius: 16px;
        padding: 8px;
    }}
    QMenu::item {{
        padding: 9px 30px 9px 14px;
        border-radius: 12px;
        color: {p.fg};
        font-size: 13px;
    }}
    QMenu::item:selected {{ background: {_rgba(p.accent, 52)}; }}
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
        border: 1px solid {_rgba(p.accent, 90)};
        border-radius: 10px; padding: 5px 9px;
        font-size: 11px;
    }}
    QDialog {{ background: {p.bg2}; }}
    QMessageBox {{ background: {p.bg2}; }}
    QMessageBox QLabel {{ color: {p.fg}; }}
    QMessageBox QPushButton {{
        background: {_rgba(p.surface2, 76)};
        border: 1px solid {_rgba(p.line2, 90)};
        border-radius: 18px; padding: 8px 18px; color: {p.fg};
    }}
    QMessageBox QPushButton:hover {{ background: {_rgba(p.accent, 46)}; }}
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
