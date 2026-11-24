"""Rotur status cards: song-specific art and both mcmusic links."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

import rotur  # noqa: E402
from music_activity.sinks.rotur import RoturSink  # noqa: E402


class RoturActivityTests(unittest.TestCase):
    def _activity(self):
        track = {
            "id": 42,
            "title": "A Song",
            "artist": "An Artist",
            "album": "An Album",
            "duration": 180,
        }
        state = rotur.listening_activity(
            track,
            position=12,
            room_url="https://mcmusic.sdisk.us/#room=abc",
            cover_url="https://mcmusic.sdisk.us/u/sandisk/A%20Song.png?track=42",
            profile_url="https://mcmusic.sdisk.us/u/sandisk",
            status_room="",
        )
        return RoturSink("test").activity(state)

    def test_image_url_is_for_the_song_in_the_activity(self):
        activity = self._activity()
        self.assertEqual(
            activity["image"],
            "https://mcmusic.sdisk.us/u/sandisk/A%20Song.png?track=42",
        )

    def test_heading_links_to_play_with_me(self):
        activity = self._activity()
        self.assertEqual(activity["url"], "https://mcmusic.sdisk.us/#room=abc")

    def test_buttons_include_play_with_me_and_profile(self):
        activity = self._activity()
        self.assertEqual(activity["buttons"], [
            {"label": "Play with me", "url": "https://mcmusic.sdisk.us/#room=abc"},
            {"label": "mcmusic profile", "url": "https://mcmusic.sdisk.us/u/sandisk"},
        ])

    def test_room_is_not_repeated_in_the_status_line(self):
        activity = self._activity()
        self.assertNotIn("room=abc", activity["status"])


if __name__ == "__main__":
    unittest.main()
