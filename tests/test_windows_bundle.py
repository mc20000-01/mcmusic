"""Regression checks for the frozen Windows client.

The bundle bug was a launcher that imported ``mcmusic_linux.cli`` while the
PyInstaller command only collected package data. These checks keep the explicit
module flags in ``build.ps1`` and verify the Windows data locations.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "app" / "linux"))

from mcmusic_linux import paths  # noqa: E402


class WindowsBundleTests(unittest.TestCase):
    def test_build_script_bundles_the_shared_client(self):
        text = (ROOT / "app" / "windows" / "build.ps1").read_text("utf-8")
        self.assertIn('--paths "$Linux"', text)
        self.assertIn("--hidden-import mcmusic_linux.cli", text)
        self.assertIn("--collect-submodules mcmusic_linux", text)
        self.assertIn("--collect-data mcmusic_linux", text)

    def test_windows_locations_use_appdata(self):
        with patch.object(sys, "platform", "win32"), patch.dict(
            os.environ,
            {"APPDATA": "C:/Users/mc/AppData/Roaming",
             "LOCALAPPDATA": "C:/Users/mc/AppData/Local"},
        ):
            self.assertEqual(
                paths.settings_file().as_posix(),
                "C:/Users/mc/AppData/Roaming/mcmusic/mcmusic-desktop.ini",
            )
            self.assertEqual(
                paths.audio_cache_dir().as_posix(),
                "C:/Users/mc/AppData/Local/mcmusic/audio",
            )

    def test_unix_locations_keep_xdg(self):
        with patch.object(sys, "platform", "linux"), patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": "/tmp/xdg-config", "XDG_CACHE_HOME": "/tmp/xdg-cache"},
        ):
            self.assertEqual(
                paths.settings_file(),
                Path("/tmp/xdg-config/mcmusic/mcmusic-desktop.conf"),
            )
            self.assertEqual(
                paths.audio_cache_dir(), Path("/tmp/xdg-cache/mcmusic/audio")
            )


if __name__ == "__main__":
    unittest.main()
