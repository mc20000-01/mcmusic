"""CORS headers are emitted only when an origin is explicitly configured."""
import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

import mcmusic  # noqa: E402

CORS_HEADERS = (
    "Access-Control-Allow-Origin",
    "Access-Control-Allow-Headers",
    "Access-Control-Allow-Methods",
    "Access-Control-Expose-Headers",
)


def vary_tokens(response):
    return {part.strip().lower() for part in
            response.headers.get("Vary", "").split(",") if part.strip()}


class CorsHeaderTests(unittest.TestCase):
    def setUp(self):
        mcmusic.app.config.update(TESTING=True)
        self.client = mcmusic.app.test_client()

    def test_empty_origin_emits_no_cors_headers(self):
        with patch.object(mcmusic, "CORS_ORIGIN", ""):
            response = self.client.get("/api/version")
        self.assertEqual(200, response.status_code)
        for name in CORS_HEADERS:
            self.assertNotIn(name, response.headers, name)
        # Flask may add Vary: Cookie when a session is touched; that is fine,
        # but an Origin dimension must not appear without a CORS grant.
        self.assertNotIn("origin", vary_tokens(response))

    def test_configured_origin_emits_cors_headers_and_vary(self):
        with patch.object(mcmusic, "CORS_ORIGIN", "https://app.example"):
            response = self.client.get("/api/version")
        self.assertEqual(200, response.status_code)
        self.assertEqual("https://app.example",
                         response.headers["Access-Control-Allow-Origin"])
        self.assertIn("origin", vary_tokens(response))
        self.assertIn("Authorization", response.headers["Access-Control-Allow-Headers"])

    def test_manifest_follows_the_same_rule(self):
        with patch.object(mcmusic, "CORS_ORIGIN", ""):
            response = self.client.get("/manifest.webmanifest")
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)
        self.assertNotIn("origin", vary_tokens(response))


if __name__ == "__main__":
    unittest.main()
