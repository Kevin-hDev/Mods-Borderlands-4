"""Tests the mod as mods_base builds it: name, a fresh install, switching off and on, living beside the other mods."""

import pathlib
import sys

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

import omni_sprint  # noqa: E402
from omni_sprint import camera, frame  # noqa: E402
from apex_camera_runtime import movement_definition as definition  # noqa: E402

mod = state["mods"][0]
from omni_sprint import panel_preferences, settings  # noqa: E402
from apex_camera_runtime.keyboard_layout import (RIGHT_OF_TAB, TOP_ROW_EIGHT, TOP_ROW_SEVEN, TOP_ROW_SIX,  # noqa: E402
                                                 key_at)
FREE_LOOK, SIX, SEVEN = key_at(RIGHT_OF_TAB, "Q"), key_at(TOP_ROW_SIX, "Six"), key_at(TOP_ROW_SEVEN, "Seven")
EIGHT = key_at(TOP_ROW_EIGHT, "Eight")
check("one mod, named Omni Sprint, with the camera settings and its window's language and page, both hidden",
      len(state["mods"]) == 1 and mod.kwargs["name"] == "Omni Sprint"
      and mod.kwargs["options"] == [*settings.OPTIONS, *panel_preferences.ALL]
      and all(option.is_hidden for option in panel_preferences.ALL))
check("the FOV option is off by default, its slider from 70 to 150",
      settings.custom_fov.value is False and (settings.fov.min_value, settings.fov.max_value) == (70, 150))
check("a fresh install switches it on and says its version",
      mod.is_enabled and state["misc"][-1] == f"[Omni Sprint] enabled, version {omni_sprint.__version__}")
check("its one hook is the clock, under the mod's own identifier: Apex Movement and Vehicle Driving use theirs on the "
      "same function, and two identifiers never replace each other",
      mod.kwargs["hooks"] == [frame.tick] and frame.tick.identifier == "omni_sprint:frame" and frame.tick.enabled)
check("P, Six, Seven, Eight, the key right of Tab and L3 are the default camera keys (the last two for Free Look, "
      "read each frame)",
      set(state["keybinds"]) == {"P", SIX, SEVEN, EIGHT, FREE_LOOK, "Gamepad_LeftThumbstick"})
source = pathlib.Path(omni_sprint.__file__).parent
text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(source.glob("*.py")))
check("nothing Apex Movement or Vehicle Driving writes is named: sprint request, slide, speeds, vehicle",
      not any(word in text for word in ("bWantsToSprint", "Move_Slide", "MinAnalogWalkSpeed", "MaxWalkSpeed",
                                        "OakVehicleMovement", "VehicleDriverComponent")))

fake = sdk_stubs.FakeMemory()
sdk_stubs.patch(fake)
COMPONENT, SIREN = sdk_stubs.BASE + 0x1000, sdk_stubs.BASE + 0x20000
fake.put_definition(SIREN, definition.KNOWN)
fake.put_pointer(COMPONENT + 0x1CF0, SIREN)
state["pc"] = sdk_stubs.player(COMPONENT)
frame.tick(sdk_stubs.body(state["pc"]), None, None, None)
check("in game, its switch opens the limit through the shared camera runtime", fake.get_float(SIREN + 580) == 180.0)
mod.disable()
check("switched off, the runtime puts the game's limit back and says so",
      fake.get_float(SIREN + 580) == 60.0
      and "[Camera Runtime] stopped, game sprint limit put back in 1 movement definition(s)" in state["misc"]
      and state["misc"][-1] == "[Omni Sprint] disabled")
check("its hook stops", not frame.tick.enabled)
mod.enable()
frame.tick(sdk_stubs.body(state["pc"]), None, None, None)
check("switched on again, the limit opens again at once", fake.get_float(SIREN + 580) == 180.0)

fake.put_float(SIREN + sdk_stubs.OFFSETS["LadderFriction"], 2.0)
mod.disable()
check("a definition gone from memory is left alone and the line says so",
      fake.get_float(SIREN + 580) == 180.0 and any("1 left alone" in line for line in state["misc"][-3:]))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
