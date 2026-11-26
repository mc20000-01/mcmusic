"""Standalone pages share the Flufi Music v3 shell and component classes."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from flufi_pages import FLUFI_CSS, flufi_page  # noqa: E402


class FlufiPageTests(unittest.TestCase):
    def test_helper_uses_the_generated_flufi_stylesheet(self):
        resp = flufi_page("Test", '<section class="container box">ok</section>')
        page = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(f'href="{FLUFI_CSS}"', page)
        self.assertIn('class="container box"', page)
        self.assertNotIn("radial-gradient", page)

    def test_profile_404_is_a_full_flufi_page(self):
        from mcmusic import app
        with app.test_client() as client:
            resp = client.get("/u/definitely-no-such-user-9f3a")
        page = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 404)
        self.assertIn(f'href="{FLUFI_CSS}"', page)
        self.assertIn('class="container box"', page)

    def test_embed_gallery_drops_the_monochrome_override(self):
        from mcmusic import app
        with app.test_client() as client:
            resp = client.get("/embed")
        page = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(f'href="{FLUFI_CSS}"', page)
        self.assertNotIn("Monochrome embeds", page)
        self.assertNotIn("--back:#000", page)
        self.assertIn('class="container box"', page)
        self.assertIn('class="table box"', page)

    def test_oauth_pages_use_flufi(self):
        import discord_link
        import rotur
        for module in (discord_link, rotur):
            page = module._html("Done", "All set").get_data(as_text=True)
            self.assertIn(f'href="{FLUFI_CSS}"', page)
            self.assertIn('class="container box"', page)
            self.assertIn('class="button variant-accent"', page)
            self.assertNotIn("/static/css/link.css", page)

    def test_widget_script_uses_flufi_tokens_and_flat_surfaces(self):
        path = os.path.join(ROOT, "web", "embed", "widgets.js")
        with open(path, encoding="utf-8") as fh:
            js = fh.read()
        js_lower = js.lower()
        self.assertIn("#171721", js_lower)
        self.assertIn("#9f7eff", js_lower)
        self.assertIn("var(--radius,10px)", js)
        self.assertNotIn("backdrop-filter", js)


if __name__ == "__main__":
    unittest.main()
