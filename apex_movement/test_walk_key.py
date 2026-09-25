"""Tests the walk key: held, it stops the auto sprint and the ground speed walks at the key's own speed.

Kevin, 2026-09-25, from a keyboard player's Nexus comment: with the auto sprint every push of a movement key sprints.
"""

import importlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import game, ground_speed, menu, ownership, pack, settings, slide  # noqa: E402
from apex_movement import speed_order, sprint, walk_key  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def press(event: str) -> None:
    walk_key.bind.callback(sdk_stubs.types.SimpleNamespace(name=event))


mod = state["mods"][0]
check("the mod declares the walk key, so the SDK hands it the key's presses",
      walk_key.bind in mod.kwargs["keybinds"])
mod.enable()
check("enabling the mod binds Caps Lock", state["keybinds"].get("CapsLock") is walk_key.bind.callback)
mod.disable()

check("the walk key is on by default", walk_key.switch.value is True)
check("Caps Lock is the default key: the game gives it no action", walk_key.key.value == "CapsLock")
check("the key has one entry in the SDK's menu", walk_key.bind.is_hidden and not walk_key.key.is_hidden)
# Kevin, 2026-09-25: 300 by default, as Valorant; 150 to 540, the key only walks slower, the Movement page goes faster.
check("the key walks at 300 by default", walk_key.speed.value == 300)
check("its slider goes from 150 up to the game's walk, no higher",
      (walk_key.speed.min_value, walk_key.speed.max_value) == (150, speed_order.GAME_WALK))

check("a key never pressed is not held", walk_key.held() is False)
press("IE_Pressed")
check("a press holds the key", walk_key.held() is True)
press("IE_Repeat")
check("the key's repeats keep it held", walk_key.held() is True)
press("IE_Released")
check("a release lets it go", walk_key.held() is False)
# Unreal hands a mouse button's second quick press as a double click (audit, 2026-09-25; Kevin put the key on a mouse
# button that day).
press("IE_Released")
press("IE_DoubleClick")
check("a double click holds the key too", walk_key.held() is True)
walk_key.switch.value = False
check("switched off, a held key walks nothing", walk_key.held() is False)
walk_key.switch.value = True

player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement
player.input = sdk_stubs.vector(1.0, 0.0)

sprint.update(player, 0)
check("the held key keeps the auto sprint from asking a sprint", movement.bWantsToSprint is False)
check("the held key asks the ground speed to walk", walk_key.asked() is True)
check("the walk is logged", any("walk key held" in line for line in state["misc"]))

scale = movement.MaxGroundSpeedScale
ground_speed.update(player, 1)
# The floor only raises the game's speed: under 540 the character's own speed scale is lowered to match, the lever
# that held in game (docs/investigations/apex_movement/mouvement/2026-09-25-marche-sous-540.md).
check("standing, the floor and the character's speed scale both give the key's speed",
      movement.MinAnalogWalkSpeed == 300.0 and abs(scale.Value - 300.0 / 470.0) < 1e-9)
check("the game's own scale is kept to put back", ownership.original(speed_order.SCALE_KEY) == 1.15)
asset = game.slide_asset()
curve_start = float(asset.SpeedScaleCurve.EditorCurveData.keys[0].Value)
slide._set_start_speed(movement, 1130.0)
# Move_Slide is shared by every character of the machine: sized on the key's scale, a co-op guest's slide would
# start 3.6 times too fast at 150 (audit, 2026-09-25, from "constant 3436" in the game's log).
check("while the key lowers the scale, the shared slide is sized on the game's scale",
      abs(float(asset.speed.constant) - 1130.0 / (1.15 * curve_start)) < 0.5)
check("the shared standing stance is left alone, the other players' too", player.ReplicatedStance.stance.speed == 470.0)
walk_key.speed.value = 200
ground_speed.update(player, 2)
check("the key's slider applies at once", movement.MinAnalogWalkSpeed == 200.0
      and abs(scale.Value - 200.0 / 470.0) < 1e-9)
scale.Value = 0.92
ground_speed.update(player, 3)
check("a scale the game computed again, aiming for one, is written back", abs(scale.Value - 200.0 / 470.0) < 1e-9)
# Put back as read at the first write, the release left the aiming scale on a character no longer aiming (audit).
check("and becomes the game's value to put back", ownership.original(speed_order.SCALE_KEY) == 0.92)
walk_key.speed.value = 540
settings.walk_speed.value = 400
ground_speed.update(player, 4)
check("the key never walks faster than the walk", movement.MinAnalogWalkSpeed == 400.0
      and abs(scale.Value - 400.0 / 470.0) < 1e-9)
settings.walk_speed.value = 672
walk_key.speed.value = 300

player.ReplicatedStance.stance = sdk_stubs.types.SimpleNamespace(_name="Stance_Player_Crouch", speed=275.0)
ground_speed.update(player, 5)
check("crouched, the scale goes back to the game's last own value: a crouch keeps its own speed",
      scale.Value == 0.92 and not ownership.is_owned(speed_order.SCALE_KEY))
scale.Value = 1.15  # The aim ends: the game computes its own scale again.
# In the air the game caps the speed at the falling stance's, 470 x the scale: put back, the scale let a jump from the
# key's walk reach 540 with the air strafe (audit, 2026-09-25).
player.ReplicatedStance.stance = sdk_stubs.types.SimpleNamespace(_name="Stance_Player_Falling", speed=470.0)
ground_speed.update(player, 6)
check("in the air, the key's speed holds too", movement.MinAnalogWalkSpeed == 300.0
      and abs(scale.Value - 300.0 / 470.0) < 1e-9)
player.ReplicatedStance.stance = sdk_stubs.types.SimpleNamespace(_name="Stance_Player_Default", speed=470.0)
ground_speed.update(player, 6)

press("IE_Released")
sprint.update(player, 7)
check("released, the auto sprint asks its sprint again", movement.bWantsToSprint is True)
check("released, the ground speed is asked no walk", walk_key.asked() is False)
check("the release is logged", any("walk key released" in line for line in state["misc"]))
ground_speed.update(player, 8)
check("released, the game's scale is put back and the mod's walk returns",
      scale.Value == 1.15 and movement.MinAnalogWalkSpeed == 672.0)

movement.bIsSprinting = True
press("IE_Pressed")
sprint.update(player, 5)
check("pressed while sprinting, the sprint the mod asked for is released", movement.bWantsToSprint is False)
ground_speed.update(player, 9)
check("until the game ends its sprint, the sprint speed stays, at the game's scale",
      movement.MinAnalogWalkSpeed == 960.0 and scale.Value == 1.15)
movement.bIsSprinting = False
ground_speed.update(player, 10)
check("then the key's speed applies", movement.MinAnalogWalkSpeed == 300.0)

sprint.stop(player)
check("stopping the auto sprint forgets the walk it asked", walk_key.asked() is False)
check("and forgets the key: its release never reaches a disabled bind", walk_key.held() is False)
ground_speed.update(player, 11)
check("so the ground speed walks at its own speed again, at the game's scale",
      movement.MinAnalogWalkSpeed == 672.0 and scale.Value == 1.15)

press("IE_Pressed")
sprint.update(player, 12)
ground_speed.update(player, 13)
ground_speed.stop(player)
check("stopping the ground speed puts the game's scale back too",
      scale.Value == 1.15 and not ownership.is_owned(speed_order.SCALE_KEY))
press("IE_Released")
sprint.update(player, 14)

# A stop that fails to write must still forget the walk: kept, the character walked slowly with the key up (audit).
sprint._requested = True
walk_key.ask(True)
try:
    sprint.stop(sdk_stubs.types.SimpleNamespace(CharacterMovement=None))
except AttributeError:
    pass
check("a stop that fails still forgets the walk it asked", walk_key.asked() is False)

check("the walk key and its speed sit on the auto sprint's page",
      [option.identifier for option in menu.auto_sprint.children]
      == ["auto_sprint", "walk", "walk_key", "walk_key_speed"])

# A separate Apex Auto Sprint file does not set the ground speed: the key walks at the game's own walk there, and a
# speed slider that changes nothing would read as broken (Kevin's rule, 2026-09-24).
pack.CARRIES = ("Auto sprint",)
alone = importlib.reload(menu)
check("a file without the ground speed shows the key but no speed slider",
      [option.identifier for option in alone.auto_sprint.children] == ["auto_sprint", "walk", "walk_key"])
check("and orders the key against the game's own walk", speed_order.walk_key_speed() == speed_order.GAME_WALK)
pack.CARRIES = ()
importlib.reload(menu)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
