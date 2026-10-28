"""Tests the frames: they listen to the player's arms, count a held key, clear in time a weapons flag the vehicle
restriction left set, and survive an error."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = heirloom_stubs.install()

from apex_heirloom import frame, keys, restriction  # noqa: E402

check("the frames are those of the first-person arms", frame.tick.path.endswith(
    "BPAnim_Player_1st.BPAnim_Player_1st_C:BlueprintUpdateAnimation"))
check("listened after the game's own frame", frame.tick.kind == "POST")

counted: list[float] = []
looked: list[object] = []
told: list[bool] = []
restriction.tick = looked.append
keys.tell = lambda: told.append(True)
arms = object()
keys.pending = lambda: False
keys.tick = counted.append
frame.tick(arms, None, None, None)
check("no key held, nothing is counted", counted == [])
check("each frame, a flag the vehicle restriction left set is looked at with the arms, key held or not",
      looked == [arms])
check("each frame, the keys in use may be written, once the settings a Restore changes are all set", told == [True])

keys.pending = lambda: True
frame.tick(None, None, None, None)
check("a key held is counted at the frame", len(counted) == 1)


def broken(_now: float) -> None:
    raise RuntimeError("boom")


keys.tick = broken
frame.tick(None, None, None, None)
frame.tick(None, None, None, None)
check("an error is written once, and the frame goes on",
      len(state["errors"]) == 1 and "held key not counted" in state["errors"][0])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
