"""Pure checks for the Qt Lucide renderer's 4.0.1 stroke/fill behaviour."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "app", "linux"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from mcmusic_linux import icons, widgets
except ImportError as exc:  # system python may not have PySide6
    QT_ERROR = str(exc)
else:
    QT_ERROR = ""


@unittest.skipIf(QT_ERROR, f"PySide6 not available: {QT_ERROR}")
class QtIconStyleTests(unittest.TestCase):
    def tearDown(self):
        icons.set_icon_style(1.0, False)

    def test_nearest_stroke_snaps_to_allowed_values(self):
        self.assertEqual(icons.nearest_stroke(0.2), 1.0)
        self.assertEqual(icons.nearest_stroke("1.7"), 1.5)
        self.assertEqual(icons.nearest_stroke(2), 2.0)
        self.assertEqual(icons.nearest_stroke("wide"), 1.0)

    def test_stroke_width_uses_lucide_default_at_1x(self):
        self.assertAlmostEqual(icons.stroke_width(1.0, 20), 20.0 / 12)
        self.assertAlmostEqual(icons.stroke_width(1.5, 20), 20.0 / 8)
        self.assertAlmostEqual(icons.stroke_width(2.0, 32), 32.0 / 6)
        self.assertAlmostEqual(icons.stroke_width(2.0, 52), 52.0 / 6)
        self.assertEqual(icons.stroke_width(1.0, 48), 4.0)
        self.assertAlmostEqual(icons._viewbox_stroke(1.0, 16), 2.0)

    def test_shape_fill_only_touches_circles_and_rects(self):
        outline = icons._build_svg("settings", "#abc", False, 2, False)
        self.assertIn('fill="none"', outline)
        self.assertNotIn('<circle cx="12" cy="12" r="3" fill=', outline)

        filled = icons._build_svg("settings", "#abc", False, 2, True)
        self.assertIn('<circle cx="12" cy="12" r="3" fill="#abc" stroke="none"/>', filled)
        self.assertEqual(filled.count('stroke="none"'), 1)

        # Explicitly filled primitives keep their original geometry treatment.
        play = icons._build_svg("play", "#abc", False, 2, True)
        self.assertIn('fill="#abc" stroke="none"', play)
        pause = icons._build_svg("pause", "#abc", False, 2, True)
        self.assertEqual(pause.count('fill="#abc" stroke="none"'), 2)

    def test_explicit_force_fill_still_fills_paths(self):
        liked = icons._build_svg("heart", "#abc", True, 2, False)
        self.assertIn('fill="#abc" stroke="none"', liked)

    def test_global_icon_style_is_used_by_the_renderer_cache(self):
        icons.set_icon_style(1.5, True)
        self.assertEqual(icons.icon_style(), (1.5, True))
        self.assertIn('stroke-width="3.0"', icons._build_svg(
            "radio", "#fff", False, icons._viewbox_stroke(1.5, 32), True))

    def test_theme_refresh_ignores_qt_style_callables(self):
        class FakeWidget:
            def __init__(self):
                self.updates = 0

            def update(self):
                self.updates += 1

        class FakeRoot(FakeWidget):
            def __init__(self, child):
                super().__init__()
                self.child = child

            def findChildren(self, _cls):
                return [self.child]

        class FakeQtCallable:
            def __call__(self):
                raise AssertionError("Qt callable must not be used as a hook")

        child = FakeWidget()
        child.refresh_theme = FakeQtCallable()
        root = FakeRoot(child)
        root.refresh_theme = lambda: None  # declared functions remain valid

        widgets.refresh_theme(root)

        self.assertEqual(root.updates, 1)
        self.assertEqual(child.updates, 1)


if __name__ == "__main__":
    unittest.main()
