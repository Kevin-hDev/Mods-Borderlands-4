"""Tests the ground speeds: walk and sprint by state, the sliders, and the game's own floor put back on stop."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import ground_speed, ownership, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement

ground_speed.update(player, 0)
check("walking sets the walk speed", movement.MinAnalogWalkSpeed == 672.0)
check("the game's floor is kept to put back", ownership.original(ground_speed.FLOOR_KEY) == 0.0)

movement.bIsSprinting = True
ground_speed.update(player, 1)
check("sprinting sets the sprint speed", movement.MinAnalogWalkSpeed == 960.0)
check("a speed change is logged", any("ground speed 960" in line for line in state["misc"]))

written = len([line for line in state["misc"] if "ground speed" in line])
ground_speed.update(player, 2)
check("an unchanged speed is not written again",
      len([line for line in state["misc"] if "ground speed" in line]) == written)

settings.sprint_speed.value = 1100
ground_speed.update(player, 3)
check("the sprint slider applies at once", movement.MinAnalogWalkSpeed == 1100.0)
settings.sprint_speed.value = 960

movement.bIsSprinting = False
settings.walk_speed.value = 700
ground_speed.update(player, 4)
check("the walk slider applies at once", movement.MinAnalogWalkSpeed == 700.0)
settings.walk_speed.value = 672

# The speeds do not belong to the auto sprint: nothing here reads its switch, and the mod registers this module
# without one (2026-09-18). A sprint the player started themselves still gets the sprint speed.
settings.auto_sprint.value = False
movement.bIsSprinting = True
ground_speed.update(player, 5)
check("auto sprint off does not give the game's speeds back", movement.MinAnalogWalkSpeed == 960.0)
settings.auto_sprint.value = True

ground_speed.stop(player)
check("stop puts the game's floor back",
      movement.MinAnalogWalkSpeed == 0.0 and not ownership.is_owned(ground_speed.FLOOR_KEY))

ground_speed.stop(None)
check("stop without a character does not raise", True)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
