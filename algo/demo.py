"""Runnable simulation / smoke test for the next-song MDL model.

    python -m algo.demo                 # 3000 simulated clicks
    python -m algo.demo --rounds 6000   # longer run
    python -m algo.demo --self-test     # assertions only, no progress output
"""

from __future__ import annotations

import argparse
import random

from .encoding import STATUS_FLAGS, pack_state, state_to_bits, unpack_state
from .mdl import NextSongMDL

USERS = 6
SONGS = 16


def _profiles(rng: random.Random) -> list[list[float]]:
    """Give each of the six users a distinct favourite set of songs."""
    profiles = []
    for user in range(USERS):
        weights = [0.15 if song % USERS == user else 0.01 for song in range(SONGS)]
        profiles.append(weights)
    return profiles


def simulate(rounds: int, seed: int = 12345, quiet: bool = False) -> dict:
    rng = random.Random(seed)
    profiles = _profiles(rng)
    model = NextSongMDL()
    window = 300
    buckets: list[list[int]] = []
    current_bucket: list[int] = []

    for step in range(rounds):
        user = rng.randrange(USERS)
        song = rng.choices(range(1, SONGS + 1), weights=profiles[user])[0]
        actual = rng.choices(range(1, SONGS + 1), weights=profiles[user])[0]
        played = tuple(rng.randrange(2) for _ in range(5))
        queued = tuple(rng.randrange(2) for _ in range(5))
        status = STATUS_FLAGS["LOOP"] if song == actual else 0
        state = pack_state(user, song, played, queued, status)

        predicted = model.predict(state)
        reward = model.observe(state, actual, predicted=predicted)
        current_bucket.append(reward > 0)

        if len(current_bucket) == window:
            buckets.append(current_bucket)
            current_bucket = []
            if not quiet:
                acc = sum(buckets[-1]) / window
                print(f"clicks {(step + 1):5d}  exact-hit rate {acc:.1%}")

    if not quiet:
        summary = model.summary()
        print("\nfinal expert costs / trust:")
        for expert in summary["experts"]:
            print(
                f"  {expert['name']:14s} contexts={expert['contexts']:4d} "
                f"bits={expert['codelength_bits']:9.1f} trust={expert['trust']:6.2f}"
            )
        print(f"\noverall exact-hit rate: {model.stats['correct'] / max(1, rounds):.1%}")

    return {
        "model": model,
        "windows": [sum(b) / len(b) for b in buckets],
        "summary": model.summary(),
    }


def self_test() -> None:
    # bit layout: user 0 is 000000, user 1 is 000001, plain binary counter
    state = pack_state(0, 0xABCDEF, (1, 0, 1, 0, 1), (0, 1, 0, 1, 0), STATUS_FLAGS["LOOP"])
    bits = state_to_bits(state)
    assert bits[:6] == "000000", bits[:6]
    assert bits[6:30] == format(0xABCDEF, "024b")
    assert bits[30:35] == "10101"
    assert bits[35:40] == "01010"
    assert bits[40:] == format(STATUS_FLAGS["LOOP"], "04b")
    assert unpack_state(state) == {
        "user": 0,
        "song": 0xABCDEF,
        "played_before": (1, 0, 1, 0, 1),
        "in_queue": (0, 1, 0, 1, 0),
        "status": STATUS_FLAGS["LOOP"],
    }
    assert state_to_bits(pack_state(1, 1))[:6] == "000001"
    assert state_to_bits(pack_state(5, 1))[:6] == "000101"
    assert state_to_bits(pack_state(63, 1))[:6] == "111111"
    try:
        pack_state(0, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("song 0 must be rejected as a state song id")

    result = simulate(3000, quiet=True)
    assert len(result["windows"]) >= 5, "not enough windows to judge learning"
    early = sum(result["windows"][:3]) / 3
    late = sum(result["windows"][-3:]) / 3
    assert late > early + 0.05, f"model did not learn: {early:.3f} -> {late:.3f}"

    # round-trip persistence and the "meh" reward
    model = result["model"]
    model.set_metadata({1: ("artist-a", "album-x"), 2: ("artist-a", "album-y")})
    assert model.reward(1, 2) == 0.0
    assert model.reward(1, 3) == -1.0
    assert model.reward(1, 1) == 1.0
    model.save_json("/tmp/opencode/mdl-selftest.json")
    loaded = NextSongMDL.load_json("/tmp/opencode/mdl-selftest.json")
    assert loaded.to_dict() == model.to_dict()

    print(f"self-test OK: hit rate {early:.1%} -> {late:.1%}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        simulate(args.rounds, args.seed)


if __name__ == "__main__":
    main()
