"""Reject gradient, blur, shadow and glass rendering primitives in UI sources.

There is deliberately no allowlist and no suppression mechanism: every
occurrence reported by this scan is a hard failure.  Comments are blanked out
for the *scan only* (so prose such as "no gradients" is not an offence); the
failure report always quotes the original line verbatim.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Directory globs plus one explicit file.  No exclusions.
SCAN_ROOTS = (
    "ui/src",
    "ui/index.html",
    "web/embed",
    "gui/android/app/src/main/java",
    "gui/android/app/src/main/res",
    "app/ios/McMusic",
    "app/linux/mcmusic_linux",
)
EXTENSIONS = frozenset({".css", ".ts", ".tsx", ".js", ".html", ".kt", ".swift", ".py", ".xml"})

# Literal identifiers, matched as literal (case-insensitive) text -- never as a
# pattern that could abstract away a variable or a different identifier.
LITERAL_TOKENS = (
    "linear-gradient",
    "radial-gradient",
    "conic-gradient",
    "createLinearGradient",
    "createRadialGradient",
    # Android/SwiftUI/Qt rendering primitives, regardless of call style.
    "LinearGradient",
    "RadialGradient",
    "SweepGradient",
    "QConicalGradient",
    "angularGradient",
    "EllipticalGradient",
    "Brush.linearGradient",
    "Brush.radialGradient",
    "Brush.sweepGradient",
    "CAGradientLayer",
    "backdrop-filter",
    "-webkit-backdrop-filter",
    "backdrop_filter",
    "NSVisualEffectView",
    "UIBlurEffect",
    "ultraThinMaterial",
    "GaussianBlur",
    "QGraphicsBlurEffect",
    "setGraphicsEffect",
    "Modifier.blur",
    "Modifier.shadow",
    "shadowElevation",
    "QGraphicsDropShadowEffect",
    ".shadow(",
    "box-shadow",
    "drop-shadow",
    "text-shadow",
    "liquidGlass",
    "glass_border",
    "glass_highlight",
    "glass_strong",
)

# Bare identifiers need word boundaries so e.g. `realGlass` or `glassPane`
# are not silently conflated with the forbidden identifier `glass`.
IDENTIFIER_TOKENS = ("glass",)

_LINE_COMMENTS = {
    ".py": ("#",),
    ".ts": ("//",),
    ".tsx": ("//",),
    ".js": ("//",),
    ".kt": ("//",),
    ".swift": ("//",),
}
_BLOCK_COMMENTS = {
    ".css": (("/*", "*/"),),
    ".html": (("<!--", "-->"),),
    ".xml": (("<!--", "-->"),),
    ".py": (('"""', '"""'), ("'''", "'''")),  # docstrings are comments here
    ".ts": (("/*", "*/"),),
    ".tsx": (("/*", "*/"),),
    ".js": (("/*", "*/"),),
    ".kt": (("/*", "*/"),),
    ".swift": (("/*", "*/"),),
}
_QUOTED = frozenset({".py", ".ts", ".tsx", ".js", ".kt", ".swift"})


def _scan_text(line, suffix, state):
    """Blank out comments in `line`, preserving offsets and original characters."""
    chars = list(line)
    line_markers = _LINE_COMMENTS.get(suffix, ())
    blocks = _BLOCK_COMMENTS.get(suffix, ())
    index = 0
    quote = ""
    while index < len(chars):
        if state["block_end"]:
            end = state["block_end"]
            stop = line.find(end, index)
            if stop < 0:
                for pos in range(index, len(chars)):
                    chars[pos] = " "
                return "".join(chars)
            for pos in range(index, stop + len(end)):
                chars[pos] = " "
            index = stop + len(end)
            state["block_end"] = ""
            continue
        for opener, closer in blocks:
            if line.startswith(opener, index):
                for pos in range(index, index + len(opener)):
                    chars[pos] = " "
                index += len(opener)
                state["block_end"] = closer
                break
        if state["block_end"]:
            continue
        if quote:
            if line.startswith(quote, index):
                index += len(quote)
                quote = ""
            else:
                index += 1
            continue
        if suffix in _QUOTED and chars[index] in "'\"`":
            mark = chars[index]
            if suffix == ".py":
                triple = mark * 3
                quote = triple if line.startswith(triple, index) else mark
            else:
                quote = mark
            index += len(quote)
            continue
        if any(line.startswith(marker, index) for marker in line_markers):
            for pos in range(index, len(chars)):
                chars[pos] = " "
            return "".join(chars)
        index += 1
    return "".join(chars)


def _tokens_on_line(line, suffix, state):
    scanned = _scan_text(line, suffix, state).casefold()
    hits = []
    for token in LITERAL_TOKENS:
        if token.casefold() in scanned:
            hits.append(token)
    for token in IDENTIFIER_TOKENS:
        pattern = r"(?<![a-z0-9_$])" + token.casefold() + r"(?![a-z0-9_$])"
        if re.search(pattern, scanned):
            hits.append(token)
    # Visual blur APIs only.  A generic JS/DOM `.blur()` is focus management,
    # not a rendering effect, so bare `blur(` is not a token; CSS needs a
    # `filter:` declaration and Kotlin needs a call/import context.
    if re.search(r"(?:-webkit-)?filter\s*:\s*[^;}\n]*\bblur\s*\(", scanned):
        hits.append("filter: blur(")
    if suffix == ".kt":
        if re.search(r"(?<![a-z0-9_$])blur\s*\(", scanned):
            hits.append("blur(")
        if re.search(r"\bimport\s+[a-z0-9_.]*\.blur\s*$", scanned):
            hits.append("import ...blur")
    for match in re.finditer(r"elevation-([12])\s*:\s*([^;}\n]+)", scanned):
        value = match.group(2).strip()
        if value.casefold() != "none":
            hits.append("elevation-%s: %s" % (match.group(1), value))
    return list(dict.fromkeys(hits))


def _source_files():
    for root in SCAN_ROOTS:
        path = ROOT / root
        if path.is_file():
            if path.suffix in EXTENSIONS:
                yield path
        elif path.is_dir():
            for candidate in sorted(path.rglob("*")):
                if candidate.is_file() and candidate.suffix in EXTENSIONS:
                    yield candidate


def test_no_gradients_blurs_shadows_or_glass():
    violations = []
    for path in _source_files():
        state = {"block_end": ""}
        with path.open(encoding="utf-8", errors="replace") as source:
            for number, line in enumerate(source, 1):
                hits = _tokens_on_line(line, path.suffix, state)
                if hits:
                    text = line.rstrip("\r\n")
                    violations.append(
                        "%s:%d: %s: %s"
                        % (path.relative_to(ROOT).as_posix(), number, ", ".join(hits), text)
                    )
    assert not violations, (
        "%d forbidden rendering identifier(s) in UI sources (no allowlist):\n%s"
        % (len(violations), "\n".join(violations))
    )
