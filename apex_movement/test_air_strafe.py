"""Tests air strafe: acceleration from the slider, Kevin's air control, logged on change, put back on stop."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import air_strafe, ownership, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


player = sdk_stubs.FakeCharacter()
movement = player.CharacterMovement

air_strafe.update(player, 0)
check("the acceleration follows the slider, 24000 by default", movement.MaxAcceleration == 24000.0)
check("air control is Kevin's Player Movement value", movement.AirControl == 20.0)
check("the change is logged", sum("air strafe acceleration 24000" in line for line in state["misc"]) == 1)
air_strafe.update(player, 1)
check("an unchanged frame logs nothing", sum("air strafe" in line for line in state["misc"]) == 1)

settings.air_acceleration.value = 32000
air_strafe.update(player, 2)
check("a new slider value applies at once", movement.MaxAcceleration == 32000.0)
check("the game's values are kept", ownership.original(air_strafe.ACCELERATION_KEY) == 2048.0
      and ownership.original(air_strafe.AIR_CONTROL_KEY) == 0.6)
settings.air_acceleration.value = 24000

air_strafe.stop(player)
check("stop puts the game's values back", movement.MaxAcceleration == 2048.0 and movement.AirControl == 0.6)
check("nothing stays owned", not ownership.is_owned(air_strafe.ACCELERATION_KEY))
check("the restore is logged once", sum("air strafe off" in line for line in state["misc"]) == 1)
air_strafe.stop(player)
check("a stop with nothing written logs nothing", sum("air strafe off" in line for line in state["misc"]) == 1)

# One value that cannot be put back must not keep the next one from it (review, 2026-09-18): each is tried, and the
# failure is raised once all were, for the frame loop to report.
air_strafe.update(player, 3)
entry = ownership._entries[air_strafe.ACCELERATION_KEY]
put = entry["put"]


def refuse(value: float) -> None:
    raise AttributeError("the movement component is gone")


entry["put"] = refuse
stop_error = ""
try:
    air_strafe.stop(player)
except Exception as exc:
    stop_error = str(exc)
check("an acceleration that cannot be put back does not keep the air control from it", movement.AirControl == 0.6)
check("its failure is raised for the frame loop to report", air_strafe.ACCELERATION_KEY in stop_error)
check("and the game's acceleration is kept to put back later",
      ownership.original(air_strafe.ACCELERATION_KEY) == 2048.0)
entry["put"] = put
air_strafe.stop(player)
check("the next stop puts it back", movement.MaxAcceleration == 2048.0)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
