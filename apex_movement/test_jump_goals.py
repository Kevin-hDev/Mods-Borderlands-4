"""Tests reaching the jump definitions: each type set in turn, the original type put back, even after a refusal."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import jump_goals  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


movement = sdk_stubs.FakeMovement()
movement.SetCurrentJumpType(types.SimpleNamespace(TagName="Movement.JumpType.SprintJump"))
movement.type_sets.clear()

found = jump_goals.collect(movement)
check("the five definitions are found", set(found) == set(jump_goals.JUMP_TYPES))
check("each type gives its own definition", found["DoubleJump"] is movement.goals["DoubleJump"])
check("every type is set once, then the original", movement.type_sets == [
    f"Movement.JumpType.{jump_type}" for jump_type in jump_goals.JUMP_TYPES
] + ["Movement.JumpType.SprintJump"])
check("the original jump type is back", movement.CurrentJump.JumpType.TagName == "Movement.JumpType.SprintJump")


def refuse(tag: object) -> None:
    movement.type_sets.append(tag.TagName)
    if tag.TagName.endswith("DoubleJump"):
        raise RuntimeError("refused")
    movement.CurrentJump = types.SimpleNamespace(JumpType=tag, JumpGoal=None)


movement.SetCurrentJumpType = refuse
try:
    jump_goals.collect(movement)
    raised = False
except RuntimeError:
    raised = True
check("a refused type raises", raised)
check("the original type is put back even then", movement.type_sets[-1] == "Movement.JumpType.SprintJump")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
