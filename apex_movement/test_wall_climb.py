"""Tests the wall climb as a movement: a trace only in the air, a climb pushing up and into the wall, its sliders, the
height, the wait, the game's mantle, and stop."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import game, jump_press, settings, wall_climb  # noqa: E402

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
movement = player.CharacterMovement

wall_climb.update(player, 0)
check("without a player controller the mantle hold is left alone", notes("mantle without the jump key") == 0)
sdk_stubs.use_character(state, player)
pc = state["pc"]
game.refresh(0)
arms = sdk_stubs.add_arms(state, player)
wall_climb.update(player, 0)
check("the game mantles without the jump key held: its 0.075 s hold goes to 0", pc.MinPassiveMantleButtonHoldDuration == 0.0)
check("logged once", notes("mantle without the jump key on") == 1)
check("on the ground nothing is traced and nothing written", kismet.calls == [] and movement.Velocity.Z == 0.0)
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
wall_climb.update(player, 10 * MS)
check("in the air a trace per height looks for a wall; without one nothing starts",
      len(kismet.calls) == 5 and notes("wall climb") == 0)

kismet.hit = (120.0, sdk_stubs.vector(-1.0, 0.0, 0.0))
player.input = sdk_stubs.vector(1.0, 0.0)
player.JumpCurrentCount = 1
wall_climb.update(player, 20 * MS)
check("a jump at a wall, stick and camera toward it, starts a climb", notes("wall climb start distance=60 stick_deg=0 view_deg=0") == 1)
check("the arms play the climb up for the longest climb, 372 at 370 a second leaning all the way", len(arms.plays) == 1
      and arms.plays[0]["SlotNodeName"] == "FullBody" and arms.plays[0]["LoopCount"] == 5)
check("the climb writes 370 up and leans into the wall",
      (movement.Velocity.X, movement.Velocity.Y, movement.Velocity.Z) == (100.0, 0.0, 370.0))
check("no Croix while the game does not allow a mantle", state["injections"] == [])
movement.mantle_allowed = True
wall_climb.update(player, 100 * MS)
wall_climb.update(player, 110 * MS)
check("while it allows one, Croix is pressed every frame", len(state["injections"]) == 2
      and str(state["injections"][0][2]["Action"].Name) == "Action_Jump_HoldToGlide")
check("and the log says so once per climb", notes("wall climb hoist: jump pressed while the game allows a mantle") == 1)
state["inject_function"] = None
jump_press.forget()
movement.Velocity = sdk_stubs.vector(0.0, 0.0, 0.0)
wall_climb.update(player, 120 * MS)
check("a failed press is reported once and the climb goes on", sum("hoist failed" in line for line in state["errors"]) == 1
      and movement.Velocity.Z == 370.0)
movement.mantle_allowed = False
player.location = sdk_stubs.vector(0.0, 0.0, 471.0)
wall_climb.update(player, 500 * MS)
check("short of twice the character's height the climb goes on", notes("wall climb end") == 0)
player.location = sdk_stubs.vector(0.0, 0.0, 472.0)
movement.Velocity = sdk_stubs.vector(0.0, 0.0, 0.0)
wall_climb.update(player, 1000 * MS)
check("twice the height, 2 x 93 x 2, ends it with its rise, time and lean",
      notes("wall climb end reason=height rise=372 ms=980 lean=0") == 1)
check("and nothing is written any more", movement.Velocity.Z == 0.0)
check("the climb's end stops the arms' animation", arms.stops == [(0.2, "FullBody")])
wall_climb.update(player, 1500 * MS)
check("within the wait no climb starts", notes("wall climb start") == 1)
wall_climb.update(player, 2500 * MS)
check("once the wait is over the next climb starts", notes("wall climb start") == 2)

settings.climb_speed.value = 500
wall_climb.update(player, 2600 * MS)
check("the climb speed follows its slider", movement.Velocity.Z == 500.0)
movement.MovementMode = sdk_stubs.Mode("MOVE_Custom")
movement.ReplicatedMantleState.ActionIndex = 0
traces = len(kismet.calls)
wall_climb.update(player, 2700 * MS)
check("the game's mantle ends it", notes("wall climb end reason=mantle rise=0 ms=200") == 1)
check("out of the air nothing is traced", len(kismet.calls) == traces)

movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
movement.ReplicatedMantleState.ActionIndex = -1
settings.climb_height.value = 100
wall_climb.update(player, 2800 * MS)
check("a mantle leaves no wait", notes("wall climb start") == 3)
player.location = sdk_stubs.vector(0.0, 0.0, 658.0)
wall_climb.update(player, 2900 * MS)
check("the height follows its slider, in percent of the character's height", notes("wall climb end reason=height rise=186 ms=100") == 1)
wall_climb.update(player, 3000 * MS)
check("that end blocks the next climb", notes("wall climb start") == 3)
settings.reclimb_delay.value = 0.0
stops = len(arms.stops)
wall_climb.stop(player)
check("stop is logged", notes("wall climb off") == 1)
check("stop outside a climb stops no animation", len(arms.stops) == stops)
check("stop puts the game's mantle hold back", pc.MinPassiveMantleButtonHoldDuration == 0.075)
wall_climb.update(player, 3100 * MS)
check("stop forgets the climb and its wait", notes("wall climb start") == 4)
wall_climb.stop(player)
check("stop during a climb stops the arms' animation", len(arms.stops) == stops + 1)

wall_climb.reset()
settings.climb_height.value = 200
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
movement.mantle_allowed = False
player.location = sdk_stubs.vector(0.0, 0.0, 100.0)
player.JumpCurrentCount = 1
wall_climb.update(player, 5000 * MS)
check("a new climb starts after a jump", notes("wall climb start") == 5)
check("with one jump counted, nothing is written", player.JumpCurrentCount == 1 and notes("both jumps are back") == 0)
player.location = sdk_stubs.vector(0.0, 0.0, 150.0)
player.JumpCurrentCount = 2
movement.CurrentJump = types.SimpleNamespace(JumpType=types.SimpleNamespace(TagName="Movement.JumpType.DoubleJump"))
wall_climb.update(player, 5100 * MS)
check("a jump from the wall ends the climb", notes("wall climb end reason=jump") == 1)
check("and the jump is written down", notes("air jump count=2 type=DoubleJump") == 1)
wall_climb.update(player, 5200 * MS)
check("the climb gives the next jump back, Croix being free", player.JumpCurrentCount == 1
      and notes("jump from the climb: the next jump is back: jump count 2 -> 1") == 1)
player.JumpCurrentCount = 2
wall_climb.update(player, 5300 * MS)
check("a climb starting again brings the count back to one jump used", player.JumpCurrentCount == 1)

wall_climb.reset()
player.location = sdk_stubs.vector(0.0, 0.0, 100.0)
player.JumpCurrentCount = 2
player.bPressedJump = True
wall_climb.update(player, 7000 * MS)
check("a climb started with both jumps used gives nothing back while Croix is held", player.JumpCurrentCount == 2)
player.bPressedJump = False
wall_climb.update(player, 7010 * MS)
check("once Croix is free, both jumps are back", player.JumpCurrentCount == 1
      and notes("wall climb: both jumps are back: jump count 2 -> 1") == 1)

# The diagonal: the stick pushed to a side tips the climb, and the end line tells the fullest lean of it.
wall_climb.reset()
state["misc"].clear()
settings.climb_speed.value = 370
settings.climb_height.value = 200
settings.reclimb_delay.value = 1.2
movement.MovementMode = sdk_stubs.Mode("MOVE_Falling")
movement.mantle_allowed = False
player.location = sdk_stubs.vector(0.0, 0.0, 0.0)
player.JumpCurrentCount = 1
player.bPressedJump = False
player.input = sdk_stubs.vector(0.70711, 0.70711)
movement.Velocity = sdk_stubs.vector(0.0, 0.0, 0.0)
wall_climb.update(player, 9000 * MS)
check("a stick pushed 45 degrees to a side starts a climb", notes("wall climb start") == 1
      and notes("stick_deg=45") == 1)
check("and the climb goes up and along the wall in equal parts",
      round(movement.Velocity.Z) == 262 and round(movement.Velocity.Y) == 262)
check("while still leaning into the wall", round(movement.Velocity.X) == 100)
player.location = sdk_stubs.vector(0.0, 0.0, 400.0)
wall_climb.update(player, 9500 * MS)
check("the end line tells the fullest lean of the climb", notes("lean=45") == 1)

settings.climb_lean.value = 0
wall_climb.reset()
player.location = sdk_stubs.vector(0.0, 0.0, 0.0)
movement.Velocity = sdk_stubs.vector(0.0, 0.0, 0.0)
wall_climb.update(player, 11000 * MS)
check("with the diagonal set to zero the same stick climbs straight up",
      round(movement.Velocity.Z) == 370 and round(movement.Velocity.Y) == 0)
settings.climb_lean.value = 60

# A try that starts no climb explains itself when the player lands.
wall_climb.reset()
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
kismet.hit = (120.0, sdk_stubs.vector(-1.0, 0.0, 0.0))

# A face only the traces below the waist meet is a step, and a step must not steal the jump leaving the ground.
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
check("seen at the character's own height too, it is a wall and the climb starts",
      notes("wall climb start distance=70") == 1)
check("and a climb never slows a rise already faster than itself", movement.Velocity.Z == 912.0)

wall_climb.reset()
state["misc"].clear()
player.location = sdk_stubs.vector(0.0, 0.0, 0.0)
kismet.hits_by_z = {round(-1.2 * 93.0): (120.0, sdk_stubs.vector(-0.5, 0.0, 0.87)),
                    0: (140.0, sdk_stubs.vector(-1.0, 0.0, 0.0))}
wall_climb.update(player, 25000 * MS)
check("a beam grazed at one height does not hide the upright panel at another",
      notes("wall climb start distance=80") == 1)
kismet.hits_by_z = None

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
