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
- [x] Android design matches flufimusic v3 web tokens (`#08060D`, `#A06BFF`,
  flat surfaces, one 10dp radius, lucide icons).
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
- [ ] Verify after the next full build: sign-in gate, email sign-in, Settings
      opens, login persists after app close/background, queue persists,
      autoplay/loop behavior, and Rotur deep-link return.
- [ ] Capture screenshot/UI dumps for the report. The emulator is extremely
      slow on this host (no xsave/avx), and `uiautomator dump` intermittently
      returns a null root or is killed; retry during final verification.

## Release and delivery steps (repeat after the next code change)

- [ ] Bump Android version to `3.3.5`, code `47`.
- [ ] Commit and push; watch GitHub Actions `Release builds` go green.
- [ ] Pull the bot commit that refreshes `builds/`.
- [ ] Copy the exact GitHub `latest` APK into
  `apps/android/mainbuild.apk`, `apps/android/mcmusic-3.3.5.apk`, and a hashed
  `apps/android/mainbuild-<hash>.apk`; prune stale copies.
- [ ] Verify live `/get` SHA-256 matches the GitHub asset byte-for-byte.
- [ ] Verify `/api/builds` reports the new version and “Android 14 and newer.”
- [ ] Verify package `dev.mcmusic.app`, `versionCode 47`, `minSdk 34`, and
      signer SHA-256 `0b0fd0fa35ff712901d42cab215d5e3cb706daef57bffa7ebef61cacda1dc4ce`.

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
      server help text points to the same guide.
- [x] **Desktop tasks:** Qt Settings has the self-hosting link plus server and
      version information.

## Desktop parity (using `docs/desktop-parity.md`)

- [x] Desktop audit completed and recorded in `docs/desktop-parity.md`.
- [x] Fixed Settings room-link crash, lyrics button, settings-schema loss and
      inconsistent version metadata (single `version.py`, default `2.6.0`).
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

## Algo model (learning only)

- [x] Wire the standalone `algo/` MDL model into the server without using it for
      song selection. Every `/api/plays` call now produces one observation.
- [x] Persist the model atomically under `DATA_DIR` (`data/next_song_mdl.json`),
      with corrupt-snapshot recovery and failure isolation.
- [x] Add admin visibility with `GET /api/admin/algo` and document the boundary
      in `docs/algo-learning.md`.
- [x] Kept predictions out of radio, queue extension, shuffle, and autoplay;
      this stays deferred until you ask for it.

## Constraints to keep

- Native Kotlin/Compose Android app; no WebView/Capacitor rewrite.
- Signed release APK only; no debug fallback.
- Keep package/signing continuity for `dev.mcmusic.app`.
- Keep violet `#A06BFF` / ink `#08060D` flufi design.
- Keep lucide icons in `ui/src`; no emoji/unicode glyphs or inline SVG icons.
- Keep `old/` untracked and gitignored; do not revert the current app/web work.
