# mcmusic 4.3.0 — Phase 0 report

Branch: `design-4.3.0` (base `4ba8845` on `fixes-4.2.x`, after the startup, OAuth and responsive prerequisite commits). This phase defines the shared redesign contract; it contains no platform UI changes, no version bump and no release action.

## What changed

- Added `docs/design-4.3.md`: the Phase 0 specification for the playful Google-app × iOS 27 spatial-blob redesign. It records the five-platform scope, flatness and material rules, spatial layout by tier, motion/haptics policy, the source-verified feature-truth audit, phase plan and verification limits. Every feature decision cites source paths.
- Authored five canonical blob tokens in `design/tokens.json` (`blob-1` circle, `blob-2` squircle, `blob-3` cookie, `blob-4` six-petal flower, `blob-5` asymmetric pebble). Each token carries a shape label, a CSS `borderRadius` fallback and a normalised 100×100 SVG path. Palette ids, aliases, family names, legacy swatches, breakpoints, motion and icon tokens were left untouched.
- Extended `scripts/gen-tokens.mjs` so `--check` covers the new contract: blob data is emitted into `design/tokens.generated.json`, blob radii become `--blob-N-radius` CSS custom properties, and generated blob modules are written for web TypeScript, Android Kotlin, iOS Swift and Qt Python. The generators remain the only way to produce these files.
- Committed the generated outputs (`ui/src/common/blobs.generated.ts`, `gui/android/.../design/Blobs.kt`, `app/ios/McMusic/Blobs.swift`, `app/linux/mcmusic_linux/blobs.py`, plus refreshed `env.css` and `tokens.generated.json`). No glyph or path geometry is hand-copied in a client.
- Added `tests/test_blobs.py`, which verifies exactly five authored ids, verbatim parity with the generated JSON, sane closed-path geometry, and that every client module plus the CSS carries the exact authored path/radius strings.
- Added `tests/test_font_bundling.py`, which verifies the only font packages are the three local `@fontsource-variable` packages, no `@import url(` exists in authored web CSS/HTML, the build strips flufi's CDN import, and the Google Sans Flex decision is documented. Google Sans Flex has no authored binary or licence in this tree, so the bundled OFL 1.1 Lexend/Inter/JetBrains Mono fonts remain in use; no network fetch was performed.
- Wired both new tests into the CI `design-checks` job alongside the existing no-gradient, WCAG AA contrast and generated-freshness gates. The flatness and contrast gates were kept strict: no allowlist, no suppression.

## What was run

- `node scripts/gen-tokens.mjs` — generated all 12 targets; a second `node scripts/gen-tokens.mjs --check` passed with zero stale files.
- `.venv/bin/python -m pytest tests/test_no_gradients.py tests/test_contrast.py tests/test_generated_fresh.py tests/test_blobs.py tests/test_font_bundling.py -q` — 7 passed.
- `.venv/bin/python -m py_compile app/linux/mcmusic_linux/blobs.py` — passed.
- `npm --prefix ui run build` — passed (`tsc --noEmit`, Vite build and CDN import strip); the new generated TypeScript module type-checks.
- `git diff --check` — no whitespace errors.
- The prerequisite responsive CI run (`4ba8845`) was watched separately; Phase 0 is only committed after that run is green.

## What was not done and why

- No web/Android/iOS/Qt visual code was changed. Phase 0 is the shared contract; each platform gets its own phase and its own CI-green commit.
- No blob is painted anywhere yet: placeholders, cards and transport components adopt the shapes in Phases 1–4. The generated modules only make the geometry available.
- No version bump, release asset, deb, signing change or network call was made. Version carriers and publication belong to Phase 5.
- No mockup was supplied, so visual fidelity to a reference cannot be claimed; the written brief and the documented geometry are authoritative.
- Kotlin and Swift compilation cannot run in this Linux workspace; CI's Android and iOS jobs remain the authoritative build gates. Qt Python was syntax-checked locally; offscreen rendering belongs to Phase 4.
- Google Sans Flex was not fetched or bundled. Its licence status is recorded from documentation only; the decision is to keep the already-bundled OFL fonts and add no remote font dependency.

## Full authored file contents

The files below are reproduced in full. Generated targets other than the blob modules are produced by `scripts/gen-tokens.mjs` and are committed separately in the tree.


### `docs/design-4.3.md`

```markdown
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
```


### `design/tokens.json`

```json
{
  "schema": 1,
  "note": "Single source of truth for 4.2.0. Legacy swatches are kept verbatim so stored palette ids still resolve to the same bytes; `seed` is the Material 3 HCT seed used to generate the full tonal role set. Change a value here and run node scripts/gen-tokens.mjs + node scripts/gen-lucide.mjs.",
  "shape": {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 28,
    "xxl": 36,
    "pill": 999,
    "coverMin": 20,
    "coverMax": 28,
    "card": 28,
    "hero": 36,
    "touchTarget": 48
  },
  "spacing": { "unit": 4 },
  "breakpoints": {
    "phone": 600,
    "tablet": 800,
    "compact": 1100,
    "shortViewport": 500
  },
  "blobs": [
    {
      "id": "blob-1",
      "shape": "circle",
      "borderRadius": "50%",
      "path": "M 50 4 A 46 46 0 1 0 50 96 A 46 46 0 1 0 50 4 Z"
    },
    {
      "id": "blob-2",
      "shape": "squircle",
      "borderRadius": "32% / 28%",
      "path": "M 22 4 H 78 C 87.94 4 96 12.06 96 22 V 78 C 96 87.94 87.94 96 78 96 H 22 C 12.06 96 4 87.94 4 78 V 22 C 4 12.06 12.06 4 22 4 Z"
    },
    {
      "id": "blob-3",
      "shape": "cookie",
      "borderRadius": "48% 52% 43% 57% / 52% 44% 56% 48%",
      "path": "M 50 4 C 63.2 0.74 75.5 5.83 82.53 17.47 C 94.17 24.5 99.26 36.8 96 50 C 99.26 63.2 94.17 75.5 82.53 82.53 C 75.5 94.17 63.2 99.26 50 96 C 36.8 99.26 24.5 94.17 17.47 82.53 C 5.83 75.5 0.74 63.2 4 50 C 0.74 36.8 5.83 24.5 17.47 17.47 C 24.5 5.83 36.8 0.74 50 4 Z"
    },
    {
      "id": "blob-4",
      "shape": "six-petal flower",
      "borderRadius": "50%",
      "path": "M 50 20 C 67.1 3.02 82.14 11.7 75.98 35 C 99.24 41.32 99.24 58.68 75.98 65 C 82.14 88.3 67.1 96.98 50 80 C 32.9 96.98 17.86 88.3 24.02 65 C 0.76 58.68 0.76 41.32 24.02 35 C 17.86 11.7 32.9 3.02 50 20 Z"
    },
    {
      "id": "blob-5",
      "shape": "asymmetric pebble",
      "borderRadius": "42% 58% 63% 37% / 57% 42% 58% 43%",
      "path": "M 50 4 C 78 4 96 22 96 48 C 96 76 72 96 44 96 C 20 96 4 74 4 50 C 4 26 24 4 50 4 Z"
    }
  ],
  "motion": {
    "spring": { "stiffness": "medium", "damping": 0.7 },
    "pressScale": 0.96,
    "morphMs": 320,
    "progressWaveHz": 0.55,
    "progressWavePx": 3,
    "settingsKey": "playfulMotion",
    "defaultEnabled": true,
    "reducedMotion": "honour platform setting and disable springs, morphs and waves"
  },
  "type": {
    "display": { "size": 36, "weight": 700, "line": 44 },
    "headline": { "size": 28, "weight": 700, "line": 36 },
    "title": { "size": 22, "weight": 700, "line": 28 },
    "body": { "size": 16, "weight": 400, "line": 24 },
    "label": { "size": 14, "weight": 600, "line": 20 }
  },
  "aliases": {
    "": "violet",
    "auto": "violet",
    "system": "violet",
    "flufi": "violet-dark",
    "dark": "violet-dark",
    "dusk": "violet-dark",
    "paper": "violet-light",
    "light": "violet-light",
    "ink": "indigo-dark",
    "amoled": "indigo-dark",
    "midnight": "sky-dark",
    "tide": "aqua-dark",
    "forest": "mint-dark",
    "rose": "violet-dark",
    "copper": "violet-dark",
    "mocha": "violet-dark"
  },
  "families": [
    {
      "id": "violet",
      "name": "Violet",
      "seed": "#9F7EFF",
      "legacy": {
        "light": {
          "bg": "#F5F2FF", "bg2": "#EDE7FF", "surface": "#FFFFFF", "surface2": "#F7F4FF",
          "fg": "#08060D", "dim": "#473872", "dim2": "#6A54AA", "line": "#DACDFF", "line2": "#CAB8FF", "accent": "#9F7EFF", "accentText": "#5B3F9E"
        },
        "dark": {
          "bg": "#171721", "bg2": "#222130", "surface": "#2A293C", "surface2": "#444361",
          "fg": "#FFFFFF", "dim": "#AAAAB7", "dim2": "#8B8A9D", "line": "#35344B", "line2": "#605F78", "accent": "#9F7EFF", "accentText": "#C6B2FF"
        }
      }
    },
    {
      "id": "indigo",
      "name": "Indigo",
      "seed": "#8293FF",
      "legacy": {
        "light": {
          "bg": "#F2F4FF", "bg2": "#E8EBFF", "surface": "#FFFFFF", "surface2": "#F5F6FF",
          "fg": "#08060D", "dim": "#3B4172", "dim2": "#5761AA", "line": "#CFD5FF", "line2": "#BAC3FF", "accent": "#8293FF", "accentText": "#4A56A8"
        },
        "dark": {
          "bg": "#12171F", "bg2": "#1B212D", "surface": "#212838", "surface2": "#36425B",
          "fg": "#FFFFFF", "dim": "#A4A9B5", "dim2": "#828999", "line": "#2A3346", "line2": "#545E73", "accent": "#8293FF", "accentText": "#B4BEFF"
        }
      }
    },
    {
      "id": "sky",
      "name": "Sky",
      "seed": "#7BBDFE",
      "legacy": {
        "light": {
          "bg": "#F1F8FE", "bg2": "#E7F3FE", "surface": "#FFFFFF", "surface2": "#F4F9FE",
          "fg": "#08060D", "dim": "#385272", "dim2": "#527CA9", "line": "#CCE5FE", "line2": "#B6DAFE", "accent": "#7BBDFE", "accentText": "#235F93"
        },
        "dark": {
          "bg": "#182127", "bg2": "#222F39", "surface": "#2A3A46", "surface2": "#455F72",
          "fg": "#FFFFFF", "dim": "#ABB7BF", "dim2": "#8B9BA7", "line": "#354A58", "line2": "#607787", "accent": "#7BBDFE", "accentText": "#A9D5FF"
        }
      }
    },
    {
      "id": "aqua",
      "name": "Aqua",
      "seed": "#7CE0E6",
      "legacy": {
        "light": {
          "bg": "#F1FBFC", "bg2": "#E7F9FA", "surface": "#FFFFFF", "surface2": "#F4FCFD",
          "fg": "#08060D", "dim": "#386168", "dim2": "#53939A", "line": "#CDF3F5", "line2": "#B6EDF1", "accent": "#7CE0E6", "accentText": "#126F77"
        },
        "dark": {
          "bg": "#15241C", "bg2": "#1F3328", "surface": "#263F32", "surface2": "#3E6751",
          "fg": "#FFFFFF", "dim": "#A8BAB0", "dim2": "#87A093", "line": "#30503F", "line2": "#5A7D6B", "accent": "#7CE0E6", "accentText": "#A6EFF3"
        }
      }
    },
    {
      "id": "mint",
      "name": "Mint",
      "seed": "#7BFFA4",
      "legacy": {
        "light": {
          "bg": "#F1FFF5", "bg2": "#E7FFEE", "surface": "#FFFFFF", "surface2": "#F4FFF7",
          "fg": "#08060D", "dim": "#386E4C", "dim2": "#52A76F", "line": "#CCFFDC", "line2": "#B6FFCC", "accent": "#7BFFA4", "accentText": "#216A43"
        },
        "dark": {
          "bg": "#15241A", "bg2": "#1F3425", "surface": "#26412E", "surface2": "#3E694B",
          "fg": "#FFFFFF", "dim": "#A8BBAE", "dim2": "#87A28F", "line": "#30513A", "line2": "#5A7F66", "accent": "#7BFFA4", "accentText": "#A9FFC2"
        }
      }
    }
  ],
  "icons": [
    "audio-lines", "cast", "check", "chevron-down", "chevron-left", "chevron-right", "chevron-up",
    "circle", "circle-alert", "circle-check", "circle-help", "circle-x", "clock", "cookie", "coffee", "compass",
    "disc-3", "download", "dumbbell", "ellipsis", "eye-off", "flame", "flower", "film", "folder-plus",
    "grip-vertical", "hard-drive", "headphones", "heart", "house", "image", "inbox", "info",
    "key", "library", "link", "list", "list-music", "list-plus", "loader-circle", "lock",
    "log-in", "log-out", "mail", "message-circle", "mic-vocal", "monitor", "moon", "music",
    "palette", "pause", "pencil", "pentagon", "picture-in-picture-2", "pin", "play", "plus", "radio", "refresh-cw",
    "repeat", "repeat-1", "search", "server", "settings", "shield", "shield-alert", "shield-check",
    "shuffle", "skip-back", "skip-forward", "smartphone", "sparkles", "squircle", "star", "trash-2",
    "user-round", "volume-1", "volume-2", "volume-x", "wifi", "wifi-off", "x", "zap"
  ],
  "iconAliases": {
    "home": "house",
    "user": "user-round",
    "music-note": "music",
    "more-horizontal": "ellipsis",
    "trash": "trash-2",
    "circle_help": "circle-help"
  }
}
```


### `scripts/gen-tokens.mjs`

```js
#!/usr/bin/env node
// Generate every client's design tokens from design/tokens.json.
//
//   node scripts/gen-tokens.mjs           # write generated files
//   node scripts/gen-tokens.mjs --check   # fail if a generated file is stale
//
// The five family accents are Material 3 HCT seeds. The generated tonal roles
// come from @material/material-color-utilities. Legacy swatches stay verbatim in
// tokens.json so saved palette ids keep resolving to the same bytes.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  Hct,
  SchemeTonalSpot,
  TonalPalette,
  argbFromHex,
  hexFromArgb,
} from "../ui/node_modules/@material/material-color-utilities/index.js";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CHECK = process.argv.includes("--check");
const tokens = JSON.parse(fs.readFileSync(path.join(ROOT, "design/tokens.json"), "utf8"));
const outputs = new Map();

// `surface` exists in every legacy token set already, so the generated M3
// surface role reuses that field rather than duplicating a constructor arg.
const ROLES = [
  "primary", "onPrimary", "primaryContainer", "onPrimaryContainer",
  "secondary", "onSecondary", "secondaryContainer", "onSecondaryContainer",
  "tertiary", "onTertiary", "tertiaryContainer", "onTertiaryContainer",
  "error", "onError", "errorContainer", "onErrorContainer",
  "background", "onBackground", "onSurface",
  "surfaceVariant", "onSurfaceVariant",
  "surfaceContainerLowest", "surfaceContainerLow", "surfaceContainer",
  "surfaceContainerHigh", "surfaceContainerHighest",
  "outline", "outlineVariant", "inverseSurface", "inverseOnSurface",
  "inversePrimary", "scrim", "shadow",
];

/** Legacy accents are deliberately bright brand swatches. Text painted on them
 *  needs the higher-contrast of ink/white, not the M3 onPrimary role (which is
 *  paired with the generated darker `primary` role instead). */
function readableOn(hex) {
  const channel = value => {
    const v = value / 255;
    return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  };
  const luminance = color => {
    const r = channel(parseInt(color.slice(1, 3), 16));
    const g = channel(parseInt(color.slice(3, 5), 16));
    const b = channel(parseInt(color.slice(5, 7), 16));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const accent = luminance(hex.toUpperCase());
  const ink = luminance("#08060D");
  const white = luminance("#FFFFFF");
  const contrast = (a, b) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  return contrast(ink, accent) >= contrast(white, accent) ? "#08060D" : "#FFFFFF";
}

function rolesFor(family, mode) {
  const dark = mode === "dark";
  const source = Hct.fromInt(argbFromHex(family.seed));
  const scheme = new SchemeTonalSpot(source, dark, 0);
  // Low-chroma surfaces in the seed's own hue stay tonal without translucency.
  const surface = TonalPalette.fromHueAndChroma(
    source.hue, Math.min(20, Math.max(8, source.chroma / 5)),
  );
  const tone = (palette, t) => hexFromArgb(palette.tone(t)).toUpperCase();
  const fixed = {
    primary: scheme.primary,
    onPrimary: scheme.onPrimary,
    primaryContainer: scheme.primaryContainer,
    onPrimaryContainer: scheme.onPrimaryContainer,
    secondary: scheme.secondary,
    onSecondary: scheme.onSecondary,
    secondaryContainer: scheme.secondaryContainer,
    onSecondaryContainer: scheme.onSecondaryContainer,
    tertiary: scheme.tertiary,
    onTertiary: scheme.onTertiary,
    tertiaryContainer: scheme.tertiaryContainer,
    onTertiaryContainer: scheme.onTertiaryContainer,
    error: scheme.error,
    onError: scheme.onError,
    errorContainer: scheme.errorContainer,
    onErrorContainer: scheme.onErrorContainer,
    outline: scheme.outline,
    // M3's default outlineVariant is decorative (1.7:1 on light surfaces).
    // Boundaries in this app carry meaning, so use tone 55 (>=3.5:1).
    outlineVariant: surface.tone(55),
    inversePrimary: scheme.inversePrimary,
  };
  const legacy = family.legacy[mode];
  const roles = {
    ...Object.fromEntries(Object.entries(fixed)
      .map(([key, value]) => [key, hexFromArgb(value).toUpperCase()])),
    background: tone(surface, dark ? 6 : 99),
    onBackground: tone(surface, dark ? 95 : 10),
    surface: legacy.surface.toUpperCase(),
    onSurface: tone(surface, dark ? 95 : 10),
    surfaceVariant: tone(surface, dark ? 24 : 90),
    onSurfaceVariant: tone(surface, dark ? 80 : 30),
    surfaceContainerLowest: tone(surface, dark ? 4 : 99),
    surfaceContainerLow: tone(surface, dark ? 10 : 96),
    surfaceContainer: tone(surface, dark ? 12 : 94),
    surfaceContainerHigh: tone(surface, dark ? 17 : 92),
    surfaceContainerHighest: tone(surface, dark ? 22 : 90),
    inverseSurface: tone(surface, dark ? 95 : 20),
    inverseOnSurface: tone(surface, dark ? 20 : 95),
    scrim: "#000000",
    shadow: "#000000",
  };
  return {
    legacy,
    roles: {
      ...roles,
      accentFg: readableOn(legacy.accent),
    },
  };
}

const variants = Object.fromEntries(tokens.families.map(family => [
  family.id,
  Object.fromEntries(["light", "dark"].map(mode => [mode, rolesFor(family, mode)])),
]));

function put(relative, content) {
  outputs.set(path.join(ROOT, relative), content);
}

function replaceMarkers(relative, begin, end, generated) {
  const file = path.join(ROOT, relative);
  const content = fs.readFileSync(file, "utf8");
  const start = content.indexOf(begin);
  const stop = content.indexOf(end);
  if (start < 0 || stop < 0 || stop <= start) {
    throw new Error(`${relative}: missing generation markers`);
  }
  const body = generated.replace(/^\n+|\n+$/g, "");
  put(relative, content.slice(0, start + begin.length) + "\n" + body + "\n" + content.slice(stop));
}

const kebab = s => s.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
const snake = s => (s === "scrim" ? "scrim_color" : s === "shadow" ? "shadow_color"
  : s.replace(/([a-z0-9])([A-Z])/g, "$1_$2").toLowerCase());

// ── machine-readable export used by the contrast test ───────────────────────
put("design/tokens.generated.json", JSON.stringify({
  schema: tokens.schema,
  families: Object.fromEntries(Object.entries(variants).map(([id, modes]) => [
    id,
    Object.fromEntries(Object.entries(modes).map(([mode, value]) => [mode, {
      seed: tokens.families.find(f => f.id === id).seed,
      legacy: value.legacy,
      roles: value.roles,
    }])),
  ])),
  shape: tokens.shape,
  spacing: tokens.spacing,
  breakpoints: tokens.breakpoints,
  blobs: tokens.blobs,
  motion: tokens.motion,
  type: tokens.type,
  aliases: tokens.aliases,
}, null, 2) + "\n");

// ── CSS ─────────────────────────────────────────────────────────────────────
function cssVars(variant) {
  const l = variant.legacy;
  const r = variant.roles;
  const lines = [
    ["--back", l.bg], ["--back-raised", l.bg2], ["--flat-hover", l.line],
    ["--prim", l.surface], ["--prim-brighter", l.surface2], ["--seco", l.bg2],
    ["--tert", l.line], ["--tert-hover", l.line2],
    ["--text", l.fg], ["--text-bright", l.fg], ["--text-dim", l.dim], ["--text-dark", l.dim2],
    ["--accent", l.accent], ["--accent-hover", l.accentText],
    ["--text-on-light", r.accentFg], ["--accent-soft", r.primaryContainer],
    ["--accent-faint", r.surfaceContainerLow], ["--surface-lift", r.surfaceContainerHigh],
    ["--layer-rim", r.outlineVariant], ["--layer-highlight", r.outline],
    ["--elevation-1", "none"], ["--elevation-2", "none"],
    ["--back-border", l.line], ["--prim-border", l.line2],
    ["--shadow", r.scrim], ["--shadow-raised", "none"], ["--backdrop", r.scrim],
    ["--success", "#1DB954"], ["--warning", "#FFBF69"], ["--equaliser", "var(--accent)"],
    ["--radius", `${tokens.shape.card}px`], ["--radius-lg", `${tokens.shape.xl}px`],
    ["--radius-xl", `${tokens.shape.hero}px`], ["--radius-pill", `${tokens.shape.pill}px`],
    ["--shape-xs", `${tokens.shape.xs}px`], ["--shape-sm", `${tokens.shape.sm}px`],
    ["--shape-md", `${tokens.shape.md}px`], ["--shape-lg", `${tokens.shape.lg}px`],
    ["--shape-xl", `${tokens.shape.xl}px`], ["--shape-xxl", `${tokens.shape.xxl}px`],
    ["--touch-target", `${tokens.shape.touchTarget}px`],
    ["--bp-phone", `${tokens.breakpoints.phone}px`],
    ["--bp-tablet", `${tokens.breakpoints.tablet}px`],
    ["--bp-compact", `${tokens.breakpoints.compact}px`],
    ...tokens.blobs.map(blob => [`--${blob.id}-radius`, blob.borderRadius]),
    ["--topbar-h", "50px"], ["--player-h", "84px"],
    ["--spring-damping", String(tokens.motion.spring.damping)],
    ["--press-scale", String(tokens.motion.pressScale)],
    ["--morph-ms", `${tokens.motion.morphMs}ms`],
    ["--progress-wave-hz", String(tokens.motion.progressWaveHz)],
    ["--progress-wave-px", `${tokens.motion.progressWavePx}px`],
  ];
  for (const [name, style] of Object.entries(tokens.type)) {
    lines.push(["--type-" + name + "-size", `${style.size}px`]);
    lines.push(["--type-" + name + "-weight", String(style.weight)]);
    lines.push(["--type-" + name + "-line", `${style.line}px`]);
  }
  for (const role of ROLES) lines.push([`--md-${kebab(role)}`, r[role]]);
  return lines.map(([key, value]) => `    ${key}: ${value};`).join("\n");
}
put("ui/src/env.css", `/* GENERATED by scripts/gen-tokens.mjs — edit design/tokens.json instead.
   Flat Material 3 tones only. Do not hand-edit this file. */
:root {
${cssVars(variants.violet.dark)}
}

${tokens.families.flatMap(f => ["light", "dark"].map(mode =>
  `[data-palette="${f.id}-${mode}"] {\n${cssVars(variants[f.id][mode])}\n}`,
)).join("\n\n")}

/* Only Lucide's rect/circle primitives are fillable; paths stay outlined. */
svg.icon-filled > rect,
svg.icon-filled > circle {
    fill: currentColor;
    stroke: none;
}
`);

// ── shared responsive tiers (CSS literals cannot read custom properties) ──
put("ui/src/common/breakpoints.generated.ts", `/* GENERATED by scripts/gen-tokens.mjs — edit design/tokens.json instead. */
export const PHONE_BREAKPOINT = ${tokens.breakpoints.phone};
export const TABLET_BREAKPOINT = ${tokens.breakpoints.tablet};
export const COMPACT_BREAKPOINT = ${tokens.breakpoints.compact};

export type ResponsiveTier = "phone" | "tablet" | "compact" | "full";

export function tierForWidth(width: number): ResponsiveTier {
    if (width < PHONE_BREAKPOINT) return "phone";
    if (width < TABLET_BREAKPOINT) return "tablet";
    if (width < COMPACT_BREAKPOINT) return "compact";
    return "full";
}

export function isMobileChrome(tier: ResponsiveTier): boolean {
    return tier === "phone" || tier === "tablet";
}
`);

// ── blob geometry (normalised 100x100; CSS uses the radius fallback) ───────
const blobConst = id => id.toUpperCase().replace(/-/g, "_");
put("ui/src/common/blobs.generated.ts", `/* GENERATED by scripts/gen-tokens.mjs — edit design/tokens.json instead. */
export interface BlobToken {
    id: string;
    shape: string;
    borderRadius: string;
    path: string;
}

export const DESIGN_BLOBS: readonly BlobToken[] = [
${tokens.blobs.map(b => `    { id: ${JSON.stringify(b.id)}, shape: ${JSON.stringify(b.shape)}, borderRadius: ${JSON.stringify(b.borderRadius)}, path: ${JSON.stringify(b.path)} },`).join("\n")}
];

/** Normalised 100x100 path data, keyed by blob id. */
export const BLOB_PATHS: Record<string, string> = {
${tokens.blobs.map(b => `    ${JSON.stringify(b.id)}: ${JSON.stringify(b.path)},`).join("\n")}
};
`);

put("gui/android/app/src/main/java/dev/mcmusic/app/ui/design/Blobs.kt", `// GENERATED by scripts/gen-tokens.mjs — edit design/tokens.json instead.
package dev.mcmusic.app.ui.design

/** Normalised 100x100 blob geometry for Compose shapes and Canvas paths. */
object BlobShapes {
${tokens.blobs.map(b => `    const val ${blobConst(b.id)}_RADIUS = ${JSON.stringify(b.borderRadius)}
    const val ${blobConst(b.id)}_PATH = ${JSON.stringify(b.path)}`).join("\n\n")}

    val ids = listOf(${tokens.blobs.map(b => JSON.stringify(b.id)).join(", ")})

    val paths = mapOf(
${tokens.blobs.map(b => `        ${JSON.stringify(b.id)} to ${JSON.stringify(b.path)},`).join("\n")}
    )
}
`);

put("app/ios/McMusic/Blobs.swift", `// GENERATED by scripts/gen-tokens.mjs — edit design/tokens.json instead.
import Foundation

/// Normalised 100x100 blob geometry for SwiftUI paths and clip shapes.
enum BlobShapes {
    static let ids = [${tokens.blobs.map(b => JSON.stringify(b.id)).join(", ")}]

    static let radii: [String: String] = [
${tokens.blobs.map(b => `        ${JSON.stringify(b.id)}: ${JSON.stringify(b.borderRadius)},`).join("\n")}
    ]

    static let paths: [String: String] = [
${tokens.blobs.map(b => `        ${JSON.stringify(b.id)}: ${JSON.stringify(b.path)},`).join("\n")}
    ]
}
`);

put("app/linux/mcmusic_linux/blobs.py", `"""GENERATED by scripts/gen-tokens.mjs — edit design/tokens.json instead.

Normalised 100x100 blob geometry for Qt painters and clip paths.
"""
from __future__ import annotations

BLOBS = [
${tokens.blobs.map(b => `    {
        "id": ${JSON.stringify(b.id)},
        "shape": ${JSON.stringify(b.shape)},
        "borderRadius": ${JSON.stringify(b.borderRadius)},
        "path": ${JSON.stringify(b.path)},
    },`).join("\n")}
]

BLOB_PATHS = {
${tokens.blobs.map(b => `    ${JSON.stringify(b.id)}: ${JSON.stringify(b.path)},`).join("\n")}
}
`);

// ── TypeScript ──────────────────────────────────────────────────────────────
const tsRoles = ROLES.map(role => `    ${role}: string;`).join("\n");
const tsFamilies = tokens.families.map(f => {
  const modes = ["light", "dark"].map(mode => {
    const v = variants[f.id][mode];
    const body = [
      ...Object.entries(v.legacy).map(([k, value]) => `            ${k}: "${value}",`),
      `            accentFg: "${v.roles.accentFg}",`,
      ...ROLES.map(role => `            ${role}: "${v.roles[role]}",`),
    ].join("\n");
    return `        ${mode}: {\n${body}\n        },`;
  }).join("\n");
  return `    {\n        id: "${f.id}",\n        name: "${f.name}",\n${modes}\n    },`;
}).join("\n");
replaceMarkers("ui/src/common/theme.ts", "// BEGIN GENERATED PALETTE DATA", "// END GENERATED PALETTE DATA",
  `export type PaletteMode = "light" | "dark";
export type FamilyId = ${tokens.families.map(f => `"${f.id}"`).join(" | ")};

export const DESIGN_SHAPE = ${JSON.stringify(tokens.shape)} as const;
export const DESIGN_SPACING = ${JSON.stringify(tokens.spacing)} as const;
export const DESIGN_MOTION = ${JSON.stringify(tokens.motion)} as const;
export const DESIGN_TYPE = ${JSON.stringify(tokens.type)} as const;

export interface PaletteTokens {
    // Legacy swatches: unchanged bytes for stored palette ids.
    bg: string; bg2: string; surface: string; surface2: string;
    fg: string; dim: string; dim2: string; line: string; line2: string;
    accent: string; accentText: string; accentFg: string;
    // Generated Material 3 tonal roles (HCT from this family's accent seed).
${tsRoles}
}

export interface Palette extends PaletteTokens {
    /** Concrete id, e.g. \`violet-dark\`. */
    id: string;
    family: FamilyId;
    mode: PaletteMode;
}

export interface PaletteFamily {
    id: FamilyId;
    name: string;
    light: PaletteTokens;
    dark: PaletteTokens;
}

/** Generated Material 3 role names, exported for CSS variable mirroring. */
export const M3_ROLE_NAMES = ${JSON.stringify(ROLES)} as const;

/** CSS custom property for each generated Material 3 role. */
export const M3_CSS_VARS: Record<string, keyof PaletteTokens> = {
${ROLES.map(role => `    "--md-${kebab(role)}": "${role}",`).join("\n")}
};

export const PALETTE_FAMILIES: readonly PaletteFamily[] = [
${tsFamilies}
];

function concrete(family: PaletteFamily, mode: PaletteMode): Palette {
    const tokens = family[mode];
    return {
        ...tokens,
        id: family.id + "-" + mode,
        family: family.id,
        mode,
    };
}

/** Every pinned half of every family, keyed by its concrete id. */
export const PALETTE_VARIANTS: Record<string, Palette> = Object.fromEntries(
    PALETTE_FAMILIES.flatMap(f => ([
        [f.id + "-light", concrete(f, "light")] as [string, Palette],
        [f.id + "-dark", concrete(f, "dark")] as [string, Palette],
    ])),
);

/** Legacy settings/embed ids. Aliases resolve to a concrete variant where the
 *  old name already implied light or dark; bare family names stay adaptive. */
export const PALETTE_ALIASES: Record<string, string> = {
${Object.entries(tokens.aliases).map(([k, v]) => `    ${JSON.stringify(k)}: "${v}",`).join("\n")}
};`);

// ── Kotlin ──────────────────────────────────────────────────────────────────
const ktRoles = ROLES.map(role => `    val ${role}: Color,`).join("\n");
const ktArgs = ROLES.map(role => `    ${role}: String,`).join("\n");
const ktAssign = ROLES.map(role => `        ${role} = color(${role}),`).join("\n");
const ktFamilies = tokens.families.map(f => {
  const modes = ["light", "dark"].map(mode => {
    const v = variants[f.id][mode];
    const args = [
      ...Object.entries(v.legacy).map(([k, value]) => `${k} = "${value.slice(1)}"`),
      `accentFg = "${v.roles.accentFg.slice(1)}"`,
      ...ROLES.map(role => `${role} = "${v.roles[role].slice(1)}"`),
    ].join(", ");
    return `        ${mode} = variant("${f.id}", "${f.name}", ${mode === "dark"}, ${args}),`;
  }).join("\n");
  return `    val ${f.id} = PaletteFamily(\n        id = "${f.id}",\n        label = "${f.name}",\n${modes}\n    )`;
}).join("\n\n");
replaceMarkers("gui/android/app/src/main/java/dev/mcmusic/app/ui/design/Design.kt",
  "// BEGIN GENERATED PALETTES", "// END GENERATED PALETTES",
  `object Palettes {
    private fun color(hex: String) = Color(android.graphics.Color.parseColor("#$hex"))

    private fun variant(
        family: String, label: String, dark: Boolean,
        bg: String, bg2: String, surface: String, surface2: String,
        fg: String, dim: String, dim2: String, line: String, line2: String,
        accent: String, accentText: String, accentFg: String,
${ktArgs}
    ) = McPalette(
        id = "$family-" + (if (dark) "dark" else "light"),
        label = label, dark = dark,
        bg = color(bg), bg2 = color(bg2), surface = color(surface), surface2 = color(surface2),
        fg = color(fg), dim = color(dim), dim2 = color(dim2), line = color(line), line2 = color(line2),
        accent = color(accent), accentText = color(accentText), accentFg = color(accentFg),
${ktAssign}
    )

${ktFamilies}

    /** Exactly five chooser entries; each adapts to system light/dark. */
    val families = listOf(violet, indigo, sky, aqua, mint)

    private val byConcreteId: Map<String, McPalette> = families.flatMap { listOf(it.light, it.dark) }
        .associateBy { it.id }

    private val byFamilyId: Map<String, PaletteFamily> = families.associateBy { it.id }

    const val AUTO = "auto"

    /** Legacy ids keep the light/dark half they used to imply. */
    private val aliases = mapOf(
${Object.entries(tokens.aliases).filter(([k]) => k)
    .map(([k, v]) => `        "${k}" to ${v === "violet" ? "AUTO" : `"${v}"`},`).join("\n")}
    )

    private fun canonicalID(id: String?): String {
        val key = (id ?: AUTO).lowercase().trim()
        return aliases[key] ?: key
    }

    /** \`auto\`, \`system\`, empty and bare family ids follow system appearance. */
    fun resolve(id: String?, systemDark: Boolean): McPalette {
        val key = canonicalID(id)
        return byConcreteId[key]
            ?: byFamilyId[key]?.resolve(systemDark)
            ?: violet.resolve(systemDark)
    }
}`);

// ── Swift ───────────────────────────────────────────────────────────────────
const swiftFamilies = tokens.families.map(f => {
  const modes = ["light", "dark"].map(mode => {
    const v = variants[f.id][mode];
    const args = [
      ...Object.entries(v.legacy).map(([k, value]) => `${k}: Color(hex: "${value.slice(1)}")`),
      `accentFg: Color(hex: "${v.roles.accentFg.slice(1)}")`,
      ...ROLES.map(role => `${role}: Color(hex: "${v.roles[role].slice(1)}")`),
      `success: Color(hex: "1DB954")`,
      `isDark: ${mode === "dark"}`,
    ].join(", ");
    return `        ${mode}: PaletteTokens(${args})`;
  }).join(",\n");
  return `    static let ${f.id} = PaletteFamily(\n        id: .${f.id},\n${modes}\n    )`;
}).join("\n\n");
replaceMarkers("app/ios/McMusic/Theme.swift", "// BEGIN GENERATED PALETTES", "// END GENERATED PALETTES",
  `${swiftFamilies}\n\n    static let families: [PaletteFamily] = [${tokens.families.map(f => f.id).join(", ")}]`);

// ── Python / Qt ─────────────────────────────────────────────────────────────
const pyParams = ROLES.map(role => `${snake(role)}`).join(", ");
const pyAssign = ROLES.map(role => `        ${snake(role)}=${snake(role)},`).join("\n");
const pyFamilies = tokens.families.map(f => ["light", "dark"].map(mode => {
  const v = variants[f.id][mode];
  const args = [
    ...Object.entries(v.legacy).map(([k, value]) => `${k}=${JSON.stringify(value.toLowerCase())}`),
    `accent_fg=${JSON.stringify(v.roles.accentFg.toLowerCase())}`,
    ...ROLES.map(role => `${snake(role)}=${JSON.stringify(v.roles[role].toLowerCase())}`),
    `dark=${mode === "dark" ? "True" : "False"}`,
    `label=${JSON.stringify(f.name)}`,
  ].join(", ");
  return `${f.id}_${mode} = _variant(${args})`;
}).join("\n")).join("\n\n");
replaceMarkers("app/linux/mcmusic_linux/theme.py", "# BEGIN GENERATED PALETTES", "# END GENERATED PALETTES",
  `def _variant(bg, bg2, surface, surface2, fg, dim, dim2, line, line2, accent, accentText, accent_fg,
             ${pyParams}, dark, label):
    name = "%s-%s" % (label.lower(), "dark" if dark else "light")
    return Palette(
        name=name, bg=bg, bg2=bg2, surface=surface, surface2=surface2,
        fg=fg, dim=dim, dim2=dim2, line=line, line2=line2,
        accent=accent, accent_text=accentText, accent_fg=accent_fg, warn="#ffbf69",
        err="#ff6b72" if dark else "#b3261e",
        scrim="rgba(23, 23, 33, 0.78)", ink=bg2,
${pyAssign}
    )


${pyFamilies}

# Public uppercase aliases used by the runtime appearance state.
VIOLET_LIGHT = violet_light
VIOLET_DARK = violet_dark

FAMILIES = {
${tokens.families.map(f => `    ${JSON.stringify(f.id)}: (${JSON.stringify(f.name)}, ${f.id}_light, ${f.id}_dark),`).join("\n")}
}

PALETTES: dict[str, Palette] = {}
for _family, (_label, _light, _dark) in FAMILIES.items():
    PALETTES[_light.name] = _light
    PALETTES[_dark.name] = _dark

# Legacy saved values resolve to the nearest family.
ALIASES = {
${Object.entries(tokens.aliases).map(([k, v]) => `    ${JSON.stringify(k)}: ${JSON.stringify(v)},`).join("\n")}
}`);

// ── embed widgets ───────────────────────────────────────────────────────────
const widgetThemes = tokens.families.flatMap(f => ["light", "dark"].map(mode => {
  const v = variants[f.id][mode];
  const body = Object.entries(v.legacy).map(([k, value]) => `${k}:'${value}'`).join(", ");
  return `    '${f.id}-${mode}': { ${body} },`;
}));
replaceMarkers("web/embed/widgets.js", "// BEGIN GENERATED THEMES", "// END GENERATED THEMES",
  `const THEMES = {
${widgetThemes.join("\n")}
${tokens.families.map(f => `    ${f.id}: 'system',`).join("\n")}
${Object.entries(tokens.aliases).map(([k, v]) => `    ${JSON.stringify(k)}: ${v === "violet" ? "'system'" : JSON.stringify(v)},`).join("\n")}
  };`);

// ── write or verify ─────────────────────────────────────────────────────────
let stale = 0;
for (const [file, content] of outputs) {
  const current = fs.existsSync(file) ? fs.readFileSync(file, "utf8") : null;
  if (current === content) continue;
  stale++;
  if (CHECK) {
    console.error(`stale generated file: ${path.relative(ROOT, file)}`);
  } else {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, content);
    console.log(`generated ${path.relative(ROOT, file)}`);
  }
}
if (CHECK && stale) {
  console.error(`${stale} generated file(s) are stale; run node scripts/gen-tokens.mjs`);
  process.exit(1);
}
if (!CHECK) console.log(`gen-tokens: ${outputs.size} files up to date`);
```


### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  pull_request:
  # CI must also run on main: release.yml gates publishing on a CI run for the
  # exact pushed SHA (see its ci-gate job).
  push:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  # Do not cancel main runs: the release gate waits for the run matching the
  # pushed SHA. PR/branch runs still cancel superseded duplicates.
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}

jobs:
  web-checks:
    name: Web checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - name: Validate service worker is parseable
        run: node --check web/sw.js

  design-checks:
    name: Design token and flatness checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: ui/package-lock.json
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install UI dependencies for generation
        run: npm --prefix ui ci --no-audit --no-fund
      - name: Generated token/icon files must be current
        run: |
          node scripts/gen-tokens.mjs --check
          node scripts/gen-lucide.mjs --check
      - name: Install test dependencies
        run: python -m pip install pytest
      - name: Design gates (flatness, WCAG AA, generated freshness, blob/font contracts)
        run: |
          python -m pytest \
            tests/test_no_gradients.py \
            tests/test_contrast.py \
            tests/test_generated_fresh.py \
            tests/test_blobs.py \
            tests/test_font_bundling.py \
            -q

  ui-checks:
    name: Web UI build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: ui/package-lock.json
      # npm run build runs `tsc --noEmit -p tsconfig.app.json` before Vite, so
      # types are checked here. There is no ESLint config in the repo; no new
      # lint dependency is added for that reason.
      - name: Build the v3 client (ui/ -> web/ui/)
        run: ./scripts/build_ui.sh

  android-checks:
    name: Android build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'
      - uses: android-actions/setup-android@v3
        with:
          packages: "platforms;android-36 build-tools;36.0.0"
      - uses: gradle/actions/setup-gradle@v4
      - name: Compile and package the debug APK
        run: (cd gui/android && ./gradlew :app:assembleDebug --no-daemon --stacktrace)
      - name: Run Android JVM unit tests
        # CleartextPolicy is pure JVM code (no emulator); these tests prove the
        # private-range parsing without DNS or sockets.
        run: (cd gui/android && ./gradlew :app:testDebugUnitTest --no-daemon --stacktrace)
      - name: Build and verify the signed release APK
        run: |
          set -euo pipefail
          version=$(grep -oP 'versionName\s*=\s*"\K[^"]+' gui/android/app/build.gradle.kts | head -1)
          rm -f gui/android/app/build/outputs/apk/release/app-release.apk
          (cd gui/android && ./gradlew :app:assembleRelease --no-daemon --stacktrace)
          apk=gui/android/app/build/outputs/apk/release/app-release.apk
          aapt="$ANDROID_HOME/build-tools/36.0.0/aapt"
          apksigner="$ANDROID_HOME/build-tools/36.0.0/apksigner"
          badging=$("$aapt" dump badging "$apk")
          apk_version=$(grep -m1 -o "versionName='[^']*'" <<<"$badging" | cut -d"'" -f2)
          if [ "$apk_version" != "$version" ]; then
            echo "APK version $apk_version does not match Gradle version $version" >&2
            exit 1
          fi
          signer=$("$apksigner" verify --print-certs "$apk" | tr '[:upper:]' '[:lower:]')
          if ! grep -q 0b0fd0fa35ff712901d42cab215d5e3cb706daef57bffa7ebef61cacda1dc4ce <<<"$signer"; then
            echo "APK has an unexpected signer certificate" >&2
            exit 1
          fi
      - name: Upload APKs
        uses: actions/upload-artifact@v4
        with:
          name: mcmusic-apks
          path: |
            gui/android/app/build/outputs/apk/debug/app-debug.apk
            gui/android/app/build/outputs/apk/release/app-release.apk
          if-no-files-found: error

  python-checks:
    name: Python checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      # Generated-freshness and icon-pref tests invoke Node against the UI
      # sources, so this job needs the same pinned dependencies as design-checks.
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: ui/package-lock.json
      - name: Install UI dependencies for Node-based tests
        run: npm --prefix ui ci --no-audit --no-fund
      # The unused imports and shadowed locals that used to trip this check
      # are gone, so pyflakes is now a release-blocking gate.
      - name: Pyflakes
        run: |
          pip install pyflakes
          python -m pyflakes app/linux src music_activity tools
      - name: Compile key Python modules
        run: |
          python -m py_compile \
            src/mcmusic.py \
            src/config.py \
            src/auth.py \
            src/database.py \
            src/next_song_model.py \
            src/routes/system_routes.py \
            src/routes/library_routes.py \
            src/routes/personal_routes.py \
            src/routes/auth_routes.py \
            src/routes/channel_routes.py \
            src/zip_import.py \
            src/flufi_pages.py \
            src/discord_link.py \
            tools/import_zip.py \
            src/discord_bot.py \
            src/music_channels.py \
            src/originchats.py \
            algo/encoding.py \
            algo/mdl.py
      - name: Install test dependencies
        run: pip install -r requirements.txt pytest
      - name: Smoke test documented server commands
        # Uses the same .venv path as the docs while reusing the system site
        # packages installed above. Each command gets its own temp data dir.
        run: |
          python -m venv --system-site-packages .venv
          ./tests/test_server_startup.sh
      - name: Run Python test suite
        # Qt-dependent suites live in qt-checks, which installs PySide6 and
        # sets QT_QPA_PLATFORM=offscreen. Running them here without Qt would
        # turn a packaging detail into a false failure.
        run: |
          python -m pytest tests -q \
            --ignore=tests/test_qt_ui.py \
            --ignore=tests/test_qt_client.py \
            --ignore=tests/test_qt_icons.py \
            --ignore=tests/test_widgets.py \
            --ignore=tests/test_no_qt_shadowing.py \
            --ignore=tests/test_qt_selftest.py \
            --ignore=tests/test_updates.py
      - name: Check version sources
        run: ./scripts/check-versions.sh
      - name: Test version consistency checker
        run: ./tests/test_check_versions.sh
      - name: Test release publish script
        # Fake gh shim: no release is created and no tag is pushed here.
        run: ./tests/test_publish_release.sh
      - name: Shellcheck shell scripts
        run: |
          sudo apt-get update
          sudo apt-get install -y --no-install-recommends shellcheck
          shellcheck scripts/*.sh tests/*.sh

  qt-checks:
    name: Qt tests (offscreen)
    runs-on: ubuntu-latest
    timeout-minutes: 20
    env:
      QT_QPA_PLATFORM: offscreen
      # GitHub runners have no sound card; constructing QAudioOutput there can
      # segfault inside Qt's platform plugin. The opt-in stub replaces only the
      # audio backend, so all client logic still runs for real.
      MC_MUSIC_QT_AUDIO_STUB: "1"
      # QSettings caches its native path on first use, so isolate the whole
      # process before any Qt suite creates a QApplication. The runner context
      # is not available at job level; github.workspace is.
      XDG_CONFIG_HOME: ${{ github.workspace }}/.mcmusic-config
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install Qt runtime libraries
        run: |
          sudo apt-get update
          sudo apt-get install -y --no-install-recommends \
            libegl1 libgl1 libxkbcommon0 libdbus-1-3 libpulse0
      - name: Install Python and Qt test dependencies
        # Full PySide6 (not PySide6-Essentials) supplies QtMultimedia.
        run: pip install -r requirements.txt pytest PySide6
      - name: Verify QtMultimedia is importable
        # The Qt suites skip themselves when PySide6/QtMultimedia cannot be
        # imported. Fail here instead so a missing module cannot turn a broken
        # setup into a green run of skipped tests. The audio backend is stubbed
        # only because runners have no sound card; Python errors and crashes in
        # the client still fail this job.
        run: python -c 'from PySide6 import QtMultimedia; from PySide6.QtWidgets import QApplication'
      - name: Run Qt tests
        # These suites have segfaulted in some sandboxes. A crash gives a
        # non-zero exit code and fails the job; it is not masked here.
        run: |
          python -m pytest \
            tests/test_qt_ui.py \
            tests/test_qt_client.py \
            tests/test_qt_icons.py \
            tests/test_widgets.py \
            tests/test_no_qt_shadowing.py \
            tests/test_qt_selftest.py \
            tests/test_updates.py \
            -q

  macos-checks:
    name: macOS native build
    runs-on: macos-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Build native Qt .app and .dmg
        run: |
          set -euo pipefail
          version=$(sed -n 's/^FALLBACK_VERSION[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' app/linux/mcmusic_linux/version.py | head -1)
          MAKE_DMG=1 VERSION="$version" ./app/macos/build.sh
      - name: Verify the bundle contains no web engine or HTML
        run: |
          set -euo pipefail
          app=app/macos/dist/mcmusic.app
          test -f "$app/Contents/MacOS/mcmusic"
          test -f "$app/Contents/Info.plist"
          /usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$app/Contents/Info.plist" | grep -qx 'dev.mcmusic.app'
          if find "$app" \( -iname 'QtWebEngine*' -o -iname 'QtWebKit*' -o -iname 'index.html' \) | grep -q .; then
            echo "macOS bundle contains a web engine or HTML assets" >&2
            exit 1
          fi
          echo "verified: native Qt bundle, no HTML/WebView"
      - uses: actions/upload-artifact@v4
        with:
          name: mcmusic-macos
          path: |
            app/macos/dist/mcmusic.app
            app/macos/dist/mcmusic-*.dmg
          if-no-files-found: error

  windows-checks:
    name: Windows native build
    runs-on: windows-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Build native Qt .exe and .zip
        shell: pwsh
        run: |
          $version = (Select-String -Path 'app/linux/mcmusic_linux/version.py' -Pattern 'FALLBACK_VERSION\s*=\s*"([^"]+)"').Matches[0].Groups[1].Value
          ./app/windows/build.ps1 -Version $version -Zip
      - name: Verify the build contains no web engine or HTML
        shell: pwsh
        run: |
          $exe = "app/windows/dist/mcmusic/mcmusic.exe"
          if (-not (Test-Path $exe)) { throw "missing $exe" }
          $web = Get-ChildItem -Path "app/windows/dist/mcmusic" -Recurse -File |
            Where-Object { $_.Name -match 'QtWebEngine|QtWebKit|index\.html' }
          if ($web) { throw "Windows build contains a web engine or HTML: $($web.FullName -join ', ')" }
          $meta = Get-Content "app/windows/dist/mcmusic/version.json" -Raw | ConvertFrom-Json
          if ($meta.name -ne 'mcmusic') { throw "unexpected version metadata" }
          Write-Host "verified: native Qt exe, no HTML/WebView"
      - uses: actions/upload-artifact@v4
        with:
          name: mcmusic-windows
          path: |
            app/windows/dist/mcmusic
            app/windows/dist/mcmusic-windows-*.zip
          if-no-files-found: error

  ios-checks:
    name: iOS native build
    runs-on: macos-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v5
      - name: Install XcodeGen
        run: brew install xcodegen
      - name: Prepare app icon
        run: |
          set -euo pipefail
          mkdir -p app/ios/McMusic/Assets.xcassets/AppIcon.appiconset
          sips -z 1024 1024 web/icon-512.png --out app/ios/McMusic/Assets.xcassets/AppIcon.appiconset/icon-1024.png >/dev/null
      - name: Generate Xcode project
        run: xcodegen generate --spec app/ios/project.yml --project app/ios
      - name: Build and test unsigned iOS Simulator app
        run: |
          set -euo pipefail
          # Build the shippable app on its own so XCTest frameworks do not end
          # up embedded in the uploaded bundle.
          derived=build/ios
          common=(-project app/ios/McMusic.xcodeproj -configuration Release CODE_SIGNING_ALLOWED=NO)
          xcodebuild "${common[@]}" -scheme McMusicApp -derivedDataPath "$derived" \
            -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
            ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO build
          # Tests get a separate derived-data path for the same reason.
          sim_id=$(xcrun simctl list devices available -j | python3 -c 'import json,sys; d=json.load(sys.stdin); devs=[x for r in d["devices"].values() for x in r if x.get("isAvailable") and x["name"].startswith("iPhone")]; print(devs[0]["udid"] if devs else "")')
          if [ -n "$sim_id" ]; then
            xcodebuild "${common[@]}" -scheme McMusic -derivedDataPath build/ios-tests \
              -sdk iphonesimulator -destination "platform=iOS Simulator,id=$sim_id" \
              test
          else
            echo "no iPhone simulator available; skipping test action" >&2
          fi
      - name: Verify the iOS bundle is native
        run: |
          set -euo pipefail
          app=$(find build/ios/Build/Products -maxdepth 2 -type d -name 'McMusic.app' | head -1)
          test -n "$app"
          test -f "$app/McMusic"
          plutil -lint "$app/Info.plist"
          /usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$app/Info.plist" | grep -qx 'dev.mcmusic.ios'
          if find "$app" \( -iname '*WebView*' -o -iname 'index.html' -o -iname '*XCTest*' \) | grep -q .; then
            echo "iOS bundle contains a web view, HTML or test frameworks" >&2
            exit 1
          fi
          echo "verified: native SwiftUI app, no HTML/WebView/test frameworks"
      - uses: actions/upload-artifact@v4
        with:
          name: mcmusic-ios-simulator
          path: build/ios/Build/Products/Release-iphonesimulator/McMusic.app
          if-no-files-found: error

  responsive-checks:
    name: Responsive UI checks
    runs-on: ubuntu-latest
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: ui/package-lock.json
      - name: Install UI dependencies
        run: npm --prefix ui ci --no-audit --no-fund
      - name: Install Playwright Chromium
        # Run from ui/ so npx resolves the @playwright/test binary from ui/node_modules.
        working-directory: ui
        run: npx playwright install --with-deps chromium
      - name: Build the v3 client (ui/ -> web/ui/)
        run: ./scripts/build_ui.sh
      - name: Run responsive Playwright tests
        run: npm --prefix ui run test:e2e
      - name: Upload Playwright results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-results
          path: ui/test-results/**
          if-no-files-found: warn
```


### `tests/test_blobs.py`

```python
"""Blob geometry is a shared, generated contract across every client.

The authored shapes live in ``design/tokens.json``; each client consumes a
generated copy so no path can drift by hand.  Paths are normalised to a
100x100 viewBox.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = ("blob-1", "blob-2", "blob-3", "blob-4", "blob-5")


def authored():
    return json.loads((ROOT / "design/tokens.json").read_text())


def test_blob_tokens_are_generated_verbatim():
    blobs = authored()["blobs"]
    generated = json.loads((ROOT / "design/tokens.generated.json").read_text())

    assert [blob["id"] for blob in blobs] == list(IDS)
    assert generated["blobs"] == blobs

    for blob in blobs:
        assert blob["shape"]
        assert blob["borderRadius"]
        path = blob["path"]
        assert path.startswith("M ") and path.endswith(" Z"), blob["id"]
        numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", path)]
        assert all(-2 <= n <= 102 for n in numbers), blob["id"]
        assert min(numbers) <= 5 and max(numbers) >= 95, blob["id"]


def test_every_client_carries_authored_geometry():
    blobs = authored()["blobs"]
    targets = (
        ROOT / "ui/src/common/blobs.generated.ts",
        ROOT / "gui/android/app/src/main/java/dev/mcmusic/app/ui/design/Blobs.kt",
        ROOT / "app/ios/McMusic/Blobs.swift",
        ROOT / "app/linux/mcmusic_linux/blobs.py",
    )
    for target in targets:
        assert target.is_file(), f"missing generated blob module: {target}"
        text = target.read_text()
        for blob in blobs:
            assert json.dumps(blob["path"]) in text, f"{target.name}: stale {blob['id']} path"
            assert json.dumps(blob["borderRadius"]) in text, f"{target.name}: stale {blob['id']} radius"

    css = (ROOT / "ui/src/env.css").read_text()
    for blob in blobs:
        assert f"--{blob['id']}-radius: {blob['borderRadius']};" in css, blob["id"]
```


### `tests/test_font_bundling.py`

```python
"""4.3.0 fonts stay local, licensed and free of network requests."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FONT_PACKAGES = frozenset({
    "@fontsource-variable/inter",
    "@fontsource-variable/jetbrains-mono",
    "@fontsource-variable/lexend",
})


def test_only_bundled_fontsource_packages():
    package = json.loads((ROOT / "ui/package.json").read_text())
    dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    font_packages = frozenset(
        name for name in dependencies
        if "font" in name.lower() or "typeface" in name.lower()
    )
    assert font_packages == EXPECTED_FONT_PACKAGES
    assert not any("google" in name.lower() for name in dependencies)

    main = (ROOT / "ui/src/main.tsx").read_text()
    for name in sorted(EXPECTED_FONT_PACKAGES):
        assert f'"{name}/index.css"' in main, name

    sources = list((ROOT / "ui/src").rglob("*.css")) + [ROOT / "ui/index.html"]
    for source in sources:
        assert "@import url(" not in source.read_text(), str(source.relative_to(ROOT))

    assert "strip-font-cdn.mjs" in (ROOT / "scripts/build_ui.sh").read_text()


def test_google_sans_flex_decision_is_recorded():
    spec = (ROOT / "docs/design-4.3.md").read_text()
    assert "Google Sans Flex" in spec
    assert "not adopted" in spec
    assert "OFL 1.1" in spec
```


### `ui/src/common/blobs.generated.ts`

```ts
/* GENERATED by scripts/gen-tokens.mjs — edit design/tokens.json instead. */
export interface BlobToken {
    id: string;
    shape: string;
    borderRadius: string;
    path: string;
}

export const DESIGN_BLOBS: readonly BlobToken[] = [
    { id: "blob-1", shape: "circle", borderRadius: "50%", path: "M 50 4 A 46 46 0 1 0 50 96 A 46 46 0 1 0 50 4 Z" },
    { id: "blob-2", shape: "squircle", borderRadius: "32% / 28%", path: "M 22 4 H 78 C 87.94 4 96 12.06 96 22 V 78 C 96 87.94 87.94 96 78 96 H 22 C 12.06 96 4 87.94 4 78 V 22 C 4 12.06 12.06 4 22 4 Z" },
    { id: "blob-3", shape: "cookie", borderRadius: "48% 52% 43% 57% / 52% 44% 56% 48%", path: "M 50 4 C 63.2 0.74 75.5 5.83 82.53 17.47 C 94.17 24.5 99.26 36.8 96 50 C 99.26 63.2 94.17 75.5 82.53 82.53 C 75.5 94.17 63.2 99.26 50 96 C 36.8 99.26 24.5 94.17 17.47 82.53 C 5.83 75.5 0.74 63.2 4 50 C 0.74 36.8 5.83 24.5 17.47 17.47 C 24.5 5.83 36.8 0.74 50 4 Z" },
    { id: "blob-4", shape: "six-petal flower", borderRadius: "50%", path: "M 50 20 C 67.1 3.02 82.14 11.7 75.98 35 C 99.24 41.32 99.24 58.68 75.98 65 C 82.14 88.3 67.1 96.98 50 80 C 32.9 96.98 17.86 88.3 24.02 65 C 0.76 58.68 0.76 41.32 24.02 35 C 17.86 11.7 32.9 3.02 50 20 Z" },
    { id: "blob-5", shape: "asymmetric pebble", borderRadius: "42% 58% 63% 37% / 57% 42% 58% 43%", path: "M 50 4 C 78 4 96 22 96 48 C 96 76 72 96 44 96 C 20 96 4 74 4 50 C 4 26 24 4 50 4 Z" },
];

/** Normalised 100x100 path data, keyed by blob id. */
export const BLOB_PATHS: Record<string, string> = {
    "blob-1": "M 50 4 A 46 46 0 1 0 50 96 A 46 46 0 1 0 50 4 Z",
    "blob-2": "M 22 4 H 78 C 87.94 4 96 12.06 96 22 V 78 C 96 87.94 87.94 96 78 96 H 22 C 12.06 96 4 87.94 4 78 V 22 C 4 12.06 12.06 4 22 4 Z",
    "blob-3": "M 50 4 C 63.2 0.74 75.5 5.83 82.53 17.47 C 94.17 24.5 99.26 36.8 96 50 C 99.26 63.2 94.17 75.5 82.53 82.53 C 75.5 94.17 63.2 99.26 50 96 C 36.8 99.26 24.5 94.17 17.47 82.53 C 5.83 75.5 0.74 63.2 4 50 C 0.74 36.8 5.83 24.5 17.47 17.47 C 24.5 5.83 36.8 0.74 50 4 Z",
    "blob-4": "M 50 20 C 67.1 3.02 82.14 11.7 75.98 35 C 99.24 41.32 99.24 58.68 75.98 65 C 82.14 88.3 67.1 96.98 50 80 C 32.9 96.98 17.86 88.3 24.02 65 C 0.76 58.68 0.76 41.32 24.02 35 C 17.86 11.7 32.9 3.02 50 20 Z",
    "blob-5": "M 50 4 C 78 4 96 22 96 48 C 96 76 72 96 44 96 C 20 96 4 74 4 50 C 4 26 24 4 50 4 Z",
};
```


### `gui/android/app/src/main/java/dev/mcmusic/app/ui/design/Blobs.kt`

```kotlin
// GENERATED by scripts/gen-tokens.mjs — edit design/tokens.json instead.
package dev.mcmusic.app.ui.design

/** Normalised 100x100 blob geometry for Compose shapes and Canvas paths. */
object BlobShapes {
    const val BLOB_1_RADIUS = "50%"
    const val BLOB_1_PATH = "M 50 4 A 46 46 0 1 0 50 96 A 46 46 0 1 0 50 4 Z"

    const val BLOB_2_RADIUS = "32% / 28%"
    const val BLOB_2_PATH = "M 22 4 H 78 C 87.94 4 96 12.06 96 22 V 78 C 96 87.94 87.94 96 78 96 H 22 C 12.06 96 4 87.94 4 78 V 22 C 4 12.06 12.06 4 22 4 Z"

    const val BLOB_3_RADIUS = "48% 52% 43% 57% / 52% 44% 56% 48%"
    const val BLOB_3_PATH = "M 50 4 C 63.2 0.74 75.5 5.83 82.53 17.47 C 94.17 24.5 99.26 36.8 96 50 C 99.26 63.2 94.17 75.5 82.53 82.53 C 75.5 94.17 63.2 99.26 50 96 C 36.8 99.26 24.5 94.17 17.47 82.53 C 5.83 75.5 0.74 63.2 4 50 C 0.74 36.8 5.83 24.5 17.47 17.47 C 24.5 5.83 36.8 0.74 50 4 Z"

    const val BLOB_4_RADIUS = "50%"
    const val BLOB_4_PATH = "M 50 20 C 67.1 3.02 82.14 11.7 75.98 35 C 99.24 41.32 99.24 58.68 75.98 65 C 82.14 88.3 67.1 96.98 50 80 C 32.9 96.98 17.86 88.3 24.02 65 C 0.76 58.68 0.76 41.32 24.02 35 C 17.86 11.7 32.9 3.02 50 20 Z"

    const val BLOB_5_RADIUS = "42% 58% 63% 37% / 57% 42% 58% 43%"
    const val BLOB_5_PATH = "M 50 4 C 78 4 96 22 96 48 C 96 76 72 96 44 96 C 20 96 4 74 4 50 C 4 26 24 4 50 4 Z"

    val ids = listOf("blob-1", "blob-2", "blob-3", "blob-4", "blob-5")

    val paths = mapOf(
        "blob-1" to "M 50 4 A 46 46 0 1 0 50 96 A 46 46 0 1 0 50 4 Z",
        "blob-2" to "M 22 4 H 78 C 87.94 4 96 12.06 96 22 V 78 C 96 87.94 87.94 96 78 96 H 22 C 12.06 96 4 87.94 4 78 V 22 C 4 12.06 12.06 4 22 4 Z",
        "blob-3" to "M 50 4 C 63.2 0.74 75.5 5.83 82.53 17.47 C 94.17 24.5 99.26 36.8 96 50 C 99.26 63.2 94.17 75.5 82.53 82.53 C 75.5 94.17 63.2 99.26 50 96 C 36.8 99.26 24.5 94.17 17.47 82.53 C 5.83 75.5 0.74 63.2 4 50 C 0.74 36.8 5.83 24.5 17.47 17.47 C 24.5 5.83 36.8 0.74 50 4 Z",
        "blob-4" to "M 50 20 C 67.1 3.02 82.14 11.7 75.98 35 C 99.24 41.32 99.24 58.68 75.98 65 C 82.14 88.3 67.1 96.98 50 80 C 32.9 96.98 17.86 88.3 24.02 65 C 0.76 58.68 0.76 41.32 24.02 35 C 17.86 11.7 32.9 3.02 50 20 Z",
        "blob-5" to "M 50 4 C 78 4 96 22 96 48 C 96 76 72 96 44 96 C 20 96 4 74 4 50 C 4 26 24 4 50 4 Z",
    )
}
```


### `app/ios/McMusic/Blobs.swift`

```swift
// GENERATED by scripts/gen-tokens.mjs — edit design/tokens.json instead.
import Foundation

/// Normalised 100x100 blob geometry for SwiftUI paths and clip shapes.
enum BlobShapes {
    static let ids = ["blob-1", "blob-2", "blob-3", "blob-4", "blob-5"]

    static let radii: [String: String] = [
        "blob-1": "50%",
        "blob-2": "32% / 28%",
        "blob-3": "48% 52% 43% 57% / 52% 44% 56% 48%",
        "blob-4": "50%",
        "blob-5": "42% 58% 63% 37% / 57% 42% 58% 43%",
    ]

    static let paths: [String: String] = [
        "blob-1": "M 50 4 A 46 46 0 1 0 50 96 A 46 46 0 1 0 50 4 Z",
        "blob-2": "M 22 4 H 78 C 87.94 4 96 12.06 96 22 V 78 C 96 87.94 87.94 96 78 96 H 22 C 12.06 96 4 87.94 4 78 V 22 C 4 12.06 12.06 4 22 4 Z",
        "blob-3": "M 50 4 C 63.2 0.74 75.5 5.83 82.53 17.47 C 94.17 24.5 99.26 36.8 96 50 C 99.26 63.2 94.17 75.5 82.53 82.53 C 75.5 94.17 63.2 99.26 50 96 C 36.8 99.26 24.5 94.17 17.47 82.53 C 5.83 75.5 0.74 63.2 4 50 C 0.74 36.8 5.83 24.5 17.47 17.47 C 24.5 5.83 36.8 0.74 50 4 Z",
        "blob-4": "M 50 20 C 67.1 3.02 82.14 11.7 75.98 35 C 99.24 41.32 99.24 58.68 75.98 65 C 82.14 88.3 67.1 96.98 50 80 C 32.9 96.98 17.86 88.3 24.02 65 C 0.76 58.68 0.76 41.32 24.02 35 C 17.86 11.7 32.9 3.02 50 20 Z",
        "blob-5": "M 50 4 C 78 4 96 22 96 48 C 96 76 72 96 44 96 C 20 96 4 74 4 50 C 4 26 24 4 50 4 Z",
    ]
}
```


### `app/linux/mcmusic_linux/blobs.py`

```python
"""GENERATED by scripts/gen-tokens.mjs — edit design/tokens.json instead.

Normalised 100x100 blob geometry for Qt painters and clip paths.
"""
from __future__ import annotations

BLOBS = [
    {
        "id": "blob-1",
        "shape": "circle",
        "borderRadius": "50%",
        "path": "M 50 4 A 46 46 0 1 0 50 96 A 46 46 0 1 0 50 4 Z",
    },
    {
        "id": "blob-2",
        "shape": "squircle",
        "borderRadius": "32% / 28%",
        "path": "M 22 4 H 78 C 87.94 4 96 12.06 96 22 V 78 C 96 87.94 87.94 96 78 96 H 22 C 12.06 96 4 87.94 4 78 V 22 C 4 12.06 12.06 4 22 4 Z",
    },
    {
        "id": "blob-3",
        "shape": "cookie",
        "borderRadius": "48% 52% 43% 57% / 52% 44% 56% 48%",
        "path": "M 50 4 C 63.2 0.74 75.5 5.83 82.53 17.47 C 94.17 24.5 99.26 36.8 96 50 C 99.26 63.2 94.17 75.5 82.53 82.53 C 75.5 94.17 63.2 99.26 50 96 C 36.8 99.26 24.5 94.17 17.47 82.53 C 5.83 75.5 0.74 63.2 4 50 C 0.74 36.8 5.83 24.5 17.47 17.47 C 24.5 5.83 36.8 0.74 50 4 Z",
    },
    {
        "id": "blob-4",
        "shape": "six-petal flower",
        "borderRadius": "50%",
        "path": "M 50 20 C 67.1 3.02 82.14 11.7 75.98 35 C 99.24 41.32 99.24 58.68 75.98 65 C 82.14 88.3 67.1 96.98 50 80 C 32.9 96.98 17.86 88.3 24.02 65 C 0.76 58.68 0.76 41.32 24.02 35 C 17.86 11.7 32.9 3.02 50 20 Z",
    },
    {
        "id": "blob-5",
        "shape": "asymmetric pebble",
        "borderRadius": "42% 58% 63% 37% / 57% 42% 58% 43%",
        "path": "M 50 4 C 78 4 96 22 96 48 C 96 76 72 96 44 96 C 20 96 4 74 4 50 C 4 26 24 4 50 4 Z",
    },
]

BLOB_PATHS = {
    "blob-1": "M 50 4 A 46 46 0 1 0 50 96 A 46 46 0 1 0 50 4 Z",
    "blob-2": "M 22 4 H 78 C 87.94 4 96 12.06 96 22 V 78 C 96 87.94 87.94 96 78 96 H 22 C 12.06 96 4 87.94 4 78 V 22 C 4 12.06 12.06 4 22 4 Z",
    "blob-3": "M 50 4 C 63.2 0.74 75.5 5.83 82.53 17.47 C 94.17 24.5 99.26 36.8 96 50 C 99.26 63.2 94.17 75.5 82.53 82.53 C 75.5 94.17 63.2 99.26 50 96 C 36.8 99.26 24.5 94.17 17.47 82.53 C 5.83 75.5 0.74 63.2 4 50 C 0.74 36.8 5.83 24.5 17.47 17.47 C 24.5 5.83 36.8 0.74 50 4 Z",
    "blob-4": "M 50 20 C 67.1 3.02 82.14 11.7 75.98 35 C 99.24 41.32 99.24 58.68 75.98 65 C 82.14 88.3 67.1 96.98 50 80 C 32.9 96.98 17.86 88.3 24.02 65 C 0.76 58.68 0.76 41.32 24.02 35 C 17.86 11.7 32.9 3.02 50 20 Z",
    "blob-5": "M 50 4 C 78 4 96 22 96 48 C 96 76 72 96 44 96 C 20 96 4 74 4 50 C 4 26 24 4 50 4 Z",
}
```
