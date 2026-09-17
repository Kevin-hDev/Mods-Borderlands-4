"""Tests the air actions: dash direction from the camera, each request kept until the game is done, chains, stop."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import air_actions  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


MS = 1_000_000
player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement
data = movement.ControlledMoveReplicationData
asset = sdk_stubs.slide_asset(state)
A = air_actions


class Move:
    """A controlled move whose text reads like the game's."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"OakControlledMove'/Game/PlayerCharacters/_Shared/Tricks/ControlledMoves/{self.name}.{self.name}'"


def direction(x: float, y: float, yaw: float) -> int:
    player.input, player.yaw = sdk_stubs.vector(x, y), yaw
    return A.dash_direction(player)


check("a stick at rest dashes forward", direction(0.0, 0.0, 0.0) == A.FORWARD)
check("stick along the camera dashes forward", direction(1.0, 0.0, 0.0) == A.FORWARD)
check("stick against the camera dashes back", direction(-1.0, 0.0, 0.0) == A.BACK)
check("stick to +Y with the camera on +X dashes right", direction(0.0, 1.0, 0.0) == A.RIGHT)
check("stick to -Y with the camera on +X dashes left", direction(0.0, -1.0, 0.0) == A.LEFT)
check("the camera turned 90 degrees turns the directions", direction(0.0, 1.0, 90.0) == A.FORWARD)
check("a diagonal picks the larger part", direction(0.9, 0.3, 0.0) == A.FORWARD)

player.input, player.yaw = sdk_stubs.vector(0.0, 1.0), 0.0
A.start_dash(player, 0)
check("a dash is asked in the stick's direction", player.calls == [("SetWantsToDash", True, A.RIGHT)])
check("the dash request is logged", any("air dash asked direction=3" in line for line in state["misc"]))
A.start_dash(player, 1 * MS)
check("a tap before the dash has started changes nothing", len(player.calls) == 1)
A.update(player, 5 * MS)
check("the request stays while the dash has not started", len(player.calls) == 1)
data.ControlledMove = Move("Move_Dash")
A.update(player, 9 * MS)
check("a started dash keeps its request", len(player.calls) == 1)
check("the start is logged", any("air dash started after_ms=9" in line for line in state["misc"]))
A.update(player, 300 * MS)
check("the request is kept while the dash runs, since releasing it ends the dash", len(player.calls) == 1)
data.ControlledMove = None
A.update(player, 333 * MS)
check("the dash's end releases the request", player.calls[-1] == ("SetWantsToDash", False, A.RIGHT))
check("the end is logged", any("air dash ended after_ms=333" in line for line in state["misc"]))

A.start_dash(player, 1000 * MS)
data.ControlledMove = Move("Move_Dash")
A.update(player, 1009 * MS)
A.update(player, 1999 * MS)
check("a dash still shown just under 1 s keeps its request", player.calls[-1] == ("SetWantsToDash", True, A.RIGHT))
A.update(player, 2009 * MS)
check("past 1 s the request is released whatever the game shows", player.calls[-1] == ("SetWantsToDash", False, A.RIGHT))

data.ControlledMove = None
A.start_dash(player, 3000 * MS)
data.ControlledMove = Move("Move_Dash")
A.update(player, 3009 * MS)
player.input = sdk_stubs.vector(0.0, -1.0)
calls = len(player.calls)
A.start_dash(player, 3150 * MS)
check("a tap during a dash ends it", player.calls[calls:] == [("SetWantsToDash", False, A.RIGHT)])
check("the chain is logged", any("air dash chained after_ms=150" in line for line in state["misc"]))
A.update(player, 3150 * MS)
check("the next dash is not asked in the same frame", len(player.calls) == calls + 1)
A.update(player, 3160 * MS)
check("the next frame asks the next dash in the stick's new direction", player.calls[-1] == ("SetWantsToDash", True, A.LEFT))
A.update(player, 3170 * MS)
check("the old move still shown is not taken for the new dash", state["misc"][-1].endswith("air dash asked direction=1"))
data.PackedDirection = sdk_stubs.vector(0.0, -100.0)
A.update(player, 3180 * MS)
check("a new direction shown is the new dash", state["misc"][-1].endswith("air dash started after_ms=20"))
data.ControlledMove = None
A.update(player, 3500 * MS)
check("the chained dash's end releases it", player.calls[-1] == ("SetWantsToDash", False, A.LEFT))
calls = len(player.calls)
A.update(player, 3600 * MS)
check("nothing more is asked after the chain", len(player.calls) == calls)

data.ControlledMove = Move("Move_Dash")
A.start_dash(player, 4000 * MS)
A.update(player, 4200 * MS)
check("the same move still shown is not a new dash", player.calls[-1] == ("SetWantsToDash", True, A.LEFT))
A.update(player, 4300 * MS)
check("a dash not started in 300 ms is released", player.calls[-1] == ("SetWantsToDash", False, A.LEFT))
check("and logged as not started, as with an empty reserve", any("air dash not started after_ms=300" in line for line in state["misc"]))
data.ControlledMove = None
data.PackedDirection = sdk_stubs.vector(0.0, 0.0)

player.calls.clear()
A.start_slide(player, 1000 * MS, 672.0, 550.0)
check("a landing slide is asked", player.calls == [("SetWantsToSlide", True)])
check("the slide request is logged with its speeds", any("landing slide asked speed_in=672 min=550" in line for line in state["misc"]))
A.start_slide(player, 1001 * MS, 672.0, 550.0)
check("a second slide waits for the first", len(player.calls) == 1)
check("and the log says why it was not asked",
      any("landing slide not asked speed_in=672: the last one is still watched" in line for line in state["misc"]))
data.ControlledMove = asset
A.update(player, 1009 * MS)
check("a started slide is logged", any("landing slide started after_ms=9" in line for line in state["misc"]))
check("the request is kept during the slide", len(player.calls) == 1)
data.ControlledMove = None
A.update(player, 2300 * MS)
check("the slide's end releases the request", player.calls[-1] == ("SetWantsToSlide", False))

A.start_slide(player, 3000 * MS, 900.0, 550.0)
data.ControlledMove = asset
A.update(player, 3010 * MS)
A.update(player, 4600 * MS)
check("a long downhill slide keeps its request past 1.6 s", player.calls[-1] == ("SetWantsToSlide", True))
A.update(player, 33000 * MS)
check("a slide as long as slide physics allows keeps its request", player.calls[-1] == ("SetWantsToSlide", True))
A.update(player, 38000 * MS)
check("a slide still running past that is released", player.calls[-1] == ("SetWantsToSlide", False))
data.ControlledMove = None

A.start_slide(player, 40000 * MS, 900.0, 550.0)
A.update(player, 40300 * MS)
check("a slide not yet started keeps its request", player.calls[-1] == ("SetWantsToSlide", True))
A.update(player, 40400 * MS)
check("a slide not started in 400 ms is released", player.calls[-1] == ("SetWantsToSlide", False))
check("and logged", any("landing slide not started within_ms=400" in line for line in state["misc"]))

A.slam(player)
check("a slam is asked and its result logged", player.calls[-1] == ("AttemptGroundSlam",)
      and any("air slam asked started=True" in line for line in state["misc"]))

player.calls.clear()
player.input = sdk_stubs.vector(0.0, 1.0)
A.start_dash(player, 6000 * MS)
A.start_slide(player, 6000 * MS, 900.0, 550.0)
A.stop(player)
check("stop releases a dash and a slide still asked", ("SetWantsToDash", False, A.RIGHT) in player.calls
      and ("SetWantsToSlide", False) in player.calls)
calls = len(player.calls)
A.stop(player)
check("a second stop calls nothing", len(player.calls) == calls)

A.start_dash(player, 7000 * MS)
A.forget()
A.stop(player)
check("forget drops the watches without calling the game", len(player.calls) == calls + 1)
A.start_dash(player, 8000 * MS)
data.ControlledMove = Move("Move_Dash")
A.update(player, 8009 * MS)
A.start_dash(player, 8100 * MS)
A.forget()
calls = len(player.calls)
A.update(player, 8200 * MS)
check("forget also drops a dash waiting to be chained", len(player.calls) == calls)
data.ControlledMove = None
A.stop(None)
check("stop without a character does not raise", True)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
