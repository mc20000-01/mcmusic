"""HTTPS checks before every urlopen that handles credentials or release bytes.

The GitHub fallback and the terminal client both accept a server/base URL from
configuration. Plaintext HTTP would expose login credentials or let a hostile
network substitute release assets, so both callers reject non-HTTPS URLs before
opening a connection. Loopback HTTP stays allowed for the shipped local TUI
default and for the hermetic integration tests.

    python3 -m pytest tests/test_url_safety.py -q
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "routes"))
sys.path.insert(0, str(ROOT / "app" / "linux"))

import github_builds  # noqa: E402
import system_routes  # noqa: E402
import yt_playlist_to_mp3  # noqa: E402
from mcmusic_linux.tui import Client, require_secure_server_url  # noqa: E402


class FakeConfig:
    def __init__(self, base_url):
        self.base_url = base_url
        self.cookies = {}


class GithubUrlTest(unittest.TestCase):
    def test_only_https_release_urls_are_accepted(self):
        self.assertEqual(
            github_builds._require_https("https://api.github.com/releases/latest"),
            "https://api.github.com/releases/latest",
        )
        for bad in ("http://api.github.com/releases/latest",
                    "file:///etc/passwd", "//api.github.com/x", ""):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                github_builds._require_https(bad)

    def test_request_does_not_open_plaintext_urls(self):
        with mock.patch.object(github_builds.urllib.request, "urlopen") as opened:
            with self.assertRaises(ValueError):
                github_builds._request("http://api.github.com/repos/x/y")
        opened.assert_not_called()

    def test_asset_download_does_not_open_plaintext_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset = {
                "name": "mcmusic-linux-source.zip",
                "url": "http://example.invalid/asset",
                "size": 10,
                "digest": "0" * 64,
            }
            with mock.patch.object(github_builds, "destinations",
                                   return_value=[os.path.join(tmp, "asset.zip")]), \
                    mock.patch.object(github_builds.urllib.request, "urlopen") as opened, \
                    self.assertLogs(github_builds._log, level="WARNING") as logged:
                self.assertFalse(github_builds.download(asset))
            self.assertIn("refusing non-HTTPS URL", logged.output[0])
        opened.assert_not_called()


class TuiUrlTest(unittest.TestCase):
    def test_remote_servers_must_use_https(self):
        self.assertEqual(require_secure_server_url("https://music.example.com"),
                         "https://music.example.com")
        for base in ("http://127.0.0.1:8000", "http://localhost:8000",
                     "http://[::1]:8000"):
            with self.subTest(base=base):
                self.assertEqual(require_secure_server_url(base), base)
        for bad in ("http://music.example.com", "file:///etc/passwd",
                    "ftp://music.example.com"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                require_secure_server_url(bad)

    def test_api_call_rejects_insecure_base_before_urlopen(self):
        client = Client(FakeConfig("http://music.example.com"))
        with mock.patch("mcmusic_linux.tui.urllib.request.urlopen") as opened:
            with self.assertRaises(ValueError):
                client.call("GET", "me")
        opened.assert_not_called()

    def test_download_stream_rejects_insecure_base_before_urlopen(self):
        client = Client(FakeConfig("http://music.example.com"))
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("mcmusic_linux.tui.urllib.request.urlopen") as opened:
                with self.assertRaises(ValueError):
                    client.download_stream(7, Path(tmp))
        opened.assert_not_called()


class OtherUrlopenTest(unittest.TestCase):
    def test_direct_download_rejects_plaintext_before_urlopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("urllib.request.urlopen") as opened:
                with self.assertRaises(ValueError):
                    system_routes._download_direct(
                        "http://example.invalid/file", os.path.join(tmp, "x"), 1)
        opened.assert_not_called()

    def test_lyrics_lookup_rejects_plaintext_before_urlopen(self):
        with mock.patch.object(yt_playlist_to_mp3, "LYRICS_API",
                               "http://example.invalid/api"), \
                mock.patch("urllib.request.urlopen") as opened:
            self.assertEqual(yt_playlist_to_mp3.fetch_lyrics("Song", "Artist"), ("", 0))
        opened.assert_not_called()


class SchemeTest(unittest.TestCase):
    def test_default_server_is_loopback_http(self):
        # The exemption above is deliberately narrow: it must not become a
        # blanket allowance for any URL with an HTTP scheme.
        from mcmusic_linux.tui import DEFAULT_SERVER
        self.assertEqual(urlsplit(DEFAULT_SERVER).hostname, "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
