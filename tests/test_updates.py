"""Version comparison, platform selection and download-page URL tests."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from mcmusic_linux.models import BuildInfo  # noqa: E402
from mcmusic_linux import updates  # noqa: E402


def build(**changes) -> BuildInfo:
    values = dict(kind="windows-zip", label="Windows", name="mcmusic for Windows",
                  available=True, file="mcmusic-windows-4.2.0.zip",
                  version="4.2.0", url="/apps/windows/mcmusic-windows-4.2.0.zip",
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


class DownloadPageTests(unittest.TestCase):
    def test_points_at_the_public_page_not_an_artifact(self) -> None:
        self.assertEqual("https://mcmusic.example/downloads",
                         updates.download_page("https://mcmusic.example/"))
        self.assertEqual("http://localhost:8000/downloads",
                         updates.download_page("http://localhost:8000"))


if __name__ == "__main__":
    unittest.main()
