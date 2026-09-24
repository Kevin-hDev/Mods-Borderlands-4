"""Tests wall-climb refusals, low obstacles, shutdown cleanup and slider transfer."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
pointers: list = []


class KeptPointer(sys.modules["unrealsdk.unreal"].WeakPointer):
    def __init__(self, obj: object = None) -> None:
        super().__init__(obj)
        pointers.append(self)


sys.modules["unrealsdk.unreal"].WeakPointer = KeptPointer

from apex_movement import game, jump_press, ownership, settings, wall_climb  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(text: str) -> int:
    return sum(text in line for line in state["misc"])


MS = 1_000_000
kismet = state["kismet"]
player = sdk_stubs.FakeCharacter()
sdk_stubs.use_character(state, player)
pc = state["pc"]
game.refresh(0)
sdk_stubs.add_arms(state, player)
wall_climb.update(player, 0)
movement = player.CharacterMovement

# A try that starts no climb explains itself when the player lands.
state["misc"].clear()
settings.climb_lean.value = 60
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
movement.mantle_allowed = False
player.location = sdk_stubs.vector(0.0, 0.0, 0.0)
player.input = sdk_stubs.vector(1.0, 0.0)
kismet.hit = (164.0, sdk_stubs.vector(-1.0, 0.0, 0.0))
wall_climb.update(player, 20000 * MS)
check("too far from the wall, no climb starts and nothing is said yet",
      notes("wall climb start") == 0 and notes("wall climb refused") == 0)
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
wall_climb.update(player, 20100 * MS)
check("landing says how far the wall was and how close it had to be",
      notes("wall climb refused reason=too_far distance=104") == 1 and notes("needs distance<=90") == 1)

state["misc"].clear()
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
kismet.hit = (120.0, sdk_stubs.vector(-0.5, 0.0, 0.87))
wall_climb.update(player, 21000 * MS)
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
wall_climb.update(player, 21100 * MS)
check("a face leaning too much to be a wall is named as such",
      notes("wall climb refused reason=slope") == 1 and notes("flat=0.50") == 1)

# A face met only below the waist is a step and must not steal the jump leaving the ground.
wall_climb.reset()
state["misc"].clear()
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
movement.Velocity = sdk_stubs.vector(0.0, 0.0, 912.0)
player.location = sdk_stubs.vector(0.0, 0.0, 0.0)
player.input = sdk_stubs.vector(1.0, 0.0)
kismet.hits_by_z = {round(-1.2 * 93.0): (130.0, sdk_stubs.vector(-1.0, 0.0, 0.0))}
wall_climb.update(player, 23000 * MS)
check("a face seen only at the feet starts no climb", notes("wall climb start") == 0)
check("and the jump keeps the speed it left the ground with", movement.Velocity.Z == 912.0)
kismet.hits_by_z = {round(-1.2 * 93.0): (130.0, sdk_stubs.vector(-1.0, 0.0, 0.0)),
                    0: (130.0, sdk_stubs.vector(-1.0, 0.0, 0.0))}
wall_climb.update(player, 23100 * MS)
check("seen at the character's height too, it starts", notes("wall climb start distance=70") == 1)
check("a climb never slows a rise already faster than itself", movement.Velocity.Z == 912.0)

wall_climb.reset()
state["misc"].clear()
player.location = sdk_stubs.vector(0.0, 0.0, 0.0)
kismet.hits_by_z = {round(-1.2 * 93.0): (120.0, sdk_stubs.vector(-0.5, 0.0, 0.87)),
                    0: (140.0, sdk_stubs.vector(-1.0, 0.0, 0.0))}
wall_climb.update(player, 25000 * MS)
check("a grazed beam does not hide the upright panel", notes("wall climb start distance=80") == 1)
kismet.hits_by_z = None

# Nothing held by an active climb may survive switching the movement off.
wall_climb.reset()
state["misc"].clear()
state["inject_function"] = types.SimpleNamespace(Name="InjectInputVectorForAction")
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
movement.Velocity = sdk_stubs.vector(0.0, 0.0, 0.0)
movement.mantle_allowed = True
player.location = sdk_stubs.vector(0.0, 0.0, 0.0)
player.JumpCurrentCount = 1
kismet.hit = (120.0, sdk_stubs.vector(-1.0, 0.0, 0.0))
wall_climb.update(player, 27000 * MS)
check("a climb starts, pressing Croix", notes("wall climb start") == 1 and notes("wall climb hoist") == 1)
wall_climb.stop(player)
check("switching off tells the active climb's end", notes("wall climb end reason=switched_off") == 1)
scans = state["subsystem_scans"]
jump_press.press()
check("the climb's cached jump input is forgotten", state["subsystem_scans"] == scans + 1)
movement.mantle_allowed = False
kismet.hit = None
wall_climb.update(player, 27100 * MS)
player.JumpCurrentCount = 2
wall_climb.update(player, 27200 * MS)
check("a jump after switch-off is not given back", player.JumpCurrentCount == 2 and notes("jump from the climb") == 0)

check("the mantle hold is written again after switch-off", pc.MinPassiveMantleButtonHoldDuration == 0.0)
for pointer in pointers:
    if pointer.obj is pc:
        pointer.obj = None
wall_climb.stop(player)
check("a controller destroyed at the title screen is never written", pc.MinPassiveMantleButtonHoldDuration == 0.0)
check("the mod records that the value was left to the game",
      ownership.is_owned(wall_climb.HOLD_KEY) and ownership.unloaded_count() >= 1)

settings.climb_speed.value, settings.climb_lean.value = 370, 60
from_sliders = wall_climb._limits(player)
check("the sliders' values pass untouched", (from_sliders.speed, from_sliders.lean_deg) == (370.0, 60.0))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
