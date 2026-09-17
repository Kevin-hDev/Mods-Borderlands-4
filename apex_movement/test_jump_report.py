"""Tests the jump report: one line at take-off with the jump's kind, speed and floor, one at landing with the rise."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import jump_report  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def lines() -> list[str]:
    return [line for line in state["misc"] if "jump " in line]


player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement
movement.CurrentFloor = types.SimpleNamespace(
    HitResult=types.SimpleNamespace(Component=types.SimpleNamespace(Name="SM_Wood_Deck")))


def ground(speed: float = 0.0) -> None:
    movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
    movement.Velocity = sdk_stubs.vector(speed, 0.0, 0.0)


def air(vz: float, jump: str = "SprintJump") -> None:
    movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
    movement.Velocity = sdk_stubs.vector(0.0, 0.0, vz)
    movement.CurrentJump = types.SimpleNamespace(JumpType=types.SimpleNamespace(TagName=f"Movement.JumpType.{jump}"))


player.location = sdk_stubs.vector(0.0, 0.0, 0.0)
ground(speed=960.0)
jump_report.update(player, 0)
check("standing on the ground says nothing", lines() == [])
air(vz=930.0)
jump_report.update(player, 1)
check("leaving the ground says the jump's kind, its upward speed, the ground speed and the floor",
      lines() == ["[Apex Movement] jump take-off type=SprintJump vz=930 speed=960 floor=SM_Wood_Deck"])
player.location = sdk_stubs.vector(0.0, 0.0, 218.0)
jump_report.update(player, 2)
player.location = sdk_stubs.vector(0.0, 0.0, 120.0)
jump_report.update(player, 3)
check("staying in the air adds nothing", len(lines()) == 1)
ground()
jump_report.update(player, 4)
check("landing says how high the jump got, counted from its highest point",
      lines()[-1] == "[Apex Movement] jump landed rise=218")

state["misc"].clear()
player.location = sdk_stubs.vector(0.0, 0.0, 0.0)
air(vz=420.0, jump="DefaultJump")
jump_report.update(player, 5)
check("a jump of another kind is named as such", "type=DefaultJump vz=420" in lines()[0])

movement.CurrentFloor = None
ground()
jump_report.update(player, 6)
state["misc"].clear()
air(vz=420.0)
jump_report.update(player, 7)
check("a floor the game will not name is written as unknown, not as an error", "floor=?" in lines()[0])

jump_report.reset()
state["misc"].clear()
ground()
jump_report.update(player, 8)
air(vz=420.0)
jump_report.update(player, 9)
check("after a reset the next jump is reported again", len(lines()) == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
