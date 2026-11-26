# mcmusic 4.3.0 — Phase 1 report

Branch: `design-4.3.0`, based on Phase 0 (`078adfa`). Web-only phase: no version bump and no release action.

## What changed

- Added a reusable `BlobAccent` web component that paints the generated canonical 100×100 blob paths with a flat M3 tonal fill and one `outlineVariant` hairline. It is decorative and `aria-hidden`; no gradient, translucency or elevation is used.
- Upgraded `CoverArt` placeholders from rounded-box Lucide glyphs to the five generated blob paths. Real cover images are untouched and keep a 28px squircle corner; only missing artwork morphs into a blob.
- Rebuilt Home's top of page as two asymmetric flat hero cards: the first uses the real first `/api/home` shelf, the second uses the next real shelf, the first real album, or an honest empty-library prompt. A centred segmented pill groups peer shelf actions.
- Turned the transport into a detached pill: flat `surfaceContainerHigh`, one rim, left transport cluster, centre metadata capsule and right action cluster. The play button morphs circle → generated squircle blob while playing; the progress fill carries a 3px, 0.55Hz wave only while playing with playful motion enabled.
- Added one segmented `Lyrics | Up next` pill shared by both peer sheets, plus a sticky pill shortcut row (`Lyrics`, `Devices`, `Queue`) in the lyrics sheet. No new endpoint is used: the queue is the existing local playback queue and lyrics stay the existing LRC/plain fetch.
- Converted the desktop sidebar into an attached capsule rail with pill destinations and active-state stroke 2.5, and gave the brand mark a generated pebble radius. Compact tiers keep the previously verified auto-collapse and touch-target rules.
- Measured the detached capsule's real occupied height (187px below 1100px, 147px at full width) and updated the content reserve and sheet offsets to match, so the open lyrics sheet no longer paints over player controls.
- Added `ui/e2e/playful.spec.ts`: generated blob-path parity, play morph/wave behaviour (including the reduced-motion/setting path), the two-tab sheet flow, and screenshot artifacts at 800/1024/1280 with full layout checks. The CI Playwright job picks this file up automatically and uploads its artifacts.

## What was run

- `node scripts/gen-tokens.mjs --check` and `node scripts/gen-lucide.mjs --check` — no drift.
- `.venv/bin/python -m pytest tests/test_no_gradients.py tests/test_contrast.py tests/test_generated_fresh.py tests/test_blobs.py tests/test_font_bundling.py -q` — 7 passed; no gradient/blur/shadow/glass violations and WCAG AA held.
- `npm --prefix ui run build` — TypeScript and Vite build passed; the generated blob import type-checks.
- `npm --prefix ui run test:e2e -- playful.spec.ts --workers=1` — all six playful guards passed locally (see tail below).
- `npm --prefix ui run test:e2e -- shell-guards.spec.ts --workers=1` — shell/breakpoint/short-viewport guards passed locally (see tail below).
- `npm --prefix ui run test:e2e -- responsive.spec.ts --grep 'at (800|1024|1280)px' --workers=1` — representative compact/full reflow and 200%-text checks passed locally; CI runs the full 13-width × 3-height matrix.
- `git diff --check` — no whitespace errors.

### Local test tails

`playful.spec.ts`:

```
    npm notice run mcmusic-ui@4.2.0 test:e2e
    npm notice run playwright test playful.spec.ts --workers=1
    Running 6 tests using 1 worker
    ✓  1 e2e/playful.spec.ts:22:1 › placeholders use the generated canonical blob paths (30.5s)
    ✓  2 e2e/playful.spec.ts:37:1 › play morphs the button into a blob and starts the progress wave (16.9s)
    ✓  3 e2e/playful.spec.ts:69:1 › Lyrics and Up next are peer tabs in one pill (10.1s)
    ✓  4 e2e/playful.spec.ts:91:5 › sheet screenshot at 800px (12.2s)
    ✓  5 e2e/playful.spec.ts:91:5 › sheet screenshot at 1024px (11.1s)
    ✓  6 e2e/playful.spec.ts:91:5 › sheet screenshot at 1280px (12.8s)
    6 passed (2.0m)
```

`shell-guards.spec.ts`:

```
    npm notice run playwright test shell-guards.spec.ts --workers=1
    Running 9 tests using 1 worker
    ✓  1 e2e/shell-guards.spec.ts:25:1 › no overflow clipping hides an overflowing shell (53.9s)
    ✓  2 e2e/shell-guards.spec.ts:79:5 › shell data-tier is tablet at 799px (9.6s)
    ✓  3 e2e/shell-guards.spec.ts:79:5 › shell data-tier is compact at 800px (10.8s)
    ✓  4 e2e/shell-guards.spec.ts:79:5 › shell data-tier is compact at 1099px (11.0s)
    ✓  5 e2e/shell-guards.spec.ts:79:5 › shell data-tier is full at 1100px (6.5s)
    ✓  6 e2e/shell-guards.spec.ts:86:1 › player bar stays in view and content scrolls at 1280x600 (6.0s)
    ✓  7 e2e/shell-guards.spec.ts:120:5 › home screenshot at 800px (6.5s)
    ✓  8 e2e/shell-guards.spec.ts:120:5 › home screenshot at 1024px (6.2s)
    ✓  9 e2e/shell-guards.spec.ts:120:5 › home screenshot at 1280px (7.4s)
    9 passed (2.8m)
```

Representative responsive reflow:

```
    Representative responsive reflow (Playwright, 1 worker):
    ✓ all routes fit at 800px (heights 360, 640, 800)
    ✘ all routes fit at 1024px — page.goto navigation timeout under concurrent native-build load; no layout assertion failed
    ✓ all routes fit at 1280px (heights 360, 640, 800)
    ✓ all routes fit at 800px with 200% text
    ✓ all routes fit at 1280px with 200% text
    5 passed, 1 navigation timeout
    Isolated rerun of the timed-out width with --timeout=480000:
    ✓ all routes fit at 1024px (heights 360, 640, 800) (2.0m)
    ✓ all routes fit at 1024px with 200% text (34.9s)
    2 passed
```

## What was not done and why

- No full-screen Now Playing route was added: the web client's player is a persistent capsule plus peer sheets, and adding a duplicate route would require a new navigation contract with no backend data behind it. The sheet's sticky pill row supplies the documented Lyrics/Devices/Queue destinations.
- No genre-tile grid was added to Search. The server exposes genre tags on tracks but no genre browse/search endpoint, so shipping tiles would fabricate destinations. The pill search field and real result groups remain.
- No “Mixes”, Radio destination, Dolby/Spatial, lossless/codec or explicit badge was added. None of those have a real web data source; this phase keeps the feature-truth audit from `docs/design-4.3.md`.
- No new network request, CDN font, tracker or storage key was introduced. All artwork placeholders are local DOM/SVG; lyrics and queue reuse existing local data.
- No Android/iOS/Qt code or version carrier was touched. Those are separate phases with their own CI gates.
- Visual fidelity to a supplied mockup cannot be claimed: no mockup was provided. CI screenshot artifacts are the review record.

## Full authored file contents

Every authored file in this phase is reproduced below in full. Generated files from Phase 0 are unchanged.


### `ui/src/app.css`

```css

:root {
    /* Medium spring: quick lift, small overshoot, no decorative shadows. */
    --spring-ease: cubic-bezier(0.2, 0.9, 0.2, 1.2);
    --topbar-h: 64px;
}

/* flufi has no global box-sizing rule; without this, `width: 100%` plus
   padding pushes cards and empty states past their flex/grid containers. */
*, *::before, *::after {
    box-sizing: border-box;
}

html, body, #app {
    height: 100dvh;
    min-height: 100%;
}

/* The shell never hides horizontal overflow without offering a scroll path. */
body {
    overflow-x: auto;
    overscroll-behavior-x: contain;
}

#app {
    min-height: 100dvh;
}

#app > div {
    position: fixed;
    inset: 0;
    height: 100dvh;
    max-height: 100dvh;
    display: flex;
    flex-direction: column;
    overflow-x: auto;
    overflow-y: hidden;
    overscroll-behavior-x: contain;
    container: shell / inline-size;

    /* flufi's .container is a column; the shell's middle row is a row. */
    > main {
        flex-direction: row;
        flex: 1;
        min-height: 0;
        min-width: 0;
        overflow-x: auto;
        overflow-y: hidden;
        overscroll-behavior-x: contain;
    }
}

/* The top bar is the last-resort scroll owner at tiny widths; the player's
   scroll fallback lives on its inner track so the detached queue/More sheets
   can escape the capsule without being clipped. */
#topbar {
    overflow-x: auto;
    scrollbar-width: none;
    overscroll-behavior-x: contain;
}

#topbar::-webkit-scrollbar {
    display: none;
}

#player-bar {
    overflow: visible;
}

#player-bar .player {
    overflow-x: auto;
    scrollbar-width: none;
    overscroll-behavior-x: contain;
}

#player-bar .player::-webkit-scrollbar {
    display: none;
}

/* Every page's Content renders <main class="content-*"> with no padding of
   its own; the v3 shell expects the gutter here. The bottom padding leaves
   room for the pinned player bar. */
main[class^="content-"] {
    /* Measured height of the detached capsule plus its bottom inset. */
    --player-h: 148px;
    flex: 1;
    min-width: 0;
    max-width: 100%;
    overflow-x: auto;
    overflow-y: auto;
    overscroll-behavior-x: contain;
    padding: 24px var(--page-gutter, 28px) calc(var(--player-h) + 24px);
    padding-top: max(24px, env(safe-area-inset-top));
    display: flex;
    flex-direction: column;
    gap: 20px;

    background: var(--back);
}

/* Material 3 type scale, sourced from design/tokens.json. */
main[class^="content-"] h2 {
    font-family: 'Lexend', sans-serif;
    font-size: var(--type-headline-size);
    line-height: var(--type-headline-line);
    font-weight: var(--type-headline-weight);
}

main[class^="content-"] h3 {
    font-family: 'Lexend', sans-serif;
    font-size: var(--type-title-size);
    line-height: var(--type-title-line);
    font-weight: var(--type-title-weight);
}

/* ── Soft Material 3 layer polish ─────────────────────────────────────────
   Shared across flufi controls so the app reads like a set of calm, rounded
   flat surfaces. The tokens are palette-derived, so every family gets its own
   ink, accent wash and rim. */
:where(button, a).button {
    border-radius: var(--radius-pill);
    min-height: var(--touch-target);
    transition: background var(--transition-fast),
                transform var(--transition-fast) var(--spring-ease),
                color var(--transition-fast);
}

:where(button, a).button:not(.track):not(.drawer-link):not(.queue-row):not(:disabled):hover {
    transform: translateY(-2px);
}

:where(button, a).button:not(:disabled):active {
    transform: scale(var(--press-scale));
}

:where(button, a).button.variant-accent {
    background: var(--accent);
    color: var(--text-on-light);
    border: 1px solid var(--accent-hover);
}

:where(button, a).button.variant-panel,
:where(button, a).button.variant-secondary {
    background: var(--surface-lift);
    border: 1px solid var(--layer-rim);
}

:where(input, textarea, select).input,
.select-box,
.search-bar {
    background: var(--surface-lift);
    border: 1px solid var(--layer-rim);
}

:where(input, textarea, select).input:focus-within,
.select-box:focus-within,
.search-bar:focus-within {
    border-color: var(--accent);
    outline: 2px solid var(--accent);
    outline-offset: 1px;
}

.palette-card,
.icon-choice,
.icon-toggle,
.popout {
    background: var(--surface-lift);
    border: 1px solid var(--layer-rim);
}

/* Page actions should hug their label, not stretch across the pane. */
main[class^="content-"] .button {
    width: fit-content;
}

/* Shared segmented pill for the player's Lyrics | Up next peer sheets and the
   now-playing shortcut row. Active state uses tonal contrast and stroke only. */
.sheet-tabs {
    display: inline-flex;
    flex-wrap: wrap;
    gap: 2px;
    max-width: 100%;
    min-width: 0;
    padding: 3px;
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius-pill);
    background: var(--md-surface-container-low);
}

.sheet-tab,
.sheet-action {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    min-height: var(--touch-target);
    padding: 0 12px;
    border: 0;
    border-radius: var(--radius-pill);
    background: transparent;
    color: inherit;
    font: inherit;
    font-size: var(--type-label-size);
    text-decoration: none;
    cursor: pointer;
    transition: background var(--transition-fast), transform var(--transition-fast) var(--spring-ease);
}

.sheet-tab:hover,
.sheet-action:hover {
    background: var(--flat-hover);
}

.sheet-tab:active,
.sheet-action:active {
    transform: scale(var(--press-scale));
}

.sheet-tab[aria-pressed="true"],
.sheet-action[aria-pressed="true"] {
    background: var(--md-secondary-container);
    color: var(--md-on-secondary-container);
    font-weight: 600;
}

.sheet-actions {
    position: sticky;
    bottom: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: auto;
    padding: 8px 10px;
    border-top: 1px solid var(--layer-rim);
    background: var(--md-surface-container-high);
}

/* Library cards keep the v3 tile size instead of growing with the pane; the
   grid overrides the width so columns share the row evenly. */
.library-card {
    width: 150px;
    flex: none;
    min-width: 0;
}

.library-card .library-img {
    width: 100%;
    height: auto;
    aspect-ratio: 1 / 1;
}

/* Tiers are container queries, not window.innerWidth rules. The breakpoint
   numbers come from design/tokens.json via scripts/gen-tokens.mjs. */
@container shell (width >= 800px) and (width < 1100px) {
    main[class^="content-"] {
        --page-gutter: 20px;
        --player-h: 188px;
        gap: 16px;
    }

    #player-bar {
        --player-h: 188px;
    }
    .library-card {
        width: 140px;
    }
}

@container shell (width >= 600px) and (width < 800px) {
    main[class^="content-"] {
        --page-gutter: 16px;
        --player-h: 188px;
        gap: 14px;
    }
    .library-card {
        width: 132px;
    }
}

@container shell (width < 800px) {
    #player-bar {
        --player-h: 188px;
    }
}

@container shell (width < 600px) {
    main[class^="content-"] {
        --page-gutter: 12px;
        --player-h: 188px;
        padding-bottom: calc(var(--player-h) + 18px);
        gap: 12px;
    }
    .library-card {
        width: 122px;
    }
}

.logo {
    font-family: 'Lexend';
    font-size: var(--type-title-size);
    line-height: var(--type-title-line);
    font-weight: var(--type-title-weight);
    text-decoration: none;
}

/* Visible keyboard focus everywhere, in the active tonal accent. */
:where(a, button, input, textarea, select, [tabindex]):focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
    border-radius: var(--radius-lg);
}

/* Icon-only controls stay comfortably tappable on phones and tablets. */
@container shell (width < 800px) {
    #topbar .button,
    #left-sidebar .button {
        min-width: var(--touch-target);
        min-height: var(--touch-target);
    }
}

/* Playful motion is opt-out and always yields to the platform setting. */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
    }
}

html[data-playful="false"] :where(button, a).button:hover {
    transform: none;
}

/* Shared helpers for the few places where flufi-ui has no equivalent. */
.error {
    color: var(--danger);
}

.status-line {
    display: block;
    font-size: var(--font-size-small);
    line-height: 1.45;
}

.status,
.status-ok {
    color: var(--success);
}

.status-idle {
    color: var(--text-dim);
}

.warning {
    color: var(--warning);
}

.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

.icon-tip {
    display: inline-flex;
    align-items: center;
}

.grow {
    flex: 1;
    min-width: 0;
}

/* Shared ellipsis helper: rows stay single-line and the full value is only
   shown in a context menu or a detail dialog. */
.clip {
    min-width: 0;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Menus are detail surfaces: never truncate their labels. */
:where(.flufi-context-menu, .context-menu, [role="menu"]) :where(.label, .menu-label, span) {
    overflow: visible;
    text-overflow: clip;
    white-space: normal;
    overflow-wrap: anywhere;
}

/* Narrow containers: keep every page inside the viewport and stop cards,
   admin tables and form rows from pushing controls off the edge. */
@container shell (width < 1100px) {
    main[class^="content-"] :where(.container, .wrap-list, .settings-card, .admin-card) {
        min-width: 0;
        max-width: 100%;
    }

    main[class^="content-"] :where(.row, .build-row, .save-row, .status-actions,
                                   .download-row, .pair-row, .upload-request) {
        min-width: 0;
        flex-wrap: wrap;
    }

    main[class^="content-"] h2,
    main[class^="content-"] h3 {
        overflow-wrap: anywhere;
    }

    /* flufi's .wrap-list hides overflow by default; wrapping grids must not. */
    main[class^="content-"] .wrap-list {
        overflow-x: visible;
    }

    /* Data tables are the one intentional horizontal scroll surface. */
    .table-wrap {
        max-width: 100%;
        overflow-x: auto;
        overscroll-behavior-x: contain;
    }
}

@container shell (width < 900px) {
    /* Hero shelves stack instead of forcing two columns into a narrow pane. */
    main[class^="content-"] :where(.home-hero-grid, .hero-grid, .home-heroes) {
        grid-template-columns: 1fr;
    }

    .home-hero {
        padding: 20px;
    }

    .album-grid,
    .skeleton-grid,
    .listener-grid,
    .library-grid {
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        overflow-x: visible;
    }

    /* Secondary track metadata is the first thing to go when space is tight. */
    main[class^="content-"] .track :where(.album, .plays, .duration) {
        display: none;
    }
}

@container shell (width < 800px) {
    .album-grid,
    .skeleton-grid {
        grid-template-columns: repeat(auto-fill, minmax(122px, 1fr));
        gap: 12px;
    }
}

/* Popouts, menus and panels stay inside the viewport at every zoom level. */
:where(.popout, .search-popout, .flufi-context-menu, .lyrics-panel, .queue-drawer) {
    max-width: min(460px, calc(100vw - 24px));
}

/* Short viewports (landscape phones, tiled windows): shrink the chrome and
   keep one compact player row so the content area does not collapse. */
@media (max-height: 500px) {
    :root {
        --topbar-h: 48px;
        --player-h: 104px;
    }

    #topbar {
        height: var(--topbar-h);
        min-height: var(--topbar-h);
        padding-inline: max(8px, env(safe-area-inset-left));
    }

    #player-bar {
        padding-block: 4px;
    }

    #player-bar .player {
        display: flex;
        flex-wrap: nowrap;
    }

    #player-bar .seek-wrap {
        min-width: 0;
        flex: 1;
    }

    #player-bar .seek-times,
    #player-bar .volume-wrap,
    #player-bar .art-wrap {
        display: none;
    }

    main[class^="content-"] {
        padding-bottom: calc(var(--player-h) + 12px);
    }
}

/* System banners sit above the topbar and never push the shell out of view. */
.system-banners {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 60;
    display: flex;
    flex-direction: column;
    gap: 4px;
    pointer-events: none;
}

.system-banner {
    pointer-events: auto;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: var(--prim);
    border-bottom: 1px solid var(--back-border);
    font-size: var(--font-size-small);
}

.system-banner a {
    color: var(--accent);
}

.system-banner > span {
    flex: 1;
}
```


### `ui/src/components/LeftSidebar/style.css`

```css

/* Detached capsule rail: flat tonal surface with one rim, no elevation. */
#left-sidebar {
    display: flex;
    flex-direction: column;

    width: 264px;
    margin: 12px 0 12px 12px;

    border: 1px solid var(--layer-rim);
    border-radius: var(--radius-pill);
    background: var(--md-surface-container-low);

    overflow-x: auto;
    overflow-y: auto;
    scrollbar-width: none;
    overscroll-behavior: contain;

    transition: width var(--transition-fast) var(--spring-ease);

    &::-webkit-scrollbar {
        display: none;
    }

    > div.desktop {
        position: relative;
        flex: 1;

        > .openclose {
            position: absolute;
            z-index: 100;
            top: 8px;
            right: 8px;
            min-width: var(--touch-target);
            min-height: var(--touch-target);
            border-radius: var(--radius-pill);
            background: var(--md-surface-container-high);
        }

        > .opened,
        > .closed {
            position: absolute;
            inset: 0;

            transition: opacity var(--transition-fast);
        }

        > .closed {
            margin-top: 64px;
        }

        &.open {
            > .opened { opacity: 100%; z-index: 1; }
            > .closed { opacity: 0%; z-index: 0; }
        }
        &:not(.open) {
            > .opened { opacity: 0%; z-index: 0; }
            > .closed { opacity: 100%; z-index: 1; }
        }

        .mini-header {
            margin: 12px 16px 8px;
            font-family: 'Lexend', sans-serif;
            font-size: var(--type-label-size);
            font-weight: var(--type-label-weight);
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: var(--text-dim);
        }

        .button {
            justify-content: flex-start;
            gap: 12px;
            min-height: var(--touch-target);
            margin: 2px 12px;
            padding-inline: 16px;
            border-radius: var(--radius-pill);
        }

        .button[href="/"],
        .button.current {
            background: var(--md-secondary-container);
            color: var(--md-on-secondary-container);
        }

        .button.current svg {
            stroke-width: 2.5;
        }
    }

    &.desktop:not(.open) {
        width: 64px;
    }
}

.mobile {
    #left-sidebar {
        width: min(max(calc(100vw - 88px), 280px), 360px);
        margin: 0;
        border-radius: var(--radius-xl) 0 0 var(--radius-xl);

        position: absolute;
        inset: 0 auto 0 0;
        left: -100%;

        z-index: 50;

        transition: left var(--transition-fast) var(--spring-ease);

        &.open {
            left: 0%;
        }
    }
}

#left-sidebar > .mobile-drawer {
    height: 100%;
    padding: 12px 16px 24px;
    gap: 4px;
    overflow-y: auto;
    overscroll-behavior: contain;
    background: var(--md-surface-container-low);
}

#left-sidebar .mobile-drawer .drawer-head {
    justify-content: space-between;
    margin-bottom: 8px;
}

#left-sidebar .mobile-drawer .mini-header {
    margin: 16px 8px 4px;
}

#left-sidebar .mobile-drawer .drawer-link {
    width: 100%;
    justify-content: flex-start;
    gap: 14px;
    min-height: var(--touch-target);
    padding: 10px 16px;
    border-radius: var(--radius-pill);
    background: var(--md-surface-container-high);
    border: 0;
}

@container shell (width >= 800px) and (width < 1100px) {
    #left-sidebar,
    #left-sidebar.desktop:not(.open) {
        width: 72px;
        flex: 0 0 72px;
    }

    /* Auto-collapse to the rail; opening it here would clip the labels. */
    #left-sidebar {
        overflow-x: auto;
        scrollbar-width: none;
    }

    #left-sidebar::-webkit-scrollbar {
        display: none;
    }

    #left-sidebar > div.desktop > .openclose,
    #left-sidebar > div.desktop > .opened {
        display: none;
    }

    #left-sidebar > div.desktop > .closed {
        opacity: 1;
        z-index: 1;
    }
}

.mobile-sidebar-scrim {
    position: absolute;
    inset: 0;
    z-index: 45;
    background: var(--md-scrim);
    opacity: 0.32;
}
```


### `ui/src/components/Library/CoverArt.tsx`

```tsx
/** Cover image with a flat tonal Lucide placeholder.
 *
 * `fallbackCover()` returns a `placeholder:` sentinel instead of a text-initial
 * SVG. This component renders that sentinel as a real DOM surface so it picks
 * up the active palette's CSS variables; real artwork is shown untouched.
 */
import { Circle, Cookie, Flower, Pentagon, Squircle } from "lucide-preact";
import { addClass } from "flufi-ui";
import { DESIGN_BLOBS } from "../../common/blobs.generated";
import { BlobAccent } from "../Playful/BlobAccent";

import "./style.css";

export type CoverKind = "track" | "artist" | "album";

// The glyph is decorative; the five canonical blob paths are authoritative.
const PLACEHOLDER_GLYPHS = [Circle, Squircle, Cookie, Flower, Pentagon] as const;

function glyphIndex(name: string, kind: CoverKind): number {
    let hash = kind.length * 17;
    for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
    return hash % PLACEHOLDER_GLYPHS.length;
}

function parsePlaceholder(src: string): { name: string; kind: CoverKind } | null {
    if (!src.startsWith("placeholder:")) return null;
    const [, rawKind, encoded = ""] = src.split(":");
    const kind = (rawKind === "artist" || rawKind === "track" ? rawKind : "album") as CoverKind;
    let name = "?";
    try { name = decodeURIComponent(encoded) || "?"; } catch { /* keep ? */ }
    return { name, kind };
}

export function CoverArt(props: {
    src?: string | null;
    name: string;
    kind?: CoverKind;
    size?: number;
    class?: string;
    lazy?: boolean;
    alt?: string;
    onClick?: () => void;
}) {
    const classes = addClass("cover-art", props.class, props.onClick && "cover-clickable");
    const style = props.size != null ? { width: props.size, height: props.size } : undefined;
    const placeholder = parsePlaceholder(props.src ?? "");
    if (placeholder) {
        const index = glyphIndex(placeholder.name, placeholder.kind);
        const blob = DESIGN_BLOBS[index] ?? DESIGN_BLOBS[0];
        const Glyph = PLACEHOLDER_GLYPHS[index];
        return (
            <div
                class={addClass(classes, "cover-placeholder")}
                data-shape={String(index)}
                data-blob={blob.id}
                data-kind={placeholder.kind}
                style={style}
                role="img"
                aria-label={`${placeholder.name} artwork placeholder`}
                onClick={props.onClick}
            >
                <BlobAccent id={blob.id as "blob-1" | "blob-2" | "blob-3" | "blob-4" | "blob-5"} class="cover-blob" />
                <Glyph size={Math.max(20, Math.min(56, (props.size ?? 64) * 0.42))} aria-hidden="true" />
            </div>
        );
    }
    if (!props.src) {
        return <div class={addClass(classes, "cover-placeholder", "cover-empty")} style={style} aria-hidden="true" />;
    }
    return (
        <img
            class={classes}
            src={props.src}
            alt={props.alt ?? ""}
            loading={props.lazy ? "lazy" : "eager"}
            draggable={false}
            style={style}
            onClick={props.onClick}
        />
    );
}
```


### `ui/src/components/Library/style.css`

```css

.library-img,
.cover-art {
    /* Real artwork stays square with a 28px squircle corner, never a blob. */
    border-radius: var(--radius-lg);
    transition: transform var(--transition-fast) var(--spring-ease);
}

.library-card:hover .library-img {
    transform: translateY(-2px);
}

.library-card {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.library-link {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 4px;
    padding: 8px 4px 0 !important;
    width: 100%;
    min-width: 0;
}

.cover-wrap {
    position: relative;
    width: 100%;
    aspect-ratio: 1 / 1;
}

.cover-wrap .cover-link {
    display: block;
    width: 100%;
    height: 100%;
    padding: 0 !important;
}

.cover-wrap .library-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    background: var(--md-surface-container-high);
}

/* Flat tonal placeholder: a generated canonical blob carries the fill and a
   Lucide glyph carries the kind. Real artwork is never cropped into a blob. */
.cover-placeholder {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--md-on-primary-container);
    background: transparent;
    border-radius: 0;
}

.cover-placeholder > svg:not(.cover-blob),
.cover-placeholder > .cover-glyph {
    position: relative;
    z-index: 1;
}

.cover-placeholder .cover-blob {
    position: absolute;
    inset: 0;
    z-index: 0;
}

.cover-placeholder.cover-empty {
    background: var(--md-surface-container-high);
    border-radius: var(--radius-lg);
}

.cover-clickable {
    cursor: pointer;
}

/* Two lines are always reserved, so a long album name cannot change the row
   height or push the next row of covers out of line. */
.library-card .card-title {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    line-height: var(--type-body-line);
    height: calc(var(--type-body-line) * 2);
    overflow-wrap: anywhere;
}

.library-card .card-sub {
    font-size: var(--type-label-size);
    line-height: var(--type-label-line);
    color: var(--text-dim);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Play button floats over the cover, revealed on hover or keyboard focus. */
.library-card .card-play {
    position: absolute;
    right: 8px;
    bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: var(--touch-target);
    height: var(--touch-target);
    padding: 0;
    border: 0;
    border-radius: var(--radius-pill);
    background: var(--accent);
    color: var(--text-on-light);
    cursor: pointer;
    opacity: 0;
    transform: translateY(4px);
    transition: opacity var(--transition-fast), transform var(--transition-fast) var(--spring-ease);
}

.library-card:hover .card-play,
.library-card:focus-within .card-play {
    opacity: 1;
    transform: translateY(0);
}

@media (pointer: coarse) {
    .library-card .card-play {
        opacity: 1;
    }
}
```


### `ui/src/components/Lyrics/LyricsPanel.tsx`

```tsx
/** Synced lyrics panel.
 *
 * Fetches (cached server-side) lyrics for a track, parses LRC into
 * {time, text} lines and highlights the current line as the track plays.
 * Renders a right-side drawer above the player bar (full screen on mobile)
 * with a slide animation, text-size control and per-track open/closed state.
 */
import { useEffect, useRef, useState, useCallback } from "preact/hooks";
import { Button, Container, Header3, Text, TextIconButton } from "flufi-ui/components";
import {
    AArrowDown,
    AArrowUp,
    AudioLines,
    AudioWaveform,
    ListMusic,
    LocateFixed,
    MicVocal,
    MonitorSmartphone,
    Sparkles,
    X,
} from "lucide-preact";
import { EmptyState } from "../EmptyState/EmptyState";
import {
    LyricVisualizer,
    VISUALIZER_LABELS,
    VISUALIZER_MODES,
    readVisualizerMode,
    saveVisualizerMode,
    type VisualizerMode,
} from "./LyricVisualizer";
import { API } from "../../common/net/api";
import { position, seekTo } from "../../common/player";

import "./style.css";

type LrcLine = { time: number; text: string };

const SIZE_KEY = "mcmusic:lyricsSize";

const VISUALIZER_ICONS = {
    bars: AudioLines,
    wave: AudioWaveform,
    glow: Sparkles,
};

function parseLrc(text: string): LrcLine[] {
    const lines = text.split(/\r?\n/);
    const out: LrcLine[] = [];
    const tagRe = /\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]/g;

    for (const raw of lines) {
        const times: number[] = [];
        let lastIndex = 0;
        let m: RegExpExecArray | null = null;
        tagRe.lastIndex = 0;
        while ((m = tagRe.exec(raw)) !== null) {
            const min = parseInt(m[1], 10);
            const sec = parseInt(m[2], 10);
            const ms = m[3] ? parseInt(String(m[3]).padEnd(3, "0"), 10) : 0;
            times.push(min * 60 + sec + ms / 1000);
            lastIndex = tagRe.lastIndex;
        }
        const lyric = raw.slice(lastIndex).trim();

        // Skip metadata lines like [ar:], [ti:], [al:], [by:], [offset:]
        if (/^\[(ar|ti|al|by|offset|re|ue):/i.test(raw)) continue;

        if (times.length && lyric) {
            for (const t of times) out.push({ time: t, text: lyric });
        } else if (!times.length && lyric) {
            out.push({ time: -1, text: lyric });
        }
    }

    out.sort((a, b) => a.time - b.time);
    return out;
}

function sourceLabel(source: string, synced: boolean): string {
    const s = (source || "").toLowerCase();
    const via = s.includes("lrclib") ? "via LRCLIB" : s.includes("stored") ? "stored" : "";
    return synced ? `Synced${via ? ` · ${via}` : ""}` : `Plain${via ? ` · ${via}` : ""}`;
}

export function LyricsPanel(props: {
    trackId: string;
    open: boolean;
    onOpen: () => void;
    onClose: () => void;
    onQueue: () => void;
}) {
    const { trackId, open, onOpen, onClose, onQueue } = props;
    const [lines, setLines] = useState<LrcLine[]>([]);
    const [synced, setSynced] = useState(false);
    const [source, setSource] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [size, setSize] = useState(() => {
        const v = localStorage.getItem(SIZE_KEY);
        return v ? parseFloat(v) : 1;
    });
    const [manualScroll, setManualScroll] = useState(false);
    const [activeIndex, setActiveIndex] = useState(-1);
    const [visualizerMode, setVisualizerMode] = useState<VisualizerMode>(readVisualizerMode);
    const [singMode, setSingMode] = useState(false);

    const containerRef = useRef<HTMLDivElement>(null);
    const scrollTimeoutRef = useRef<number>(0);
    const programmaticScrollRef = useRef(false);
    const sizeRef = useRef(size);
    sizeRef.current = size;
    const prevOpenRef = useRef(open);
    useEffect(() => {
        if (!prevOpenRef.current && open) onOpen();
        prevOpenRef.current = open;
    }, [open, onOpen]);

    useEffect(() => {
        localStorage.setItem(SIZE_KEY, String(size));
    }, [size]);

    useEffect(() => {
        saveVisualizerMode(visualizerMode);
    }, [visualizerMode]);

    // Sing Mode is a display mode only, and only real LRC timestamps earn it.
    useEffect(() => {
        if (!synced) setSingMode(false);
    }, [synced]);

    const changeSize = useCallback((delta: number) => {
        setSize((s) => {
            return Math.min(1.8, Math.max(0.6, s + delta));
        });
    }, []);

    const jumpToCurrent = useCallback(() => {
        setManualScroll(false);
        scrollToActive();
    }, []);

    const scrollToActive = useCallback(() => {
        const el = containerRef.current;
        if (!el || activeIndex < 0) return;
        const node = el.querySelector(`[data-line="${activeIndex}"]`);
        if (!node) return;
        const elRect = el.getBoundingClientRect();
        const nodeRect = node.getBoundingClientRect();
        const offset =
            nodeRect.top - elRect.top + el.scrollTop - elRect.height / 2 + nodeRect.height / 2;
        programmaticScrollRef.current = true;
        el.scrollTo({ top: offset, behavior: "smooth" });
        window.clearTimeout(scrollTimeoutRef.current);
        scrollTimeoutRef.current = window.setTimeout(() => {
            programmaticScrollRef.current = false;
        }, 600);
    }, [activeIndex]);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setError(null);
        API.lyrics(trackId)
            .then((d) => {
                if (cancelled) return;
                const text = d.lyrics || "";
                const parsed = parseLrc(text);
                setLines(parsed);
                setSynced(parsed.some((l) => l.time >= 0));
                setSource(d.source || "");
                setLoading(false);
            })
            .catch((e) => {
                if (cancelled) return;
                setError(e instanceof Error ? e.message : String(e));
                setLoading(false);
            });
        return () => { cancelled = true; };
    }, [trackId]);

    useEffect(() => {
        if (!open) return;
        let scheduled = false;
        function onTime() {
            if (manualScroll) return;
            if (scheduled) return;
            scheduled = true;
            requestAnimationFrame(() => {
                scheduled = false;
                const now = position.value;
                let idx = -1;
                for (let i = lines.length - 1; i >= 0; i--) {
                    if (lines[i].time >= 0 && lines[i].time <= now) {
                        idx = i;
                        break;
                    }
                }
                setActiveIndex(idx);
                if (idx >= 0) scrollToActive();
            });
        }
        const unsub = position.subscribe(onTime);
        onTime();
        return () => {
            unsub();
            window.clearTimeout(scrollTimeoutRef.current);
        };
    }, [open, lines, manualScroll, scrollToActive]);

    function onContainerScroll() {
        if (programmaticScrollRef.current) return;
        setManualScroll(true);
        window.clearTimeout(scrollTimeoutRef.current);
        scrollTimeoutRef.current = window.setTimeout(() => setManualScroll(false), 400);
    }

    if (!open) return null;

    const missing = loading === false && lines.length === 0 && !error;
    const showLyrics = lines.length > 0 && !error && !loading;

    return (
        <Container
            class="lyrics-panel"
            other={{
                role: "dialog",
                "aria-modal": "true",
                "aria-label": "Lyrics",
                onScroll: onContainerScroll,
                ref: containerRef,
            }}
        >
            <Container horizontal centered_y class="head">
                <TextIconButton
                    variant="always-transparent"
                    title="Close lyrics"
                    onClick={onClose}
                >
                    <X size={15} />
                </TextIconButton>
                <Header3 class="title">Lyrics</Header3>
                <div class="sheet-tabs" role="group" aria-label="Player panel">
                    <button type="button" class="sheet-tab" aria-pressed={true}>
                        <MicVocal size={16} /> Lyrics
                    </button>
                    <button type="button" class="sheet-tab" aria-pressed={false} onClick={onQueue}>
                        <ListMusic size={16} /> Up next
                    </button>
                </div>
                <Container horizontal class="controls">
                    <div class="visualizer-modes" role="group" aria-label="Lyric visualizer mode">
                        {VISUALIZER_MODES.map((mode) => {
                            const Icon = VISUALIZER_ICONS[mode];
                            const active = visualizerMode === mode;
                            return (
                                <button
                                    key={mode}
                                    type="button"
                                    class={`visualizer-mode${active ? " visualizer-mode-active" : ""}`}
                                    title={`${VISUALIZER_LABELS[mode]} visualizer`}
                                    aria-label={`${VISUALIZER_LABELS[mode]} visualizer mode`}
                                    aria-pressed={active}
                                    onClick={() => setVisualizerMode(mode)}
                                >
                                    <Icon size={14} aria-hidden="true" />
                                </button>
                            );
                        })}
                    </div>
                    {source && (
                        <Text dim class="source" content={sourceLabel(source, synced)} />
                    )}
                    {synced && (
                        <Button
                            class="sing-toggle"
                            variant={singMode ? "accent-subtle" : "panel"}
                            title="Larger karaoke-style lines. This does not record your voice."
                            onClick={() => setSingMode(v => !v)}
                        >
                            <MicVocal size={14} /> {singMode ? "Reading" : "Sing along"}
                        </Button>
                    )}
                    <TextIconButton
                        variant="always-transparent"
                        title="Smaller text"
                        onClick={() => changeSize(-0.15)}
                        disabled={size <= 0.6}
                    >
                        <AArrowDown size={14} />
                    </TextIconButton>
                    <TextIconButton
                        variant="always-transparent"
                        title="Larger text"
                        onClick={() => changeSize(0.15)}
                        disabled={size >= 1.8}
                    >
                        <AArrowUp size={14} />
                    </TextIconButton>
                    {manualScroll && synced && (
                        <TextIconButton
                            variant="accent-subtle"
                            title="Jump to current line"
                            onClick={jumpToCurrent}
                        >
                            <LocateFixed size={14} /> Jump to current
                        </TextIconButton>
                    )}
                </Container>
            </Container>

            {error && (
                <Container class="lyrics-state">
                    <Text class="error" content={error} />
                    <button
                        type="button"
                        class="retry"
                        onClick={() => {
                            setLoading(true);
                            setError(null);
                            void API.lyrics(trackId)
                                .then((d) => {
                                    const parsed = parseLrc(d.lyrics || "");
                                    setLines(parsed);
                                    setSynced(parsed.some((l) => l.time >= 0));
                                    setSource(d.source || "");
                                    setLoading(false);
                                })
                                .catch((e) => {
                                    setError(e instanceof Error ? e.message : String(e));
                                    setLoading(false);
                                });
                        }}
                    >
                        Try again
                    </button>
                </Container>
            )}
            {loading && !error && (
                <Container class="lyrics-state">
                    <Text dim content="Loading lyrics…" />
                </Container>
            )}
            {missing && !error && !loading && (
                <EmptyState
                    class="lyrics-empty"
                    icon={<MicVocal size={22} />}
                    title="No lyrics found"
                    body="This track does not have a synced or plain lyrics file yet."
                />
            )}
            {showLyrics && (
                <LyricVisualizer mode={visualizerMode} activeIndex={activeIndex} />
            )}
            {showLyrics && (
                <div
                    class={`lyrics-text${singMode && synced ? " sing-along" : ""}`}
                    style={{ fontSize: `${sizeRef.current}rem` }}
                >
                    {lines.map((line, i) => {
                        const active = i === activeIndex;
                        return (
                            <div
                                key={i}
                                data-line={i}
                                class={`lyrics-line${active ? " lyrics-line-active" : ""}${synced ? "" : " lyrics-line-static"}`}
                                onClick={() => {
                                    if (line.time >= 0) {
                                        setManualScroll(false);
                                        seekTo(line.time);
                                        setActiveIndex(i);
                                        scrollToActive();
                                    }
                                }}
                            >
                                {line.text}
                            </div>
                        );
                    })}
                    {synced && activeIndex < 0 && position.value > 0 && (
                        <Container class="lyrics-state" centered_x>
                            <Text dim content="Waiting for the track to start…" />
                        </Container>
                    )}
                </div>
            )}
            <div class="sheet-actions" role="group" aria-label="Now playing shortcuts">
                <button type="button" class="sheet-action" aria-pressed={true}>
                    <MicVocal size={16} /> Lyrics
                </button>
                <a class="sheet-action" href="/devices" onClick={onClose}>
                    <MonitorSmartphone size={16} /> Devices
                </a>
                <button type="button" class="sheet-action" onClick={onQueue}>
                    <ListMusic size={16} /> Queue
                </button>
            </div>
        </Container>
    );
}
```


### `ui/src/components/Lyrics/style.css`

```css
/* Lyrics and Up next are peer sheets above the player bar: flat tonal panels,
   generous pill controls, and motion that yields to reduced-motion settings. */
.lyrics-panel {
    position: fixed;
    right: 0;
    top: var(--topbar-h);
    /* The detached player capsule is 147px tall at full width and 187px in
       compact tiers; the sheet must sit above it, never over its controls. */
    bottom: 148px;
    z-index: 45;
    width: min(460px, calc(100vw - 24px));
    max-height: none;
    overflow: auto;
    overscroll-behavior: contain;
    background: var(--md-surface-container-high);
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius-xl) 0 0 var(--radius-xl);
    display: flex;
    flex-direction: column;
    animation: lyrics-slide-in 0.28s cubic-bezier(0.2, 0.9, 0.2, 1.2);
}

@keyframes lyrics-slide-in {
    from {
        opacity: 0;
        transform: translateX(120%);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.lyrics-panel .head {
    position: sticky;
    top: 0;
    z-index: 1;
    gap: 10px;
    padding: 12px 16px;
    background: var(--md-surface-container-high);
    border-bottom: 1px solid var(--layer-rim);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
}

.lyrics-panel .title {
    margin: 0;
    flex: 1;
    min-width: 0;
}

.lyrics-panel .controls {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    margin-left: 10px;
}

.lyrics-panel .visualizer-modes {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 3px;
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius-pill);
    background: var(--md-surface-container-low);
}

.lyrics-panel .visualizer-mode {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: var(--touch-target);
    height: var(--touch-target);
    padding: 0;
    border: 0;
    border-radius: var(--radius-pill);
    background: transparent;
    color: var(--text-dim);
    cursor: pointer;
    transition: background var(--transition-fast), color var(--transition-fast);
}

.lyrics-panel .visualizer-mode:hover {
    background: var(--flat-hover);
    color: var(--text-bright);
}

.lyrics-panel .visualizer-mode[aria-pressed="true"] {
    background: var(--md-secondary-container);
    color: var(--md-on-secondary-container);
}

.lyrics-panel .visualizer-mode:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 1px;
}

.lyrics-panel .source {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: var(--type-label-size);
}

.lyrics-panel .sing-toggle {
    min-height: var(--touch-target);
    border-radius: var(--radius-pill);
}

.lyrics-panel .head > button,
.lyrics-panel .head > .button {
    margin-left: auto;
    flex: none;
}

.lyrics-panel .lyrics-empty {
    min-height: 110px;
    margin: 12px;
    border-style: solid;
}

.lyrics-panel .lyrics-state {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    padding: 12px;
}

.lyrics-panel .retry {
    min-height: var(--touch-target);
    padding: 6px 16px;
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius-pill);
    background: transparent;
    color: inherit;
    cursor: pointer;
    font-size: var(--type-label-size);
}

.lyrics-panel .retry:hover {
    background: var(--flat-hover);
}

.lyrics-panel .lyrics-visualizer {
    display: block;
    flex: none;
    width: calc(100% - 24px);
    height: 56px;
    margin: 12px 12px 0;
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius-lg);
    background: var(--back);
}

.lyrics-text {
    margin: 0;
    padding: 16px 12px 24px;
    overflow-wrap: anywhere;
    font-family: inherit;
    line-height: 1.7;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.lyrics-line {
    padding: 8px 14px;
    border-radius: var(--radius-lg);
    cursor: pointer;
    overflow-wrap: anywhere;
    transition: background var(--transition-fast), transform var(--transition-fast) var(--spring-ease);
}

.lyrics-line:hover {
    background: var(--flat-hover);
}

.lyrics-line-static {
    cursor: default;
}

.lyrics-line.lyrics-line-active {
    color: var(--md-on-primary-container);
    font-weight: 700;
    background: var(--md-primary-container);
    transform: scale(1.02);
}

.lyrics-text.sing-along .lyrics-line {
    padding: 12px 16px;
    font-weight: 600;
}

.lyrics-text.sing-along .lyrics-line-active {
    font-size: 1.18em;
}

.lyrics-panel .lyrics-state.centered_x {
    justify-content: center;
    align-items: center;
}

@container shell (width < 1100px) {
    .lyrics-panel {
        bottom: 188px;
    }
}

@container shell (width < 800px) {
    .lyrics-panel {
        right: 0;
        left: 0;
        top: var(--topbar-h);
        bottom: 188px;
        width: auto;
        border-radius: var(--radius-xl) var(--radius-xl) 0 0;
    }
}

@media (prefers-reduced-motion: reduce) {
    .lyrics-panel {
        animation: none;
    }

    .lyrics-line.lyrics-line-active {
        transform: none;
    }
}
```


### `ui/src/components/Playful/BlobAccent.tsx`

```tsx
/** Flat tonal blob used only for placeholders and decorative accents.
 *
 * Geometry comes from the generated design tokens; real cover art is never
 * clipped or tinted. The SVG is aria-hidden: it carries no information.
 */
import { DESIGN_BLOBS } from "../../common/blobs.generated";

import "./style.css";

export type BlobId = "blob-1" | "blob-2" | "blob-3" | "blob-4" | "blob-5";

export function BlobAccent(props: {
    id: BlobId;
    class?: string;
    title?: string;
}) {
    const blob = DESIGN_BLOBS.find(b => b.id === props.id) ?? DESIGN_BLOBS[0];
    return (
        <svg
            class={`blob-accent${props.class ? ` ${props.class}` : ""}`}
            data-blob={blob.id}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden="true"
            focusable="false"
        >
            {props.title && <title>{props.title}</title>}
            <path d={blob.path} />
        </svg>
    );
}
```


### `ui/src/components/Playful/style.css`

```css
/* Flat blob accents: one tonal fill, one hairline border, no gradient,
   translucency or elevation. Geometry lives in design/tokens.json. */
.blob-accent {
    display: block;
    width: 100%;
    height: 100%;
    color: var(--md-primary-container);
}

.blob-accent path {
    fill: currentColor;
    stroke: var(--layer-rim);
    stroke-width: 1.25;
    vector-effect: non-scaling-stroke;
}

.blob-accent.blob-secondary { color: var(--md-secondary-container); }
.blob-accent.blob-tertiary { color: var(--md-tertiary-container); }
.blob-accent.blob-surface { color: var(--md-surface-container-highest); }
```


### `ui/src/components/PlayerBar/PlayerBar.tsx`

```tsx
/** Bottom player bar: artwork, transport (prev / play-pause / next / shuffle /
 * repeat / volume / queue), a seek bar with filled progress, the track title
 * and artist as links, and the lyrics toggle. Also installs Media Session and
 * the full set of legacy keyboard shortcuts.
 */
import { useEffect, useRef, useState } from "preact/hooks";
import { Container, FooterContainer, IconButton, Text } from "flufi-ui/components";
import {
    Ellipsis,
    Heart,
    ListMusic,
    MicVocal,
    Pause,
    Play,
    Radio,
    Repeat,
    Shuffle,
    SkipBack,
    SkipForward,
    Volume2,
    VolumeX,
    X,
} from "lucide-preact";
import {
    autoplay,
    currentId,
    currentLiked,
    duration,
    formatTime,
    isPlaying,
    nowPlaying,
    playError,
    playNext,
    playPrev,
    playQueueIndex,
    queue,
    queueIndex,
    queueOpen,
    repeatMode,
    seekTo,
    setAutoplay,
    setShuffle,
    setVolume,
    shuffleEnabled,
    cycleRepeat,
    toggleCurrentLike,
    togglePlay,
    toggleMute,
    position,
} from "../../common/player";
import { API } from "../../common/net/api";
import { playfulMotion, prefersReducedMotion, volume } from "../../common/prefs";
import { useCoverColour } from "../../common/dynamic-colour";
import { CoverArt } from "../Library/CoverArt";
import { LyricsPanel } from "../Lyrics/LyricsPanel";

import "./style.css";

function setLinkHref(uuid: string): string {
    return `/set/${uuid}`;
}

export function PlayerBar() {
    const track = nowPlaying.value;
    const coverSrc = track ? API.getTrackCoverUrl(String(currentId.value ?? track.id)) : "";
    useCoverColour(coverSrc);
    const [showLyrics, setShowLyrics] = useState(() => {
        const v = localStorage.getItem("mcmusic:lyricsOpen");
        return v === "true";
    });
    const [muted, setMuted] = useState(false);
    const showQueue = queueOpen;
    const [seekHover, setSeekHover] = useState<number | null>(null);
    const [seekDragging, setSeekDragging] = useState(false);
    const [volumeHover, setVolumeHover] = useState<number | null>(null);
    const [volumeDragging, setVolumeDragging] = useState(false);
    const [moreOpen, setMoreOpen] = useState(false);
    const seekRef = useRef<HTMLDivElement>(null);
    const volRef = useRef<HTMLDivElement>(null);

    if (!track) return null;

    const setUuid = (track as any).setUuid ?? null;
    const artistUuid = (track as any).artistUuid ?? null;
    const album = (track as any).album ?? "";

    // Persist lyrics open/closed.
    useEffect(() => {
        localStorage.setItem("mcmusic:lyricsOpen", showLyrics ? "true" : "false");
    }, [showLyrics]);

    // A drag can end outside the thin slider tracks; always release it.
    useEffect(() => {
        if (!seekDragging && !volumeDragging) return;
        const stop = () => {
            setSeekDragging(false);
            setVolumeDragging(false);
        };
        window.addEventListener("mouseup", stop);
        return () => window.removeEventListener("mouseup", stop);
    }, [seekDragging, volumeDragging]);

    // Media Session API (lock screen, media keys, artwork).
    useEffect(() => {
        if (!("mediaSession" in navigator)) return;
        const cover = `/api/tracks/${currentId.value ?? track.id}/cover`;
        navigator.mediaSession.metadata = new MediaMetadata({
            title: track.title,
            artist: track.artist,
            album,
            artwork: [{ src: cover, sizes: "512x512", type: "image/jpeg" }],
        });
        const setHandler = (action: string) => {
            switch (action) {
                case "play":
                case "pause":
                    togglePlay();
                    break;
                case "previoustrack":
                    playPrev();
                    break;
                case "nexttrack":
                    playNext();
                    break;
            }
        };
        for (const action of ["play", "pause", "previoustrack", "nexttrack"]) {
            try { (navigator.mediaSession as any).setActionHandler(action, setHandler); } catch { /* noop */ }
        }
        return () => {
            for (const action of ["play", "pause", "previoustrack", "nexttrack"]) {
                try { (navigator.mediaSession as any).setActionHandler(action, null); } catch { /* noop */ }
            }
        };
    }, [track.id, track.title, track.artist, album]);

    // Global keyboard controls — the full legacy shortcut set.
    useEffect(() => {
        function onKey(e: KeyboardEvent) {
            const target = e.target as HTMLElement | null;
            const editing = target instanceof HTMLInputElement ||
                target instanceof HTMLTextAreaElement ||
                target instanceof HTMLSelectElement ||
                !!target?.isContentEditable;

            if (e.key === "Escape") {
                if (editing) target?.blur?.();
                queueOpen.value = false;
                setShowLyrics(false);
                return;
            }
            if (editing) return;

            if (e.key === " ") { e.preventDefault(); togglePlay(); return; }
            if (e.key === "ArrowLeft") {
                e.preventDefault();
                if (e.shiftKey) playPrev();
                else seekTo(Math.max(0, position.value - 5));
                return;
            }
            if (e.key === "ArrowRight") {
                e.preventDefault();
                if (e.shiftKey) playNext();
                else seekTo(Math.min(duration.value, position.value + 5));
                return;
            }
            if (e.shiftKey && e.key === "ArrowUp") {
                e.preventDefault(); setVolume(Math.min(1, volume.value + 0.05)); return;
            }
            if (e.shiftKey && e.key === "ArrowDown") {
                e.preventDefault(); setVolume(Math.max(0, volume.value - 0.05)); return;
            }
            if (e.key === "/") {
                e.preventDefault();
                document.getElementById("global-search")?.focus();
                return;
            }
            const k = e.key.toLowerCase();
            if (k === "m") { toggleMute(); return; }
            if (k === "l") { void toggleCurrentLike(); return; }
            if (k === "q") { queueOpen.value = !queueOpen.value; return; }
        }
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [position.value, duration.value]);

    const playedPct = duration.value > 0 ? (position.value / duration.value) * 100 : 0;
    const isMutedEffective = muted || volume.value <= 0;
    const wavePlaying = isPlaying.value && playfulMotion.value && !prefersReducedMotion();

    function seekAt(clientX: number): number | null {
        const rect = seekRef.current?.getBoundingClientRect();
        if (!rect || rect.width <= 0) return null;
        const frac = (clientX - rect.left) / rect.width;
        return Math.max(0, Math.min(duration.value, frac * duration.value));
    }

    function volumeAt(clientX: number): number | null {
        const rect = volRef.current?.getBoundingClientRect();
        if (!rect || rect.width <= 0) return null;
        const frac = (clientX - rect.left) / rect.width;
        return Math.max(0, Math.min(1, frac));
    }

    function onSeekMove(clientX: number) {
        const t = seekAt(clientX);
        if (t == null) return;
        setSeekHover(t);
        if (seekDragging) seekTo(t);
    }

    function onVolumeMove(clientX: number) {
        const v = volumeAt(clientX);
        if (v == null) return;
        setVolumeHover(v);
        if (volumeDragging) setVolume(v);
    }

    function toggleMuteButton() {
        // A zero volume is silent even when audio.muted is false.
        if (volume.value <= 0) {
            setVolume(0.8);
            if (muted) { toggleMute(); setMuted(false); }
            return;
        }
        setMuted(!muted);
        toggleMute();
    }

    const queueTracks = queue.value;

    return (
        <>
            <LyricsPanel
                trackId={track.id}
                open={showLyrics}
                onOpen={() => setShowLyrics(true)}
                onClose={() => setShowLyrics(false)}
                onQueue={() => { setShowLyrics(false); queueOpen.value = true; }}
            />
            <FooterContainer other={{ id: "player-bar" }}>
                <Container horizontal centered_y class="player">
                    {/* Cover art — 56px, opens the album. */}
                    <div class="art-wrap">
                        <CoverArt
                            class="art"
                            src={coverSrc}
                            name={track.title}
                            kind="track"
                            alt=""
                            onClick={() => { if (setUuid) window.location.href = setLinkHref(setUuid); }}
                        />
                    </div>

                    {/* Transport controls. */}
                    <Container horizontal centered_y class="transport">
                        <IconButton
                            title="Previous"
                            onClick={playPrev}
                        >
                            <SkipBack size={17} />
                        </IconButton>
                        <IconButton
                            title={isPlaying.value ? "Pause" : "Play"}
                            onClick={togglePlay}
                            class={isPlaying.value ? "play-pause playing" : "play-pause"}
                        >
                            {isPlaying.value ? <Pause size={19} /> : <Play size={19} />}
                        </IconButton>
                        <IconButton
                            title="Next"
                            onClick={() => playNext()}
                        >
                            <SkipForward size={17} />
                        </IconButton>
                        <IconButton
                            title={shuffleEnabled.value ? "Shuffle on" : "Shuffle off"}
                            class="control-shuffle"
                            variant={shuffleEnabled.value ? "accent-subtle" : "always-transparent"}
                            onClick={() => setShuffle(!shuffleEnabled.value)}
                        >
                            <Shuffle size={16} />
                        </IconButton>
                        <IconButton
                            title={repeatMode.value === "one" ? "Repeat one" : repeatMode.value === "all" ? "Repeat all" : "Repeat off"}
                            class="control-repeat"
                            variant={repeatMode.value !== "off" ? "accent-subtle" : "always-transparent"}
                            onClick={() => cycleRepeat()}
                        >
                            <Repeat size={16} />
                        </IconButton>
                    </Container>

                    {/* Title / artist links. */}
                    <Container vertical class="meta">
                        <div class="title-row">
                            <a
                                href={setUuid ? setLinkHref(setUuid) : "/"}
                                class="title-link"
                                title={track.title}
                                onClick={(e) => {
                                    if (setUuid) { e.preventDefault(); window.location.href = setLinkHref(setUuid); }
                                }}
                            >
                                {track.title}
                            </a>
                        </div>
                        <div class="artist-row">
                            {artistUuid ? (
                                <a
                                    href={`/artist/${artistUuid}`}
                                    class="artist-link"
                                    title={track.artist}
                                    onClick={(e) => { e.preventDefault(); window.location.href = `/artist/${artistUuid}`; }}
                                >
                                    {track.artist}
                                </a>
                            ) : (
                                <span class="artist-link">{track.artist}</span>
                            )}
                        </div>
                        {playError.value && (
                            <span class="play-error" role="status">{playError.value}</span>
                        )}
                    </Container>

                    {/* Seek bar with filled progress. */}
                    <div class="seek-wrap">
                        <div
                            class="seek-track"
                            ref={seekRef}
                            onMouseMove={(e) => onSeekMove(e.clientX)}
                            onMouseLeave={() => { setSeekHover(null); setSeekDragging(false); }}
                            onMouseDown={(e) => {
                                const t = seekAt(e.clientX);
                                if (t == null) return;
                                seekTo(t);
                                setSeekHover(t);
                                setSeekDragging(true);
                            }}
                            onMouseUp={() => setSeekDragging(false)}
                            role="slider"
                            aria-label="Seek"
                            aria-valuenow={position.value}
                            aria-valuemin={0}
                            aria-valuemax={duration.value}
                            tabIndex={-1}
                        >
                            <div class="seek-fill" style={{ width: `${playedPct}%` }}>
                                {wavePlaying && (
                                    <svg class="seek-wave" viewBox="0 0 120 12" preserveAspectRatio="none" aria-hidden="true">
                                        <path d="M0 6 Q3 3 6 6 T12 6 T18 6 T24 6 T30 6 T36 6 T42 6 T48 6 T54 6 T60 6 T66 6 T72 6 T78 6 T84 6 T90 6 T96 6 T102 6 T108 6 T114 6 T120 6" />
                                    </svg>
                                )}
                            </div>
                            {seekHover != null && !seekDragging && duration.value > 0 && (
                                <div class="seek-preview" style={{ left: `${(seekHover / duration.value) * 100}%` }}>
                                    {formatTime(seekHover)}
                                </div>
                            )}
                            <div class="seek-thumb" style={{ left: `${playedPct}%` }} />
                        </div>
                        <div class="seek-times">
                            <Text dim content={formatTime(position.value)} />
                            <Text dim content={formatTime(duration.value)} />
                        </div>
                    </div>

                    {/* Volume with mute. */}
                    <Container horizontal centered_y class="volume-wrap">
                        <IconButton
                            title={isMutedEffective ? "Unmute" : "Mute"}
                            onClick={toggleMuteButton}
                        >
                            {isMutedEffective ? <VolumeX size={16} /> : <Volume2 size={16} />}
                        </IconButton>
                        <div
                            class="volume-track"
                            ref={volRef}
                            onMouseMove={(e) => onVolumeMove(e.clientX)}
                            onMouseLeave={() => setVolumeHover(null)}
                            onMouseDown={(e) => {
                                const v = volumeAt(e.clientX);
                                if (v == null) return;
                                setVolume(v);
                                setVolumeHover(v);
                                setVolumeDragging(true);
                            }}
                            onMouseUp={() => setVolumeDragging(false)}
                        >
                            <div class="volume-fill" style={{ width: `${Math.max(0, volume.value) * 100}%` }} />
                            <div class="volume-thumb" style={{ left: `${Math.max(0, volume.value) * 100}%` }} />
                        </div>
                        {volumeHover != null && (
                            <Text dim class="volume-preview" content={`${Math.round(volumeHover * 100)}%`} />
                        )}
                    </Container>

                    {/* Like / queue / lyrics. */}
                    <Container horizontal centered_y class="player-actions">
                        <IconButton
                            title={currentLiked.value ? "Unlike" : "Like"}
                            variant={currentLiked.value ? "accent-subtle" : "always-transparent"}
                            onClick={() => void toggleCurrentLike()}
                        >
                            <Heart size={16} fill={currentLiked.value ? "currentColor" : "none"} />
                        </IconButton>
                        <IconButton
                            title={showQueue.value ? "Hide up next" : "Up next"}
                            variant={showQueue.value ? "accent-subtle" : "always-transparent"}
                            onClick={() => { queueOpen.value = !queueOpen.value; }}
                        >
                            <ListMusic size={16} />
                        </IconButton>
                        <IconButton
                            title={showLyrics ? "Hide lyrics" : "Lyrics"}
                            class="control-lyrics"
                            variant={showLyrics ? "accent-subtle" : "always-transparent"}
                            onClick={() => setShowLyrics(!showLyrics)}
                        >
                            <MicVocal size={16} />
                        </IconButton>
                        <IconButton
                            title="More player controls"
                            class="control-more"
                            variant={moreOpen ? "accent-subtle" : "always-transparent"}
                            onClick={() => setMoreOpen(!moreOpen)}
                        >
                            <Ellipsis size={18} />
                        </IconButton>
                    </Container>
                </Container>

                {moreOpen && (
                    <div class="player-more-menu" role="dialog" aria-label="More player controls">
                        <div class="more-head">
                            <Text content="More controls" />
                            <IconButton title="Close more controls" onClick={() => setMoreOpen(false)}>
                                <X size={16} />
                            </IconButton>
                        </div>
                        <div class="more-volume">
                            <Volume2 size={18} />
                            <input
                                type="range"
                                min={0}
                                max={100}
                                value={Math.round(Math.max(0, volume.value) * 100)}
                                aria-label="Volume"
                                onInput={(e) => setVolume(Number((e.target as HTMLInputElement).value) / 100)}
                            />
                        </div>
                        <div class="more-actions">
                            <IconButton
                                title={shuffleEnabled.value ? "Shuffle on" : "Shuffle off"}
                                variant={shuffleEnabled.value ? "accent-subtle" : "always-transparent"}
                                onClick={() => setShuffle(!shuffleEnabled.value)}
                            >
                                <Shuffle size={18} />
                            </IconButton>
                            <IconButton
                                title={repeatMode.value === "one" ? "Repeat one" : repeatMode.value === "all" ? "Repeat all" : "Repeat off"}
                                variant={repeatMode.value !== "off" ? "accent-subtle" : "always-transparent"}
                                onClick={() => cycleRepeat()}
                            >
                                <Repeat size={18} />
                            </IconButton>
                            <IconButton
                                title={showLyrics ? "Hide lyrics" : "Lyrics"}
                                variant={showLyrics ? "accent-subtle" : "always-transparent"}
                                onClick={() => { setShowLyrics(!showLyrics); setMoreOpen(false); }}
                            >
                                <MicVocal size={18} />
                            </IconButton>
                            <a class="button variant-panel" href="/devices" onClick={() => setMoreOpen(false)}>
                                Devices
                            </a>
                        </div>
                    </div>
                )}

                {showQueue.value && (
                    <Container class="queue-drawer">
                        <Container horizontal centered_y class="queue-head">
                            <div class="sheet-tabs" role="group" aria-label="Player panel">
                                <button
                                    type="button"
                                    class="sheet-tab"
                                    aria-pressed={false}
                                    onClick={() => { queueOpen.value = false; setShowLyrics(true); }}
                                >
                                    <MicVocal size={16} /> Lyrics
                                </button>
                                <button type="button" class="sheet-tab" aria-pressed={true}>
                                    <ListMusic size={16} /> Up next
                                </button>
                            </div>
                            <Text dim content={`${queueTracks.length} track${queueTracks.length == 1 ? "" : "s"}`} />
                            <IconButton title="Close queue" onClick={() => { queueOpen.value = false; }}>
                                <X size={14} />
                            </IconButton>
                        </Container>
                        {queueTracks.length === 0 && (
                            <div class="queue-empty">Nothing queued — play an album to fill this up.</div>
                        )}
                        <div class="queue-list">
                            {queueTracks.map((t, i) => (
                                <button
                                    type="button"
                                    key={`${t.id}-${i}`}
                                    class={`queue-row${i === queueIndex.value ? " queue-row-active" : ""}`}
                                    onClick={() => playQueueIndex(i)}
                                >
                                    <Text dim content={i + 1} class="queue-num" />
                                    <span class="queue-info">
                                        <span class="queue-title-text">{t.title}</span>
                                        <span class="queue-artist-text">{t.artist}</span>
                                    </span>
                                    {i === queueIndex.value && <Text dim content={formatTime(position.value)} />}
                                </button>
                            ))}
                            <button
                                type="button"
                                class={`queue-row queue-autoplay${autoplay.value ? " queue-row-active" : ""}`}
                                title={autoplay.value ? "Autoplay on — similar tracks are added at the end" : "Autoplay off"}
                                onClick={() => setAutoplay(!autoplay.value)}
                            >
                                <Radio size={15} />
                                <span class="queue-info">
                                    <span class="queue-title-text">Autoplay</span>
                                    <span class="queue-artist-text">
                                        {autoplay.value ? "On — keep the music going" : "Off"}
                                    </span>
                                </span>
                            </button>
                        </div>
                    </Container>
                )}
            </FooterContainer>
        </>
    );
}
```


### `ui/src/components/PlayerBar/style.css`

```css
#player-bar {
    position: fixed;
    /* Detached transport capsule: flat tonal fill, one hairline rim. */
    left: 12px;
    right: 12px;
    bottom: max(12px, env(safe-area-inset-bottom));
    z-index: 40;
    padding: 10px 18px;
    padding-bottom: 10px;
    background: var(--md-surface-container-high);
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius-pill);
    display: flex;
    align-items: center;
}

#player-bar .player {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    max-width: 100%;
    min-width: 0;
    flex-wrap: nowrap;
}

#player-bar .player > * {
    min-width: 0;
}

#player-bar .button {
    min-width: var(--touch-target);
    min-height: var(--touch-target);
}

#player-bar .art-wrap {
    position: relative;
    flex: none;
    cursor: pointer;
    border-radius: var(--radius-lg);
    overflow: hidden;
    background: var(--surface-lift);
}

#player-bar .art,
#player-bar .art-wrap .cover-art {
    width: 56px;
    height: 56px;
    border-radius: var(--radius-lg);
    object-fit: cover;
    background: var(--surface-lift);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--accent);
}

#player-bar .transport {
    gap: 4px;
    flex: 0 1 auto;
}

#player-bar .button:active {
    transform: scale(var(--press-scale));
}

#player-bar .play-pause {
    min-width: var(--touch-target);
    min-height: var(--touch-target);
    justify-content: center;
    background: var(--accent);
    color: var(--text-on-light);
    border-radius: var(--radius-pill);
    transition: border-radius var(--morph-ms) cubic-bezier(0.2, 0.9, 0.2, 1.2),
                transform var(--transition-fast), background var(--transition-fast);
}

/* Circle while paused, canonical squircle blob while playing. */
#player-bar .play-pause.playing {
    border-radius: var(--blob-2-radius);
    background: var(--accent-hover);
}

#player-bar .play-pause svg {
    transition: transform var(--morph-ms) cubic-bezier(0.2, 0.9, 0.2, 1.2);
}

#player-bar .play-pause.playing svg {
    transform: rotate(90deg) scale(0.92);
}

#player-bar .meta {
    min-width: 0;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
}

#player-bar .title-row {
    display: flex;
    align-items: center;
    min-height: var(--touch-target);
}

#player-bar .title-link {
    display: flex;
    align-items: center;
    min-height: var(--touch-target);
    min-width: 44px;
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--text-bright);
    text-decoration: none;
    font-weight: 600;
}

#player-bar .title-link:hover {
    text-decoration: underline;
}

#player-bar .artist-row {
    display: flex;
    align-items: center;
    min-height: var(--touch-target);
}

#player-bar .artist-link {
    display: flex;
    align-items: center;
    min-height: var(--touch-target);
    min-width: 44px;
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--text-dim);
    text-decoration: none;
    font-size: var(--font-size-medium);
}

#player-bar .artist-link:hover {
    text-decoration: underline;
}

#player-bar .play-error {
    display: block;
    color: var(--danger);
    font-size: var(--font-size-small);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Seek bar: filled progress in the accent color. */
#player-bar .seek-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    flex: 2 1 0;
}

#player-bar .seek-track {
    position: relative;
    flex: 1;
    min-width: 0;
    height: 44px;
    display: flex;
    align-items: center;
    cursor: pointer;
}

#player-bar .seek-track::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    height: 8px;
    border-radius: var(--radius-pill);
    background: var(--md-surface-container-highest);
}

#player-bar .seek-fill {
    position: relative;
    height: 8px;
    border-radius: var(--radius-pill);
    background: var(--accent);
    width: 0%;
    transition: width 0.1s linear;
}

/* The wave only exists while playing and playful motion is on; the whole
   filled capsule carries a 3px, 0.55Hz wave instead of a bobbing badge. */
#player-bar .seek-wave {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    color: var(--text-on-light);
    overflow: hidden;
    border-radius: inherit;
}

#player-bar .seek-wave path {
    fill: none;
    stroke: currentColor;
    stroke-width: 1.6;
    stroke-linecap: round;
    vector-effect: non-scaling-stroke;
    animation: seek-wave-drift calc(1s / var(--progress-wave-hz)) linear infinite;
}

@keyframes seek-wave-drift {
    from { transform: translateX(0); }
    to { transform: translateX(-12px); }
}

html[data-playful="false"] #player-bar .seek-wave { display: none; }
html[data-playful="false"] #player-bar .play-pause,
html[data-playful="false"] #player-bar .play-pause.playing {
    border-radius: var(--radius-pill);
    transition: none;
}

@media (prefers-reduced-motion: reduce) {
    #player-bar .seek-wave { display: none; }
    #player-bar .seek-wave path { animation: none; }
    #player-bar .play-pause,
    #player-bar .play-pause.playing {
        border-radius: var(--radius-pill);
        transition: none;
    }
    #player-bar .play-pause.playing svg { transform: none; }
}

#player-bar .seek-thumb {
    position: absolute;
    left: 0%;
    top: 50%;
    width: 14px;
    height: 14px;
    margin-top: -7px;
    margin-left: -7px;
    border-radius: 50%;
    background: var(--text-bright);
    transition: left 0.1s linear, width 0.1s, height 0.1s, margin-top 0.1s, margin-left 0.1s;
}

#player-bar .seek-track:hover .seek-thumb {
    width: 18px;
    height: 18px;
    margin-top: -9px;
    margin-left: -9px;
    background: var(--accent-hover);
}

#player-bar .seek-preview {
    position: absolute;
    top: -20px;
    transform: translateX(-50%);
    padding: 2px 6px;
    border-radius: 6px;
    background: var(--prim);
    border: 1px solid var(--back-border);
    color: var(--text-bright);
    font-size: var(--font-size-small);
    font-variant-numeric: tabular-nums;
    pointer-events: none;
    white-space: nowrap;
}

#player-bar .seek-times {
    display: flex;
    gap: 10px;
    flex: 0 1 auto;
}

#player-bar .seek-times > * {
    font-size: var(--font-size-small);
    color: var(--text-dim);
    font-variant-numeric: tabular-nums;
}

/* Volume bar. */
#player-bar .volume-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    flex: 0 1 110px;
    min-width: 0;
}

#player-bar .volume-track {
    position: relative;
    flex: 1;
    min-width: 0;
    height: 44px;
    display: flex;
    align-items: center;
    cursor: pointer;
}

#player-bar .volume-track::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    height: 8px;
    border-radius: var(--radius-pill);
    background: var(--md-surface-container-highest);
}

#player-bar .volume-fill {
    position: relative;
    height: 8px;
    border-radius: var(--radius-pill);
    background: var(--accent);
    width: 0%;
    transition: width 0.1s linear;
}

#player-bar .volume-thumb {
    position: absolute;
    left: 0%;
    top: 50%;
    width: 12px;
    height: 12px;
    margin-top: -6px;
    margin-left: -6px;
    border-radius: 50%;
    background: var(--text);
    transition: left 0.1s linear, width 0.1s, height 0.1s, margin-top 0.1s, margin-left 0.1s;
}

#player-bar .volume-track:hover .volume-thumb {
    width: 14px;
    height: 14px;
    margin-top: -7px;
    margin-left: -7px;
    background: var(--accent-hover);
}

#player-bar .volume-preview {
    font-size: var(--font-size-small);
    font-variant-numeric: tabular-nums;
    flex-shrink: 0;
}

#player-bar .queue-drawer {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 100%;
    margin-bottom: 6px;
    z-index: 46;
    background: var(--md-surface-container-high);
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius);
    width: min(460px, calc(100vw - 24px));
    margin-left: auto;
    margin-right: auto;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    animation: queue-slide-in 0.2s ease-out;
}

@keyframes queue-slide-in {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

#player-bar .queue-head {
    gap: 8px;
    padding: 8px 10px;
    flex-wrap: wrap;
    border-bottom: 1px solid var(--back-border);
}

#player-bar .queue-head .sheet-tabs {
    flex: 1 1 auto;
}

/* The queue drawer is a peer sheet, not a floating card with elevation. */
#player-bar .queue-drawer {
    border-radius: var(--radius-xl);
}

#player-bar .queue-list {
    max-height: 260px;
    overflow: auto;
    overscroll-behavior: contain;
}

#player-bar .queue-row {
    display: flex;
    align-items: center;
    width: 100%;
    min-height: var(--touch-target);
    padding: 8px 12px;
    gap: 10px;
    cursor: pointer;
    background: transparent;
    border: 0;
    border-radius: var(--radius-pill);
    color: inherit;
    font: inherit;
    text-align: left;
}

#player-bar .queue-row:hover {
    background: var(--flat-hover);
}

#player-bar .queue-row-active {
    background: var(--accent-soft);
    border-radius: var(--radius-pill);
}

#player-bar .queue-num {
    flex: none;
    min-width: 20px;
    text-align: right;
    color: var(--text-dim);
}

/* Autoplay is the last queue row; a separator makes it read as a setting
   rather than another track. */
#player-bar .queue-autoplay {
    border-top: 1px solid var(--back-border);
    color: var(--text-dim);
}

#player-bar .queue-autoplay.queue-row-active {
    color: var(--accent);
}

#player-bar .queue-autoplay > svg {
    flex: none;
    min-width: 20px;
}

#player-bar .queue-empty {
    padding: 20px 16px 24px;
    text-align: center;
    color: var(--text-dim);
    font-size: var(--font-size-small);
}

#player-bar .queue-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
}

#player-bar .queue-title-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

#player-bar .queue-artist-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: var(--font-size-small);
    color: var(--text-dim);
}

#player-bar .player-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    flex: 0 1 auto;
}

/* Shuffle/repeat/volume/lyrics/devices move here in the compact tier. */
#player-bar .control-more {
    display: none;
}

#player-bar .player-more-menu {
    position: absolute;
    right: 12px;
    bottom: 100%;
    margin-bottom: 8px;
    z-index: 47;
    width: min(320px, calc(100vw - 24px));
    max-height: min(70vh, 420px);
    overflow-y: auto;
    overscroll-behavior: contain;
    padding: 12px;
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius);
    background: var(--md-surface-container-high);
    display: flex;
    flex-direction: column;
    gap: 8px;
}

#player-bar .more-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    min-width: 0;
}

#player-bar .more-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}

#player-bar .more-volume {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: var(--touch-target);
}

#player-bar .more-volume input[type="range"] {
    flex: 1;
    min-width: 0;
    accent-color: var(--accent);
}

/* Compact (800-1100): two rows so the seek times survive, with volume and
   secondary transport controls collapsed into the More popover. */
@container shell (width >= 800px) and (width < 1100px) {
    #player-bar {
        padding: 6px 12px calc(6px + env(safe-area-inset-bottom));
    }

    #player-bar .player {
        display: grid;
        grid-template-columns: 48px minmax(0, 1fr) auto auto;
        grid-template-areas:
            "art meta transport actions"
            "seek seek seek seek";
        column-gap: 8px;
        row-gap: 2px;
        min-height: 76px;
    }

    #player-bar .art-wrap { grid-area: art; }
    #player-bar .art { width: 48px; height: 48px; }
    #player-bar .meta { grid-area: meta; }
    #player-bar .transport { grid-area: transport; }
    #player-bar .player-actions { grid-area: actions; }

    #player-bar .seek-wrap {
        grid-area: seek;
        width: 100%;
        flex: none;
    }

    #player-bar .volume-wrap,
    #player-bar .transport .control-shuffle,
    #player-bar .transport .control-repeat,
    #player-bar .player-actions .control-lyrics {
        display: none;
    }

    #player-bar .control-more {
        display: inline-flex;
    }

    #player-bar .transport .button,
    #player-bar .player-actions .button {
        min-width: var(--touch-target);
        min-height: var(--touch-target);
        padding: 0 6px;
    }
}

/* Tablet / phone: art / title / transport / actions, then a full seek line. */
@container shell (width < 800px) {
    #player-bar {
        padding: 6px 10px calc(6px + env(safe-area-inset-bottom));
    }

    #player-bar .player {
        display: grid;
        grid-template-columns: 42px minmax(0, 1fr) auto auto;
        grid-template-areas:
            "art meta transport actions"
            "seek seek seek seek";
        column-gap: 8px;
        row-gap: 4px;
    }

    #player-bar .art-wrap { grid-area: art; }
    #player-bar .art { width: 42px; height: 42px; }
    #player-bar .meta { grid-area: meta; }
    #player-bar .transport { grid-area: transport; }
    #player-bar .player-actions { grid-area: actions; }
    #player-bar .seek-wrap { grid-area: seek; width: 100%; flex: none; }

    #player-bar .volume-wrap,
    #player-bar .transport .control-shuffle,
    #player-bar .transport .control-repeat,
    #player-bar .player-actions .control-lyrics {
        display: none;
    }

    #player-bar .control-more {
        display: inline-flex;
    }

    #player-bar .seek-times {
        display: none;
    }

    #player-bar .transport .button,
    #player-bar .player-actions .button {
        min-width: var(--touch-target);
        min-height: var(--touch-target);
        padding: 0 6px;
    }
}

/* Phone: secondary actions move into the More popover so the transport,
   title and seek line all stay reachable without horizontal scrolling. */
@container shell (width < 600px) {
    #player-bar .player {
        grid-template-columns: 40px minmax(44px, 1fr) auto 44px;
        column-gap: 8px;
    }

    #player-bar .art { width: 40px; height: 40px; }

    #player-bar .transport { gap: 0; }

    #player-bar .transport .button,
    #player-bar .player-actions .button {
        min-width: 44px;
        min-height: 44px;
        width: 44px;
        height: 44px;
        padding: 0;
    }

    #player-bar .player-actions > *:not(.control-more) {
        display: none;
    }

    #player-bar .player-more-menu {
        right: 8px;
        width: min(304px, calc(100vw - 16px));
    }
}

@container shell (width < 360px) {
    #player-bar .player {
        grid-template-columns: minmax(0, 1fr) auto auto;
        grid-template-areas:
            "meta transport actions"
            "seek seek seek";
    }

    #player-bar .art-wrap,
    #player-bar .player-actions .button:first-child {
        display: none;
    }
}
```


### `ui/src/components/Topbar/style.css`

```css
/* One horizontal chrome row. flufi's HeaderContainer is a column by default,
   so override it here; the title must share the row with search and actions. */
#topbar {
    display: flex;
    flex-direction: row;
    align-items: center;
    min-height: var(--topbar-h);
    height: var(--topbar-h);
    padding: 0 16px;
    border-bottom: 1px solid var(--layer-rim);
    background: var(--md-surface-container-low);
    position: relative;
    z-index: 2;
}

#topbar > .middle {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 8px;
    width: 100%;
    min-width: 0;
    height: 100%;
}

#topbar .brand-link {
    gap: 10px;
    padding: 0 6px 0 0;
    flex: none;
    text-decoration: none;
}

#topbar .brand-link .logo {
    white-space: nowrap;
}

#topbar .search-bar {
    width: min(380px, 34vw);
    min-width: 180px;
    margin-inline: auto;
}

#topbar .user-pill {
    display: inline-flex;
    align-items: center;
    min-height: 40px;
    max-width: 160px;
    padding: 0 16px;
    border-radius: var(--radius-pill);
    background: var(--md-secondary-container);
    color: var(--md-on-secondary-container);
    flex: none;
}

#topbar .user {
    max-width: 140px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.brand-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    color: var(--md-on-primary-container);
    background: var(--md-primary-container);
    border-radius: var(--blob-5-radius);
    transition: transform var(--transition-fast) var(--spring-ease);
}

#topbar .brand-link:hover .brand-mark {
    transform: rotate(-8deg);
}

.mobile {
    #topbar {
        padding: 0 8px;
    }

    #topbar > .middle {
        gap: 4px;
    }

    #topbar .user-pill,
    #topbar .icon-tip[title="Home"] {
        display: none;
    }

    #topbar .brand-link {
        padding-right: 0;
        gap: 0;
    }

    /* Phones keep only the compact mark; the page title carries the name. */
    #topbar .brand-mark {
        display: inline-flex;
    }

    #topbar .brand-link .logo {
        display: none;
    }

    #topbar .search-bar {
        width: auto;
        min-width: 70px;
        flex: 1;
        margin-inline: 0;
    }

    #topbar .icon-tip .button,
    #topbar > .middle > .button {
        min-width: var(--touch-target);
        min-height: var(--touch-target);
        padding: 0 6px;
    }
}

#topbar > .middle > * {
    min-width: 0;
}

#topbar .button,
#topbar .search-bar .button {
    min-width: var(--touch-target);
    min-height: var(--touch-target);
}

#topbar .user-avatar {
    display: none;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: var(--radius-pill);
    background: var(--md-primary-container);
    color: var(--md-on-primary-container);
    font-weight: 700;
}

/* Compact: keep every control at full touch size, drop only the user label. */
@container shell (width >= 800px) and (width < 1100px) {
    #topbar {
        padding-inline: 12px;
    }

    #topbar .brand-link {
        flex: 0 0 auto;
        padding-right: 0;
    }

    #topbar .brand-link .logo {
        display: none;
    }

    #topbar .search-bar {
        width: auto;
        min-width: 0;
        flex: 1 1 0;
        margin-inline: 8px;
    }

    #topbar .user-pill {
        min-width: var(--touch-target);
        padding: 0 8px;
        justify-content: center;
    }

    #topbar .user {
        display: none;
    }

    #topbar .user-avatar {
        display: inline-flex;
    }

    #topbar .icon-tip .button,
    #topbar > .middle > .button {
        min-width: var(--touch-target);
        min-height: var(--touch-target);
    }
}

/* Tablet/phone chrome: avatar only, never a full user pill. */
@container shell (width < 800px) {
    .mobile #topbar .user-pill {
        display: none;
    }

    .mobile #topbar .search-bar {
        min-width: 0;
    }
}

/* Phone chrome keeps only brand, menu and search in the bar; account and
   upload actions live in the drawer so nothing is silently clipped. */
@container shell (width < 600px) {
    #topbar .icon-tip[title="Add music"],
    #topbar .icon-tip[title="Log out"],
    #topbar .user-pill {
        display: none;
    }

    #topbar .brand-link {
        gap: 0;
        padding-right: 0;
    }

    #topbar .search-bar {
        margin-inline: 0;
    }
}
```


### `ui/src/pages/Home/Home.tsx`

```tsx
/** Home: a bold, flat greeting, real personalised shelves, then the library.
 *
 * Shelf titles come straight from /api/home. Nothing is relabelled as a Mix,
 * Radio destination or global chart; "Made for you" only appears when the
 * server actually produced that recommendation shelf.
 */
import { useEffect, useState } from "preact/hooks";
import {
    Button, Container, Content, Header2, Header3, Input, Loading, SelectBox, Text,
} from "flufi-ui/components";
import { ArrowDownUp, Disc3, ListFilter, Play, Sparkles } from "lucide-preact";
import { BlobAccent } from "../../components/Playful/BlobAccent";
import { EmptyState } from "../../components/EmptyState/EmptyState";
import { SetCard } from "../../components/Library/Card";
import { TrackList } from "../../components/TrackList/TrackList";
import { API, parseArtistUuid } from "../../common/net/api";
import type { HomeSection, Set, Track } from "../../common/net/types";
import { playQueue } from "../../common/player";

import "./style.css";

const PAGE = 60;

const SORTS = [
    { value: "name", label: "A–Z" },
    { value: "artist", label: "Artist" },
    { value: "recent", label: "Recently added" },
];

function artistNames(set: Set): string {
    const names: string[] = [];
    for (const track of set.tracks.value) {
        for (const uuid of track.artists.value) {
            const name = parseArtistUuid(uuid).name;
            if (!names.includes(name)) names.push(name);
        }
    }
    return names.join(", ") || set.artistName || "";
}

function queueFor(section: HomeSection) {
    return section.tracks.map(t => ({
        id: t.uuid,
        title: t.name.value,
        artist: t.artists.value.map(u => parseArtistUuid(u).name).join(", "),
        setUuid: t.set ?? undefined,
        artistUuid: t.artists.value[0],
    }));
}

export function HomePage() {
    const [albums, setAlbums] = useState<Set[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [query, setQuery] = useState("");
    const [sort, setSort] = useState("name");
    const [singles, setSingles] = useState(false);
    const [count, setCount] = useState(PAGE);

    const [tracks, setTracks] = useState<Track[] | null>(null);
    const [shelves, setShelves] = useState<HomeSection[]>([]);

    useEffect(() => {
        API.listTracks(50).then(setTracks).catch(() => setTracks([]));
        API.home()
            .then(d => setShelves(d.sections.filter(s => s.tracks.length > 0).slice(0, 4)))
            .catch(() => { /* personalised shelves are optional */ });
    }, []);

    useEffect(() => {
        let cancelled = false;
        const timer = setTimeout(() => {
            setLoading(true);
            API.listAlbums({
                limit: count,
                offset: 0,
                q: query.trim(),
                sort,
                minTracks: singles ? 1 : 2,
            })
                .then((r) => {
                    if (cancelled) return;
                    setAlbums(r.albums);
                    setTotal(r.total);
                    setError(null);
                })
                .catch(() => {
                    if (cancelled) return;
                    setAlbums([]);
                    setTotal(0);
                    setError("Could not load albums. Check the connection and try again.");
                })
                .finally(() => {
                    if (!cancelled) setLoading(false);
                });
        }, query ? 250 : 0);

        return () => {
            cancelled = true;
            clearTimeout(timer);
        };
    }, [query, sort, singles, count]);

    function changeQuery(value: string) {
        setQuery(value);
        setCount(PAGE);
    }

    function changeSort(value: string | null) {
        setSort(value ?? "name");
        setCount(PAGE);
    }

    function toggleSingles() {
        setSingles(v => !v);
        setCount(PAGE);
    }

    async function playAlbum(set: Set) {
        try {
            const full = await API.getSet(set.uuid);
            const ts = full.tracks.value;
            if (ts.length === 0) return;
            const list = ts
                .filter(t => t.uuid)
                .map(t => ({
                    id: t.uuid,
                    title: t.name.value,
                    artist: t.artists.value.map(u => parseArtistUuid(u).name).join(", "),
                    setUuid: full.uuid,
                    artistUuid: t.artists.value[0] ?? null,
                }));
            if (list.length > 0) playQueue(list, 0);
        } catch {
            setError("Could not start that album.");
        }
    }

    function playShelf(section: HomeSection) {
        const list = queueFor(section);
        if (list.length) playQueue(list, 0);
    }

    const [hero, second, ...otherShelves] = shelves;
    const skeletonCount = loading && albums.length === 0 ? Math.min(total || PAGE, PAGE) : 0;
    const secondaryAlbum = albums[0] ?? null;

    return (
        <Content class="home">
            <Container extra_gap>
                <div class="home-hero-row">
                    {hero ? (
                        <Container class="home-hero hero-primary">
                            <BlobAccent id="blob-3" class="hero-blob blob-tertiary" />
                            <div class="hero-badge"><Sparkles size={18} /> Your music</div>
                            <Header2 class="hero-title">{hero.title}</Header2>
                            <Text dim content="A real shelf from your listening history — press play whenever you're ready." />
                            <div class="hero-actions">
                                <Button variant="accent" class="hero-play" onClick={() => playShelf(hero)}>
                                    <Play size={18} /> Play {hero.title}
                                </Button>
                                <Text dim content={`${hero.tracks.length} tracks`} />
                            </div>
                        </Container>
                    ) : (
                        <Container class="home-hero hero-primary">
                            <BlobAccent id="blob-3" class="hero-blob blob-tertiary" />
                            <div class="hero-badge"><Sparkles size={18} /> Your library</div>
                            <Header2 class="hero-title">Start with your music</Header2>
                            <Text dim content="Add music and real shelves built from plays and likes appear here." />
                            <div class="hero-actions">
                                <a class="button variant-accent hero-play" href="/upload">Add music</a>
                            </div>
                        </Container>
                    )}

                    <Container class="home-hero hero-secondary">
                        <BlobAccent id="blob-5" class="hero-blob blob-secondary" />
                        {second ? (
                            <>
                                <div class="hero-badge"><Disc3 size={16} /> From your listening</div>
                                <Header3 class="hero-title">{second.title}</Header3>
                                <Text dim content="Built from plays and likes on this server." />
                                <div class="hero-actions">
                                    <Button variant="panel" class="hero-play" onClick={() => playShelf(second)}>
                                        <Play size={16} /> Play
                                    </Button>
                                    <Text dim content={`${second.tracks.length} tracks`} />
                                </div>
                            </>
                        ) : secondaryAlbum ? (
                            <>
                                <div class="hero-badge"><Disc3 size={16} /> From your library</div>
                                <Header3 class="hero-title">{artistNames(secondaryAlbum) || secondaryAlbum.name.value}</Header3>
                                <Text dim content={`${secondaryAlbum.tracks.value.length} tracks in this album.`} />
                                <div class="hero-actions">
                                    <Button variant="panel" class="hero-play" onClick={() => void playAlbum(secondaryAlbum)}>
                                        <Play size={16} /> Play album
                                    </Button>
                                </div>
                            </>
                        ) : (
                            <>
                                <div class="hero-badge"><Disc3 size={16} /> Your library</div>
                                <Header3 class="hero-title">Albums live here</Header3>
                                <Text dim content="Nothing is invented while your library is empty." />
                                <div class="hero-actions">
                                    <a class="button variant-panel hero-play" href="/playlists">Open library</a>
                                </div>
                            </>
                        )}
                    </Container>
                </div>

                {otherShelves.length > 0 && (
                    <Container class="home-shelves">
                        <Container horizontal centered_y class="shelves-head">
                            <Header3>From your listening</Header3>
                            {otherShelves.length > 0 && (
                                <Text dim content="Built from plays and likes on this server" />
                            )}
                        </Container>
                        <div class="shelf-chips">
                            {otherShelves.map(section => (
                                <Button
                                    key={section.title}
                                    variant="panel"
                                    class="shelf-chip"
                                    title={`Play ${section.title}`}
                                    onClick={() => playShelf(section)}
                                >
                                    <Play size={14} /> {section.title}
                                </Button>
                            ))}
                        </div>
                        {otherShelves.map(section => (
                            <Container key={section.title} class="home-shelf">
                                <Container horizontal centered_y class="shelf-head">
                                    <Header3>{section.title}</Header3>
                                    <Button variant="panel" title={`Play ${section.title}`} onClick={() => playShelf(section)}>
                                        <Play size={14} /> Play
                                    </Button>
                                </Container>
                                <TrackList tracks={section.tracks.slice(0, 8)} showDuration={true} />
                            </Container>
                        ))}
                    </Container>
                )}

                <Container class="home-library">
                    <Header2>Albums</Header2>
                    <Container horizontal centered_y class="album-controls">
                        <label class="control-with-icon">
                            <ListFilter size={15} aria-hidden="true" />
                            <Input
                                class="album-filter"
                                placeholder="Filter albums"
                                value={query}
                                onInput={changeQuery}
                            />
                        </label>
                        <label class="control-with-icon">
                            <ArrowDownUp size={15} aria-hidden="true" />
                            <SelectBox
                                class="album-sort"
                                options={SORTS}
                                value={sort}
                                onChange={changeSort}
                            />
                        </label>
                        <Button
                            variant={singles ? "accent" : "panel"}
                            title="Include one-song albums"
                            onClick={toggleSingles}
                        >
                            <Disc3 size={15} /> Singles
                        </Button>
                        {!loading && (
                            <Text dim content={`${total} album${total == 1 ? "" : "s"}`} />
                        )}
                    </Container>

                    {error && <Text class="error" content={error} />}

                    {loading && albums.length === 0
                        ? (
                            <div class="album-grid skeleton-grid">
                                {[...Array(skeletonCount)].map((_, i) => (
                                    <div key={i} class="skeleton-card">
                                        <div class="skeleton-cover" />
                                        <div class="skeleton-title" />
                                        <div class="skeleton-sub" />
                                    </div>
                                ))}
                            </div>
                        )
                        : albums.length === 0
                            ? (
                                <EmptyState
                                    icon={<Disc3 size={22} />}
                                    title={query ? "No matching albums" : "No albums yet"}
                                    body={query
                                        ? `Nothing matches “${query}”. Try a different filter.`
                                        : "Add music from the top bar and it will show up here."}
                                />
                            )
                            : (
                                <div class="album-grid">
                                    {albums.map(a => (
                                        <SetCard
                                            key={a.uuid}
                                            set={a}
                                            subtitle={artistNames(a) || a.artistName}
                                            onPlay={() => playAlbum(a)}
                                        />
                                    ))}
                                </div>
                            )}

                    {!loading && albums.length > 0 && albums.length < total && (
                        <Button
                            variant="panel"
                            class="load-more"
                            onClick={() => setCount(c => c + PAGE)}
                        >
                            Load more
                        </Button>
                    )}
                </Container>

                <Container class="home-songs">
                    <Header2>Songs</Header2>
                    <Loading loaded={tracks != null}>
                        {() => <TrackList tracks={tracks!} />}
                    </Loading>
                </Container>
            </Container>
        </Content>
    )
}
```


### `ui/src/pages/Home/style.css`

```css
/* Home uses the shell's own page padding; the grid stretches to the content
   width so album tiles fill the row instead of shrink-wrapping to the centre. */
.content-home {
    align-items: stretch;
    justify-content: flex-start;
}

/* Two asymmetric hero cards: real shelves first, a second card that only
   reports data that actually exists. Flat tonal fills, no elevation. */
.home-hero-row {
    display: grid;
    grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
    gap: 16px;
    min-width: 0;
}

.home-hero {
    position: relative;
    align-items: flex-start;
    gap: 12px;
    padding: 28px;
    min-width: 0;
    border-radius: var(--radius-xl);
    background: var(--md-primary-container);
    color: var(--md-on-primary-container);
    overflow: hidden;
}

.home-hero.hero-secondary {
    background: var(--md-secondary-container);
    color: var(--md-on-secondary-container);
}

.home-hero > .hero-blob {
    position: absolute;
    right: -12px;
    bottom: -24px;
    width: min(150px, 42%);
    height: auto;
    aspect-ratio: 1;
    pointer-events: none;
}

.home-hero > *:not(.hero-blob) {
    position: relative;
    z-index: 1;
}

.home-hero .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: var(--radius-pill);
    background: var(--md-secondary-container);
    color: var(--md-on-secondary-container);
    font-size: var(--type-label-size);
    font-weight: var(--type-label-weight);
}

.home-hero.hero-secondary .hero-badge {
    background: var(--md-primary-container);
    color: var(--md-on-primary-container);
}

.home-hero .hero-title {
    margin: 0;
    max-width: 22ch;
    overflow-wrap: anywhere;
}

.home-hero .dim,
.home-hero .hero-actions .dim {
    color: var(--md-on-primary-container);
    opacity: 0.82;
}

.home-hero .hero-actions {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 8px;
}

.home-hero .hero-play {
    background: var(--accent);
    color: var(--text-on-light);
    border: 0;
}

.home-shelves {
    gap: 12px;
}

.home-shelves .shelves-head {
    justify-content: space-between;
    gap: 12px;
}

/* Peer shelves read as one floating segmented pill, not loose buttons. */
.shelf-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    width: fit-content;
    max-width: 100%;
    min-width: 0;
    margin-inline: auto;
    padding: 4px;
    border: 1px solid var(--layer-rim);
    border-radius: var(--radius-pill);
    background: var(--md-surface-container-low);
}

.shelf-chips .shelf-chip {
    min-height: var(--touch-target);
    border-radius: var(--radius-pill);
}

.home-shelf {
    padding: 16px;
    border-radius: var(--radius);
    background: var(--md-surface-container-low);
}

.home-shelf .shelf-head {
    gap: 10px;
    margin-bottom: 6px;
}

.home-shelf .shelf-head > :last-child {
    margin-left: auto;
}

.album-controls {
    gap: 10px;
    flex-wrap: wrap;
    margin: 10px 0 16px;
}

.album-controls .album-filter {
    width: 220px;
    min-width: 0;
}

.album-controls .album-sort {
    width: 170px;
}

.control-with-icon {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    min-width: 0;
    color: var(--text-dim);
}

.control-with-icon > svg {
    flex: none;
    color: var(--accent);
}


/* auto-fill keeps every column the same width, so the last card in a row can
   never overflow the pane or get clipped. min-width: 0 on cards lets them
   shrink below their content size inside grid cells. */
.album-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(clamp(140px, 12vw, 210px), 1fr));
    gap: 16px;
    width: 100%;
    min-width: 0;
    overflow-x: visible;
}

.album-grid .library-card {
    width: 100%;
    min-width: 0;
}

.load-more {
    margin-top: 16px;
}

/* Skeleton cards shown while the first page of albums loads. */
.skeleton-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(clamp(140px, 12vw, 210px), 1fr));
    gap: 16px;
    width: 100%;
    min-width: 0;
    overflow-x: visible;
}

.skeleton-card {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.skeleton-cover {
    width: 100%;
    aspect-ratio: 1 / 1;
    border-radius: var(--radius);
    background: var(--prim);
    position: relative;
    overflow: hidden;
}

.skeleton-cover::before {
    content: "";
    position: absolute;
    inset: 0;
    background: var(--surface-lift);
    animation: skeleton-pulse 1.5s infinite linear;
}

.skeleton-title {
    margin-top: 8px;
    height: 1.3em;
    border-radius: 4px;
    background: var(--prim);
    width: 70%;
    animation: skeleton-pulse 1.5s infinite linear;
}

.skeleton-sub {
    margin-top: 4px;
    height: 1em;
    border-radius: 4px;
    background: var(--prim);
    width: 55%;
    animation: skeleton-pulse 1.5s infinite linear;
}

@keyframes skeleton-pulse {
    0%, 100% { opacity: 0.35; }
    50% { opacity: 0.8; }
}

/* Compact tiers stack the asymmetric pair instead of squeezing two cards. */
@container shell (width < 1100px) {
    .home-hero-row {
        grid-template-columns: minmax(0, 1fr);
    }

    .home-hero {
        padding: 20px;
    }
}

@container shell (width < 800px) {
    .album-grid,
    .skeleton-grid {
        grid-template-columns: repeat(auto-fill, minmax(122px, 1fr));
        gap: 12px;
    }

    .album-controls .album-filter,
    .album-controls .album-sort {
        flex: 1;
        width: auto;
    }

    .home-hero > .hero-blob {
        width: min(110px, 36%);
        right: -8px;
        bottom: -16px;
    }
}

@container shell (width < 600px) {
    .home-hero {
        padding: 16px;
        gap: 8px;
    }

    .home-hero .hero-actions {
        gap: 8px;
    }
}
```


### `ui/e2e/playful.spec.ts`

```ts
/** Phase 1 guards for the playful web language: generated blob placeholders,
 *  the play/pause morph, the wavy progress line and the Lyrics | Up next
 *  segmented pill. Screenshots of the open sheet are uploaded as artifacts.
 */
import { expect } from "@playwright/test";
import { checkLayout, openRoute, test } from "./fixtures";

/** Make the media element report a real play event without decoding audio. */
async function fakePlayback(page: import("@playwright/test").Page) {
    await page.addInitScript(() => {
        HTMLMediaElement.prototype.play = function () {
            this.dispatchEvent(new Event("play"));
            return Promise.resolve();
        };
        HTMLMediaElement.prototype.pause = function () {
            this.dispatchEvent(new Event("pause"));
            return Promise.resolve();
        };
    });
}

test("placeholders use the generated canonical blob paths", async ({ signedInPage }) => {
    await openRoute(signedInPage, "/");
    const shapes = signedInPage.locator("#player-bar .cover-placeholder[data-blob]");
    await expect(shapes.first()).toBeVisible();

    const paths = await signedInPage.locator("#player-bar .cover-blob path").evaluateAll(
        nodes => nodes.map(node => node.getAttribute("d") ?? ""));
    expect(paths.length).toBeGreaterThan(0);
    for (const path of paths) {
        expect(path.startsWith("M ")).toBe(true);
        expect(path.endsWith(" Z")).toBe(true);
        expect(path.length).toBeGreaterThan(40);
    }
});

test("play morphs the button into a blob and starts the progress wave", async ({ signedInPage }) => {
    await fakePlayback(signedInPage);
    await openRoute(signedInPage, "/");

    const play = signedInPage.locator("#player-bar .play-pause");
    const pausedRadius = await play.evaluate(el => getComputedStyle(el).borderRadius);
    await play.click();
    await expect(play).toHaveClass(/playing/);

    const playingRadius = await play.evaluate(el => getComputedStyle(el).borderRadius);
    expect(playingRadius).not.toBe(pausedRadius);
    expect(playingRadius).toContain("%");
    await expect(signedInPage.locator("#player-bar .seek-wave path")).toBeVisible();

    // The wave is decorative: turning playful motion off removes it.
    await signedInPage.evaluate(() => {
        document.documentElement.dataset.playful = "false";
    });
    await expect(signedInPage.locator("#player-bar .seek-wave")).toBeHidden();
});

/** Compact tiers fold the lyrics action into the More popover. */
async function openLyrics(page: import("@playwright/test").Page) {
    const more = page.locator("#player-bar .control-more");
    if (await more.isVisible()) {
        await more.click();
        await page.locator('.player-more-menu .button[title="Lyrics"]').click();
    } else {
        await page.locator("#player-bar .control-lyrics").click();
    }
}

test("Lyrics and Up next are peer tabs in one pill", async ({ signedInPage }) => {
    await signedInPage.setViewportSize({ width: 1280, height: 800 });
    await openRoute(signedInPage, "/");
    await openLyrics(signedInPage);

    const lyricsTabs = signedInPage.locator(".lyrics-panel .sheet-tabs");
    await expect(lyricsTabs).toBeVisible();
    await expect(lyricsTabs.locator('.sheet-tab[aria-pressed="true"]')).toContainText("Lyrics");
    await expect(signedInPage.locator(".lyrics-panel .sheet-actions")).toBeVisible();

    await lyricsTabs.locator(".sheet-tab", { hasText: "Up next" }).click();
    await expect(signedInPage.locator(".queue-drawer")).toBeVisible();
    await expect(
        signedInPage.locator('.queue-drawer .sheet-tab[aria-pressed="true"]'),
    ).toContainText("Up next");

    await signedInPage.locator(".queue-drawer .sheet-tab", { hasText: "Lyrics" }).click();
    await expect(signedInPage.locator(".lyrics-panel")).toBeVisible();
    await expect(signedInPage.locator(".queue-drawer")).toHaveCount(0);
});

for (const width of [800, 1024, 1280]) {
    test(`sheet screenshot at ${width}px`, async ({ signedInPage }, testInfo) => {
        await signedInPage.setViewportSize({ width, height: 800 });
        await openRoute(signedInPage, "/");
        await openLyrics(signedInPage);
        await expect(signedInPage.locator(".lyrics-panel .sheet-tabs")).toBeVisible();
        await signedInPage.screenshot({
            path: testInfo.outputPath(`playful-sheet-${width}.png`),
            fullPage: true,
        });
        await checkLayout(signedInPage, `playful sheet @ ${width}x800`);
    });
}
```
