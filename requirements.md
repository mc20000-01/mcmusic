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

## In progress

- [ ] **Android login does not persist after app close / focus loss.**
  - Token is already in `Prefs` SharedPreferences; nothing clears it on pause.
  - Real cause: `Account.refresh()` drops the cached identity on any `/api/me`
    failure, so a Wi-Fi blip shows the gate. A real 401 also clears the token.
  - Fix: persist last verified `Me`, keep it on transient failures, clear only
    on 401, revalidate on resume, and make Rotur deep-link token adoption
    retryable/race-safe.
- [ ] **A few songs disappear from the Android queue.**
  - `Playback.queueTracks` is in-memory only; duplicate IDs collapse LazyColumn
    keys; shuffle index mismatch and 200-item server mirror cap also hide songs.
  - Fix: persist queue/index/position/repeat/shuffle/autoplay, use occurrence
    aware keys, and restore on cold start / service recreation.
- [ ] **Autoplay at the end of the queue (Android and web).**
  - Add visible toggle at the end of the queue, **on by default**.
  - Only append 5 unique songs when playback truly reaches the end of the
    queue, not while one or two tracks before it.
  - One-song queue + autoplay off plays that one song and stops.
  - Loop-one repeats only the current song and does not append anything.
  - Any repeat mode on turns autoplay off; autoplay on turns repeat off.
  - Server endpoint: `GET /api/radio/<id>`.
- [ ] **Web queue and playback persistence.**
  - Current v3 web has no queue persistence, no autoplay, no `/api/radio` call,
    and no focus/reload restoration despite an unused `common/idb.ts`.
  - Port legacy `player.js` snapshot/restore behavior into the v3 client.
- [ ] **Rotur activity integration.**
  - Port `old/web/js/rotur.js`: status/health/session validity, `describe()`,
    link/unlink, and activity start/stop tied to playback.
  - Current web has partial status/link/unlink/activity in Settings; extend it.
- [ ] **Full web/Android parity with old commit `581b995f...`.**
  - Audit complete; concrete gaps are below. Android first, then web.
  - Backend routes are mostly still present; these are client-surface gaps.

## Parity gaps from the audit (work list)

### Android — missing or regressed vs old commit

- [ ] Settings: Rotur activity toggle, Discord activity toggle, Appearance
      controls (palette/design language, covers, hide explicit).
- [ ] Home listener cards: public profile link, listener position/duration.
- [ ] Search: directory/profile lookup alongside tracks/albums/artists.
- [ ] Track menus: Like (`Api.toggleLike` already exists) and Add to playlist
      (`Api.addToPlaylist` already exists).
- [ ] Queue reorder: wire `Playback.move()` to drag handles if feasible.

### Web — missing or regressed vs old commit

- [ ] Full search page/route and `/` shortcut; Likes view; Downloads view.
- [ ] Public profile links and listener info from `/api/public/listening`.
- [ ] PWA service-worker registration, install prompt, update-ready handling.
- [ ] Keyboard shortcuts: Space, Shift+Arrow keys, `/`, `m`, `l`, `q`, Escape.
- [ ] Home via `/api/home`; playback presence `/api/playback`; device
      heartbeat/command polling; offline cache/outbox; build/version UI.
- [ ] Discord link/unlink/status UI; richer Rotur health/session display.
- [ ] Admin Devices/Channels/Enrich/Lyrics panels where backend routes exist.
- [ ] Email change, track explicit-flag edit, track info/sources dialog.

## Emulator verification (time is not a constraint)

- [ ] Fresh Android 14 (API 34) AVD `mcmusic34fresh`.
  - First two attempts failed instantly because `-accel kvm` is invalid; valid
    values are `on`, `off`, `auto`. Corrected command uses `-accel on`.
  - Corrected boot is running with a 90-minute timeout.
- [ ] Install newest signed APK once booted.
- [ ] Verify: sign-in gate, email sign-in, settings opens, login persists after
      app close/background, queue persists, autoplay/loop behavior, and Rotur
      deep-link return.
- [ ] Capture screenshot/UI dumps for the report.

## Release and delivery steps (repeat after the next code change)

- [ ] Bump Android version (`3.3.4`, code `46` is already staged in source).
- [ ] Commit and push; watch GitHub Actions `Release builds` go green.
- [ ] Pull the bot commit that refreshes `builds/`.
- [ ] Copy the exact GitHub `latest` APK into
  `apps/android/mainbuild.apk`, `apps/android/mcmusic-3.3.4.apk`, and a hashed
  `apps/android/mainbuild-<hash>.apk`; prune stale copies.
- [ ] Verify live `/get` SHA-256 matches the GitHub asset byte-for-byte.
- [ ] Verify `/api/builds` reports the new version and “Android 14 and newer.”
- [ ] Verify package `dev.mcmusic.app`, `versionCode 46`, `minSdk 34`, and
      signer SHA-256 `0b0fd0fa35ff712901d42cab215d5e3cb706daef57bffa7ebef61cacda1dc4ce`.

## Constraints to keep

- Native Kotlin/Compose Android app; no WebView/Capacitor rewrite.
- Signed release APK only; no debug fallback.
- Keep package/signing continuity for `dev.mcmusic.app`.
- Keep violet `#A06BFF` / ink `#08060D` flufi design.
- Keep lucide icons in `ui/src`; no emoji/unicode glyphs or inline SVG icons.
- Keep `old/` untracked and gitignored; do not revert the current app/web work.
