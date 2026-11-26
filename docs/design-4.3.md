# mcmusic 4.3.0 — Phase 0 design / feature specification

## 0. Status and inputs

- Phase 0 record for the 4.3.0 “Playful Google-app × iOS 27 spatial blob” redesign. It defines the shared contract before platform phases; the implementation is committed separately per phase.
- **No mockup images were supplied in the chat.** The written spatial/component brief is authoritative. Details below are derived from that description and the existing 4.2.0 foundations, not from pixel references.
- Platform delivery order: shared tokens/gates (Phase 0) → web (Phase 1) → Android (Phase 2) → iOS (Phase 3) → Qt (Phase 4) → version/release (Phase 5).
- Prerequisite fixes (startup command, OAuth anchor, responsive reflow with Playwright gates) land before Phase 0 as their own commits. They are not folded into the redesign phases.

## 1. Foundations — single source of truth

- `design/tokens.json` remains the only authored source. Both generators keep `--check`: `scripts/gen-tokens.mjs` (HCT/M3 roles via `@material/material-color-utilities`) and `scripts/gen-lucide.mjs` (`lucide-static` SVG geometry). Generated outputs are committed and `tests/test_generated_fresh.py` fails on drift.
- Generated targets: `design/tokens.generated.json`, `ui/src/env.css`, `ui/src/common/theme.ts`, `ui/src/common/breakpoints.generated.ts`, `gui/android/.../Design.kt`, `gui/android/.../Lucide.kt` + Android vectors, `app/ios/McMusic/Theme.swift`, `app/ios/McMusic/Lucide.swift`, `app/linux/mcmusic_linux/theme.py`, `app/linux/mcmusic_linux/icons.py`, `web/embed/widgets.js`, `ui/src/common/lucide.tsx`.
- **Palette contract unchanged.** Family ids/names stay `violet`/Violet, `indigo`/Indigo, `sky`/Sky, `aqua`/Aqua, `mint`/Mint. Legacy swatches and every alias (`""`, `auto`, `system`, `flufi`, `dark`, `dusk`, `paper`, `light`, `ink`, `amoled`, `midnight`, `tide`, `forest`, `rose`, `copper`, `mocha`) keep resolving to the same bytes. Each family accent remains the HCT seed for generated primary/secondary/tertiary + container, surface container 0–4, outline/outlineVariant and all `on-*` roles.
- **Responsive source of truth:** `design/tokens.json` `breakpoints` generates both CSS variables and `ui/src/common/breakpoints.generated.ts`. Half-open tiers: full ≥1100, compact 800–1099, tablet 600–799, phone <600. Exactly 800 is compact desktop chrome. Short viewport threshold is 500px height. CSS literals live in one generated CSS/TS pair because custom properties cannot be used in `@container` conditions.
- **Shape scale:** `4 / 8 / 12 / 16 / 28 / 36` plus pill `9999px` (`999px` CSS alias retained for stored compatibility); covers 20–28; cards 28; hero cards 36; floating docks and transport bars full pill; spacing on a 4px grid; touch targets ≥48px.
- **Type:** keep the bundled Lexend/inter/JetBrains Mono Fontsource packages. Their local `LICENSE` files are SIL OFL 1.1 (Lexend: Copyright 2019 The Lexend Project Authors; Inter: Copyright 2016 The Inter Project Authors; JetBrains Mono: Copyright 2020 The JetBrains Mono Project Authors). Google Sans Flex is not present in the authored tree and no network fetch was made for 4.3; it is **not adopted**. The build continues to strip flufi’s CDN `@import`, so no remote font request ships.
- **Lucide only.** All listed glyphs are already in `design/tokens.json:icons` (including `house`, `search`, `compass`, `library`, `list-music`, `disc-3`, `heart`, `star`, `clock`, `download`, `user-round`, `play`, `pause`, `skip-back`, `skip-forward`, `shuffle`, `repeat`, `repeat-1`, `volume-2`, `cast`, `mic-vocal`, `picture-in-picture-2`, `ellipsis`, `chevron-right`, `pencil`, `sparkles`, `headphones`, `pin` and category glyphs `headphones`/`zap`/`coffee`/`flame`/`moon`/`dumbbell`). Generate, never hand-copy. Lucide has no filled variants: active state = M3 indicator pill + stroke `2.5` + accent colour.
- **Flatness gate:** `tests/test_no_gradients.py` rejects `gradient(`, `backdrop-filter`, `Brush.*Gradient`, `drawBackdrop`, `blur(`, Swift gradients/`.material`/`.ultraThin*` and Qt gradient classes with no allowlist. No decorative shadows: elevation comes from `surfaceContainer*` contrast and `outlineVariant` borders only.
- **Contrast gate:** all five families × light/dark must satisfy the existing WCAG AA test (4.5:1 body text, 3:1 large text/icons). No role value is changed without regenerating and re-running that test.

## 2. Blob and component geometry

Canonical blob tokens are authored in `design/tokens.json` and generated into every client. Geometry is normalized to a 100×100 viewBox; `borderRadius` is the CSS fallback for cards/tiles, `path` is used for SVG/Canvas/Path drawing.

| Token | Shape | Border radius | Path spec (normalised) |
| --- | --- | --- | --- |
| `blob-1` | circle | `50%` | single 46px-radius arc centred at 50,50 |
| `blob-2` | squircle | `32% / 28%` | rounded rectangle from 4,4 to 96,96 with 18px corner curves |
| `blob-3` | cookie | `48% 52% 43% 57% / 52% 44% 56% 48%` | eight shallow scallops joined by cubic curves |
| `blob-4` | 6-petal flower | not representable by radius | six equal lobes alternating radius 50/30 around the centre |
| `blob-5` | asymmetric pebble | `42% 58% 63% 37% / 57% 42% 58% 43%` | four unequal cubic lobes, wider at bottom-right |

Rules:
- Covers stay square/squircle (20–28 radius) for real artwork. Only a **placeholder** or the Now Playing visualizer may morph into a blob; real art is never cropped into a blob or tinted.
- Mood/genre tiles use an oversized cropped Lucide glyph plus one flat tonal blob accent selected from the family’s primary/secondary/tertiary containers. No gradient wash, no glass, no shadow.
- Docks, segmented controls, chips and transport bars are pills (`full`). Cards are 28, hero cards 36. Overlap comes from positioning and tonal contrast, not shadows.
- Active icon state = accent colour + stroke 2.5 + M3 indicator pill; never a filled Lucide variant.

## 3. Spatial layout rules

### Wide (web/Android/Qt ≥900px)

- Detached left capsule rail: pill search at top; `Listen now`, `Browse`, `Artists`; library shortcuts `Recently added`, `Albums`, `Liked songs`; playlists as flat tonal blob tiles.
- Centred floating pill view switcher where the page has peer views; large page title with a status badge on the right.
- Canvas (`surface`) holds two asymmetric hero cards (36 radius, flat `primaryContainer`/`secondaryContainer`, pill chip, bold title, subtitle, pill play) and a “Recently played” row of squircle covers with active track in `primary`.
- Overlapping bottom capsule transport (`surfaceContainerHigh`): left cluster shuffle/prev/morphing play/next/repeat; centre capsule (`surfaceContainerHighest`) with title, artist, real quality info when available, and wavy/flat progress; right cluster like/volume/devices/lyrics/avatar.
- Compact 800–1099 keeps desktop chrome but auto-collapses the rail and folds secondary transport controls into a More popover; pages use smaller gutters and no horizontal clipping.

### Compact (phone/tablet <900px)

- Large collapsing title + avatar chip; top-picks hero card; 2-column recently-played grid.
- Detached mini-player pill above a detached NavigationBar capsule with at most five destinations: `Listen now`, `Browse`, `Search`, `Library`, plus `Mixes` **only if a real source exists** (see §5).
- Search: large title, pill SearchBar, 2-column blobby genre tiles cycling tonal containers, oversized cropped Lucide glyphs, `0.96` press spring.
- Library: `Edit` pill, flat tonal blob icon badges, rows with Lucide leading icons and chevrons (`Playlists`, `Artists`, `Albums`, `Downloaded` + real size), plus 2-column `Recently added`.
- Now Playing: drag handle, large cover or morphing blob placeholder, title/artist, like + more pills, wavy progress with times and truthful quality text, large transport with morphing play, bottom pill row `Lyrics`/`Devices`/`Queue`.
- Short viewports (<500px height) shrink chrome, hide less-important metadata and keep the player inside the viewport with a vertically scrollable content pane.

### Lyrics / Up Next panel and floating windows

- Segmented pill `Lyrics | Up next`. Lyrics: current line large in a flat tonal pill/blob highlight, neighbours dimmed. Up next: queue with a Skip pill on the next track. `Sing mode` chip appears only for genuine LRC line timings.
- Qt adds a 360×300 mini-player (blob art frame, always-on-top pin) and a 360×380 Lyrics & Queue window; the active window mode persists in settings.

## 4. Motion and feedback

- Medium spring, damping ~0.7; press scale 0.96; play/pause morph ~320ms (`circle ↔ rounded square/blob`); wavy progress while playing (0.55Hz, 3px), flat when paused.
- Android/iOS haptics on play/pause and seek ticks only; no haptics on scroll or passive view changes.
- `prefers-reduced-motion`, Android animator scale and iOS Reduce Motion disable springs, morphs and waves. Settings toggle `playfulMotion` defaults on; generated key stays unchanged.
- Document PiP on web is feature-detected and skipped silently where unsupported; no new network calls.

## 5. Feature truth audit (source-verified)

| Claim / surface | Actual state in source | 4.3.0 rule |
| --- | --- | --- |
| Dolby Atmos / Spatial Audio / Spatial Mix | No product label anywhere in `src/`, `ui/src/`, `gui/android`, `app/ios`, `app/linux`. | Never show these labels. |
| “Mix” / “Editorial Mix” chips | No mix entity or `/api/mixes` exists. `src/routes/personal_routes.py:509-532` has a real similarity endpoint used as **Start radio**; the MDL only reorders a supplied candidate list (`src/next_song_model.py:162-186`) and is gated by `is_active()`. | No Mixes tab and no fabricated Mix chip. Keep Start radio as Radio, not Mix. |
| Lossless / codec badge | `tracks` has no codec/bitrate column (`src/database.py:22-45`); tag readers only read length/title/artist/album/genre/date/tracknumber (`src/routes/library_routes.py:30-54`). No client badge exists. | Do **not** show Lossless or a codec badge in 4.3. No DB migration or new extraction pipeline is in scope. If real metadata is added later, show `FLAC`/`ALAC`/`WAV` as Lossless and real values such as `MP3 320`/`OPUS 160` otherwise. |
| Explicit `E` | Real chain: `explicit_auto`/`explicit_ovr` (`src/database.py:40-41,271-272`), override wins (`src/database.py:468-474`), YouTube age/title detection (`src/library_scan.py:302-304`), admin override (`src/routes/library_routes.py:273-285`). Only Qt draws an inline `E` today (`app/linux/mcmusic_linux/widgets.py:687-700`). | Show `E` only when the resolved flag is true. No badge from genre/mood/artwork. |
| Made for you / hero | `/api/home` really emits `Made for you` and `Discover` from `recommend()` (plays/likes/genre affinity, optionally model-gated) plus `Your top tracks` and `Faves` (`src/routes/personal_routes.py:168-192,383-410,462-484`). | **Chosen:** keep the real `Made for you` shelf where populated; otherwise use `Your top tracks`/`Faves` (“Most played”) as the honest fallback. No invented “Featured”. |
| Radio / Mixes | Similarity endpoint is real; no curated Mixes backend. | Four destinations are acceptable. Omit Mixes until a real source exists. |
| Browse / Charts | Genre is real tag data (`src/database.py:29`, `library_scan.py:52`); user-visible ranking comes from play counts and YouTube likes (`personal_routes.py:464-477`). No public global chart endpoint. | Browse uses actual genre tags. “Charts” uses `Your top tracks` / `Most liked on YouTube` shelves; no fabricated global chart. |
| Featured Artist / Sing Mode | Artist pages exist; LRC line timings exist on web/Android/iOS, Qt has a raw lyrics view only (`ui/src/components/Lyrics/LyricsPanel.tsx:44-81`, `gui/android/.../Player.kt:518-551`, `app/ios/McMusic/LyricVisualizer.swift:3-33`). | Artist pages get a blob avatar frame. Sing Mode only for genuine LRC; plain lyrics stay read-only. No word-level karaoke or microphone feature. |
| Desktop mini/lyrics windows | Qt has main shell and a raw lyrics window (`app/linux/mcmusic_linux/shell.py:2134-2162`). | Add the two documented compact window modes in Phase 4; persist mode in settings. |

No live DB changes, no new network calls, no trackers and no weakening of cleartext/CORS/signing checks are part of 4.3.0.

## 6. Phase plan and exit gates

| Phase | Commit scope | Exit gate |
| --- | --- | --- |
| Pre-phases | Startup fix, OAuth anchor fix, responsive reflow + Playwright gates. | CI green; screenshots uploaded; tier boundaries asserted. |
| Phase 0 | This document, blob tokens/generators, generated files, flatness/contrast/freshness gates. | CI green; all generated checks pass. |
| Phase 1 | Web shell, pages, player, lyrics/up-next, wavy progress, morphing play, blob placeholders. | CI green; UI build + responsive Playwright suite pass. |
| Phase 2 | Android Compose shell/screens, dynamic cover colour, Wallpaper option, haptics, screenshot tests. | CI green; assemble + JVM tests + signing gate pass. |
| Phase 3 | iOS SwiftUI compact layouts, flat tonal chrome, haptics, Reduce Motion/Dynamic Type. | CI green; unsigned Simulator build passes. |
| Phase 4 | Qt flat painting, wide shell, mini-player + lyrics/queue windows, offscreen tests. | CI green; Qt offscreen + selftest pass. |
| Phase 5 | Version carriers 4.3.0, real deb, docs/release notes, publish `v4.3.0`/`latest`. | CI green; release workflow green; assets verified. |

One logical change per commit; CI must be green before the next phase commit is published.

## 7. Verification limits

- No mockup images were provided, so visual fidelity to a reference cannot be checked locally. Playwright screenshots at 800/1024/1280 are CI artifacts.
- No device rendering is available for Android/iOS; CI covers builds and JVM/Simulator tests, not on-device appearance.
- Qt rendering is verified offscreen only; manual window-manager behaviour is not verifiable here.
- Codesign and store distribution are out of local reach; the release workflow’s existing signing gates remain authoritative.
- No live database or network-backed feature was added; all feature decisions above are code/source-verified.
