# `algo/` — next-song MDL

Standalone, standard-library-only Python. Nothing outside this folder is
imported, modified, or required. Not wired into the server yet.

```bash
python -m algo.demo                 # simulated learning run
python -m algo.demo --self-test     # format + learning + persistence checks
```

## Input: one 44-bit state

```
bits  0..5   user id, plain 6-bit binary counter: 000000, 000001, ... 111111 (0..63)
bits  6..29  current song / sid: 24-bit unsigned big-endian, 1 .. 16777215
              0 is null / no song and is never a prediction output
bits 30..34  played before, 5 back:  1 = occupied, 0 = empty (oldest first)
bits 35..39  in queue, 5 forward:    1 = occupied, 0 = empty (nearest first)
bits 40..43  status flags (4 bits)
```

Status flags: `LOOP=1`, `FIRST_CLICKED=2`, `REPEAT_ONE=4`, `SHUFFLE=8`. They can
be OR-ed together (0..15).

`encoding.pack_state(user, song, played_before, in_queue, status)` builds the
integer; `unpack_state` decodes it; `state_to_bits` shows the bit string.

## Output

`NextSongMDL.predict(state)` returns one 24-bit song id (>= 1). `predict_ranked(state,
k)` returns `(song, probability)` pairs. With no data it returns `0` (null), so
wait for at least one observation before asking for a real pick. Song `0` may
be passed to `observe` as a "nothing was clicked" event; it is recorded but
never predicted.

## Learning

`model.observe(state, actual_next_song, predicted=predicted)` is called once per
click. It updates every expert and returns the reward:

| outcome | reward |
| --- | --- |
| predicted song was clicked | `+1` good |
| different song, same artist or album | `0` meh |
| different song, different artist and album | `-1` bad |

Register `song -> (artist, album)` with `set_metadata()` / `set_song_metadata()`
to enable the "meh" case. Pass `reward=` explicitly to override the automatic
scoring. Rewards also adjust each expert's decaying trust score, so a context
level that keeps being right gains influence.

Five nested experts predict in parallel: global, per-user, per-user+context
(5-back/5-forward + status), per-user+current-song, and the full state. Each is
a Dirichlet process with a uniform base over all 2^24 songs: a brand new song
costs ~24 bits, a familiar one gets cheaper every time it plays. An expert's
description length is its sequential codelength plus the MDL cost of the
contexts it has memorised. Experts are blended with weights proportional to
`2 ** -(description length + cost)`, so specificity is only paid for when the
clicks justify it. Per-user experts are what let each user's preferences
diverge from everyone else's. Codelengths are discounted by `length_decay`
(default `0.999`, ~700-click half-life) so tastes can change without the model
being stuck with what it learned at the start.

`save_json(path)` / `load_json(path)` persist everything (counts, codelengths,
trust, metadata) for later integration.
