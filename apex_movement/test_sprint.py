"""Tests auto sprint: request, release, restart after a slide, ground speeds by state, restore on stop."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import ownership, settings, sprint  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement

sprint.update(player, 0)
check("a released stick asks no sprint", movement.bWantsToSprint is False)
check("walking sets the walk speed", movement.MinAnalogWalkSpeed == 672.0)
check("the game's floor is kept to put back", ownership.original(sprint.FLOOR_KEY) == 0.0)

player.input = sdk_stubs.vector(0.9, 0.0)
sprint.update(player, 1)
check("a stick below 0.95 asks no sprint", movement.bWantsToSprint is False)

player.input = sdk_stubs.vector(1.0, 0.0)
sprint.update(player, 2)
check("a fully pushed stick on the ground asks sprint", movement.bWantsToSprint and movement.bWantsToStartSprinting)
check("the request is logged once", sum("sprint request on" in line for line in state["misc"]) == 1)

movement.bIsSprinting = True
sprint.update(player, 3)
check("sprinting sets the sprint speed", movement.MinAnalogWalkSpeed == 960.0)
check("a speed change is logged", any("ground speed 960" in line for line in state["misc"]))

player.ZoomState.bWantsToZoom = True
sprint.update(player, 4)
check("aiming releases the sprint", movement.bWantsToSprint is False)
player.ZoomState.bWantsToZoom = False

movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
movement.bIsSprinting = False
sprint.update(player, 5)
check("in the air no sprint is asked", movement.bWantsToSprint is False)
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")

sprint.update(player, 6)
movement.bWantsToStartSprinting = False
movement.bIsSprinting = False
sprint.update(player, 7)
check("sprint wanted but stopped is started again", movement.bWantsToStartSprinting is True)
check("the restart is logged once", sum("sprint restart" in line for line in state["misc"]) == 1)
movement.bWantsToStartSprinting = False
player.bIsCrouched = True
sprint.update(player, 8)
check("no restart while crouched, so a slide is left alone", movement.bWantsToStartSprinting is False)
player.bIsCrouched = False

settings.walk_speed.value = 700
movement.bIsSprinting = False
sprint.update(player, 9)
check("the walk slider applies at once", movement.MinAnalogWalkSpeed == 700.0)
settings.walk_speed.value = 672

sprint.stop(player)
check("stop releases the sprint the mod asked for", movement.bWantsToSprint is False)
check("stop puts the game's floor back", movement.MinAnalogWalkSpeed == 0.0 and not ownership.is_owned(sprint.FLOOR_KEY))

movement.bWantsToSprint = True
sprint.stop(player)
check("stop leaves a sprint the mod did not ask for", movement.bWantsToSprint is True)
sprint.stop(None)
check("stop without a character does not raise", True)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
