"""Server settings schema for the unified icon-style preferences."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from mcmusic import DEFAULT_SETTINGS, _sanitize_settings  # noqa: E402


class SettingsSchemaTests(unittest.TestCase):
    def test_defaults_include_icon_styles(self):
        self.assertEqual(DEFAULT_SETTINGS["iconStroke"], 1)
        self.assertIs(DEFAULT_SETTINGS["iconFilled"], False)

    def test_icon_styles_are_normalised(self):
        out = _sanitize_settings({
            "theme": "mint-dark",
            "iconStroke": "1.7",
            "iconFilled": 1,
            "unknown": "ignored",
        })
        self.assertEqual(out["theme"], "mint-dark")
        self.assertEqual(out["iconStroke"], 1.5)
        self.assertIs(out["iconFilled"], True)
        self.assertNotIn("unknown", out)

    def test_bad_icon_stroke_falls_back_to_default(self):
        out = _sanitize_settings({"iconStroke": "wide"})
        self.assertEqual(out["iconStroke"], 1)


if __name__ == "__main__":
    unittest.main()
