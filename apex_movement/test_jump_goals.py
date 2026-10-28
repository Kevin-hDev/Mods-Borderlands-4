"""Tests reaching the jump definitions: each type set in turn, each definition read and distinct, the original type
put back, even after a refusal."""

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


def game_answering(answers: dict[str, object]) -> None:
    """The game's SetCurrentJumpType, except for the types in answers: a definition to give, or an error to raise."""

    def set_type(tag: object) -> None:
        movement.type_sets.append(tag.TagName)
        short = tag.TagName.rsplit(".", 1)[-1]
        answer = answers.get(short, movement.goals.get(short))
        if isinstance(answer, Exception):
            raise answer
        movement.CurrentJump = types.SimpleNamespace(JumpType=tag, JumpGoal=answer)

    movement.SetCurrentJumpType = set_type


def collect_error() -> Exception | None:
    try:
        jump_goals.collect(movement)
    except Exception as exc:
        return exc
    return None


game_answering({"DoubleJump": RuntimeError("refused")})
check("a refused type raises", isinstance(collect_error(), RuntimeError))
check("the original type is put back even then", movement.type_sets[-1] == "Movement.JumpType.SprintJump")

game_answering({"SlideJump": None})
error = collect_error()
check("an empty definition raises, naming its type", isinstance(error, ValueError) and "SlideJump" in str(error))
check("the original type is put back after it", movement.type_sets[-1] == "Movement.JumpType.SprintJump")


class Unresolved:
    """An unresolved FGbxDefPtr, as the game gave through GetJumpGoalForJumpType: its fields do not read."""

    def __getattr__(self, name: str) -> object:
        raise AttributeError(f"unresolved FGbxDefPtr has no attribute '{name}'")


game_answering({"DoubleJump": Unresolved()})
error = collect_error()
check("an unresolved definition raises too", isinstance(error, ValueError) and "DoubleJump" in str(error))

game_answering({"SlideJump": movement.goals["SprintJump"]})
error = collect_error()
check("a definition given for two types raises, naming both, before its height is added twice",
      isinstance(error, ValueError) and "SprintJump" in str(error) and "SlideJump" in str(error))
check("the original type is put back after that too", movement.type_sets[-1] == "Movement.JumpType.SprintJump")

game_answering({})
check("five distinct definitions still collect", collect_error() is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
