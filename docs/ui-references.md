# UI/library research shortlist

These are the repositories and packages worth reusing or studying while making
the web, Android and desktop clients better. They are references only: nothing
here is vendored automatically, and none of them replaces the native
Kotlin/Compose Android client or the Preact web client.

## Direct upstream references

- **flufi-music/client** — <https://git.flufi.uk/flufi-music/client>
  The upstream TypeScript/Preact v3 web client that `ui/` was forked from. The
  Forgejo instance returned 502 during this pass, but the mirror below is
  readable and is the best source for design/behavior comparison.
- **Andrew/flufimusic-client (Rotur mirror)** —
  <https://git.rotur.dev/Andrew/flufimusic-client>
  Built copy of the upstream client, useful for checking component structure,
  CSS variables and routes when the main forge is unavailable.
- **`old/` snapshot in this repo** — commit
  `581b995f7a5a510d936d022af52e2e8b638d0908`.
  Still the authority for features that existed before the `ui/` rewrite:
  queue snapshots, autoplay radio, keyboard shortcuts, Rotur activity and the
  richer settings/admin surfaces.

## Web client (Preact + TypeScript)

- **lucide-preact** — <https://github.com/lucide-icons/lucide/tree/main/packages/lucide-preact>
  Already in `ui/package.json`. Keep using it for every icon; no emoji/unicode
  glyphs or hand-written inline SVG.
- **flufi-ui** — <https://www.npmjs.com/package/flufi-ui>
  Already declared in `ui/package.json`. Search results show it is intended to
  pair with lucide icons. Worth auditing locally before widening its use: it
  may already provide the exact v3 tokens/components the redesign targets.
- **@preact/signals** — <https://github.com/preactjs/signals>
  Already used by `common/player.ts`; the right place to keep queue/session
  state instead of adding another state manager.
- **idb-keyval / Workbox** — useful optional additions for offline queue
  snapshots and service-worker caching if `ui/src/common/idb.ts` needs a
  companion. The repo already has `web/sw.js`, so prefer extending that before
  adding a dependency.
- **PreactHub curated list** — <https://preacthub.com/libraries?q=ui>
  Good catalog when looking for small, Preact-compatible components.

## Android (native Kotlin/Compose)

- **Coil 3** — <https://github.com/coil-kt/coil>
  `io.coil-kt.coil3:coil-compose` + `coil-network-okhttp` for cached artwork.
  Strong fit for covers/avatars; keeps image work off the main thread and
  respects R8.
- **ComposeReorderable** — <https://github.com/aclassen/ComposeReorderable>
  `org.burnoutcrew.composereorderable:reorderable`. Supports LazyColumn drag
  handles, which is the most direct way to finish the queue-reorder task.
  Occurrence-aware keys (`trackId + index`) still matter so duplicates do not
  collapse.
- **Official Compose Material 3** — <https://developer.android.com/jetpack/androidx/releases/compose-material3>
  Stay with the official component set. The five swatch-derived palette
  families are expressed through `MaterialTheme` colours/shapes; a bare family
  id follows the device appearance via `isSystemInDarkTheme()`. Do not add a
  second Material library.
- **Kindling** — <https://github.com/ClementBobin/Kindling>
  shadcn/ui-inspired Material 3 components, typed navigation and ViewModels.
  Interesting as a reference for structure, but avoid adopting a whole new
  navigation layer while the current app is being stabilized.
- **Lucide Android assets** — <https://github.com/lucide-icons/lucide>
  Continue generating the existing `ic_lucide_*.xml` drawables from Lucide's
  path data so Android icons stay consistent with `lucide-preact` on web.

## Desktop (PySide6 / Qt)

- **PySide6 / Qt 6** — <https://doc.qt.io/qtforpython-6/>
  Already used by `app/linux/mcmusic_linux`. Qt Widgets plus QtMultimedia is
  the right native path; do not replace it with a web wrapper.
- **Lucide static assets** — the desktop client already mirrors Lucide icon
  geometry from the web tokens; keep that shared language when adding screens.

## How to use this list

1. Prefer the `old/` snapshot for *behavior parity* (what the feature did).
2. Prefer the flufi upstream/mirror for *visual parity* (how v3 looks).
3. Add a third-party dependency only when it removes real hand-written code
   (Coil for images, ComposeReorderable for drag) and does not weaken the
   signed-release, Android 14+ or offline constraints.
