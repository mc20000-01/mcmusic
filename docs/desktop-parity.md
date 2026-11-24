# Desktop parity task list

This is the detailed audit for the PySide6 desktop client
(`app/linux/mcmusic_linux`, shared with the macOS and Windows launchers). It is
a task source for `requirements.md`. The historical reference is the `old/`
snapshot at commit `581b995f7a5a510d936d022af52e2e8b638d0908`; the frozen old
desktop files are effectively mirrored under `old/app/linux/mcmusic_linux`.
Current web/Android code is also a comparison point where the feature moved
forward after the old commit.

No files were changed by the audit itself.

## Already present — do not redo

- Cookie session persistence and cached identity:
  `app/linux/mcmusic_linux/api.py:SessionStore.load_cookies`,
  `save_cookies`, `cached_me`; `shell.py:McWindow.after_login`, `sign_out`,
  `change_server`.
- Core library/search/likes/playlists/download requests:
  `screens.py:HomeScreen.load`, `SearchScreen._search`, `LibraryScreen.load`,
  `LikesScreen.load`, `PlaylistsScreen.load`, `PlaylistScreen.load`,
  `RequestsScreen.load`.
- Basic admin stats/users/role toggle/scan:
  `screens.py:AdminScreen.load`, `api.py:Repo.admin_stats`, `admin_users`,
  `admin_set_admin`, `admin_scan`.
- Linux MPRIS2: `mpris.py:Mpris`, `_Service.handleMessage`, `_metadata`.
- Qt/TUI dispatch: `cli.py:main`, `tui.py:main`.

## 1. Login, session, account recovery

### 1.1 Offline-resilient session restore
- **Status:** Partial. `shell.py:McWindow.__init__` loads `store.cached_me`, but
  any `/api/me` failure calls `show_login`. `ApiError` does not reliably
  distinguish offline vs unauthorized at the shell layer.
- **Do:** Classify `ApiError.status == 401` as logout. On timeout/connection/5xx
  keep cached `Me`, show “offline — using saved session”, retry later, and do
  not clear cookies/UI. Mirror Android `Account.refresh`.

### 1.2 Password reset / email change
- **Status:** Absent from desktop. `login.py:LoginPage._submit` only does
  login/register; `Repo.change_password` exists but reset endpoints do not.
- **Do:** Add `Repo.request_reset/check_reset/confirm_reset/set_email`; add
  “Forgot password?” and reset-token entry/deep-link handling to `LoginPage`;
  add email field under Settings/Account tools.

### 1.3 Rotur sign-in from login screen
- **Status:** Linking only. `SettingsScreen._open_rotur` opens the authorize
  URL; login has no Rotur option or callback handling.
- **Do:** Add desktop sign-in action, custom URL scheme or paste-token fallback,
  pending-token persistence, and verification through `/api/auth/*`.

## 2. Settings / preferences

### 2.1 Preserve full server preference schema
- **Status:** Broken/partial. `models.py:Settings` lacks `material`,
  `rotur_activity`, `discord_activity`, `show_room_url`, `real_glass`.
  `Settings.to_json` sends only 12 keys, so desktop saves revert flags managed
  by web/Android.
- **Do:** Extend `Settings` with all `src/mcmusic.py:DEFAULT_SETTINGS` keys
  except derived `room_url`; preserve unknown keys by merging remote settings
  before save, or change the client contract to patch semantics; add UI for
  missing toggles.

### 2.2 Settings screen crashes on room-link row
- **Status:** Broken. `screens.py:SettingsScreen.load` reads
  `self.window.settings.room_url` and `self.window.me.rotur_user_id`, neither of
  which exist in `models.py`.
- **Do:** Store derived `room_url` separately from persisted settings, gate on
  `show_room_url`, use the correct `Me` Rotur id field, and guard missing fields.

### 2.3 Private listening and activity toggles
- **Status:** Partial. Covers, autoplay, explicit, YouTube stats, remember
  volume, prefetch and offline cache exist; `private`, `rotur_activity`,
  `discord_activity`, `show_room_url` do not.
- **Do:** Add missing switches to Playback/Account panels and emit activity
  changes to playback code.

### 2.4 Discord link/status/unlink
- **Status:** Absent. `Repo` has Rotur status/unlink only.
- **Do:** Add `Repo.discord_status/unlink/authorize_url/activity`, Settings rows,
  browser open action, and activity publishing.

### 2.5 Server/self-host metadata and builds
- **Status:** Minimal account panel only. No `version`, `ping`, `builds`,
  `builds/email` or outbox APIs.
- **Do:** Add Repo methods and Settings panels: server/public URL, version,
  pending offline writes + “Sync now”, build list + email build, and a visible
  self-hosting guide link
  (`https://github.com/mc20000-01/mcmusic/blob/main/docs/selfhost.md`).

## 3. Playback

### 3.1 Queue persistence across restart
- **Status:** Absent. `player.py:PlayerEngine.play` initializes an in-memory
  list; no snapshot persistence.
- **Do:** Add `QueueSnapshot` persistence via `SessionStore`, throttled saves,
  validate track IDs, reset stale positions safely, and wire into
  `PlayerEngine.__init__`/`play`/`shutdown`.

### 3.2 Queue reorder
- **Status:** Absent. `PlayerEngine` has `add`, `remove_at`, `clear_upcoming`
  but no `move`; `QueueDrawer.refresh` only renders.
- **Do:** Add `PlayerEngine.move(from_index, to_index)` and drag/keyboard
  controls in `QueueDrawer`.

### 3.3 Sleep timer
- **Status:** Absent.
- **Do:** Add timer state persisted in `SessionStore`, a menu in
  `NowPlayingOverlay`, and a periodic check that pauses at the deadline.

### 3.4 Lyrics panel is wired to a nonexistent method
- **Status:** Broken. `NowPlayingOverlay.__init__` connects Lyrics to
  `window.show_lyrics`, which does not exist.
- **Do:** Implement `McWindow.show_lyrics` using existing `Repo.lyrics`, or
  disable the button until implemented.

### 3.5 Remote playback command polling
- **Status:** Publish-only. `shell.py:McWindow._publish_playback` POSTs state;
  `Repo.publish_playback` has no GET counterpart.
- **Do:** Add `Repo.playback(device_hash)` and a poll timer applying play/pause,
  next/prev, seek and enqueue commands to `PlayerEngine`.

### 3.6 Rotur/Discord activity publishing and cleanup
- **Status:** Absent. `closeEvent` stops audio but publishes no
  `playing: false`.
- **Do:** Add Repo activity methods, dedupe/throttle signature, publish on
  track/play/pause/time updates, clear on pause/stop/close, and honor settings
  toggles.

### 3.7 `offline_audio` option is not honored
- **Status:** Partial. `_load` always checks `_cached_file`; `_start` honors
  `prefetch`; `offline_audio` is never read.
- **Do:** Honor `offline_audio` in `_load/_fetch/_prefetch_next`, or relabel the
  toggle as “stream cache” to match behavior.

## 4. Library, search, likes, downloads, playlists, requests, admin

### 4.1 User-visible downloads manager
- **Status:** Internal cache only. No GUI download list/progress/remove/clear.
- **Do:** Add desktop `DownloadsScreen`, cache index, progress/bytes/remove/
  clear, sidebar nav, and playback preference for downloaded files.

### 4.2 Advanced download-request actions/log
- **Status:** Partial. `RequestLine` only exposes Approve/Reject.
- **Do:** Add cancel/retry/delete and a log sheet using
  `/api/admin/requests/<id>/log`.

### 4.3 Advanced admin console
- **Status:** Minimal stats/users/scan. Missing invites, delete user, admin
  devices, channels, enrich, lyrics, rooms and request log.
- **Do:** Extend `Repo` and add sectioned screens matching web/Android.

### 4.4 Track metadata/source info
- **Status:** Partial. Explicit toggle exists; no source panel.
- **Do:** Add `Repo.track_sources` and extend `_track_info` dialog.

## 5. Devices, Rotur activity, public profiles

### 5.1 Device pairing and management
- **Status:** Presence only (`Repo.heartbeat`, `_heartbeat`). No Devices screen.
- **Do:** Add full device endpoints, pairing-code flow, token management,
  activate/rename/forget/clear/cleanup, and admin-devices entry.

### 5.2 Public listening and profiles
- **Status:** Absent.
- **Do:** Add `Repo.public_listening/public_now`, a Listening screen, profile
  dialog/page with cover/title/artist/position, and sidebar link.

### 5.3 Listen-along / room URL
- **Status:** Intended but broken through task 2.2.
- **Do:** Fix 2.2, then add optional room join/leave controls if current server
  room APIs are still supported.

## 6. Updates and builds

### 6.1 Build list, download, email-build links
- **Status:** Absent. `Api.VERSION` is only a static User-Agent constant.
- **Do:** Add `Repo.builds/email_build/version/ping`, a “Get the app/Updates”
  Settings panel, download open action, and self-hosting link.

### 6.2 Desktop update UX
- **Status:** Absent.
- **Do:** Poll `/api/builds`, surface “download available”; for packaged builds,
  optionally download installer and launch it with explicit user consent.

### 6.3 Version metadata is inconsistent
- **Status:** `pyproject.toml` is `2.6.0`, `Api.VERSION` is `1.0.0`, macOS
  `build.sh` defaults `VERSION=1.1`, Windows `build.ps1` defaults `"1.1"`.
- **Do:** Generate one version module or read installed package metadata; use it
  everywhere and in Settings/About.

## 7. Notifications, MPRIS, media keys

### 7.1 Linux MPRIS2 — present, retain
- No major gap. Optionally connect `engine.tick` to position-property updates.

### 7.2 macOS Now Playing integration
- **Status:** Absent; README calls it a follow-up.
- **Do:** Add `MPNowPlayingInfoCenter`/remote command events wired to
  `PlayerEngine`.

### 7.3 Windows SMTC media keys
- **Status:** Absent; README calls it a follow-up.
- **Do:** Add SMTC integration in the Windows bundle and wire metadata/controls.

### 7.4 Offline/update/sync notifications
- **Status:** Internal toasts only.
- **Do:** Add persistent status strip/tray-style notifications for offline,
  pending writes, and available updates.

## 8. Offline caching and sync

### 8.1 Cached GET fallback and offline write outbox
- **Status:** Absent. `Api.request` immediately raises on connection errors.
- **Do:** Add persistent response cache for safe GETs and a replayable write
  queue for likes/playlist edits/settings; flush on reconnect/startup; expose
  pending count in Settings.

### 8.2 Cache visibility/pruning/quota
- **Status:** Hidden cache; TUI has `prune_cache` but GUI does not.
- **Do:** Add cache stats/clear/prune controls to Settings/Downloads; reuse the
  TUI pruning logic.

## 9. Keyboard shortcuts

### 9.1 Restore full legacy shortcut set
- **Status:** Ctrl-only set in `_build_shortcuts`: `Ctrl+F`, `Ctrl+Space`,
  `Ctrl+Left/Right`, `Ctrl+M`, `Ctrl+Up/Down`, `Alt+Left`, `Escape`; no editing
  guard.
- **Do:** Add direct legacy keys alongside Ctrl shortcuts, with input/textarea
  guard: Space, Shift+Arrow track/volume, `/`, `m`, `l`, `q`, Escape.

## 10. macOS / Windows packaging

### 10.1 Register desktop builds in server build registry
- **Status:** `src/builds.py:BUILDS` lists Android, Linux AppImage and Linux deb
  only. macOS and Windows scripts exist but are not registered.
- **Do:** Add `macos`, `macos-dmg`, `windows`, `windows-zip` entries, publish
  artifacts to matching directories, and expose through desktop Settings.

### 10.2 Packaging metadata/signing parity
- **Status:** Partial. macOS script supports `CODESIGN_ID` and DMG; Windows is
  unsigned. Version strings disagree (task 6.3).
- **Do:** Wire notarization/codesign and Authenticode into release docs/scripts
  if credentials exist; unify version; align build descriptions.

### 10.3 Platform media integration must ship in bundles
- **Do:** Include tasks 7.2 and 7.3 in macOS/Windows release checklist and
  verify in packaged builds, not only source checkouts.
