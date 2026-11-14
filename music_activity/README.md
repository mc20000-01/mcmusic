# music_activity

Publishes mcmusic's now-playing state as a live Rotur activity and (optionally)
a Discord Rich Presence. Rotur is the sink that originChats can see.

```
music_activity/
  state.py        # Track / PlayerState + shared text formatting
  manager.py      # 500 ms debounce, fan-out, per-sink error isolation
  sinks/base.py   # Sink protocol, backoff
  sinks/rotur.py  # status websocket, one long-lived connection
  sinks/discord.py# local Discord IPC, 15 s minimum interval
  config.py       # env only; never prints ROTUR_TOKEN
  demo.py         # fake player + live acceptance checks
  bridge.py       # watches the mcmusic playback table
```

## Install

```bash
.venv/bin/pip install websockets pypresence
```

Config (env):

| Variable | Meaning |
| --- | --- |
| `ROTUR_TOKEN` | Rotur **sub-token** with `account:profile` (never the password) |
| `ROTUR_ROOMS` | comma separated rooms, default `originChats` |
| `ROTUR_ACTIVITY_ID` | activity id, default `mcmusic` |
| `DISCORD_APP_ID` | Discord application id (local IPC only) |
| `MCMUSIC_BASE` | public server, default `https://mcmusic.sdisk.us` |
| `MCMUSIC_USER_ID` | account whose playback `bridge.py` watches |
| `DATA_DIR` | where `mcmusic.db` lives (default `<repo>/data`) |

## Run

```bash
# fake player, publishes while it runs
ROTUR_TOKEN=... .venv/bin/python -m music_activity.demo

# automated acceptance checks against the live API
ROTUR_TOKEN=... .venv/bin/python -m music_activity.demo --selftest

# real server state (run beside the Flask service)
MCMUSIC_USER_ID=1 ROTUR_TOKEN=... .venv/bin/python -m music_activity.bridge
```

`bridge.py` polls `playback` every 2 s, detects track/play/seek/queue changes and
feeds the manager. It does not import Flask and only reads the sqlite database.

## What was verified (2026-11-09, live account)

Run: `.venv/bin/python -m music_activity.demo --selftest` → **PASS (0 failed checks)**.

- `wss://api.rotur.dev/v2/status/ws`: `auth` → `ready` in under 15 s, `join`
  → `join_ok` for `originChats`.
- `add_activity` with the fixed id: play/pause/resume/seek/track change/loop/
  shuffle/queue all visible through
  `GET https://api.rotur.dev/v2/status/live?name=your-rotur-name`.
- `media.start` / `media.end` are Unix **milliseconds** and match the expected
  position within 3 s; seek moves them.
- Pause: the payload omits the timestamps, but **Rotur normalises them to
  `0`/`0` rather than removing the keys**. Treat `start == 0` as "no timer".
- The custom `player` block (`playing`, `loop`, `shuffle`, `queue_index`,
  `queue_len`, `next`) is stored and returned unchanged.
- `remove_activity` removes it immediately; closing the socket also makes the
  activity disappear (`stop` and process exit both tested).
- Status strings: `🔂 One · 🔀 · 2/3 · ▰▱▱▱▱▱▱▱ 0:30/3:34`.

Not verified: a forced socket drop/reconnect (the sink reconnects with backoff
and resends the last state, but the network failure was not simulated), a dead
sink while others continue (the manager isolates exceptions, not exercised), and
any Discord IPC behaviour (see below).

## originChats

Checked against the client source (`git.rotur.dev/originChats/client`, cloned
`main` on 2026-11-09):

- Activities are rendered. `src/pages/chat/dms/DMHomeTab/components.tsx` imports
  `ActivityCard` from `@rotur/ui/status` and renders one per activity; the
  profile card passes `activities` into the profile body. They show on profile
  and DM-home surfaces, **not as chat messages**.
- The client's status socket joins `originChats:<serverUrl>` per server
  (`src/net/status.ts`, `joinServerRoom`). To be visible on a specific
  originChats server, include that room:
  `ROTUR_ROOMS=originChats,originChats:originchats.com`.
- Markdown: the client has its own message renderer (`src/lib/render/render.ts`,
  `parseMessageTokens`) and embeds render through it, so a markdown status
  message is supported if a text fallback is ever needed. Not UI-tested.
- The `@rotur/ui` package itself could not be fetched here (`npm pack` produced
  nothing), so which fields `ActivityCard` draws — e.g. whether it uses
  `media.start/end` for a progress bar — is unverified. The `player` block is a
  pass-through for clients like GlassMod, built-in clients ignore it.

## originChats room + text fallback

Set `ORIGINCHATS_SERVER=originchats.com` to append
`originChats:originchats.com` to the joined Rotur rooms (verified live:
`joined originChats, originChats:originchats.com`). That is the room the
client's members are in, so they can see the activity.

If activities turn out not to render for someone, the text fallback posts a
single message and edits it in place using the same REST contract as
`src/originchats.py`:

```bash
ORIGINCHATS_BASE=https://chat.example.com/api \
ORIGINCHATS_TOKEN=... ORIGINCHATS_CHANNEL=... \
MCMUSIC_USER_ID=1 ROTUR_TOKEN=... .venv/bin/python -m music_activity.bridge
```

The message id is persisted in `data/music_activity_originchats.json`; a restart
edits the same message, and a 404 posts one replacement. Verified with a fake
transport (POST → PATCH same id, 404 → one new POST) and the rendered markdown
(`**Title** — Artist` plus the progress line). **It is inert on this host:**
`ORIGINCHATS_BASE`/`TOKEN`/`CHANNEL` are not in `mcmusic.env`, so the sink is
skipped until those are set.

## Discord

`pypresence 4.6.2` is installed; `Presence.update()` accepts `activity_type`,
`start`, `end` and `ActivityType.LISTENING` exists (value 2). The sink uses it,
falls back to a plain "Playing" presence if the field is rejected, throttles to
one update per 15 s, and retries every 30 s when Discord is not running.

**Not verified visually:** this host has no Discord desktop client, so the
Listening type, the elapsed-time bar and the uploaded art assets were not seen in
the UI. The code path is exercised only up to the IPC call. Discord must run on
the same machine as the script; it cannot work from the server.
