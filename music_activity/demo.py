"""Demo player + live acceptance checks against the Rotur API.

  python -m music_activity.demo            # fake player, Rotur from env
  python -m music_activity.demo --selftest # asserts each state against /v2/status/live
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import requests

from music_activity.config import MCMUSIC_BASE, ROTUR_ACTIVITY_ID, ROTUR_TOKEN, rotur_rooms
from music_activity.manager import Manager
from music_activity.sinks.rotur import RoturSink
from music_activity.state import PlayerState, Track

TRACKS = [
    Track("demo-1", "Night Drive", "The Midnight", "Endless Summer", 245, None, f"{MCMUSIC_BASE}/"),
    Track("demo-2", "Resonance", "HOME", "Odyssey", 214, None, f"{MCMUSIC_BASE}/"),
    Track("demo-3", "Sunset Lover", "Petit Biscuit", "Presence", 238, None, None),
]


def playing(i: int = 0, position: float = 42.0, **kw) -> PlayerState:
    nxt = TRACKS[(i + 1) % len(TRACKS)]
    base = dict(playing=True, position=position, updated_at=time.time(),
                queue_index=i, queue_len=len(TRACKS), next=nxt)
    base.update(kw)
    return PlayerState(track=TRACKS[i], **base)


def scenarios():
    yield "play", playing(0)
    yield "pause", PlayerState(track=TRACKS[0], playing=False, position=42.0,
                               queue_index=0, queue_len=3, next=TRACKS[1])
    yield "resume", playing(0, 42.0)
    yield "seek", playing(0, 100.0)
    yield "track change", playing(1, 5.0)
    yield "loop one + shuffle", playing(1, 30.0, loop="one", shuffle=True)
    yield "loop all", playing(2, 12.0, loop="all", queue_index=2)
    yield "stop", PlayerState(track=None, playing=False)


def live_status() -> dict | None:
    try:
        r = requests.get(
            "https://api.rotur.dev/v2/status/live",
            params={"name": os.environ.get("ROTUR_NAME", "your-rotur-name")},
            timeout=15,
        )
        if r.status_code != 200:
            print(f"  (status read: HTTP {r.status_code})")
            return None
        return r.json()
    except requests.RequestException as exc:
        print(f"  (status read failed: {exc})")
        return None


def find_activity(status: dict | None) -> dict | None:
    for a in (status or {}).get("activities") or []:
        if a.get("id") == ROTUR_ACTIVITY_ID:
            return a
    return None


def run_demo(seconds: float = 1.2) -> int:
    if not ROTUR_TOKEN:
        print("ROTUR_TOKEN is not set; cannot publish or verify")
        return 2
    sink = RoturSink(ROTUR_TOKEN, rotur_rooms())
    manager = Manager([sink], debounce=0.1, log=print)
    sink.connect()
    failures = 0
    try:
        for i, (label, state) in enumerate(scenarios()):
            print(f"→ {label}")
            manager.on_event(state)
            time.sleep(seconds)
            if label in ("stop",):
                continue
            act = find_activity(live_status())
            if not act:
                print("  FAIL: no mcmusic activity on the account")
                failures += 1
                continue
            media = act.get("media") or {}
            # The server normalises omitted timestamps to 0, so 0/0 means "no bar".
            has_times = bool(media.get("start")) and bool(media.get("end"))
            expected_times = state.playing and state.track is not None and state.track.duration > 0
            if has_times != expected_times:
                print(f"  FAIL: start/end present={has_times}, expected={expected_times}")
                failures += 1
            if state.playing and has_times:
                drift = abs(media["start"] - state.start_ms) / 1000
                if drift > 3:
                    print(f"  FAIL: start drift {drift:.1f}s")
                    failures += 1
            if state.track and media.get("title") != state.track.title:
                print(f"  FAIL: media.title={media.get('title')!r}")
                failures += 1
            if state.loop == "one" and "One" not in (act.get("status") or ""):
                print("  FAIL: loop=one missing from status")
                failures += 1
            if state.shuffle and "🔀" not in (act.get("status") or ""):
                print("  FAIL: shuffle missing from status")
                failures += 1
            player = act.get("player") or {}
            if player.get("loop") != state.loop or player.get("queue_len") != state.queue_len:
                print(f"  FAIL: player block {player}")
                failures += 1
            print(f"  ok: {act.get('status')!r}")

        # stop removes it
        print("→ verifying removal")
        time.sleep(1.5)
        if find_activity(live_status()):
            print("  FAIL: activity still present after stop")
            failures += 1
        else:
            print("  ok: activity removed")
    finally:
        manager.close()
        time.sleep(1.5)
        remaining = find_activity(live_status())
        print("→ socket closed:", "activity gone" if not remaining else "FAIL activity still present")
        if remaining:
            failures += 1
    print(f"\n{'PASS' if failures == 0 else 'FAIL'} ({failures} failed checks)")
    return 0 if failures == 0 else 1


def run_player(seconds: float = 4.0) -> int:
    sink = RoturSink(ROTUR_TOKEN, rotur_rooms())
    manager = Manager([sink], debounce=0.5, log=print)
    sink.connect()
    try:
        for i in range(60):
            state = playing(i % len(TRACKS), position=20 + i * 5, loop="all" if i % 2 else "off")
            manager.on_event(state)
            time.sleep(seconds)
    except KeyboardInterrupt:
        pass
    finally:
        manager.close()
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--seconds", type=float, default=1.2)
    args = ap.parse_args(argv)
    if args.selftest:
        return run_demo(args.seconds)
    return run_player(max(args.seconds, 1.0))


if __name__ == "__main__":
    sys.exit(main())
