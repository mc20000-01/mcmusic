"""Backend tests for the song puller's parsing, dedup and metadata storage.

Pure functions first (no network, no yt-dlp), then a throwaway SQLite DB to
check that the new columns exist and reach the API row shape.
"""
import json
import os
import sqlite3
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import database  # noqa: E402
import dedupe_library  # noqa: E402
import song_meta  # noqa: E402


class SongMetaTests(unittest.TestCase):
    def test_title_filtering_keeps_version_info(self):
        self.assertEqual(
            song_meta.clean_title("A & B - Song (Official Audio) (HD)"),
            "Song",
        )
        self.assertEqual(
            song_meta.clean_title("01 - Mesmerizer (High Version)"),
            "Mesmerizer (High Version)",
        )
        self.assertEqual(
            song_meta.clean_title("Mesmerizer Official Music Video (4K)"),
            "Mesmerizer",
        )

    def test_all_credited_artists_without_channel_noise(self):
        meta = song_meta.parse_song_meta(
            "IRIS OUT (English Cover)「CHAINSAW MAN - Reze Arc OP」【Will Stetson】",
            uploader="Some Channel",
        )
        self.assertEqual(meta["artists"], ["Will Stetson"])
        self.assertNotIn("Some Channel", meta["artist"])

        meta = song_meta.parse_song_meta(
            "A feat. B - Song (Official Video)", uploader="Uploader Topic"
        )
        self.assertEqual(meta["title"], "Song")
        self.assertEqual(meta["artists"], ["A", "B"])

    def test_channel_is_fallback_only(self):
        meta = song_meta.parse_song_meta("Just A Song", uploader="A Random Uploader")
        self.assertEqual(meta["artists"], ["A Random Uploader"])

    def test_themes_from_any_available_metadata(self):
        meta = song_meta.parse_song_meta(
            "Hito Mania (English Cover)「人マニア」【Will Stetson】",
            description="#Vocaloid\nArtist: Will Stetson",
            tags=["anime", "cover"],
            categories="Music",
        )
        for theme in ("English Cover", "Vocaloid", "人マニア", "anime"):
            self.assertIn(theme, meta["themes"])
        self.assertNotIn("Will Stetson", meta["themes"])

    def test_video_id(self):
        self.assertEqual(
            song_meta.video_id("https://www.youtube.com/watch?v=5VDg9GJ0UJ4"),
            "5VDg9GJ0UJ4",
        )
        self.assertIsNone(song_meta.video_id(
            "https://music.youtube.com/playlist?list=PLa7A5.JeQiTQE"))

    def test_dedup_keeps_non_latin_titles_and_sorts_artist_credits(self):
        self.assertTrue(dedupe_library.norm("しろいき。"))
        rows = [
            {
                "id": 1, "path": "a.mp3", "title": "Mesmerizer (Official Video)",
                "artist": "A feat. B", "artists": json.dumps(["A", "B"]),
                "duration": 180.0, "yt_id": None,
            },
            {
                "id": 2, "path": "b.mp3", "title": "Mesmerizer",
                "artist": "B, A", "artists": json.dumps(["B", "A"]),
                "duration": 181.0, "yt_id": None,
            },
            {
                "id": 3, "path": "c.mp3", "title": "Mesmerizer (Nightcore)",
                "artist": "A feat. B", "artists": json.dumps(["A", "B"]),
                "duration": 180.0, "yt_id": None,
            },
        ]
        groups = dedupe_library.find_groups(rows)
        self.assertEqual(len(groups), 1)
        self.assertEqual([r["id"] for r in groups[0]], [1, 2])


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db_path = database.DB_PATH
        database.DB_PATH = os.path.join(self.tmp.name, "test.db")
        self.conn = sqlite3.connect(database.DB_PATH)
        self.conn.row_factory = sqlite3.Row
        database.ensure_schema(self.conn)

    def tearDown(self):
        self.conn.close()
        database.DB_PATH = self.old_db_path
        self.tmp.cleanup()

    def test_themes_column_reaches_api_rows(self):
        self.conn.execute(
            "insert into tracks(path,title,artist,artists,themes,yt_tags) "
            "values(?,?,?,?,?,?)",
            ("song.mp3", "Song", "A, B", json.dumps(["A", "B"]),
             json.dumps(["Cover", "Anime"]), json.dumps(["tag"])),
        )
        row = self.conn.execute("select * from tracks").fetchone()
        data = database.track_dict(self.conn, row)
        self.assertEqual(data["artists"], ["A", "B"])
        self.assertEqual(data["themes"], ["Cover", "Anime"])
        self.assertEqual(data["yt_tags"], ["tag"])

    def test_repeat_requests_and_library_checks(self):
        self.conn.execute(
            "insert into requests(user_id,url,status,created) values(1,?,'approved',0)",
            ("https://www.youtube.com/watch?v=5VDg9GJ0UJ4",),
        )
        repeat = database.find_repeat_request(
            self.conn, "https://youtu.be/5VDg9GJ0UJ4")
        self.assertIsNotNone(repeat)
        self.assertFalse(database.video_in_library(
            self.conn, "https://www.youtube.com/watch?v=5VDg9GJ0UJ4"))
        self.conn.execute(
            "insert into tracks(path,title,artist,yt_id) values(?,?,?,?)",
            ("song.mp3", "Song", "A", "5VDg9GJ0UJ4"),
        )
        self.assertTrue(database.video_in_library(
            self.conn, "https://www.youtube.com/watch?v=5VDg9GJ0UJ4"))


if __name__ == "__main__":
    unittest.main()
