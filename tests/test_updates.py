"""Updater selection, version comparison and verified download tests."""
from __future__ import annotations

import hashlib
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from mcmusic_linux.models import BuildInfo  # noqa: E402
from mcmusic_linux import updates  # noqa: E402


def build(**changes) -> BuildInfo:
    values = dict(kind="windows-zip", label="Windows", name="mcmusic for Windows",
                  available=True, file="mcmusic-windows-4.2.0.zip",
                  version="4.2.0", url="/apps/windows/mcmusic-windows-4.2.0.zip?v=abc",
                  bytes=0)
    values.update(changes)
    return BuildInfo(**values)


class VersionTests(unittest.TestCase):
    def test_dotted_versions_only(self) -> None:
        self.assertEqual((4, 1, 0), updates.version_tuple("4.1.0"))
        self.assertEqual((), updates.version_tuple("x86_64"))
        self.assertEqual((), updates.version_tuple(""))

    def test_newer_requires_a_real_dotted_version(self) -> None:
        self.assertTrue(updates.is_newer("4.2.0", "4.1.0"))
        self.assertTrue(updates.is_newer("4.1.1", "4.1.0"))
        self.assertFalse(updates.is_newer("4.1.0", "4.1.0"))
        self.assertFalse(updates.is_newer("4.0.9", "4.1.0"))
        self.assertFalse(updates.is_newer("x86_64", "4.1.0"))


class SelectionTests(unittest.TestCase):
    def test_platform_preference(self) -> None:
        self.assertEqual(("macos-dmg", "macos"), updates.platform_kinds("Darwin"))
        self.assertEqual(("windows-zip", "windows"), updates.platform_kinds("Windows"))
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(("linux-deb", "linux-appimage"),
                             updates.platform_kinds("Linux"))
        with patch.dict(os.environ, {"APPIMAGE": "/tmp/mcmusic.AppImage"}):
            self.assertEqual(("linux-appimage", "linux-deb"),
                             updates.platform_kinds("Linux"))

    def test_finds_newest_platform_build_and_skips_unversioned(self) -> None:
        rows = [
            build(kind="android", version="9.9.9"),
            build(kind="linux-appimage", version="", file="mcmusic-x86_64.AppImage"),
            build(kind="linux-deb", version="4.2.0", url="/apps/linux/a.deb"),
            build(kind="linux-deb", version="4.1.0", url="/apps/linux/old.deb"),
        ]
        found = updates.find_update(rows, "4.1.0", system="Linux")
        self.assertEqual("4.2.0", found.version)
        self.assertEqual("/apps/linux/a.deb", found.url)

    def test_no_update_when_everything_is_current(self) -> None:
        rows = [build(version="4.1.0"), build(kind="android", version="9.0.0")]
        self.assertIsNone(updates.find_update(rows, "4.1.0", system="Windows"))


class DownloadTests(unittest.TestCase):
    def test_streams_verifies_and_reuses_the_cached_artifact(self) -> None:
        payload = b"mcmusic installer bytes" * 128
        digest = hashlib.sha256(payload).hexdigest()[:16]
        requests_seen = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests_seen.append(self.path)
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        root = tempfile.TemporaryDirectory()
        # addCleanup runs in reverse order: stop serving first, then join.
        self.addCleanup(thread.join)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.addCleanup(root.cleanup)
        with patch.object(updates, "updates_dir", return_value=Path(root.name)):
            artifact = build(bytes=len(payload), url=f"/build.zip?v={digest}")
            first = updates.download(artifact, f"http://127.0.0.1:{server.server_port}")
            second = updates.download(artifact, f"http://127.0.0.1:{server.server_port}")

        self.assertEqual(first, second)
        self.assertEqual(payload, first.read_bytes())
        self.assertTrue(hashlib.sha256(payload).hexdigest().startswith(digest))
        self.assertEqual(1, len(requests_seen))
        self.assertEqual([], list(Path(root.name).glob("*.part")))

    def test_corrupt_payload_is_rejected(self) -> None:
        payload = b"not the published bytes"

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        root = tempfile.TemporaryDirectory()
        # addCleanup runs in reverse order: stop serving first, then join.
        self.addCleanup(thread.join)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.addCleanup(root.cleanup)
        with patch.object(updates, "updates_dir", return_value=Path(root.name)):
            artifact = build(bytes=len(payload),
                             url="/build.zip?v=" + "0" * 16)
            with self.assertRaises(IOError):
                updates.download(artifact, f"http://127.0.0.1:{server.server_port}")
        self.assertEqual([], list(Path(root.name).glob("*.part")))


if __name__ == "__main__":
    unittest.main()
