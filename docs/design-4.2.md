# mcmusic 4.2.0 — Phase 0 design / feature specification

## 0. Status and inputs

- This document is the Phase 0 design record. It changes documentation only: no code, tokens, tests, CI or generated files are edited here.
- **No mockup images were supplied in the chat; only the written structure brief was available.** The written structure is authoritative. Visual details below are derived from Google app / Material 3 Expressive principles, not from pixel references.
- Platforms in scope, in delivery order: web, Android, iOS, Qt/desktop.

## 1. Foundations — single source of truth

- `design/tokens.json` is the single source of truth for 4.2.0. Its own note says to change values there and run `node scripts/gen-tokens.mjs` and `node scripts/gen-lucide.mjs` (`design/tokens.json:3`).
- Generated targets are produced by **both** generators, both of which are present in Phase 0 and support `--check`:
  - `scripts/gen-tokens.mjs` reads `design/tokens.json`, derives Material 3 roles with `@material/material-color-utilities@0.3.0` HCT, and writes `design/tokens.generated.json`, `ui/src/env.css`, and the marked blocks in `ui/src/common/theme.ts`, `gui/android/.../Design.kt`, `app/ios/McMusic/Theme.swift`, `app/linux/mcmusic_linux/theme.py` and `web/embed/widgets.js`.
  - `scripts/gen-lucide.mjs` reads every glyph from `ui/node_modules/lucide-static/icons/*.svg` and writes the marked blocks in `ui/src/common/lucide.tsx`, `gui/android/.../Lucide.kt`, `app/ios/McMusic/Lucide.swift`, `app/linux/mcmusic_linux/icons.py` plus 127 Android vector drawables. No glyph geometry is hand-copied.
- Generated files must never be hand-edited. `ui/src/env.css:1-2` is already marked as generated and flat-only.

### Palette and aliases

- Family ids and displayed family names are unchanged: `violet`/Violet, `indigo`/Indigo, `sky`/Sky, `aqua`/Aqua, `mint`/Mint (`design/tokens.json:54-130`; iOS `app/ios/McMusic/Theme.swift:6-10`).
- All legacy aliases must keep resolving: empty, `auto`, `system`, `flufi`, `dark`, `dusk`, `paper`, `light`, `ink`, `amoled`, `midnight`, `tide`, `forest`, `rose`, `copper`, `mocha` (`design/tokens.json:36-53`). Existing resolvers already implement the contract: web `ui/src/common/theme.ts:1-10,839-859`, Android `gui/android/.../Design.kt:221-252`, iOS `app/ios/McMusic/Theme.swift:12-28`, embed palette docs `src/routes/system_routes.py:505,512`.
- Legacy swatches stay byte-identical so stored user settings and embed tags keep working (`design/tokens.json:3`; `ui/src/common/theme.ts:31-35`; `src/database.py` track data is unaffected).

### Shape, spacing, type

- Shape scale: `4 / 8 / 12 / 16 / 28 / 36` plus pill (`design/tokens.json:4-11`). Cards use 28, hero cards 36, chips and buttons are pill, covers stay in the 20–28 range (`design/tokens.json:12-16`). Generated CSS exposes the same values at `ui/src/env.css:34-44`.
- Spacing is a strict 4px grid (`design/tokens.json:18`).
- Every interactive target is at least 48×48 CSS/dp/pt (`design/tokens.json:16`; `ui/src/env.css:44`). Current web override of 40px in `ui/src/app.css:133-140` is below the 4.2.0 floor and must be raised in Phase 1.
- Material 3 type scale, sizes/line heights from `design/tokens.json:29-35`: display 36/44 (700), headline 28/36 (700), title 22/28 (700), body 16/24 (400), label 14/20 (600).
- **Keep Lexend for 4.2.0.** Lexend is referenced in the client (`ui/src/app.css:119-124`, `ui/src/pages/Set/style.css:27`) and requested through the flufi-ui CDN import. No local font binaries were found in the tracked tree (search for `*.woff`, `*.woff2`, `*.ttf`, `*.otf` outside `node_modules` returned none), so do not claim Lexend is already bundled locally.
- **Google Sans Flex licence evidence:** fetched `https://raw.githubusercontent.com/googlefonts/googlesans-flex/main/OFL.txt`. It states: `Copyright 2022 The Google Sans Flex Project Authors (github.com/googlefonts/googlesans-flex)` and `SIL Open Font License, Version 1.1`. The licence permits bundling/embedding/redistribution with software subject to its conditions (OFL 1.1, clauses 1–5).
- **Decision:** Google Sans Flex is bundleable OFL, but it is **not adopted** for 4.2.0. No mockups were supplied; changing the face without a visual reference would be a branding risk.
- **Font delivery:** Phase 0 adds `@fontsource-variable/inter`, `@fontsource-variable/jetbrains-mono` and `@fontsource-variable/lexend` (all OFL-1.1) as local dependencies, imports them from `ui/src/main.tsx`, and adds `scripts/strip-font-cdn.mjs` to `scripts/build_ui.sh`. The build strips the Google Fonts CDN `@import` carried by `flufi-ui/dist/style.css` (and fails on any unexpected remote `@import`), so no CDN font request ships. The font family remains Lexend as before.

## 2. Visual language

- Flat tonal containers only. No gradients, blur, glass, backdrop effects or decorative shadows. The generated baseline already sets `--elevation-1/2: none` and `--shadow-raised: none` (`ui/src/env.css:24-29`).
- Pre-4.2 exceptions (canvas gradients, widget washes, glass brush/highlight, `Glass.kt`, kyant backdrop dependency) are removed in Phase 0 so `tests/test_no_gradients.py` can gate every later phase with no allowlist.
- Icons are Lucide only: web registry `ui/src/common/lucide.tsx:1-20`, policy `docs/ui-references.md:26-28`, Android `gui/android/.../ui/Lucide.kt`, iOS `app/ios/McMusic/Lucide.swift:3-9`, Qt `app/linux/mcmusic_linux/icons.py:1-5`. No emoji, icon fonts, SF Symbols or hand-written one-off SVGs.
- Cover placeholders: a flat tonal container with a Lucide glyph/shape rotating among circle, squircle (rounded rect), cookie, flower and pentagon. Real artwork is shown as-is — never re-tinted or gradient-washed. Current fallback is a text-initial SVG (`ui/src/common/net/api.ts:176-180`) and must be replaced in Phase 1; the new glyph names must be included in the Lucide generated target.

## 3. Dynamic colour

- Web and Android are first-class for dynamic colour: derive a tonal scheme from the current cover's dominant colour through HCT, then fall back to the selected family palette when there is no artwork or extraction fails. The HCT machinery already exists in the shared generator (`scripts/gen-tokens.mjs:7-19,41-48`; `ui/src/common/theme.ts:13-19`).
- iOS and Qt stay on static family palettes in 4.2.0 (`app/ios/McMusic/Theme.swift:4-10,72-80`; `app/linux/mcmusic_linux/theme.py:3-30`).
- Android additionally supports the Wallpaper palette (Material You, Android 12+). The app's `minSdk`/`targetSdk` are 34 (`gui/android/app/build.gradle.kts:13-14`), so the platform APIs are available; there is no current `DynamicColors`/wallpaper usage in `gui/android/app/src/main`, so this is new Phase 2 work.
- Dynamic schemes never change a family id or a legacy alias; they only supply tonal role values for the active surface.

## 4. Motion and feedback

- Medium spring with damping ~0.7 (`design/tokens.json:19-21`), press scale 0.96 (`design/tokens.json:21`), play/pause shape morph with ~320ms duration (`design/tokens.json:22`), wavy progress while playing and flat progress when paused (`design/tokens.json:23-24`).
- Android and iOS haptics on primary transport/press actions. No haptic calls exist today (`gui/android/app/src/main` and `app/ios` have no `performHaptic`/`UIFeedback` matches), so this is new native work in Phases 2 and 3.
- Honour platform reduced-motion settings: disable springs, morphs and waves (`design/tokens.json:27`; existing web precedent `ui/src/components/Equaliser/style.css:12-16`).
- Playful motion is a user setting keyed `playfulMotion`, default on (`design/tokens.json:25-26`). It is not yet present in client prefs; Phases 1–4 must wire it.

## 5. Feature truth audit (source-verified)

| Claim / surface | Actual state in source | 4.2.0 rule |
| --- | --- | --- |
| Dolby Atmos / Spatial Audio / Spatial Mix | No matches for `Dolby`, `Atmos`, `Spatial` in `src/`, `ui/src/`, `gui/android/...`, `app/ios/`, `app/linux/`, `web/`. `src/song_meta.py:20` only treats `mix` as a title-noise token. | Never show these labels. |
| “Mix” chips | No Mix chip/shelf exists. Home sections are `Made for you`, `Discover`, `Your top tracks`, `Recently added`, `Most liked on YouTube` (`src/routes/personal_routes.py:472-478`); radio is a separate action (`ui/src/pages/Set/Set.tsx:147-149`). | Use `Mix` **only** for a server-generated mix. Otherwise omit the chip; do not relabel radio or a filtered library as a Mix. |
| Lossless badge / codec | `src/config.py:89` allows `.mp3/.m4a/.aac/.opus/.flac/.wav/.webm/.ogg`; `src/yt_playlist_to_mp3.py:25,143` exposes the same download formats. Metadata read in `src/routes/library_routes.py:30-54` has no codec/bitrate; `tracks` schema has no codec/bitrate columns (`src/database.py:25-44`). | Show `Lossless` only for real `flac`, `alac` or `wav`. Otherwise show actual codec/bitrate from file metadata; never infer quality from a container or extension alone. |
| Explicit `E` | Real flag chain exists: `explicit_auto`/`explicit_ovr` (`src/database.py:40-41`), override wins in `track_dict` (`src/database.py:468-474`), auto detection from YouTube `age_limit >= 18` or an `[explicit]` title marker (`src/library_scan.py:302-304`), admin override endpoint (`src/routes/library_routes.py:273-280`), web `hide_explicit` pref and info dialog (`ui/src/common/prefs.ts:43,71,90`; `ui/src/components/TrackInfo/TrackInfoDialog.tsx:62,103-116`). | Show `E` only when the resolved flag is true from a real tag/age limit/admin override. Never infer it from genre, mood or artwork. |
| `Made for you` | Real: `/api/home` emits it from `recommend(uid, 30)` (`src/routes/personal_routes.py:458-486`); `recommend` uses plays/likes/genre affinity and calls `rank_for` from the model (`src/routes/personal_routes.py:382-455`). The model is gated by observations/work rate (`src/next_song_model.py:146-152,162-170`) and the affinity fallback remains real. Faves is rebuilt from `listening_events` (`src/routes/personal_routes.py:168-192`). Empty sections are dropped (`src/routes/personal_routes.py:484`). | Keep `Made for you`. If no recommendation/history backs it, use `Pick up where you left off` (recent plays) or `Most played` (play counts), not a fake personalised claim. |
| Radio / Mixes | The brief’s rule is `no Radio backend -> Mixes only if real else omit`. Source check finds a real similarity endpoint: `GET /api/radio/<tid>` returns up to 40 similar tracks (`src/routes/personal_routes.py:509-532`), used by web `ui/src/common/net/api.ts:387-391`, Android `gui/android/.../data/Api.kt:394-396` and iOS `app/ios/McMusic/Repo.swift:179-180`. There is no dedicated curated Radio/Mixes product backend. | Do not present a curated `Radio` destination or `Mixes` tab. Keep the existing `Start radio` action because it is backed by real data; label it Radio, not Mix. If that endpoint is ever removed, omit the surface entirely. |
| Browse / Charts | Genres are real tag data shown via `ui/src/components/GenreList/GenreList.tsx:1-12` and carried in API state (`ui/src/common/net/api.ts:230,248`). User-visible ranking shelves come from plays/YouTube likes (`src/routes/personal_routes.py:464-477`); detailed listening top-tracks exist only behind the admin gate (`src/routes/system_routes.py:1618-1654`). | Build Browse from actual genre tags. Build Charts from real listening stats or likes; use `Your top tracks` / `Most liked on YouTube` for user-facing shelves until a public stats endpoint exists. No fabricated global chart. |
| Sing Mode | Synced vs plain lyrics are distinguished at source (`src/lyrics.py:36-41,49-52`) and exposed with `source` (`src/routes/library_routes.py:354-372`). Web parses LRC (`ui/src/components/Lyrics/LyricsPanel.tsx:1-4,44-65`); Android parses LRC timestamps and highlights by playback position (`gui/android/.../ui/screens/Player.kt:527-560,587-597`). | Enable Sing Mode only for genuine time-synced LRC/`lrclib-synced` lyrics. Plain lyrics get a read-only lyrics sheet. |

## 6. Phase plan

Each phase is a **separate commit** and must be **CI-green before the next phase starts** (`.github/workflows/ci.yml:1`; release already requires passing CI for the commit, `.github/workflows/release.yml:32-50`).

| Phase | Commit scope | Exit gate |
| --- | --- | --- |
| Phase 0 — foundations | This design record; token contract, alias/name guarantees, licence/font decision, feature truth audit, both generators, generated files, local fonts, flatness/contrast/freshness gates and removal of pre-existing gradient/glass/shadow effects in all four clients. | CI green; doc and audit reviewed; no hand-edited generated files. |
| Phase 1 — web | `ui/` + built `web/ui/`: shell/transport rebuild, Home/Search/Library, Lyrics\|Up next, wavy progress, morphing play, tonal pills/covers, playful motion, truth-checked labels. | CI green; built stylesheet contains no Google Fonts CDN import. |
| Phase 2 — Android | `gui/android/`: generated palette/Lucide targets, cover-derived HCT dynamic colour, Wallpaper palette (Android 12+), haptics, motion, truth-checked labels. | CI green; Android build/tests pass. |
| Phase 3 — iOS | `app/ios/`: static family palettes, generated tokens/icons, motion settings, haptics, truth-checked labels. | CI green; unsigned Simulator build passes. |
| Phase 4 — Qt | `app/linux/`: static family palettes, generated tokens/icons, flat painting, motion settings, truth-checked labels. | CI green; Linux/deb build passes. |
| Phase 5 — version/release | Align version surfaces: Android `versionName`/`versionCode` (`gui/android/app/build.gradle.kts:15-16`), iOS `MARKETING_VERSION`/`CURRENT_PROJECT_VERSION` (`app/ios/project.yml:48-49`), Qt `app/linux/mcmusic_linux/version.py:9-21`, and server `BUILD`/`SHELL_VERSION` reporting (`src/config.py:124`, `src/mcmusic.py:371-376`). Publish via the existing release workflow. | CI green plus release verification; no phase after this. |

## 7. Verification limits

- Mockups are unavailable: visual fidelity to a reference cannot be checked, so structure and the written brief govern.
- Device rendering cannot be verified locally for web, Android, iOS or Qt at this stage.
- Codesign is unavailable on Linux; macOS signing verification happens in CI/release (`.github/workflows/release.yml:181-185`).
- There is no paid Apple Developer account, so device builds and store distribution are out of local reach; CI builds/tests the unsigned iOS Simulator target.
- Local `apt-get` is unavailable; native dependency installation and system-level packaging checks must rely on the existing CI images.
- Live database changes require explicit user permission; this Phase 0 work reads source only and does not mutate data.
