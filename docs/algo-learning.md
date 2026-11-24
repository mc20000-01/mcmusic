# Next-song MDL: work-rate gated integration

The standalone `algo/` module is wired into the server through
`src/next_song_model.py`. It always learns; it only **chooses** once it has
proved itself. The gate is an exact-hit work rate of **76%** over at least ten
observations.

## What happens

Every successful `POST /api/plays` records a play as before, then passes the new
play to `src/next_song_model.py`. That module:

1. Reads the previous five plays for the user to form the 5-back occupancy bits.
2. Reads the last published playback queue to form the 5-forward occupancy bits.
3. Uses the previous track as the state song and the newly played track as the
   actual next song.
4. Derives status flags from repeat-one (same track twice) and an optional
   `algo_status` integer in the play payload.
5. Calls `NextSongMDL.observe(...)` and atomically saves the model to
   `data/next_song_mdl.json` under `DATA_DIR`.

Users are mapped to the model's 6-bit user code with `user_id % 64`. That is
intentional for this experimental phase: it keeps the standalone format intact
without creating a separate identity mapping.

## Earning the switch

`model.summary()["work_rate"]` is `correct / observations`. Once it reaches
`0.76` with ten or more observations, `next_song_model.is_active()` returns true
and the admin status note flips. From then on a single helper, `rank_for()`,
orders:

- `/api/home` recommendations (not the unplayed Discover list),
- `/api/radio/<id>` (which also feeds natural-end autoplay on every client),
- shuffle on web, Android and desktop through `POST /api/model/rank`,
- the Android queue rebuild/autoplay path.

A ranked pool is always followed by any unranked candidates, so no song is lost.
If the model has no ranked candidates, the existing affinity/similarity order is
the fallback. The chosen setting in the user's request was to switch **all**
next-track choices together, never one at a time.

`POST /api/model/rank` accepts `{ "current": <track id>, "ids": [...] }` and
returns `{ "active": bool, "ids": [...] }`. It is a no-op while the gate is
closed, so older clients keep their current behavior.

## Safety and operations

- Learning or ranking failures are logged and ignored; they never fail a play
  count or a queue response.
- The model snapshot is written to a temp file and atomically renamed, so a
  crash cannot truncate it.
- A corrupt snapshot is moved to `data/next_song_mdl.json.corrupt` and learning
  restarts from an empty model.
- `data/` is gitignored. The model and its backup are never published.
- Admins can inspect progress with `GET /api/admin/algo`. The response includes
  `work_rate`, `threshold`, `active`, `learning_only`, `used_for_choices`, and a
  human-readable `note`.

## Status on this host

The persisted snapshot has far more wrong/exact-miss observations than exact
hits (work rate around 3%), so `active` remains false and all next-track choices
still use the original rankings. No behavior changes until the gate is earned.
