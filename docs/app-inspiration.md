# What we borrowed, and what we deliberately left

Three open-source Android players were read for this pass — SimpMusic,
MusicBobber, and Echo Music. They are good at things we are not, and they are
also trying to be something we are not: a YouTube client, a floating widget, a
"smart" recommender. This note records the difference so a future pass doesn't
re-litigate it.

**Rule for everything below: inspiration, not copy.** No source code, strings,
drawables, layouts, or assets were lifted. What follows is a list of *behaviours*
that were worth rethinking in our own idiom, and a list of behaviours that
actively fight what mcmusic is.

| Project | License | What it is |
| --- | --- | --- |
| [SimpMusic](https://github.com/maxrave-dev/SimpMusic) | GPL-3.0 | YouTube Music client, Compose Multiplatform |
| [MusicBobber](https://github.com/Cleveroad/MusicBobber) | MIT | Floating audio widget library (not a player) |
| [Echo Music](https://github.com/Davarco/Echo-Music-Player) | GPL-3.0 | Local-file player with EQ and smart playlists |

---

## SimpMusic

The closest thing to a peer: Compose, a real queue, lyrics, offline. Its player
offers three visual styles, which is a nice idea and also a warning — three
styles is three sets of bugs.

**Taken, reshaped**

- **The player is more than the transport.** SimpMusic treats artwork, lyrics
  and queue as views of one surface rather than separate destinations. We did
  the cheap version of that: `LyricsSheet.kt` and the queue sheet both open *over*
  the player, so the track never disappears while you read or reorder.
- **A line-level synced lyrics sheet that highlights the current line and
  scrolls with a little lead-in.** Ours parses LRC on the device from the text
  the server already stores (`LRC` → `LyricLine`, `activeLine` binary search),
  pretty-prints the rest, and fades the top and bottom edges instead of
  clipping them.
- **A sleep timer that is a first-class control, not a settings row.**
  `PlaybackEngine.setSleep` counts down in minutes, the deck shows the remaining
  time, and the sheet offers 15/30/60 plus "turn it off". It pauses; it does not
  kill the app.
- **Shuffle and repeat as states you can *see*.** A small `ModeStrip` under the
  transport spells out "Shuffle on · Repeat one", so the tinted icons don't have
  to carry the whole meaning.

**Considered, not taken (yet)**

- **Swipe the artwork to skip.** Lovely gesture, but the artwork is already the
  tap target that opens and closes the player, and the sheets drag. Deferred
  until there is a design that doesn't make one surface mean three things.
- **Word-by-word lyrics.** Our provider (LRCLIB) and our DB store line-level LRC.
  Word timing would mean a second lyrics backend, and a worse one for a
  self-hosted library.
- **Crossfade / gapless.** Needs two player instances or a concatenating media
  source. Worth doing later; not worth half-doing now.
- **A real 10-band EQ.** See Echo, below.
- **Android Auto, home-screen widgets, Discord RPC.** Real wins, separate
  projects. Noted in `docs/roadmap.md`.

**Rejected on principle**

- **Home / Charts / Podcasts / Moods.** A discovery feed is the thing mcmusic
  exists to not have. "No feed. No algorithm. Only the records you put here." is
  a promise, not marketing.
- **Listening analytics and a yearly "Wrapped".** Same reason.
- **Cast/output picker.** We solve this differently and more simply: the server
  allows one active speaker, and taking over is an explicit "Play here".
- **Synced group listening ("Listen Together").** Our room link is *presence*,
  not a shared clock. Async handoff is honest and doesn't drift.

---

## MusicBobber

A library, not a player. Its one contribution is an always-on-top audio widget
that can be dragged around and dismissed by throwing it at a target.

**Taken, reshaped**

- **A player that collapses rather than closes.** Our deck is the small, always
  present form of the player; the full overlay is the expanded form. Same track,
  two sizes, no navigation.
- **Haptics as confirmation, not decoration.** Every transport press ticks
  (`HapticFeedbackType.LongPress` in `NowPlaying.kt`), and destructive gestures —
  long-press to remove a track from the queue — tick *and* say what happened
  ("Removed …") so the removal is reversible in the user's head.
- **The drag-away-to-dismiss idea.** Expressed as the sheet drag handle rather
  than a floating bubble.

**Rejected**

- **`SYSTEM_ALERT_WINDOW` overlay.** Drawing over other apps is a permission
  people are right to be suspicious of, it costs battery, and it competes with
  the system media notification that already works.
- **Permanent floating bubble.** For a music app the notification and the lock
  screen are the correct surfaces. One place for controls, not three.

---

## Echo Music

An older, local-file player. Its selling points are EQ presets and "AI" smart
playlists.

**Taken, reshaped**

- **Search that filters as you type**, rather than a submit-and-wait search
  screen.
- **A queue you can actually control.** Remove by long-press, reorder by tapping
  a track to pull it to the front of "up next".
- **Notification controls.** Ours go through a real platform `MediaSession` in
  `PlaybackService.kt`, which is also what gives us lock-screen controls and the
  headphone buttons for free.

**Rejected**

- **The equalizer.** A visualizer is honest: it reacts to playback and costs
  nothing. A DSP EQ is per-device, per-output, and usually makes a phone speaker
  worse. We show the shape of the sound; we don't pretend to master it.
- **"Smart playlists" from listening habits and AI.** This is the algorithm under
  another name. Related tracks and radio already exist and are explicit.
- **Built-in sharing of audio files.** Files leave through the download button,
  not a share sheet that quietly re-uploads someone's library.

---

## Net effect on this pass

| Change | File |
| --- | --- |
| Animated equalizer strip, held low when paused | `ui/NowPlaying.kt` (`Equalizer`) |
| Shuffle / repeat / sleep spelled out under the transport | `ui/NowPlaying.kt` (`ModeStrip`) |
| Haptics on transport, like, queue, playlist, and queue removal | `ui/NowPlaying.kt`, `ui/Shell.kt` |
| Long-press "Up next" row to remove, with a toast | `ui/NowPlaying.kt` |
| Synced LRC lyrics sheet with soft edges and auto-scroll | `ui/LyricsSheet.kt` |
| Sleep timer with a live countdown in the deck | `play/PlaybackEngine.kt`, `ui/Shell.kt` (`SleepSheet`) |

Everything here is written from scratch against our own theme tokens
(`ui/theme/Theme.kt`), our own icon geometry (`ui/AppIcons.kt`, sourced from
`lucide-static`), and our own copy. If a screenshot of mcmusic could be mistaken
for a screenshot of one of these apps, the borrow went too far.
