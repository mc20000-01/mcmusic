# Next-song MDL: learning-only integration

The standalone `algo/` module is now wired into the server, but **only to
learn**. It does not choose or reorder songs, does not affect radio, shuffle,
autoplay, or queue extension, and its output is never sent to a client.

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

The internal `predict()` call is used only to score the click as exact / same
artist or album / wrong, which is required for learning. Its result is
discarded.

Users are mapped to the model's 6-bit user code with `user_id % 64`. That is
intentional for this experimental phase: it keeps the standalone format intact
without creating a separate identity mapping. Large installations with more
than 64 users will see code collisions until a real mapping is added.

## Safety and operations

- Learning failures are logged and ignored; they never fail a play count.
- The model snapshot is written to a temp file and atomically renamed, so a
  crash cannot truncate it.
- A corrupt snapshot is moved to `data/next_song_mdl.json.corrupt` and learning
  restarts from an empty model.
- `data/` is gitignored. The model and its backup are never published.
- Admins can inspect progress with `GET /api/admin/algo`. The response includes
  observation counts, reward totals, per-expert costs, `learning_only: true`,
  and `used_for_choices: false`.

## Explicitly not done yet

- No endpoint returns a prediction to web, Android or desktop.
- `/api/radio/<id>` still uses the existing recommendation path.
- Queue-end autoplay still uses `/api/radio/<id>` only.
- No client sends `algo_status` today; the field is accepted for future use.
