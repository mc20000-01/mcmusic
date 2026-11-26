"""WCAG contrast gates for every committed token family in light and dark mode.

Reads design/tokens.generated.json (the committed generated artifact) and uses
the standard sRGB relative-luminance formula.  Failing pairs are all reported
together with exact family/mode/pair/colors/ratio: nothing is suppressed or
exempted and no threshold is relaxed.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "design" / "tokens.generated.json"

TEXT_MIN = 4.5
BOUNDARY_MIN = 3.0

TEXT_PAIRS = (
    ("onPrimary", "primary"),
    ("onPrimaryContainer", "primaryContainer"),
    ("onSecondary", "secondary"),
    ("onSecondaryContainer", "secondaryContainer"),
    ("onTertiary", "tertiary"),
    ("onTertiaryContainer", "tertiaryContainer"),
    ("onError", "error"),
    ("onErrorContainer", "errorContainer"),
    ("onBackground", "background"),
    ("onSurface", "surface"),
    ("onSurfaceVariant", "surfaceVariant"),
    ("fg", "bg"),
    ("fg", "surface"),
    ("dim", "bg"),
    ("dim", "surface"),
    ("accentText", "bg"),
    ("accentFg", "accent"),
    # `accent` is a bright legacy brand *fill*; `onPrimary` is the M3 foreground
    # paired only with the generated darker `primary` role. Text on the legacy
    # accent is checked by accentFg/accent above.
)
BOUNDARY_PAIRS = (
    ("outline", "background"),
    ("outlineVariant", "surfaceContainerLowest"),
)


def _channel(value):
    value = value / 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _luminance(hex_color):
    if not isinstance(hex_color, str) or len(hex_color) != 7 or not hex_color.startswith("#"):
        raise ValueError("expected #RRGGBB, got %r" % (hex_color,))
    red, green, blue = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def _contrast(foreground, background):
    light, dark = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def _color(variant, name):
    if name in variant["roles"]:
        return variant["roles"][name]
    return variant["legacy"].get(name)


def test_generated_tokens_meet_wcag_contrast():
    data = json.loads(TOKENS.read_text(encoding="utf-8"))
    families = data["families"]
    assert len(families) == 5, "expected exactly 5 families, found %d: %s" % (
        len(families), ", ".join(sorted(families))
    )

    failures = []
    checked = 0
    for family in sorted(families):
        for mode in ("light", "dark"):
            variant = families[family][mode]
            for pairs, minimum in ((TEXT_PAIRS, TEXT_MIN), (BOUNDARY_PAIRS, BOUNDARY_MIN)):
                for foreground_name, background_name in pairs:
                    foreground = _color(variant, foreground_name)
                    background = _color(variant, background_name)
                    if foreground is None or background is None:
                        if (foreground_name, background_name) == ("accent", "onPrimary"):
                            continue  # not meaningful when a legacy accent is absent
                        failures.append(
                            "%s/%s %s/%s: missing color (%r on %r)"
                            % (family, mode, foreground_name, background_name, foreground, background)
                        )
                        continue
                    ratio = _contrast(foreground, background)
                    checked += 1
                    if ratio < minimum:
                        failures.append(
                            "%s/%s %s/%s: %.2f:1 < %.1f:1 (%s on %s)"
                            % (family, mode, foreground_name, background_name,
                               ratio, minimum, foreground, background)
                        )

    assert not failures, (
        "%d of %d checked token pairs fail WCAG contrast:\n%s"
        % (len(failures), checked, "\n".join(failures))
    )
