"""Tests the first-person arms' lookup: the instance on this character's FirstPersonArms mesh, found once, looked up
again while missing."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import arms  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("no arms without a character, and nothing scanned", arms.find(None) is None and state["anim_scans"] == 0)
owner = sdk_stubs.FakeCharacter()
sdk_stubs.add_arms(state, sdk_stubs.FakeCharacter())
sdk_stubs.add_arms(state, owner, mesh_name="FirstPersonLegs")
hands = sdk_stubs.add_arms(state, owner)
check("the arms are the instance on this character's FirstPersonArms mesh", arms.find(owner) is hands)
arms.find(owner)
check("looked up once", state["anim_scans"] == 1)
hands.Outer.GetAnimInstance = lambda: None
arms.forget()
check("an instance its mesh does not answer with is not the arms", arms.find(owner) is None and state["anim_scans"] == 2)
arms.find(owner)
check("missing arms are looked up again", state["anim_scans"] == 3)
hands.Outer.GetAnimInstance = lambda: hands
check("found again once they answer", arms.find(owner) is hands)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
