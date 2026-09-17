"""Tests heavier fall: definitions read standing, heights and speeds compensated, sliders applied, all put back."""

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import heavier_fall, ownership, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(a: float, b: float) -> bool:
    return abs(a - b) < 0.01


player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement
goals = movement.goals

movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
heavier_fall.update(player, 0)
check("nothing is read or written in the air", movement.type_sets == [] and movement.GravityScale == 1.0)
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")

heavier_fall.update(player, 1)
check("the gravity scale follows the slider", near(movement.GravityScale, 1.6))
check("the standing jump gets its extra height, times the scale", near(goals["DefaultJump"].GoalHeight, 218.0 * 1.6))
check("a height-only jump keeps its launch speed", goals["DefaultJump"].InitialZVelocity == 840.0)
check("the double jump gets its extra height, times the scale", near(goals["DoubleJump"].GoalHeight, 245.0 * 1.6))
check("the sprint jump gets its extra height, times the scale", near(goals["SprintJump"].GoalHeight, 218.0 * 1.6))
check("a jump with a launch speed gets it times the root of the scale",
      near(goals["SprintJump"].InitialZVelocity, 735.0 * math.sqrt(1.6)))
check("slide and ladder jumps get it too", near(goals["SlideJump"].GoalHeight, 210.0 * 1.6)
      and near(goals["UpwardLadderJump"].GoalHeight, 195.0 * 1.6)
      and near(goals["UpwardLadderJump"].InitialZVelocity, 700.0 * math.sqrt(1.6)))
check("the change is logged once", sum("fall weight 1.60" in line for line in state["misc"]) == 1)

sets = len(movement.type_sets)
heavier_fall.update(player, 2)
check("definitions are read once per character", len(movement.type_sets) == sets)
check("an unchanged frame writes and logs nothing", sum("fall weight" in line for line in state["misc"]) == 1)

settings.fall_weight.value = 1.5
settings.jump_height_bonus.value = 0
heavier_fall.update(player, 3)
check("a new scale is computed from the game's values, not the written ones",
      near(goals["DefaultJump"].GoalHeight, 198.0 * 1.5) and near(goals["SprintJump"].InitialZVelocity, 735.0 * math.sqrt(1.5)))
check("the game's values are kept to put back", ownership.original("JumpGoal_DoubleJump.GoalHeight") == 225.0)

heavier_fall.reset()
sets = len(movement.type_sets)
heavier_fall.update(player, 4)
check("a level change reads the definitions again", len(movement.type_sets) > sets)
check("and keeps the game's first values", ownership.original("JumpGoal_SprintJump.InitialZVelocity") == 735.0)

heavier_fall.stop(player)
check("stop puts every jump back", goals["DefaultJump"].GoalHeight == 198.0 and goals["DoubleJump"].GoalHeight == 225.0
      and goals["SprintJump"].InitialZVelocity == 735.0 and goals["UpwardLadderJump"].GoalHeight == 175.0)
check("stop puts the gravity back", movement.GravityScale == 1.0)
check("the restore is logged", any("heavier fall off" in line for line in state["misc"]))
check("nothing stays owned", not any(key.startswith("JumpGoal_") for key in ownership._entries)
      and not ownership.is_owned(heavier_fall.GRAVITY_KEY))
settings.fall_weight.value, settings.jump_height_bonus.value = 1.6, 20

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
