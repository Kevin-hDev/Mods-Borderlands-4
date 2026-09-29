"""Tests the settings: both keys held by default, Off to press, a hold never shorter than the game's reload
tap."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


heirloom_stubs.install()

from apex_heirloom import holster_settings  # noqa: E402
from apex_heirloom.key_press import HOLD, PRESS  # noqa: E402

check("the keyboard key is held by default", holster_settings.mode(holster_settings.KEYBOARD) == HOLD)
check("the controller button is held by default", holster_settings.mode(holster_settings.CONTROLLER) == HOLD)
check("each choice is an On/Off switch, On to hold",
      holster_settings.keyboard_hold.default_value is True and holster_settings.controller_hold.default_value is True)
check("the hold lasts 0.4 s by default", holster_settings.hold_seconds() == 0.4)
check("the hold is never shorter than the game's reload tap (0.2 s)", holster_settings.hold_time.min_value == 0.2)
for edited, meant in ((0, 0.2), (-3, 0.2), (0.05, 0.2), (5, 1.0), (float("nan"), 0.4), ("fast", 0.4), (None, 0.4),
                      (0.6, 0.6)):
    holster_settings.hold_time.value = edited
    check(f"a hold time edited by hand to {edited!r} holds {meant} s", holster_settings.hold_seconds() == meant)
holster_settings.hold_time.value = 0.4
holster_settings.controller_hold.value = False
check("each key reads its own switch: Off presses",
      holster_settings.mode(holster_settings.CONTROLLER) == PRESS
      and holster_settings.mode(holster_settings.KEYBOARD) == HOLD)
holster_settings.keyboard_hold.value = "yes"
check("a malformed saved value keeps the hold", holster_settings.mode(holster_settings.KEYBOARD) == HOLD)
check("the controller's text says why it holds: Square also reloads",
      "Square also reloads" in holster_settings.controller_hold.description)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
