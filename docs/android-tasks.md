# Android tasks

Source of truth for APK-specific work in this release round. The broad parity
checklist stays in `requirements.md`; this file tracks the Android/web link
import work, the web-to-Android parity items, track gestures/removal, and their
release verification.

> Historical note: references to binaries in `builds/` describe the old
> committed snapshot. Builds are no longer tracked in git; GitHub Releases and
> the server's ignored `apps/` cache are authoritative. Old snapshots were
> preserved in non-latest releases for rollback.

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
- [x] **Release verification:** CI was green (`45355629516`); the published
      signed APK installed over 3.3.6 and launched to the sign-in gate on API 34.
      Kotlin compile, web build, Python checks and `tests.test_puller_meta` passed.
      Deeper UI paths were already exercised in the 3.3.6 emulator round and are
      unchanged structurally here.
- [x] **Delivery verification:** GitHub `latest` and live `/get` serve
      `sha256:99dc3cc77a7723bc6dd86e22398a439f8e09b0d0c2d5d037ba3b90d3bf013d43`
      (29,298,427 bytes); `apps/android`, `builds/` and `web/apps` hold the same
      bytes. Package `dev.mcmusic.app`, `versionCode 49`, `versionName 3.3.7`,
      min/target SDK 34, compile SDK 36 and the signer SHA-256 are unchanged.

## 3.3.8 round

- [x] **Player:** artwork/title drag now previews nearby queue entries while the
      finger is down without changing playback. On release it snaps to the
      nearest whole song and seeks directly to that queue index, so a long drag
      can cross several tracks instead of firing one fixed skip.
- [x] **Version:** APK bumped to `3.3.8`, code `50`, with the same signing
      identity and SDK levels.
- [x] **Release verification:** CI was green after rerunning transient failures
      (`45426118030`, `45426118741`, `45426118637`). The published signed APK
      installed over 3.3.7 and opened on API 34. In the player, left/right drags
      on the artwork and the title changed tracks only on release; a long drag
      jumped several queue entries instead of firing one fixed skip.
- [x] **Delivery verification:** this release served
      `sha256:60565f98a3a9b43247659afd4a4f3055bfc812c750b2b60b0671bd0c076ff012`
      (29,298,427 bytes) before the 3.3.9 bump; `builds/mcmusic-3.3.8.apk` is
      retained as the rollback artifact. Package `dev.mcmusic.app`, `versionCode 50`,
      `versionName 3.3.8`, min/target SDK 34, compile SDK 36 and the signer
      SHA-256 are unchanged.

## 3.3.9 styling round

- [x] **Design:** web, Android, iOS, macOS and Windows now share the five
      swatch-derived palette families (Violet, Indigo, Sky, Aqua, Mint), each
      with a light and dark half. Bare family ids follow the system appearance;
      legacy ids keep their old half. All non-icon UI uses Material 3-style
      tokens and every icon comes from a shared Lucide path registry.
- [x] **Version:** APK bumped to `3.3.9`, code `51`, with the same package,
      signing identity and SDK levels.
- [x] **Release verification:** CI run `45523137833` was green; the signed APK
      was verified against the original signer and installed over 3.3.8 on API 34.
- [x] **Delivery verification:** GitHub `latest` and live `/get` served
      `sha256:6a83502b6eda906825c3b5220162cbfea38538973581ba10f1fdf3a6dab081b2`
      (29,331,347 bytes). This was the interim Material/Lucide build; the client
      version line was then unified at 4.0.0.

## 4.0.0 unified version round

- [x] **Version:** web, Android, iOS, macOS, Windows and Linux all report
      `4.0.0`; Android code `52` and iOS build `52`, with the same signer and
      SDK levels.
- [x] **Cache:** the web shell cache and server shell generation were bumped so
      clients fetch the new bundle instead of the 3.3.9 shell.
- [x] **Release verification:** CI run `45526499418` was green. The signed APK
      installed over 3.3.9 on API 34 with package `dev.mcmusic.app`, version
      `4.0.0` (code `52`), `minSdk 34`, `targetSdk 34`, `compileSdk 36`, and
      signer SHA-256
      `0b0fd0fa35ff712901d42cab215d5e3cb706daef57bffa7ebef61cacda1dc4ce`.
- [x] **Delivery verification:** GitHub `latest` and live `/get` served
      `sha256:43892ee2b36d9de3123a88f6c5b8f4ad05c0c0e09b9d4c35bfe2e5787e06f5ba`
      (29,331,347 bytes), and `/api/builds` reported `4.0.0` with “Android 14
      and newer.” The 3.3.9 APK above stays as the rollback artifact.

## 4.0.1 icon widths

- [x] Android uses pref key `icon_stroke`, with `1x/1.5x/2x` in Appearance.
      Compose icons are built as `ImageVector`s from the vendored Lucide XMLs
      through AndroidX `PathParser`, using
      `min(size * scale / 12, size / 6)` for the rendered width. Filled mode is
      intentionally absent because the drawables are path-only outlines.
- [x] The same 1x/1.5x/2x math is used by web, iOS and Qt. The old 4px floor
      that made 1x look like 2x was removed.
- [x] CI run `45545773860` was green. The signed APK installed over 4.0.0 on
      API 34 with package `dev.mcmusic.app`, `versionCode 53`, `versionName
      4.0.1`, `minSdk 34`, `targetSdk 34`, `compileSdk 36`, and signer SHA-256
      `0b0fd0fa35ff712901d42cab215d5e3cb706daef57bffa7ebef61cacda1dc4ce`.
- [x] GitHub `latest`, live `/get`, `/api/builds`, and
      `builds/mcmusic-4.0.1.apk` all serve
      `sha256:8a8d8e1a1d42afe4073cbd811175868d68cb7a21024715b952ee66d48fc836ff`
      (29,347,731 bytes).

## Verification commands

```sh
.venv/bin/python -m unittest -q tests.test_puller_meta
(cd ui && npm run build)
(cd gui/android && ./gradlew :app:assembleRelease --no-daemon)
```
