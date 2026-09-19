"""Tests the mod as a whole: menu and hook registered, enabled on a fresh install, disable restores the game."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
state["settings_exists"] = False
sys.modules["auto_sprint"] = types.ModuleType("auto_sprint")

import apex_movement  # noqa: E402
from apex_movement import frame, menu, ownership, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


mod = state["mods"][0]
check("the mod is named Apex Movement", mod.kwargs["name"] == "Apex Movement")
check("the menu is registered", mod.kwargs["options"] == menu.MENU)
check("the frame hook is registered", mod.kwargs["hooks"] == [frame.tick])
check("the frame hook listens to the animation update", frame.tick.path == "/Script/Engine.AnimInstance:BlueprintUpdateAnimation")
check("the frame hook carries the package's own name, so that a separate file never replaces it",
      frame.tick.identifier == "apex_movement:frame")
check("a fresh install enables the mod", mod.is_enabled)
check("enabling with Auto Sprint loaded warns about it", any("Auto Sprint" in line for line in state["warnings"]))

player = sdk_stubs.FakeCharacter()
sdk_stubs.use_character(state, player)
player.input = sdk_stubs.vector(1.0, 0.0)
frame.tick(player.anim, None, None, None)
movement = player.CharacterMovement
check("a frame runs auto sprint", movement.bWantsToSprint is True and movement.MinAnalogWalkSpeed == 672.0)
check("a frame lets the game mantle without the jump key", state["pc"].MinPassiveMantleButtonHoldDuration == 0.0)
asset = sdk_stubs.slide_asset(state)
check("a frame binds the air crouch keys", "Gamepad_FaceButton_Right" in state["keybinds"])
check("a frame runs momentum slides", asset.LaunchDirection.RelativeDirection is sdk_stubs.Direction.ParentVelocity2D)
dash_asset = sdk_stubs.dash_asset(state)
slope_keys = asset.SpeedSlopeScaleCurve.EditorCurveData.keys
check("a frame runs slide physics, the game's slope effect kept switched on but flat",
      asset.Duration.constant == 30.0 and asset.bUseSlopeCurve is True and [key.Value for key in slope_keys] == [1.0] * 4)
check("a frame runs the longer dash and, the Axle slide being off, leaves the game's slide steering",
      asset.MoveLRRate.constant == 55.0 and abs(dash_asset.Duration.constant - 0.5332) < 1e-9)
settings.axle_slide.value = True
movement.bIsSprinting = True
frame.tick(player.anim, None, None, None)
check("with the Axle slide on, a frame steers slides", asset.MoveLRRate.constant == 350.0)
check("a sprint frame runs the slide speed, boosted by the Axle slide",
      abs(asset.speed.constant * 1.15 * 1.1017 - 1412.5) < 0.01)
settings.axle_slide.value = False
frame.tick(player.anim, None, None, None)
check("switching the Axle slide off puts the game's slide steering back", asset.MoveLRRate.constant == 55.0)
settings.axle_slide.value = True
frame.tick(player.anim, None, None, None)
check("a frame runs air strafe and heavier fall", movement.MaxAcceleration == 24000.0
      and abs(movement.GravityScale - 2.0) < 1e-9 and movement.goals["DefaultJump"].GoalHeight > 198.0)

movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
state["kismet"].hit = (60.0, sdk_stubs.vector(-1.0, 0.0, 0.0))
player.JumpCurrentCount = 1
frame.tick(player.anim, None, None, None)
check("a frame in the air at a wall runs the wall climb", movement.Velocity.Z == 370.0)
movement.MovementMode = sdk_stubs.Mode("MOVE_Walking")

errors_before = list(state["errors"])
mod.disable()
check("disabling releases the sprint", movement.bWantsToSprint is False)
check("disabling puts the game's ground speed back", movement.MinAnalogWalkSpeed == 0.0)
check("disabling puts the game's slide speed back", asset.speed.constant == 720.0)
check("disabling puts the game's slide direction back",
      asset.LaunchDirection.RelativeDirection is sdk_stubs.Direction.ParentAimDirection2D)
check("disabling gives the crouch key back to the game", state["keybinds"] == {})
check("disabling puts the game's gravity and acceleration back",
      (movement.GravityScale, movement.MaxAcceleration, movement.AirControl) == (1.0, 2048.0, 0.6))
check("disabling puts the game's slide timer and curves back", asset.Duration.constant == 1.35
      and [key.Value for key in slope_keys] == [0.5, 1.0, 2.0, 2.0]
      and asset.SpeedScaleCurve.EditorCurveData.keys[3].Value == 0.3722)
check("disabling puts the game's slide steering and dash back", asset.MoveLRRate.constant == 55.0
      and dash_asset.Duration.constant == 0.33 and dash_asset._keys[3].time == 0.33)
check("disabling puts every jump height back", movement.goals["DefaultJump"].GoalHeight == 198.0
      and movement.goals["SprintJump"].InitialZVelocity == 735.0)
check("disabling puts the game's mantle hold back", state["pc"].MinPassiveMantleButtonHoldDuration == 0.075)
check("disabling is logged", any("disabled" in line for line in state["misc"]))
check("disabling stops the frame hook", not frame.tick.enabled)
# Every movement registered has a stop: one without it wrote an error at every disable since 0.10.2 (review,
# 2026-09-18), and no test looked at the errors a disable writes.
new_errors = state["errors"][len(errors_before):]
check("disabling writes no error" + (f" (found {new_errors})" if new_errors else ""), new_errors == [])

settings.dash_distance.value = 10000
mod.enable()
check("switching on brings a hand-edited setting back within its slider, and says so",
      settings.dash_distance.value == 300 and any("dash_distance=10000" in line for line in state["warnings"]))

# The title screen (2026-09-19, 06:40:34): switched off with the character gone and Move_Slide unloaded by the game.
frame.tick(player.anim, None, None, None)
check("switched back on, the mod writes the slide again", asset.Duration.constant == 30.0)
del state["objects"][("OakControlledMove", sdk_stubs.SLIDE_PATH)]
sdk_stubs.use_character(state, None)
errors_before = list(state["errors"])
mod.disable()
new_errors = state["errors"][len(errors_before):]
check("switched off at the title screen, it writes no error" + (f" (found {new_errors})" if new_errors else ""),
      new_errors == [])
check("and says the game values are restored, the unloaded slide's left to the game",
      "[Apex Movement] disabled, game values restored" in state["misc"][-2:]
      and any("unloaded" in line for line in state["misc"][-2:]))
reloaded = sdk_stubs.FakeSlideAsset()
state["objects"][("OakControlledMove", sdk_stubs.SLIDE_PATH)] = reloaded
sdk_stubs.use_character(state, player)
mod.enable()
frame.tick(player.anim, None, None, None)
check("the next game, the slide the game loaded again is written", reloaded.Duration.constant == 30.0
      and reloaded.MoveLRRate.constant == 350.0)
mod.disable()
check("and switched off, it gets the game's own values back", reloaded.Duration.constant == 1.35
      and reloaded.MoveLRRate.constant == 55.0)
mod.enable()



def stuck_put(value: float) -> None:
    if value == 1.0:
        raise RuntimeError("the game refused it")


ownership.write("test.stuck", ownership.ASSET, lambda: 1.0, stuck_put, 2.0)
mod.disable()
check("a switch-off that could not put a value back does not claim it did",
      state["misc"][-1] == "[Apex Movement] disabled, 1 game value could not be restored")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
