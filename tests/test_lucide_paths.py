"""Generated Android Lucide drawables must carry the upstream SVG geometry.

The drawable generator converts Lucide's relative SVG path commands into the
absolute form Android's vector format requires. A relative/absolute mix-up
produces drawables that still look plausible as data but render as scrambled
icons, so this test independently converts the source SVG and compares every
emitted command. It also bounds every coordinate to the 24x24 icon viewport.
"""

import re
from pathlib import Path
from xml.etree import ElementTree

import pytest

from ui_deps import problem

ROOT = Path(__file__).resolve().parents[1]
SVG_DIR = ROOT / "ui/node_modules/lucide-static/icons"
DRAWABLE_DIR = ROOT / "gui/android/app/src/main/res/drawable"
_skip = problem(need_modules=True, sentinel=SVG_DIR)
if _skip:
    pytest.skip(_skip, allow_module_level=True)

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"
SOURCE_RE = re.compile(r"from lucide-static (\S+)\.svg")
NUMBER_RE = re.compile(r"[a-zA-Z]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
SHAPE_RE = re.compile(r"<(path|circle|rect|line|polyline|polygon)\b([^>]*)>")
ATTR_RE = re.compile(r'([A-Za-z][A-Za-z0-9-]*)\s*=\s*"([^"]*)"')

# Commands whose parameter count is fixed; H/V/L/M take one point, C takes
# three, Q takes two, A takes rx/ry/rotation/two flags/a point, Z takes none.
ARITY = {"m": 2, "l": 2, "h": 1, "v": 1, "c": 6, "s": 4, "q": 4, "t": 2, "a": 7, "z": 0}


def parse_path(data):
    """Return [(uppercase command, absolute parameters), ...] for SVG path data."""
    tokens = NUMBER_RE.findall(data)
    out = []
    i = 0
    command = None
    cx = cy = sx = sy = 0.0
    cubic = quad = None
    def take_number():
        nonlocal i
        if i >= len(tokens) or re.fullmatch(r"[a-zA-Z]", tokens[i]):
            raise AssertionError(f"truncated path: {data}")
        value = float(tokens[i])
        i += 1
        return value

    def take_flag():
        nonlocal i
        if i >= len(tokens):
            raise AssertionError(f"truncated arc flags: {data}")
        token = tokens[i]
        if token[0] not in "01":
            raise AssertionError(f"bad arc flag {token} in {data}")
        value = int(token[0])
        if len(token) > 1:
            tokens[i] = token[1:]
        else:
            i += 1
        return value

    while i < len(tokens):
        if re.fullmatch(r"[a-zA-Z]", tokens[i]):
            command = tokens[i]
            i += 1
        if command is None:
            raise AssertionError(f"path without command: {data}")
        letter = command.lower()
        relative = command == letter

        def point(x, y):
            return (cx + x, cy + y) if relative else (x, y)

        if letter == "a":
            rx, ry, rotation = take_number(), take_number(), take_number()
            large, sweep = take_flag(), take_flag()
            px, py = take_number(), take_number()
            end = point(px, py)
            out.append(("A", (rx, ry, rotation, large, sweep, *end)))
            cx, cy = end
            cubic = quad = None
            continue

        args = []
        for _ in range(ARITY[letter]):
            if i >= len(tokens):
                raise AssertionError(f"truncated path: {data}")
            args.append(tokens[i])
            i += 1
        values = [float(value) for value in args]

        if letter == "m":
            px, py = point(values[0], values[1])
            out.append(("M", (px, py)))
            sx, cx, sy, cy = px, px, py, py
            command = "l" if relative else "L"
        elif letter == "l":
            cx, cy = point(values[0], values[1])
            out.append(("L", (cx, cy)))
        elif letter == "h":
            cx = cx + values[0] if relative else values[0]
            out.append(("L", (cx, cy)))
        elif letter == "v":
            cy = cy + values[0] if relative else values[0]
            out.append(("L", (cx, cy)))
        elif letter in ("c", "s"):
            if letter == "c":
                c1 = point(values[0], values[1])
                c2 = point(values[2], values[3])
                end = point(values[4], values[5])
            else:
                c1 = (2 * cx - cubic[0], 2 * cy - cubic[1]) if cubic else (cx, cy)
                c2 = point(values[0], values[1])
                end = point(values[2], values[3])
            out.append(("C", (*c1, *c2, *end)))
            cubic = c2
            cx, cy = end
        elif letter in ("q", "t"):
            if letter == "q":
                control = point(values[0], values[1])
                end = point(values[2], values[3])
            else:
                control = (2 * cx - quad[0], 2 * cy - quad[1]) if quad else (cx, cy)
                end = point(values[0], values[1])
            out.append(("Q", (*control, *end)))
            quad = control
            cx, cy = end
        elif letter == "z":
            out.append(("Z", ()))
            cx, cy = sx, sy
            command = None
            cubic = quad = None
        else:
            raise AssertionError(f"unsupported path command {command} in {data}")
        if letter not in ("c", "s"):
            cubic = None
        if letter not in ("q", "t"):
            quad = None
    return out


def source_primitives(svg):
    out = []
    for match in SHAPE_RE.finditer(re.sub(r"<!--[\s\S]*?-->", "", svg)):
        attrs = dict(ATTR_RE.findall(match.group(2)))
        out.append((match.group(1), attrs))
    return out


def primitive_path(tag, attrs):
    fmt = lambda value: str(float(value))
    if tag == "path":
        return attrs["d"]
    if tag == "circle":
        x, y, r = (float(attrs[key]) for key in ("cx", "cy", "r"))
        return (f"M{fmt(x - r)} {fmt(y)}a{fmt(r)} {fmt(r)} 0 1 0 {fmt(2 * r)} 0"
                f"a{fmt(r)} {fmt(r)} 0 1 0 {fmt(-2 * r)} 0Z")
    if tag == "rect":
        x, y = float(attrs["x"]), float(attrs["y"])
        width, height = float(attrs["width"]), float(attrs["height"])
        r = float(attrs.get("rx", attrs.get("ry", 0)))
        if not r:
            return f"M{fmt(x)} {fmt(y)}h{fmt(width)}v{fmt(height)}h{fmt(-width)}Z"
        return (f"M{fmt(x + r)} {fmt(y)}h{fmt(width - 2 * r)}a{fmt(r)} {fmt(r)} 0 0 1 {fmt(r)} {fmt(r)}"
                f"v{fmt(height - 2 * r)}a{fmt(r)} {fmt(r)} 0 0 1 {fmt(-r)} {fmt(r)}"
                f"h{fmt(-width + 2 * r)}a{fmt(r)} {fmt(r)} 0 0 1 {fmt(-r)} {fmt(-r)}"
                f"v{fmt(-height + 2 * r)}a{fmt(r)} {fmt(r)} 0 0 1 {fmt(r)} {fmt(-r)}Z")
    if tag == "line":
        return f"M{fmt(float(attrs['x1']))} {fmt(float(attrs['y1']))}L{fmt(float(attrs['x2']))} {fmt(float(attrs['y2']))}"
    points = [float(value) for value in re.split(r"[\s,]+", attrs["points"].strip())]
    d = f"M{fmt(points[0])} {fmt(points[1])}"
    for n in range(2, len(points), 2):
        d += f"L{fmt(points[n])} {fmt(points[n + 1])}"
    return d + ("Z" if tag == "polygon" else "")


def test_every_generated_drawable_matches_its_lucide_source():
    drawables = sorted(DRAWABLE_DIR.glob("ic_lucide_*.xml"))
    assert drawables, "no generated Lucide drawables"
    checked = 0
    for drawable in drawables:
        match = SOURCE_RE.search(drawable.read_text())
        assert match, f"{drawable.name} has no lucide-static source header"
        svg = (SVG_DIR / f"{match.group(1)}.svg").read_text()
        expected = []
        for tag, attrs in source_primitives(svg):
            expected.extend(parse_path(primitive_path(tag, attrs)))

        root = ElementTree.parse(drawable).getroot()
        actual = []
        for element in root.iter():
            data = element.get(ANDROID_NS + "pathData")
            if data is not None:
                actual.extend(parse_path(data))
        assert actual, f"{drawable.name} has no pathData"
        assert len(actual) == len(expected), f"{drawable.name}: command count differs"
        for (got_cmd, got_args), (want_cmd, want_args) in zip(actual, expected):
            assert got_cmd == want_cmd, f"{drawable.name}: {got_cmd} != {want_cmd}"
            assert all(abs(a - b) < 1e-4 for a, b in zip(got_args, want_args)), (
                f"{drawable.name}: {got_cmd} {got_args} != {want_args}"
            )
        checked += 1
    assert checked == len(drawables)


def test_generated_drawables_stay_inside_the_icon_viewport():
    for drawable in DRAWABLE_DIR.glob("ic_lucide_*.xml"):
        root = ElementTree.parse(drawable).getroot()
        for element in root.iter():
            data = element.get(ANDROID_NS + "pathData")
            if data is None:
                continue
            for command, args in parse_path(data):
                for index, value in enumerate(args):
                    if command in ("M", "L", "C", "Q") or (command == "A" and index >= 5):
                        assert -2 <= value <= 26, (
                            f"{drawable.name}: {command} coordinate {value} outside 24x24 viewport"
                        )
