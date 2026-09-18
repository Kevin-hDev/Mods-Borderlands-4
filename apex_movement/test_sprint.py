"""Tests auto sprint: request, release while aiming or in the air, restart after a slide, release on stop."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import sprint  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement

sprint.update(player, 0)
check("a released stick asks no sprint", movement.bWantsToSprint is False)

player.input = sdk_stubs.vector(0.9, 0.0)
sprint.update(player, 1)
check("a stick below 0.95 asks no sprint", movement.bWantsToSprint is False)

player.input = sdk_stubs.vector(1.0, 0.0)
sprint.update(player, 2)
check("a fully pushed stick on the ground asks sprint", movement.bWantsToSprint and movement.bWantsToStartSprinting)
check("the request is logged once", sum("sprint request on" in line for line in state["misc"]) == 1)

player.ZoomState.bWantsToZoom = True
sprint.update(player, 3)
check("aiming releases the sprint", movement.bWantsToSprint is False)
player.ZoomState.bWantsToZoom = False

movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
sprint.update(player, 4)
check("in the air no sprint is asked", movement.bWantsToSprint is False)
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")

sprint.update(player, 5)
movement.bWantsToStartSprinting = False
movement.bIsSprinting = False
sprint.update(player, 6)
check("sprint wanted but stopped is started again", movement.bWantsToStartSprinting is True)
check("the restart is logged once", sum("sprint restart" in line for line in state["misc"]) == 1)
movement.bWantsToStartSprinting = False
player.bIsCrouched = True
sprint.update(player, 7)
check("no restart while crouched, so a slide is left alone", movement.bWantsToStartSprinting is False)
player.bIsCrouched = False

# The ground speeds left this module on 2026-09-18: they live in ground_speed, with no switch of their own.
check("auto sprint no longer touches the ground speed", not hasattr(sprint, "FLOOR_KEY"))

sprint.stop(player)
check("stop releases the sprint the mod asked for", movement.bWantsToSprint is False)

movement.bWantsToSprint = True
sprint.stop(player)
check("stop leaves a sprint the mod did not ask for", movement.bWantsToSprint is True)
sprint.stop(None)
check("stop without a character does not raise", True)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
