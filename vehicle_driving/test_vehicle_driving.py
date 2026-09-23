"""Tests the mod as mods_base builds it: name, settings, a fresh install, switching off and on, living beside Apex."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = sdk_stubs.install()
state["settings_exists"] = False

import vehicle_driving  # noqa: E402
from vehicle_driving import frame, menu, panel_preferences, settings  # noqa: E402

mod = state["mods"][0]
check("one mod with two visual pages and six original top-level settings",
      len(state["mods"]) == 1 and mod.kwargs["name"] == "Vehicle Driving"
      and mod.kwargs["options"] == [*settings.OPTIONS, *panel_preferences.ALL]
      and [option for group in menu.MENU for option in group.children] == settings.OPTIONS)
check("a fresh install switches it on and says its version",
      mod.is_enabled and state["misc"][-1] == f"[Vehicle Driving] enabled, version {vehicle_driving.__version__}")
check("its one hook is the frame, under the mod's own identifier: Apex Movement's is apex_movement:frame on the same "
      "function, and two identifiers never replace each other (spec section 4)",
      mod.kwargs["hooks"] == [frame.tick] and frame.tick.identifier == "vehicle_driving:frame" and frame.tick.enabled)
check("no key is bound: Apex Movement binds the crouch and jump keys", state["keybinds"] == [])
source = pathlib.Path(vehicle_driving.__file__).parent
text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(source.glob("*.py")))
check("nothing Apex Movement writes is named in the mod: the character's movement, the slide, the keys",
      not any(word in text for word in ("CharacterMovement", "Move_Slide", "keybind(")))

driver = sdk_stubs.Driver()
car = sdk_stubs.Vehicle("OakVehicle_1", driver)
hover = car.OakVehicleMovement.HoverSetup
state["pc"] = types.SimpleNamespace(Pawn=car)
frame.tick(object(), None, None, None)
check("at the wheel the values are set", hover.PowerslideJumpHeight.constant == 330.0)
mod.disable()
check("switched off, the game's values are back and it says so",
      hover.PowerslideJumpHeight.constant == 165.0
      and driver.VehicleDriverComponent.VehicleAttributesState.MaxAccel.BaseValue == 1000.0
      and state["misc"][-1] == "[Vehicle Driving] disabled, game values restored")
check("its hook stops", not frame.tick.enabled)
mod.enable()
frame.tick(object(), None, None, None)
check("switched on again at the wheel, the values come back, once", hover.PowerslideJumpHeight.constant == 330.0)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
