"""Tests Axle slide steering: the rate follows the slider through a whole struct, logged on change, put back on stop.

Switching it on and off with the Axle slide is the frame's job, tested in test_apex_movement.py.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import game, ownership, settings, slide_steering  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(text: str) -> int:
    return sum(text in line for line in state["misc"])


player = sdk_stubs.FakeCharacter()
asset = sdk_stubs.slide_asset(state)

slide_steering.update(player, 0)
check("the Axle rate is Kevin's 350 by default, through a whole struct", asset.MoveLRRate.constant == 350.0)
check("the game's 55 is kept to put back", ownership.original(slide_steering.RATE_KEY) == 55.0)
check("the change is logged", notes("axle slide steering 350 degrees a second") == 1)
slide_steering.update(player, 1)
check("an unchanged frame logs nothing", notes("slide steering") == 1)

settings.axle_steering.value = 450
slide_steering.update(player, 2)
check("a new slider value applies at once", asset.MoveLRRate.constant == 450.0)
check("the game's value stays the one kept", ownership.original(slide_steering.RATE_KEY) == 55.0)
settings.axle_steering.value = 350

slide_steering.stop(player)
check("stop puts the game's rate back", asset.MoveLRRate.constant == 55.0 and not ownership.is_owned(slide_steering.RATE_KEY))
check("the restore is logged", notes("game slide steering restored") == 1)
slide_steering.stop(player)
check("a stop with nothing written logs nothing", notes("game slide steering restored") == 1)

del state["objects"][("OakControlledMove", sdk_stubs.SLIDE_PATH)]
game.forget()
slide_steering.update(player, 3)
check("a slide asset not loaded yet is reported once and skipped", len(state["errors"]) == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
