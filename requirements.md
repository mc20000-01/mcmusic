# mcmusic implementation requirements

Working checklist for the current round. Earlier redesign requests, the newest
fixes, and the old-client parity audit are consolidated here. Anything marked
**Need input** is blocked on information from you; everything else is actionable.

## Done

- [x] Archive the pre-`ui/` repo as an untracked, gitignored `old/` folder.
  - Exact source: `581b995f7a5a510d936d022af52e2e8b638d0908`.
  - `old/app/` and `old/web/` are present.
  - Current working tree was not reverted.
- [x] Android app is gated behind a verified sign-in; no app screens render
  before `Account.loaded && Account.signedIn`.
- [x] Android design uses the five shared palette families (Violet, Indigo,
  Sky, Aqua, Mint) with Material 3 surfaces, one 10dp radius and Lucide icons.
- [x] Android in-app self-update uses `/api/builds` and the same signed APK the
  website serves.
- [x] Android 14+ is the supported floor (`minSdk = 34`, `targetSdk = 34`).
- [x] Signed release chain is aligned: GitHub `latest` = `builds/` =
  `apps/android/` = live `/get`; original signer SHA-256 unchanged.
- [x] CI was green for the previous published source commit.
- [x] **Settings cannot open on Android — root cause found and fixed in source.**
  `SettingRow`'s trailing composable was used for click actions, so opening
  Settings immediately ran sign-out and opened Android notification settings.
  Sign out and Notifications now use named `onClick`.
- [x] **Rotur activity source choice:** use legacy `old/web/js/rotur.js` as the
  reference and port it into the current `ui/` web client.
- [x] **Android parity merge compile fixes:** explicit `Runnable` type in
  `Playback`, `rememberCoroutineScope` import, public `Playback.tick()`, and
  `LocalUriHandler` read from a composable scope.

## Implemented — final verification pending

- [x] **Android login does not persist after app close / focus loss.**
  - Token is already in `Prefs` SharedPreferences; nothing clears it on pause.
  - Real cause: `Account.refresh()` drops the cached identity on any `/api/me`
    failure, so a Wi-Fi blip shows the gate. A real 401 also clears the token.
  - Fix: persist last verified `Me`, keep it on transient failures, clear only
    on 401, revalidate on resume, and make Rotur deep-link token adoption
    retryable/race-safe.
- [x] **A few songs disappear from the Android queue.**
  - `Playback.queueTracks` is in-memory only; duplicate IDs collapse LazyColumn
    keys; shuffle index mismatch and 200-item server mirror cap also hide songs.
  - Fix: persist queue/index/position/repeat/shuffle/autoplay, use occurrence
    aware keys, and restore on cold start / service recreation.
- [x] **Autoplay at the end of the queue (Android and web).**
  - Add visible toggle at the end of the queue, **on by default**.
  - Only append 5 unique songs when playback truly reaches the end of the
    queue, not while one or two tracks before it.
  - One-song queue + autoplay off plays that one song and stops.
  - Loop-one repeats only the current song and does not append anything.
  - Any repeat mode on turns autoplay off; autoplay on turns repeat off.
  - Server endpoint: `GET /api/radio/<id>`.
- [x] **Web queue and playback persistence.** Queue, index, position, duration,
      repeat, shuffle and autoplay now persist with paused restore, stale-position
      reset and 7-day expiry. `npm run build` passes.
- [x] **Rotur activity integration.** Ported `old/web/js/rotur.js` behavior:
      status/health/session validity, describe text, link/unlink, and activity
      start/stop tied to playback. Discord status/link/unlink was also added.
- [x] **Full web/Android parity with old commit `581b995f...`.**
  - Web and Android source parity items are done; final signed build and emulator
    pass are still pending.
  - Backend routes are mostly still present; these are client-surface gaps.

## Parity gaps from the audit (work list)

### Android — missing or regressed vs old commit

- [x] Settings: Rotur activity toggle, Discord activity toggle, Appearance
      controls (palette/design language, covers, hide explicit).
- [x] Home listener cards: public profile link, listener position/duration.
- [x] Search: directory/profile lookup alongside tracks/albums/artists.
- [x] Track menus: Like (`Api.toggleLike` already exists) and Add to playlist
      (`Api.addToPlaylist` already exists).
- [x] Android track rows now support swipe-right like, long-press menu, and
      admin swipe-left “Remove from mcmusic” with confirmation; the menu also
      has Start radio, Go to artist and Track info.
- [x] Android parity for Liked songs and the synced/plain lyrics panel; both
      are reachable from Library and the Player respectively.
- [x] Queue reorder: wire `Playback.move()` to drag handles if feasible.

### Web — missing or regressed vs old commit

- [x] Full search page/route and `/` shortcut; Likes view; Downloads view.
- [x] Public profile links and listener info from `/api/public/listening`.
- [x] PWA service-worker registration, install prompt, update-ready handling.
- [x] Keyboard shortcuts: Space, Shift+Arrow keys, `/`, `m`, `l`, `q`, Escape.
- [x] Home via `/api/home`; playback presence `/api/playback`; device
      heartbeat/command polling; offline cache/outbox; build/version UI.
- [x] Discord link/unlink/status UI; richer Rotur health/session display.
- [x] Admin Devices/Channels/Enrich/Lyrics panels where backend routes exist.
- [x] Email change, track explicit-flag edit, track info/sources dialog.

## Emulator verification (time is not a constraint)

- [x] Fresh Android 14 (API 34) AVD `mcmusic34fresh` booted successfully after
      switching from invalid `-accel kvm` to `-accel on`.
- [x] Installed the `3.3.4` signed hotfix APK and launched the app. Android's
      POST_NOTIFICATIONS prompt appeared as expected and was accepted.
- [x] Verify after the next full build: sign-in gate, signed-in home, Settings
      opens, login persists after app force-stop/relaunch, queue/player restore,
      liked songs, synced lyrics, track menu, swipe-to-like, admin remove
      confirmation, and the Downloads direct-link form. Email-password entry was
      exercised against the API but the slow emulator dropped injected keystrokes,
      so the app was signed in with an API-issued device token instead. Rotur
      deep-link return still needs the external OAuth round trip.
- [x] Capture UI dumps for the report. The emulator is extremely slow on this
      host (no xsave/avx); system ANR overlays from Launcher/System UI were
      cleared with `CLOSE_SYSTEM_DIALOGS` before capturing each screen.

## Release and delivery steps (repeat after the next code change)

- [x] Bump every client to `4.0.0`; Android code `52`, iOS build `52`.
- [x] Commit and push; GitHub Actions `Release builds` run `45526499418` went
      green.
- [x] Pull the bot commit that refreshes `builds/`.
- [x] Confirm the exact GitHub `latest` APK is copied into
  `apps/android/mainbuild.apk`, `apps/android/mcmusic-4.0.0.apk`, and a hashed
  `apps/android/mainbuild-<hash>.apk`. The 3.3.9 and 3.3.8 APKs and their
  hashes stay as rollback artifacts.
- [x] Verify live `/get` SHA-256 matches the GitHub asset byte-for-byte:
      `sha256:43892ee2b36d9de3123a88f6c5b8f4ad05c0c0e09b9d4c35bfe2e5787e06f5ba`.
- [x] Verify `/api/builds` reports `4.0.0` and “Android 14 and newer.”
- [x] Verify package `dev.mcmusic.app`, `versionCode 52`, `minSdk 34`,
      `targetSdk 34`, `compileSdk 36`, and signer SHA-256
      `0b0fd0fa35ff712901d42cab215d5e3cb706daef57bffa7ebef61cacda1dc4ce`.

## UI research

- [x] Research reusable references for web/Android/desktop GUI work and record
      the shortlist in `docs/ui-references.md` (flufi upstream/mirror, `old/`
      snapshot, lucide-preact, flufi-ui, Coil, ComposeReorderable, Qt/PySide6).
- [x] Audit the Qt desktop client against `old/`, web and Android; the detailed
      task source is `docs/desktop-parity.md`.

## Self-hosting accessibility

- [x] Add a dedicated `docs/selfhost.md` with install, env, systemd, HTTPS,
      client setup, backups and troubleshooting.
- [x] Link the self-hosting guide from the top of `README.md`.
- [x] **Server tasks:** ship a generic deploy unit template with placeholders
      (`deploy/mcmusic.service.example`), add a one-command bootstrap script
      (`scripts/bootstrap_selfhost.sh`), confirm health/version endpoints
      (`/api/ping`, `/api/version`), make `/api/docs` link to the self-hosting
      guide, and link the guide from the “build the UI” 503 page.
- [x] **Web tasks:** Settings now has a Self-hosting guide link, server origin,
      public URL, room URL, ping/version metadata, and build/download links;
      the 503 “build the UI” page and offline banner also link to the guide.
      Server SPA aliases for `/search`, `/likes`, `/downloads`, `/listeners` and
      `/not-allowed` were added so deep links do not 404.
- [x] **Android tasks:** Settings has a “Self-hosting” entry opening the public
      guide, shows the configured server and app version, and the sign-in screen's
      server help text points to the same guide. The detailed APK task source is
      `docs/android-tasks.md`; it now covers direct HTTPS MP3/ZIP import links,
      swipe/long-press track gestures, and admin track removal in the APK.
- [x] **Desktop tasks:** Qt Settings has the self-hosting link plus server and
      version information.

## Desktop parity (using `docs/desktop-parity.md`)

- [x] Desktop audit completed and recorded in `docs/desktop-parity.md`.
- [x] Fixed Settings room-link crash, lyrics button, settings-schema loss and
      inconsistent version metadata (single `version.py`, now `4.0.0`).
- [x] Offline-resilient login, password reset/email, and Rotur sign-in.
- [x] Queue persistence/reorder, sleep timer, remote commands, activity
      publishing, and `offline_audio` behavior.
- [x] Settings metadata: server/public URL, version, builds, outbox/sync,
      Discord link, all activity/appearance toggles, and self-hosting link.
- [x] Downloads manager, public listening/profiles, devices, advanced requests
      and admin panels, track sources.
- [x] Legacy shortcuts, offline cache/outbox, cache stats/prune.
- [x] macOS Now Playing and Windows SMTC hooks; macOS/Windows builds registered
      in `/api/builds`. Compile/mock checks passed; packaged macOS/Windows
      runtime tests and signing/notarization still need release credentials.

## Algo model (work-rate gated)

- [x] Wire the standalone `algo/` MDL model into the server. Every `/api/plays`
      call produces one observation and the exact-hit work rate is tracked.
- [x] Persist the model atomically under `DATA_DIR` (`data/next_song_mdl.json`),
      with corrupt-snapshot recovery and failure isolation.
- [x] Add admin visibility with `GET /api/admin/algo`, including `work_rate`,
      `threshold`, `active`, `learning_only` and the human-readable `note`.
- [x] Gate all next-track choices at 76% exact-hit work rate with at least ten
      observations. Once earned, the model orders recommendations, radio,
      shuffle, queue extension and autoplay; the affinity/similarity fallback
      remains until then and whenever ranking has no candidates.
- [x] Expose `POST /api/model/rank` so web, Android and desktop can adopt the
      same order; current persisted work rate is far below the gate, so behavior
      today is unchanged.

## 3.3.7 parity additions

- [x] Native account linking uses one-use server tickets (`src/app_links.py`) so
      Rotur/Discord OAuth browser returns can bind to the signed-in Android
      account without a bearer header. Settings shows linked state/configuration
      and supports connect/unlink.
- [x] Cached music videos are prepared when a YouTube import succeeds, streamed
      from `/video-cache/<id>.mp4`, listed at `/api/videos`, and expire four
      hours after the last view. The APK plays them natively with ExoPlayer and
      no YouTube embed; music ducks while a video is open.
- [x] Direct HTTPS audio/ZIP request links are validated server-side with
      actionable errors for truncated playlist IDs; the import watchdog rescues
      orphaned approved rows after a restart.
- [x] Lyric visualizers (Bars/Wave/Glow) exist on web, Android, desktop and iOS,
      driven by playback position and the active lyric line; paused playback
      freezes the frame.
- [x] Public GitHub Release build fallback: `/api/builds`, `/apps/...`, `/get`
      and the new `/downloads` page serve published bytes even when the server
      never built a client locally. `./scripts/pull_builds.sh` refreshes the
      cache; local artifacts still win until the next sync.

## Constraints to keep

- Native Kotlin/Compose Android app; no WebView/Capacitor rewrite.
- Signed release APK only; no debug fallback.
- Keep package/signing continuity for `dev.mcmusic.app`.
- Keep the five swappable palette families (Violet, Indigo, Sky, Aqua, Mint)
  shared by web, Android, iOS, macOS and Windows; each has a light variant from
  the top half of the supplied swatch sheet and a dark variant from the bottom
  half, with dark text/icons on light and white text/icons on dark.
- Use Material 3 for all non-icon UI on every client; use Lucide for every icon
  on every client. No SF Symbols, Material Icons, emoji/unicode glyphs or
  hand-written inline SVG icons outside the shared Lucide path registries.
- Keep `old/` untracked and gitignored; do not revert the current app/web work.
