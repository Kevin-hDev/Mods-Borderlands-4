"""Tests the commands the COMMANDS page sets (sketch I1, 2026-09-30): PUT AWAY then INSPECT, each a keyboard/mouse key
and a controller button, their options the keys' own, each served by its part's switch; the keys Restore puts back."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()

from apex_heirloom import control_config as config, heirloom_settings, holster_settings  # noqa: E402
from apex_heirloom import inspect_keys, keys  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("two commands, PUT AWAY then INSPECT, as the sketch's cards",
      [command.name for command in config.COMMANDS] == ["put_away", "inspect"])
put_away, inspect = config.COMMANDS
check("putting away sets the holster's two keys, served by its switch",
      put_away.keyboard is keys.keyboard_key and put_away.controller is keys.controller_key
      and put_away.binds == (keys.keyboard_bind, keys.controller_bind)
      and put_away.part == holster_settings.holster.identifier)
check("inspecting sets the heirloom's two keys, served by its switch",
      inspect.keyboard is inspect_keys.keyboard_key and inspect.controller is inspect_keys.controller_key
      and inspect.binds == (inspect_keys.keyboard_bind, inspect_keys.controller_bind)
      and inspect.part == heirloom_settings.heirloom.identifier)
check("a keyboard row then a controller row per card",
      config.SLOTS == (("put_away", "keyboard"), ("put_away", "controller"),
                       ("inspect", "keyboard"), ("inspect", "controller")))
check("Restore and Undo save the four keys",
      config.ALL == (keys.keyboard_key, keys.controller_key, inspect_keys.keyboard_key, inspect_keys.controller_key))
check("put back, the put-away keys take their defaults and the inspection's none (Kevin, 2026-09-30)",
      keys.controller_key.default_value == "Gamepad_FaceButton_Left"
      and inspect_keys.keyboard_key.default_value is None and inspect_keys.controller_key.default_value is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
