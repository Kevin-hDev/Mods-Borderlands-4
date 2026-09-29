"""Tests the climbing watch: a ladder, a ledge and Apex Movement's wall climb are told apart from walking and from
Apex Grapple's montage; an unreadable field counts as not climbing and is said once, not at every frame."""

import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()
from apex_heirloom import apex_climb_watch as watch  # noqa: E402

fails: list[str] = []
said: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def movement(climbable=None, mantle: int = -1) -> types.SimpleNamespace:
    return types.SimpleNamespace(LadderState=types.SimpleNamespace(CurrentClimbable=climbable),
                                 ReplicatedMantleState=types.SimpleNamespace(ActionIndex=mantle))


def montage(animation: str | None) -> types.SimpleNamespace:
    played = None if animation is None else types.SimpleNamespace(Name=animation)
    segment = types.SimpleNamespace(AnimReference=played)
    return types.SimpleNamespace(SlotAnimTracks=[types.SimpleNamespace(
        AnimTrack=types.SimpleNamespace(AnimSegments=[segment]))])


def arms(playing=None) -> types.SimpleNamespace:
    return types.SimpleNamespace(GetCurrentActiveMontage=lambda: playing)


check("walking: not climbing", watch.climbing(movement(), arms(), said.append) == "")
check("on a ladder or a game climbing wall", watch.climbing(movement(climbable=object()), arms(), said.append)
      == watch.LADDER)
check("over a ledge", watch.climbing(movement(mantle=0), arms(), said.append) == watch.LEDGE)
check("in Apex Movement's wall climb",
      watch.climbing(movement(), arms(montage("AS_Wall_Climb_U")), said.append) == watch.WALL)
check("Apex Grapple's montage is no climb", watch.climbing(movement(), arms(montage("AS_Grapple")), said.append) == "")
check("a montage without animation is no climb", watch.climbing(movement(), arms(montage(None)), said.append) == "")
check("nothing unreadable, nothing said", said == [])

broken = types.SimpleNamespace(ReplicatedMantleState=types.SimpleNamespace(ActionIndex=-1))
check("a ladder field that cannot be read counts as no ladder", watch.climbing(broken, arms(), said.append) == "")
watch.climbing(broken, arms(), said.append)
check("and is said once, not at every frame", len(said) == 1 and "ladder could not be read" in said[0])
check("the ledge is still read when the ladder is not", watch.climbing(
    types.SimpleNamespace(ReplicatedMantleState=types.SimpleNamespace(ActionIndex=0)), arms(), said.append)
      == watch.LEDGE)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
