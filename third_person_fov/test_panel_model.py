"""Menu persistence, rollback, camera ownership and restoration use the saved SDK options."""

import pathlib
import sys
import weakref

import sdk_stubs

state = sdk_stubs.install()
assert (pathlib.Path(__file__).parent / "third_person_fov" / "panel_model.py").is_file(), "Camera menu missing"

from third_person_fov import camera, mod, panel_open, panel_preferences as prefs, settings
from third_person_fov.panel_model import Model
from apex_camera_runtime import constants, shared

fails = []


def check(label, condition):
    print(("OK | " if condition else "ECHEC | ") + label)
    if not condition:
        fails.append(label)


model = Model(mod)
check("SDK entry opens the custom window", getattr(mod, panel_open.MARKER, False))
check("only camera settings and five separate command pairs are exposed",
      model.pages == ("camera", "commands") and model.page == "camera"
      and list(model.options) == ["third_person", "shoulder_left", "orbit", "fov", "extended_loot", "loot_reach"]
      and len(model.command_options) == 10)
check("preferences belong to the mod's existing save file",
      all(option in mod.kwargs["options"] and option.mod is mod for option in prefs.ALL))
check("reopening restores the selected page, language and icon family",
      model.change_page("commands") and model.change_language("FR") and model.change_controller_icons("XSX")
      and Model(mod).page == "commands" and Model(mod).language == "FR" and Model(mod).controller_icons == "XSX")
check("settings and keys are retained by a new menu model",
      model.write({"fov": 125}) and model.assign_command("zoom_in", "controller", "Gamepad_LeftShoulder")
      and Model(mod).options["fov"].value == 125
      and Model(mod).command_options["zoom_in_controller"].value == "Gamepad_LeftShoulder")
check("duplicate controller keys are refused", not model.assign_command("zoom_out", "controller", "Gamepad_LeftShoulder"))
state["refuse_save"] = True
check("failed preference save keeps the prior page", not model.change_page("camera") and Model(mod).page == "commands")
check("failed value save keeps the prior FOV", not model.write({"fov": 135}) and settings.fov.value == 125)
state["refuse_save"] = False
settings.zoom.option.value = 450
check("command reset leaves zoom and FOV alone", model.default_commands()
      and settings.zoom.distance() == 450 and settings.fov.value == 125)
model.assign_command("zoom_out", "keyboard", "H")
check("global restore also resets distance and commands", model.restore()
      and settings.zoom.distance() == 300 and settings.fov.value == 110
      and settings.commands.option("zoom_out_key").value is None)
check("Undo restores the whole preceding setup", model.undo()
      and settings.zoom.distance() == 450 and settings.fov.value == 125
      and settings.commands.option("zoom_out_key").value == "H")
check("invalid stored page falls back safely", not model.change_page("unknown"))
prefs.last_page.value = float("nan")
check("corrupt saved page opens Camera", Model(mod).page == "camera")
prefs.last_page.value = 1
owner = shared.shared(weak_ref=weakref.ref, address_of=id)
owner.register("apex_movement", 200, object(), constants.PROTOCOL)
elsewhere = Model(mod)
check("another camera owner hides ineffective controls", elsewhere.camera_elsewhere
      and not elsewhere.restore()
      and not elsewhere.write({"fov": 130}) and not elsewhere.assign_command("orbit", "keyboard", "J"))
owner.unregister("apex_movement")
check("controls return after the other owner leaves", bool(Model(mod).options))
shared.reset_for_tests()
print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
