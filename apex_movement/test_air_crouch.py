"""Tests the air crouch movement: keys bound on the first frame, requests played, landing slide from the minimum."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
# Stands for unrealsdk.unreal.WeakPointer, which air_actions keeps the asking character in: no character dies here.
sys.modules["unrealsdk.unreal"].WeakPointer = lambda obj=None: (lambda: obj)

from apex_movement import air_bindings, air_crouch, air_keys, game, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


MS = 1_000_000
Block = sys.modules["unrealsdk.hooks"].Block
pressed, released = types.SimpleNamespace(name="IE_Pressed"), types.SimpleNamespace(name="IE_Released")
pad, cross = "Gamepad_FaceButton_Right", "Gamepad_FaceButton_Bottom"
player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement
sdk_stubs.use_character(state, player)
game.refresh(0)
now = [0]
# Key events read the clock themselves; the test drives it so presses and frames share one time line.
air_bindings.time = types.SimpleNamespace(perf_counter_ns=lambda: now[0])


def key(name: str, event: types.SimpleNamespace, at_ns: int) -> object:
    now[0] = at_ns
    return state["keybinds"][name](event)


def fly(speed: float, now_ns: int) -> None:
    movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
    movement.Velocity = sdk_stubs.vector(speed, 0.0)
    air_crouch.update(player, now_ns)


def land(now_ns: int) -> None:
    movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")
    air_crouch.update(player, now_ns)


air_crouch.update(player, 0)
check("the first frame binds the keys", pad in state["keybinds"] and cross in state["keybinds"])

fly(700.0, 100 * MS)
check("a crouch held in the air is blocked", key(pad, pressed, 150 * MS) is Block)
fly(680.0, 400 * MS)
land(500 * MS)
check("a hold landing above the minimum asks a slide", ("SetWantsToSlide", True) in player.calls)
key(pad, released, 600 * MS)
movement.Velocity = sdk_stubs.vector(0.0, 0.0)
air_crouch.update(player, 1000 * MS)
check("the slide request is released when no slide came", player.calls[-1] == ("SetWantsToSlide", False))

player.calls.clear()
fly(540.0, 2000 * MS)
key(pad, pressed, 2100 * MS)
land(2500 * MS)
check("a hold landing below the minimum asks nothing", player.calls == [])
check("and says why", any("landing held speed_in=540 below min=550" in line for line in state["misc"]))
key(pad, released, 2600 * MS)

settings.landing_slide_min_speed.value = 500
fly(540.0, 3000 * MS)
key(pad, pressed, 3100 * MS)
land(3500 * MS)
check("the minimum follows its slider", ("SetWantsToSlide", True) in player.calls)
settings.landing_slide_min_speed.value = 550
key(pad, released, 3600 * MS)
air_crouch.update(player, 4000 * MS)

player.calls.clear()
fly(900.0, 5000 * MS)
land(5500 * MS)
check("a landing without a held crouch asks nothing", player.calls == [])

fly(900.0, 6000 * MS)
key(pad, pressed, 6010 * MS)
air_crouch.update(player, 6050 * MS)
key(pad, released, 6090 * MS)
fly(900.0, 6100 * MS)
check("a tap in the air dashes at the next frame", player.calls and player.calls[0][:2] == ("SetWantsToDash", True))
land(6500 * MS)
check("a landing after a tap asks no slide", ("SetWantsToSlide", True) not in player.calls)

player.calls.clear()
fly(900.0, 8000 * MS)
key(pad, pressed, 8010 * MS)
key(cross, pressed, 8040 * MS)
air_crouch.update(player, 8100 * MS)
check("the slam waits 200 ms", ("AttemptGroundSlam",) not in player.calls)
fly(900.0, 8300 * MS)
check("crouch then jump slams", ("AttemptGroundSlam",) in player.calls)
key(pad, released, 8350 * MS)
land(8600 * MS)
check("a slam combination asks no landing slide", ("SetWantsToSlide", True) not in player.calls)

air_crouch.update(player, 20000 * MS)
check("a crouch pressed on the ground reaches the game", key(pad, pressed, 20100 * MS) is None)
fly(1200.0, 20200 * MS)
land(20400 * MS)
check("kept down through a slide jump, it slides at landing", ("SetWantsToSlide", True) in player.calls)
movement.Velocity = sdk_stubs.vector(0.0, 0.0)
air_crouch.update(player, 20900 * MS)
player.calls.clear()
fly(1100.0, 21000 * MS)
land(21200 * MS)
check("and again at the next jump, without being pressed again", ("SetWantsToSlide", True) in player.calls)
check("its release reaches the game", key(pad, released, 21250 * MS) is None)
movement.Velocity = sdk_stubs.vector(0.0, 0.0)
air_crouch.update(player, 21700 * MS)
player.calls.clear()
fly(1100.0, 21800 * MS)
land(22000 * MS)
check("released, the next landing asks nothing", ("SetWantsToSlide", True) not in player.calls)
key(pad, pressed, 22100 * MS)
fly(1100.0, 22200 * MS)
movement.MovementMode = sdk_stubs.Mode("MOVE_Custom")
air_crouch.update(player, 22300 * MS)
check("held into a mantle, no slide, and the log says into what", ("SetWantsToSlide", True) not in player.calls
      and any("landing held into MOVE_Custom: no slide" in line for line in state["misc"]))
key(pad, released, 22400 * MS)
land(22500 * MS)

fly(900.0, 23000 * MS)
key(pad, pressed, 23010 * MS)
air_crouch.stop(player)
check("stop releases the keys: the game gets its crouch back", state["keybinds"] == {})
check("stop forgets the held press", not air_keys.is_held())
air_crouch.update(player, 23100 * MS)
check("the next frame binds the keys again", pad in state["keybinds"])

# A level change with the switch then turned off: the frame loop resets the movement and updates it no more.
air_crouch.reset()
if pad in state["keybinds"]:
    key(pad, pressed, 23150 * MS)
    key(pad, released, 23190 * MS)
player.calls.clear()
fly(900.0, 23200 * MS)
check("switched back on, no tap made while it was off is played", player.calls == [])
land(23250 * MS)

game_mappings = list(state["mappings"])
state["mappings"][:] = [sdk_stubs.mapping("Action_Crouch_Hold", "LeftShift"),
                        sdk_stubs.mapping("Action_Jump_HoldToGlide", cross)]
air_crouch.update(player, 23300 * MS)
check("a key changed in the options is not read again mid-level", pad in state["keybinds"])
air_crouch.reset()
check("a level change gives the old key back to the game at once", pad not in state["keybinds"])
air_crouch.update(player, 23400 * MS)
check("the next frame binds the key now in the options",
      "LeftShift" in state["keybinds"] and pad not in state["keybinds"])

state["mappings"][:] = [sdk_stubs.mapping("Action_Jump_HoldToGlide", cross)]
air_crouch.stop(player)
air_crouch.update(player, 24000 * MS)
air_crouch.update(player, 24001 * MS)
check("a key list without crouch is reported once", sum("no crouch key" in line for line in state["errors"]) == 1)
check("and binds nothing", state["keybinds"] == {})
state["mappings"][:] = game_mappings
air_crouch.update(player, 24002 * MS)
check("a refused list is not read again every frame", state["keybinds"] == {})
air_crouch.reset()
air_crouch.update(player, 24003 * MS)
check("a level change reads the key list again and binds the crouch key", pad in state["keybinds"])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
