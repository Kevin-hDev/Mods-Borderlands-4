"""Tests the climb's jump budget: a climb counts as a landing (both jumps back), one jump given back after the next one
spent in the air, gifts written only once Croix is released, dropped after two seconds held, and the air jump lines."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import air_jumps  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(text: str) -> int:
    return sum(text in line for line in state["misc"])


MS = 1_000_000
S = 1_000_000_000
player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")


def jump_type(name: str) -> None:
    movement.CurrentJump = types.SimpleNamespace(JumpType=types.SimpleNamespace(TagName=f"Movement.JumpType.{name}"))


# Both jumps used, Croix still down from the second one, and a climb starts.
player.JumpCurrentCount, player.bPressedJump = 2, True
jump_type("DoubleJump")
air_jumps.update(player, 0)
air_jumps.climb_started(player, 10 * MS)
check("Croix held: the count is left alone", air_jumps.update(player, 20 * MS) is None and player.JumpCurrentCount == 2)
player.bPressedJump = False
check("released: the climb puts the count back to one jump used", air_jumps.update(player, 100 * MS) == 1
      and player.JumpCurrentCount == 1 and notes("wall climb: both jumps are back: jump count 2 -> 1") == 1)

# The jump from the wall.
player.JumpCurrentCount, player.bPressedJump = 2, True
air_jumps.update(player, 200 * MS)
check("the jump from the wall is written down", notes("air jump count=2 type=DoubleJump croix=held") == 1)
check("and nothing is given back while Croix is held", player.JumpCurrentCount == 2)
player.bPressedJump = False
check("released, the next jump is given back", air_jumps.update(player, 300 * MS) == 1 and player.JumpCurrentCount == 1
      and notes("jump from the climb: the next jump is back: jump count 2 -> 1") == 1)

# The double jump that follows: the climb owes nothing more.
player.JumpCurrentCount = 2
air_jumps.update(player, 400 * MS)
air_jumps.update(player, 500 * MS)
check("the double jump keeps both jumps used", player.JumpCurrentCount == 2)

# A new climb starts the budget over.
air_jumps.climb_started(player, 600 * MS)
check("a new climb gives both jumps back", air_jumps.update(player, 700 * MS) == 1 and player.JumpCurrentCount == 1)
player.JumpCurrentCount = 2
air_jumps.update(player, 800 * MS)
check("and owes one again", player.JumpCurrentCount == 1)

# Landing: the game puts the count back itself, and the climb owes nothing.
air_jumps.climb_started(player, 900 * MS)
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
air_jumps.update(player, 1000 * MS)
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
player.JumpCurrentCount = 1
air_jumps.update(player, 1100 * MS)
player.JumpCurrentCount = 2
air_jumps.update(player, 1200 * MS)
check("after a landing the climb gives nothing back", player.JumpCurrentCount == 2)

# A gift held too long is dropped.
air_jumps.climb_started(player, 2000 * MS)
player.bPressedJump = True
check("held for two seconds, the gift waits", air_jumps.update(player, 2000 * MS + 2 * S) is None
      and player.JumpCurrentCount == 2)
check("past two seconds it is dropped and said", air_jumps.update(player, 2001 * MS + 2 * S) is None
      and notes("not given back, Croix still held") == 1)
player.bPressedJump = False
check("a dropped gift is not written later", air_jumps.update(player, 5000 * MS) is None and player.JumpCurrentCount == 2)

state["misc"].clear()
air_jumps.reset()
player.JumpCurrentCount = 1
jump_type("DefaultJump")
air_jumps.update(player, 6000 * MS)
check("the first air frame writes nothing down", state["misc"] == [])
jump_type("DoubleJump")
air_jumps.update(player, 6100 * MS)
check("a change of jump type alone is written down, without giving anything back",
      notes("air jump count=1 type=DoubleJump croix=free") == 1 and player.JumpCurrentCount == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
