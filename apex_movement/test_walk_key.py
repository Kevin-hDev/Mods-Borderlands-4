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

from apex_movement import frame, game, ground_speed, menu, ownership, pack, settings, slide  # noqa: E402
from apex_movement import slow_walk, speed_order, sprint, walk_key  # noqa: E402

S = 1_000_000_000

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
# A settings file from before the toggle loads no mode line: the state is written whole at every enable (review).
check("enabling the mod writes the slow walk's whole state, mode included",
      any(line.endswith("slow walk on mode hold key CapsLock") for line in state["misc"]))
mod.disable()

check("the walk key is on by default", walk_key.switch.value is True)
check("Caps Lock is the default key: the game gives it no action", walk_key.key.value == "CapsLock")
check("the key has one entry in the SDK's menu", walk_key.bind.is_hidden and not walk_key.key.is_hidden)
# Kevin, 2026-09-25: "Slow walk", never "Walk": the Movement page already has a walk speed.
check("every player-facing name says slow walk, not walk",
      all(option.display_name.startswith("Slow walk")
          for option in (walk_key.switch, walk_key.toggle, walk_key.key, walk_key.speed)))
# Kevin, 2026-09-25: 300 by default, as Valorant; 150 to 540, the key only walks slower, the Movement page goes faster.
check("the key walks at 300 by default", walk_key.speed.value == 300)
check("its slider goes from 150 up to the game's walk, no higher",
      (walk_key.speed.min_value, walk_key.speed.max_value) == (150, speed_order.GAME_WALK))

check("a key never pressed is not held", walk_key.walking() is False)
press("IE_Pressed")
check("a press holds the key", walk_key.walking() is True)
press("IE_Repeat")
check("the key's repeats keep it held", walk_key.walking() is True)
press("IE_Released")
check("a release lets it go", walk_key.walking() is False)
# Unreal hands a mouse button's second quick press as a double click (audit, 2026-09-25; Kevin put the key on a mouse
# button that day).
press("IE_Released")
press("IE_DoubleClick")
check("a double click holds the key too", walk_key.walking() is True)
walk_key.switch.value = False
check("switched off, a held key walks nothing", walk_key.walking() is False)
lines = len(state["misc"])
press("IE_Pressed")
check("switched off, a press writes no walk line: nothing happens in game", len(state["misc"]) == lines)
press("IE_Released")
walk_key.switch.value = True
check("switching the key off or on lets a held key go: its release may never come", walk_key.walking() is False)

# Kevin, 2026-09-25, from a Nexus comment: hold or toggle, the player's choice; held by default, as published.
check("the key is held, not toggled, by default", walk_key.toggle.value is False)
walk_key.toggle.value = True
press("IE_Pressed")
check("toggled, a press starts the walk", walk_key.walking() is True)
press("IE_Repeat")
check("toggled, the repeats of a key kept down change nothing", walk_key.walking() is True)
press("IE_Released")
check("toggled, a release keeps walking", walk_key.walking() is True)
press("IE_Pressed")
press("IE_Released")
check("toggled, a second press ends the walk", walk_key.walking() is False)
press("IE_DoubleClick")
check("toggled, a mouse button's quick second press counts as a press", walk_key.walking() is True)
walk_key.toggle.value = False
check("back to held, a walk toggled on ends: its release never comes", walk_key.walking() is False)
press("IE_Pressed")
check("and a press holds the key again", walk_key.walking() is True)

player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement
player.input = sdk_stubs.vector(1.0, 0.0)

sprint.update(player, 0)
check("the held key keeps the auto sprint from asking a sprint", movement.bWantsToSprint is False)
check("the walk is logged as it starts", any(line.endswith("slow walk on") for line in state["misc"]))

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
check("the end of the walk is logged", any(line.endswith("slow walk off") for line in state["misc"]))
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
# Kevin, 2026-09-25: the walk key is a movement of its own, it goes on without the auto sprint.
check("stopping the auto sprint keeps the walk: the key does not depend on it", walk_key.walking() is True)
ground_speed.update(player, 11)
check("so the ground speed still walks at the key's speed with the auto sprint off",
      movement.MinAnalogWalkSpeed == 300.0 and abs(scale.Value - 300.0 / 470.0) < 1e-9)
press("IE_Released")
ground_speed.update(player, 11)
check("released, the ground speed walks at its own speed again, at the game's scale",
      movement.MinAnalogWalkSpeed == 672.0 and scale.Value == 1.15)

press("IE_Pressed")
sprint.update(player, 12)
ground_speed.update(player, 13)
ground_speed.stop(player)
check("stopping the ground speed puts the game's scale back too",
      scale.Value == 1.15 and not ownership.is_owned(speed_order.SCALE_KEY))
press("IE_Released")
sprint.update(player, 14)

# Kevin, 2026-09-26: the slow walk wins over every sprint, the game's own included, whatever the auto sprint does.
sprint.stop(player)  # The auto sprint is off: what sprints now is the game's own request.
movement.bWantsToSprint = movement.bIsSprinting = True
press("IE_Pressed")
lines = len(state["misc"])
slow_walk.update(player, 15)
check("a sprint the game runs on its own ends while the key walks", movement.bWantsToSprint is False)
check("the refusal is written once", state["misc"][-1].endswith("sprint refused: slow walk")
      and len(state["misc"]) == lines + 1)
movement.bWantsToSprint = True
slow_walk.update(player, 16)
check("the game asking again in the same walk is refused again, without a second line",
      movement.bWantsToSprint is False and len(state["misc"]) == lines + 1)
movement.bIsSprinting = False
ground_speed.update(player, 17)
check("the sprint over, the ground speed walks at the key's speed", movement.MinAnalogWalkSpeed == 300.0)
press("IE_Released")
slow_walk.update(player, 18)
movement.bWantsToSprint = True
slow_walk.update(player, 19)
check("released, the game's sprint is left alone", movement.bWantsToSprint is True)
movement.bWantsToSprint = False
# The normal walk, faster than the key, is slowed too: nothing depends on a sprint (Kevin, 2026-09-26).
settings.walk_speed.value = 672
press("IE_Pressed")
ground_speed.update(player, 20)
check("a normal walk faster than the key slows to the key's speed", movement.MinAnalogWalkSpeed == 300.0)
press("IE_Released")
ground_speed.update(player, 21)
check("released, the normal walk is back", movement.MinAnalogWalkSpeed == 672.0)

# A stop that fails to write must still drop its own request (audit, 2026-09-25).
sprint._requested = True
try:
    sprint.stop(sdk_stubs.types.SimpleNamespace(CharacterMovement=None))
except AttributeError:
    pass
check("a stop that fails still drops the sprint it asked", sprint._requested is False)

# The walk ends with the character: after a death, a vehicle or a new game nobody comes back walking slowly
# (Kevin, 2026-09-25).
press("IE_Pressed")
check("the mode is logged, so a player's log says how they play",
      any(line.endswith("slow walk mode hold") for line in state["misc"]))
sdk_stubs.use_character(state, player)
frame.on_frame(player.anim, 10 * S)
check("a new character forgets the walk", walk_key.walking() is False)
walk_key.toggle.value = True
check("a change of mode is logged", any(line.endswith("slow walk mode toggle") for line in state["misc"]))
press("IE_Pressed")
state["pc"].OakCharacter = None
frame.on_frame(player.anim, 11 * S)
check("a ride away from the character forgets a toggled walk", walk_key.walking() is False)
sdk_stubs.use_character(state, player)
frame.on_frame(player.anim, 12 * S)
press("IE_Pressed")
press("IE_Released")
press("IE_DoubleClick")
press("IE_Released")
check("toggled, a press then a quick second press walk then stop: back where it started",
      walk_key.walking() is False)
press("IE_Pressed")
frame.stop_all()
check("the whole mod stopping forgets a toggled walk", walk_key.walking() is False)

# Kevin, 2026-09-27, first trial in game: toggled, the sprint key must sprint, and a death must not bring the player
# back walking slowly. Held, the key under the finger keeps winning.
movement.bWantsToSprint = True
press("IE_Pressed")
slow_walk.update(player, 30)
check("toggled, the sprint under way when the walk begins is ended: the walk wins at its start",
      walk_key.walking() is True and movement.bWantsToSprint is False)
movement.bWantsToSprint = True  # The player presses the sprint key.
slow_walk.update(player, 31)
check("toggled, a sprint asked afterwards ends the walk and goes on",
      walk_key.walking() is False and movement.bWantsToSprint is True)
check("and the log says why", state["misc"][-1].endswith("slow walk ended: sprint asked"))
slow_walk.update(player, 32)
check("with the walk over, the sprint is left alone", movement.bWantsToSprint is True)
movement.bWantsToSprint = False
walk_key.toggle.value = False
press("IE_Pressed")
slow_walk.update(player, 33)
movement.bWantsToSprint = True
slow_walk.update(player, 34)
check("held, a sprint asked during the walk is refused: the key under the finger wins",
      walk_key.walking() is True and movement.bWantsToSprint is False)
press("IE_Released")
slow_walk.update(player, 35)

# Going down: the frame loop sees no new character at a death (log of 2026-09-27), the animation's flag does.
walk_key.toggle.value = True
player.anim = sdk_stubs.types.SimpleNamespace(ATTRIBUTE_is_in_ffyl=False)
frame.on_frame(player.anim, 40 * S)
press("IE_Pressed")
frame.on_frame(player.anim, 40 * S + 1)
check("toggled, the walk goes on while the player stands", walk_key.walking() is True)
player.anim.ATTRIBUTE_is_in_ffyl = True
frame.on_frame(player.anim, 40 * S + 2)
check("toggled, going down ends the walk: the player never comes back walking slowly", walk_key.walking() is False)
check("and the log says why", any(line.endswith("slow walk ended: downed") for line in state["misc"]))
player.anim.ATTRIBUTE_is_in_ffyl = False
frame.on_frame(player.anim, 40 * S + 3)
check("back up, the walk stays off until the key is pressed again", walk_key.walking() is False)
walk_key.toggle.value = False
press("IE_Pressed")
player.anim.ATTRIBUTE_is_in_ffyl = True
frame.on_frame(player.anim, 40 * S + 4)
check("held, going down leaves the key alone: its release ends the walk", walk_key.walking() is True)
press("IE_Released")
player.anim.ATTRIBUTE_is_in_ffyl = False
frame.stop_all()

# Kevin, 2026-09-26: the slow walk is a speed, so it sits with the speeds, and the auto sprint's page keeps its switch.
check("the slow walk sits on the Movement page, after the speeds",
      [option.identifier for option in menu.movement.children]
      == ["walk_speed", "sprint_speed", "walk", "walk_key", "walk_toggle", "walk_key_speed"])
check("the auto sprint's page holds its switch alone",
      [option.identifier for option in menu.auto_sprint.children] == ["auto_sprint"])

# Full pack only (Kevin, 2026-09-26): a separate file would show a slow walk that only half works, so it shows none.
for carried in (("Auto sprint",), ("Movement",)):
    pack.CARRIES = carried
    alone = importlib.reload(menu)
    check(f"a separate {carried[0]} file shows no slow walk at all",
          all(option.identifier not in ("walk", "walk_key", "walk_toggle", "walk_key_speed")
              for group in alone.ALL for option in group.children)
          and not pack.carries_module("slow_walk"))
pack.CARRIES = ()
importlib.reload(menu)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
