"""Tests the saves of the CONTROLS page, Restore and Undo: all values together, or none and the previous ones kept."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

state = heirloom_stubs.install()

from apex_heirloom import control_actions, holster_settings, mod  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


saves = state["settings_saves"]
check("values are set and saved together",
      control_actions.save_values(mod, ((holster_settings.keyboard_hold, False), (holster_settings.hold_time, 0.6)))
      and holster_settings.keyboard_hold.value is False and holster_settings.hold_time.value == 0.6
      and state["settings_saves"] == saves + 1)
state["refuse_saves"] = True
check("a refused save puts every value back", not control_actions.save_values(
    mod, ((holster_settings.keyboard_hold, True), (holster_settings.hold_time, 0.8)))
      and holster_settings.keyboard_hold.value is False and holster_settings.hold_time.value == 0.6)
check("and says it once, without detail", len(state["errors"]) == 1 and "could not be saved" in state["errors"][0])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
