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

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
