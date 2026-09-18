"""Tests momentum slides: Move_Slide launches along the velocity, written once, put back on stop."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import game, ownership, slide_direction  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


Direction = sdk_stubs.Direction
asset = sdk_stubs.slide_asset(state)
player = sdk_stubs.FakeCharacter()


def direction() -> Direction:
    return asset.LaunchDirection.RelativeDirection


slide_direction.update(player, 0)
check("slides launch along the velocity", direction() is Direction.ParentVelocity2D)
check("the game's aim direction is kept to put back", ownership.original(slide_direction.DIRECTION_KEY) is Direction.ParentAimDirection2D)
check("the change is logged with the old value", any("slide direction ParentVelocity2D (was ParentAimDirection2D)" in line for line in state["misc"]))

slide_direction.update(player, 1)
check("a direction already set is not written or logged again", sum("slide direction" in line for line in state["misc"]) == 1)

asset.LaunchDirection = type(asset.LaunchDirection)(RelativeDirection=Direction.ParentAimDirection2D)
slide_direction.update(player, 2)
check("a direction the game put back is set again", direction() is Direction.ParentVelocity2D)
check("the first original is still the one kept", ownership.original(slide_direction.DIRECTION_KEY) is Direction.ParentAimDirection2D)

key = ("OakControlledMove", sdk_stubs.SLIDE_PATH)
del state["objects"][key]
game.forget()
slide_direction.update(player, 3)
check("a slide asset not loaded yet skips the frame and is reported", len(state["errors"]) == 1)
check("in words true of the slide's direction, not of its speed", "speed" not in state["errors"][0])
state["objects"][key] = asset

slide_direction.stop(player)
check("stop puts the game's direction back", direction() is Direction.ParentAimDirection2D)
check("the restore is logged", any("slide direction restored" in line for line in state["misc"]))
slide_direction.stop(player)
check("a second stop logs nothing", sum("slide direction restored" in line for line in state["misc"]) == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
