# Android tasks

Source of truth for APK-specific work in this release round. The broad parity
checklist stays in `requirements.md`; this file tracks the Android/web link
import work, the web-to-Android parity items, track gestures/removal, and their
release verification.

## Direct music links (web + APK)

- [x] **Server:** `POST /api/requests` accepts YouTube links and direct https
      audio/ZIP links. Plain http, embedded credentials, unsupported extensions
      and oversized files are rejected.
- [x] **Server:** direct audio files stream into staging (2 GiB cap) and move
      into `MUSIC_DIR/Direct Imports` for the normal scan. ZIP links are handed
      to the existing `src/zip_import.py` importer, which reads tags, keeps
      sidecars and queues YouTube enrichment.
- [x] **Web:** Add music accepts YouTube, direct MP3/audio, and ZIP links; the
      request list and approval flow are unchanged.
- [x] **APK:** Downloads has an “Add music” form for YouTube/MP3/ZIP links,
      mirrors the server’s validation, and submits through `/api/requests`.
- [x] **APK:** Downloads shows “Your requests” with the same status wording as
      the web client, so an import can be followed without leaving the app.

## Web-to-Android parity (liked songs, lyrics, track actions)

- [x] **APK:** `LikesScreen` (`ui/screens/Likes.kt`) loads `GET /api/likes` through
      `Api.likes()`, lists tracks with the normal `TrackRow` menu, plays them all
      with `Playback.play`, and refreshes with the shared library revision.
      Library opens it from a dedicated “Liked songs” card; the route is a
      full-screen tab so Back returns to the previous page.
- [x] **APK:** The Player controls have a lyrics toggle (`ListMusic` glyph) and a
      panel that calls `Api.lyrics(trackId)` (`GET /api/tracks/<id>/lyrics`) only
      while open. LRC lines are timestamp-highlighted and followed while plain
      text is shown as-is; loading, missing, retry and error states are covered.
- [x] **APK:** The track action menu adds “Start radio” (seed + `Api.radio`),
      “Go to artist” where a collection sheet route exists (Home, Search,
      Library, collection sheets and Playlists), and “Track info” using the
      fields already in the `Track` model. Like, Add to playlist and admin
      Remove are unchanged. UUID and source counts are not shown because the
      app's `Track` model does not carry them.
- [x] Verify on the emulator: liked-songs card, lyrics panel, radio/artist menu
      entries and the info dialog. Radio playback and artist sheet were not
      launched; their menu entries and data paths are present.

## Track row gestures and library removal

- [x] Every track row supports swipe right to like/unlike and long-press to open
      the same action menu as the ellipsis button.
- [x] Admins get swipe left (or the action menu) to remove a track from
      mcmusic, with a confirmation dialog. The server endpoint deletes the row,
      file, likes, playlists and queue references.
- [x] A shared library revision refreshes Home, Search, Library, collection
      sheets and Playlists after a like or deletion; `Playback.removeTrack`
      also drops a deleted track from the local queue so it cannot be streamed
      again.
- [x] Verify on the emulator: swipe-right like/unlike (liked count changed),
      ellipsis menu with Like/Start radio/Go to artist/Track info, and the admin
      Remove confirmation dialog. The deletion was cancelled so library data was
      not destroyed; long-press opens the same menu in code but the slow
      emulator's injected long-press was read as a normal tap.

## 3.3.7 round

- [x] **Account links:** Settings shows Rotur/Discord linked state, connect and
      unlink controls. Native browser flows use one-use server tickets so the
      OAuth callback can bind the account without an `Authorization` header.
- [x] **Videos:** the Videos tab lists locally cached MP4s from request imports;
      playback uses ExoPlayer over a `SurfaceView`, no YouTube embed. Viewing
      slides the four-hour cache expiry forward. Music pauses while a video
      plays and resumes at the returned song position.
- [x] **Player:** horizontal cover/title swipes skip tracks, queue rows swipe
      left to remove, LRC parsing/offsets and tap-to-seek were tightened, and a
      current-line preview sits above the scrubber.
- [x] **MDL:** shuffle asks `POST /api/model/rank` and only adopts the server
      order once the 76% work-rate gate opens; Media3 random shuffle remains the
      fallback. Radio-driven autoplay inherits the server's MDL ranking.
- [x] **Lyrics visualizer:** Bars/Wave/Glow modes are available in the lyrics
      panel, driven deterministically by playback position and active line.
- [x] **Version:** APK bumped to `3.3.7`, code `49`, so it installs over 3.3.6
      with the same signing identity.
- [ ] **Release verification:** after CI publishes, install the signed APK and
      confirm sign-in, Settings, likes, lyrics/visualizer, track menu, videos,
      direct-link request form and queue gestures.
- [ ] **Delivery verification:** GitHub `latest` and live `/get` serve the same
      `3.3.7` bytes; package/signer/SDK versions match the release checklist.

## Verification commands

```sh
.venv/bin/python -m unittest -q tests.test_puller_meta
(cd ui && npm run build)
(cd gui/android && ./gradlew :app:assembleRelease --no-daemon)
```
