"""Tests the controlled move watch: one line each time the game's controlled move changes, none otherwise, bounded."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import move_watch  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def lines() -> list[str]:
    return [line for line in state["misc"] if "game controlled move" in line]


player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement
data = movement.ControlledMoveReplicationData
slam = types.SimpleNamespace(Name="Move_GroundSlam")

move_watch.update(player, 0)
check("the first frame says what the game's controlled move is, none here",
      lines() == ["[Apex Movement] game controlled move none performing=False mode=MOVE_Walking"])
move_watch.update(player, 1)
check("an unchanged move writes nothing", len(lines()) == 1)

movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
data.ControlledMove = slam
movement.performing = True
move_watch.update(player, 2)
check("a move starting is written with its name, the game's own answer and where the character is",
      lines()[-1] == "[Apex Movement] game controlled move Move_GroundSlam performing=True mode=MOVE_Falling")
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
move_watch.update(player, 3)
check("landing with the same move and the same answer writes nothing: the mode is not what is watched",
      len(lines()) == 2)
movement.performing = False
move_watch.update(player, 4)
check("the game's answer changing alone is written: session 3 saw the copy keep a slam the game had ended",
      lines()[-1] == "[Apex Movement] game controlled move Move_GroundSlam performing=False mode=MOVE_Walking")
data.ControlledMove = None
move_watch.update(player, 5)
check("the move clearing is written too",
      lines()[-1] == "[Apex Movement] game controlled move none performing=False mode=MOVE_Walking")

data.ControlledMove = types.SimpleNamespace()
move_watch.update(player, 6)
check("a move without a readable name is still written, as unnamed", "game controlled move ? " in lines()[-1])

move_watch.reset()
move_watch.update(player, 7)
check("a new character says its move again", len(lines()) == 6)

move_watch.stop(player)
state["misc"].clear()
bound = move_watch.MAX_LINES
move_watch.MAX_LINES = 3
for step in range(10):
    data.ControlledMove = slam if step % 2 else None
    move_watch.update(player, 10 + step)
check("the lines are bounded", len(lines()) == 3)
move_watch.reset()
data.ControlledMove = None
move_watch.update(player, 30)
check("a level load does not lift the bound", len(lines()) == 3)
move_watch.stop(player)
move_watch.update(player, 31)
check("switching off and on starts a new count", len(lines()) == 4)
move_watch.MAX_LINES = bound

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
