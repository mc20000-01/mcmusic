# mcmusic desktop (Linux)

A **native Linux client** for the mcmusic server, written with Qt 6 Widgets and
PySide6. It is not the web app in a window: there is no QWebEngine, no HTML and
no embedded website. Every control is drawn by Qt, using the same design tokens
(`web/css/variables.css`) and the same Lucide icon geometry (`web/js/icons.js`)
as the browser and Android builds.

Two front ends ship from one package: the Qt window (the default) and a
terminal client (`--tui`). The terminal client needs no display, no Qt and no
third-party packages, so the same server is reachable over SSH on a headless
box.

New to mcmusic? The [self-hosting guide](../../docs/selfhost.md) covers server
setup, HTTPS and connecting this desktop client.

```
┌─────────────┬───────────────────────────────────────────────┐
│  mcmusic    │  ←  search                    queue   user   │
│  Home       ├───────────────────────────────────────────────┤
│  Search     │                                               │
│  Library    │   content: home / library / album / artist    │
│             │   playlists / requests / settings / admin     │
│  YOUR LISTS │                                               │
│  Liked      │                                               │
│  Playlists  │                                               │
│  Requests   │                                               │
│  …lists…    ├───────────────────────────────────────────────┤
│  Settings   │  art  title / artist   ⏮  ▶  ⏭   queue  vol  │
└─────────────┴───────────────────────────────────────────────┘
```

## Works across Linux desktops

* Qt 6 runs on **Wayland and X11**, including KDE Plasma, GNOME, Hyprland,
  sway/wlroots, XFCE, Cinnamon and bare window managers.
* The app forces Qt's **Fusion** style and installs its own palette, so buttons,
  menus, inputs and dialogs keep the mcmusic look under every desktop instead
  of picking up Breeze/Adwaita chrome.
* All painting is DPI-aware vector/QPainter work; icons stay crisp on HiDPI and
  fractional scaling.
* **MPRIS2** media controls are exported when a session bus is available, so
  KDE's media applet, GNOME's media menu, Waybar, `playerctl` and media keys
  work. Without a bus the app runs normally, just without that integration.
* Audio uses QtMultimedia's FFmpeg backend with PipeWire/PulseAudio output.

## Features

* Password / invite login against the same session API as the web player.
* Home shelves (recommendations, recently added, top tracks, YouTube likes),
  album shelf and quick album browsing.
* Library tabs for songs, albums and artists; album/artist detail pages with
  play, shuffle and radio.
* Search across songs, albums and artists.
* Liked songs, playlist grid, playlist detail, create/rename/delete, add/remove
  tracks, and a rail list of your playlists.
* Track menus: play next, add to queue, add to playlist, radio, go to album /
  artist, like, track info, remove from playlist, admin explicit toggle.
* Player deck with queue drawer, full now-playing view, seek, volume/mute,
  shuffle, repeat (off/all/one), next/prev and "up next".
* Download requests with admin approve/reject; admin stats, user admin toggles
  and library rescan.
* Settings: 5 palettes (dusk, paper, ink, tide, copper), accent overrides,
  density, cover art, autoplay, hide explicit, YouTube stats, remembered volume,
  prefetch and offline audio cache.
* Playback is prefetched and cached on disk, so tracks resume instantly and the
  session cookie is never placed in a media URL.
* Publishes device heartbeats and playback state to the server (same endpoints
  as the Android client) for cross-device awareness.

## Install

Requires Python 3.10+ and a normal desktop session (for audio: PipeWire or
PulseAudio). The full `PySide6` package is required — `PySide6-Essentials` does
not include QtMultimedia.

### Quick start from a checkout

```bash
cd app/linux
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./mcmusic-desktop
```

or run the module directly:

```bash
.venv/bin/python -m mcmusic_linux
```

The terminal client runs from the same checkout with the system Python — it is
standard library only:

```bash
python3 -m mcmusic_linux --tui
./mcmusic-desktop --tui          # same thing, no flags means the Qt window
./mcmusic-desktop --help         # front-end flags
```

### Install for the application menu

```bash
cd app/linux
./install.sh
```

This creates `.venv`, installs the package, and writes
`~/.local/share/applications/mcmusic.desktop` plus the scalable icon. Launch
* mcmusic* from your app menu afterwards.

### Pointing at a server

The default is `http://127.0.0.1:8000`. Set it on the login card, or later in
**Settings → Account → Server**. `http://`, `https://` and bare `host:port`
forms are accepted.

## Terminal client (`--tui`)

`--tui` starts a curses front end that talks to the same `/api` endpoints as
the other clients and keeps its own config at `~/.config/mcmusic/tui.json`, so
it never rewrites the Qt client's QSettings. Audio is played by an external
process: **mpv** when installed (pause, volume and track changes through its
IPC socket), otherwise **ffplay** (playback only). With neither, everything
except audio output still works.

The same front end manages playlists (create, rename, delete, add and remove
tracks), submits and moderates YouTube download requests, and shows the admin
dashboard with stats, users and a library rescan. Playback state is published
to the server so bots, the dashboard and other devices see the terminal
session.

```
 mcmusic  Library                     mala · http://127.0.0.1:8000
 1 Home  2 Library  3 Albums  4 Artists  5 Liked  6 Playlists  7 Queue
 ▶ Midnight City                     M83 · 4:03            ♥
   Outro                             M83 · 4:07
 ▶ Midnight City — M83   vol 70%
```

| Key | Action |
| --- | --- |
| `1`–`8` | Home, Library, Albums, Artists, Liked, Playlists, Queue, Requests |
| `9` | Admin dashboard (admins only) |
| `↑` `↓` / `j` `k` | Move |
| `Enter` | Play, or open an album / artist / playlist |
| `space` | Pause or resume (mpv) |
| `n` / `p` | Next / previous track |
| `l` | Like or unlike |
| `a` | Append the selection to the queue |
| `r` | Start radio from the selection |
| `c` | Clear the queue |
| `N` | New playlist (Playlists) or new download request (Requests) |
| `A` | Add the selection to a playlist |
| `R` / `d` | Rename / delete the selected playlist |
| `x` | Remove a playlist track, or reject a request |
| `y` | Approve a pending request (admin) |
| `t` / `s` | Toggle admin for a user / rescan the library (admin) |
| `/` | Search the library |
| `Esc` | Back (or quit from the sign-in card) |
| `+` / `-` | Volume |
| `S` / `u` | Change server or account / sign out |
| `?` | Key help |
| `q` | Quit |

Transcoded audio is cached under `~/.cache/mcmusic/tui-audio/` and trimmed to
the 300 most recent tracks. On first run the terminal client adopts the server
address saved by the Qt client, then asks you to sign in.

## Keyboard

| Shortcut | Action |
| --- | --- |
| `Ctrl+F` | Focus search |
| `Ctrl+Space` | Play / pause |
| `Ctrl+←` / `Ctrl+→` | Previous / next track |
| `Ctrl+M` | Mute |
| `Ctrl+↑` / `Ctrl+↓` | Volume up / down |
| `Alt+←` | Back |
| `Esc` | Close queue / now-playing overlay |

Media keys work through MPRIS when your desktop routes them.

## Where things live

| Path | Contents |
| --- | --- |
| `~/.config/mcmusic/mcmusic-desktop.conf` | server URL, session cookie, cached account, theme, volume |
| `~/.cache/mcmusic/audio/` | streamed audio cache used by the player |
| `mcmusic_linux/cli.py` | front-end dispatch: Qt window by default, `--tui` for the terminal |
| `mcmusic_linux/tui.py` | standard-library curses client used by `--tui` |
| `~/.config/mcmusic/tui.json` | terminal client server, session cookie, volume |
| `~/.cache/mcmusic/tui-audio/` | audio cache used by the terminal client |
| `mcmusic_linux/api.py` | HTTP client, cookie persistence, background runner, endpoint map |
| `mcmusic_linux/models.py` | typed API payloads (`database.track_dict` contract) |
| `mcmusic_linux/theme.py` | palette tokens, typography, QSS, Qt palette |
| `mcmusic_linux/icons.py` | the exact web Lucide paths rendered through QtSvg |
| `mcmusic_linux/widgets.py` | painted buttons, rows, tiles, shelves, sheets, toasts |
| `mcmusic_linux/player.py` | queue, shuffle/repeat, prefetch, cache, QtMultimedia |
| `mcmusic_linux/mpris.py` | MPRIS2 D-Bus service |
| `mcmusic_linux/screens.py` | home, search, library, collections, likes, playlists, requests, settings, admin |
| `mcmusic_linux/shell.py` | rail, masthead, deck, queue drawer, now-playing, menus |
| `mcmusic_linux/login.py` | splash and login/register card |

## Tests

The Linux client has integration suites that start a real server on a free port
with a throwaway `DATA_DIR` and `MUSIC_DIR`, sign in, and drive the routes the
clients use — playlists, requests, admin, settings, streaming and the playback
registry. `tests/test_terminal_client.py` covers the TUI's HTTP client (standard
library only); `tests/test_qt_client.py` covers the Qt `Api`/`Repo`/`Async`
layer and `tests/test_qt_ui.py` boots the real window on Qt's offscreen
platform and visits every screen. Both skip themselves when PySide6 is absent:

    .venv/bin/python -m unittest discover -s tests -v

Nothing they do touches the running instance, and the downloader is replaced
with a stub, so approving a request never reaches YouTube.

## Troubleshooting

* **`ModuleNotFoundError: PySide6.QtMultimedia`** — install the full package:
  `pip install PySide6` (not `PySide6-Essentials`).
* **No sound** — confirm PipeWire or PulseAudio is running and the session bus
  is available to the app. QtMultimedia can also report the selected backend via
  `QT_DEBUG_PLUGINS=1`.
* **App uses the wrong display backend** — force one with
  `QT_QPA_PLATFORM=wayland` or `QT_QPA_PLATFORM=xcb`.
* **MPRIS check** — `playerctl -l` should list `mcmusic` while the app is open.
* **`--tui` has no sound** — install `mpv` (full controls) or `ffplay`. The
  terminal client plays through an external process so it stays dependency-free.
* **`--tui` starts without PySide6** — expected: that mode is standard library
  only and never imports Qt.
* **RoturLink** — linking is an OAuth browser flow. The desktop app opens the
  server's authorize URL in your browser and shows the resulting link status;
  password/invite login stays inside the app.

## Notes on parity

The desktop client deliberately follows the same contracts as the other
clients: `/api/login`, `/api/home`, `/api/playlists/...`, `/api/requests/...`,
`/api/settings`, `/api/devices/heartbeat`, `/api/playback`, and the same
`track_dict` payloads and error strings. Theme keys, accent behaviour and
density names match `web/css/variables.css` and the Android `Settings` class, so
a theme picked on one client renders the same everywhere.
