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

import artists  # noqa: E402
import database  # noqa: E402
import dedupe_library  # noqa: E402
import library_scan  # noqa: E402
import song_meta  # noqa: E402
import zip_import  # noqa: E402


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

    def test_with_is_not_an_artist_credit(self):
        meta = song_meta.parse_song_meta(
            "Good Kid - Alone With Me (Official Video)", uploader="Good Kid")
        self.assertEqual(meta["title"], "Alone With Me")
        self.assertNotIn("Me", meta["artists"])

        meta = song_meta.parse_song_meta(
            "Good Kid - Down with the King (Official Video)", uploader="Good Kid")
        self.assertEqual(meta["title"], "Down with the King")
        self.assertNotIn("the King", meta["artists"])

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

    def test_dedupe_merges_uncredited_rip_and_keeps_fuller_credit(self):
        def row(rid, artists, **extra):
            base = dict(
                id=rid, path=f"{rid}.mp3", title="Break", artist="",
                artists=json.dumps(artists), duration=180.0, yt_id=None,
                lyrics="", genre="", album="",
            )
            base.update(extra)
            return base

        rows = [
            row(1, []),
            row(2, ["Good Kid", "Jonathon Kereliuk", "David Wood"]),
        ]
        groups = dedupe_library.find_groups(rows)
        self.assertEqual(len(groups), 1)
        self.assertEqual(dedupe_library.survivor(groups[0])["id"], 2)

    def test_dedupe_ignores_duration_for_same_name_and_artist(self):
        rows = [
            dict(id=1, path="a.mp3", title="Summer", artist="Good Kid",
                 artists=json.dumps(["Good Kid"]), duration=180.0, yt_id="a" * 11,
                 lyrics="", genre="", album="", themes=""),
            dict(id=2, path="b.mp3", title="Summer", artist="Good Kid",
                 artists=json.dumps(["Good Kid"]), duration=240.0, yt_id="b" * 11,
                 lyrics="", genre="", album="", themes=""),
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


class ArtistPageTests(unittest.TestCase):
    def test_every_credited_artist_gets_its_own_page(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("create table tracks(id integer primary key, path text, title text, "
                     "artist text, artists text)")
        conn.execute("create table track_artists(track_id integer, artist text, "
                     "position integer, artist_key text)")
        conn.execute("insert into tracks(id,path,title,artist) values(1,'s.mp3','Song','A, B')")
        artists.index_track(conn, 1, "A, B", "Song", names=["A", "B"])
        self.assertEqual(
            [r["artist"] for r in conn.execute(
                "select artist from track_artists where track_id=1 order by position")],
            ["A", "B"],
        )
        for name in ("A", "B"):
            rows = conn.execute(
                "select t.* from tracks t join track_artists a on a.track_id=t.id "
                "where a.artist_key=?", (artists.norm_key(name),),
            ).fetchall()
            self.assertEqual([r["id"] for r in rows], [1])
        conn.close()


class UnknownMetadataTests(unittest.TestCase):
    def test_unknown_artist_is_not_a_real_credit(self):
        self.assertFalse(library_scan.has_real_artist(
            {"artist": "Unknown Artist", "artists": "[]"}))
        self.assertFalse(library_scan.has_real_artist(
            {"artist": "", "artists": json.dumps(["Unknown Artist"])}))
        self.assertTrue(library_scan.has_real_artist(
            {"artist": "Good Kid", "artists": json.dumps(["Good Kid"])}))

    def test_zip_fallback_uses_artist_from_filename(self):
        meta = zip_import.clean_meta(
            "Unknown Artist", "Unknown Artist", rel="Good_Kid_-_Break.mp3")
        self.assertEqual(meta["title"], "Break")
        self.assertEqual(meta["artists"], ["Good Kid"])
        self.assertEqual(zip_import.filename_meta("Good_Kid_-_Break.mp3"),
                         ("Break", "Good Kid"))


class DirectLinkTests(unittest.TestCase):
    def test_youtube_links_are_still_accepted(self):
        from routes.system_routes import valid_request_url
        self.assertTrue(valid_request_url("https://youtu.be/abc123"))
        self.assertTrue(valid_request_url("https://music.youtube.com/watch?v=abc123"))

    def test_direct_audio_and_zip_links_are_accepted(self):
        from routes.system_routes import direct_file_ext, valid_request_url
        cases = {
            "https://cdn.example.com/album.zip": ".zip",
            "https://cdn.example.com/song.MP3?token=1": ".mp3",
            "https://cdn.example.com/song%2Emp3": ".mp3",
            "https://cdn.example.com/track.flac": ".flac",
        }
        for url, ext in cases.items():
            self.assertEqual(direct_file_ext(url), ext)
            self.assertTrue(valid_request_url(url))

    def test_plain_http_and_unsupported_files_are_rejected(self):
        from routes.system_routes import direct_file_ext, valid_request_url
        for url in (
            "http://cdn.example.com/album.zip",
            "https://cdn.example.com/notes.txt",
            "https://user:pass@cdn.example.com/album.zip",
            "https://cdn.example.com/no-extension",
        ):
            self.assertEqual(direct_file_ext(url), "")
            self.assertFalse(valid_request_url(url))


class PlaylistLinkTests(unittest.TestCase):
    def test_short_legacy_and_standard_playlist_ids_are_accepted(self):
        from routes.system_routes import request_url_problem, valid_request_url
        for playlist in (
            "PLa7A5JeQiTQE",                      # 13-character legacy playlist
            "PL96C35uN7xGLLeET0dOWaKHkAlPsrkcha",  # standard 34-character playlist
            "OLAK5uy_nTjJd7OaiHPtS4Nfr1IyB0",     # YouTube Music album playlist
            "WL",                                  # watch later
        ):
            url = f"https://www.youtube.com/playlist?list={playlist}&si=y8lNVEZO5eu2pTfH"
            self.assertIsNone(request_url_problem(url), playlist)
            self.assertTrue(valid_request_url(url), playlist)

    def test_truncated_or_malformed_playlist_ids_are_rejected(self):
        from routes.system_routes import request_url_problem, valid_request_url
        for playlist in ("PLa7A5", "PLa7A5.JeQiTQE", "PL" + "!" * 12):
            url = f"https://www.youtube.com/playlist?list={playlist}"
            self.assertIsNotNone(request_url_problem(url), playlist)
            self.assertFalse(valid_request_url(url), playlist)


if __name__ == "__main__":
    unittest.main()
