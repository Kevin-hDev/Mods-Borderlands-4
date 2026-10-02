"""Tests which view the player has: the camera's mode for the character, and first person when it cannot be read."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import view  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


pc, character = sdk_stubs.player(state)
asked = []
mode = pc.PlayerCameraManager.GetActorCameraMode
pc.PlayerCameraManager.GetActorCameraMode = lambda actor: asked.append(actor) or mode(actor)

check("the game's Default mode is first person", view.third_person(pc, character) is False)
check("the mode is asked for the character", asked == [character])
state["camera_mode"] = "Slide"
check("sliding is still first person", view.third_person(pc, character) is False)
state["camera_mode"] = "ThirdPerson"
check("ThirdPerson is third person", view.third_person(pc, character) is True)
state["camera_mode"] = "ThirdPersonVehicle"
check("so is a mode that holds that name", view.third_person(pc, character) is True)

del pc.PlayerCameraManager.GetActorCameraMode
errors = len(state["errors"])
check("a camera that cannot be read counts as first person, said once",
      view.third_person(pc, character) is False and view.third_person(pc, character) is False
      and len(state["errors"]) == errors + 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
