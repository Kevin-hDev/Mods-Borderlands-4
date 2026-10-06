"""Menu persistence, rollback, camera ownership and restoration use the saved SDK options."""

import pathlib
import sys
import types
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
check("only camera settings, over five pages (Kevin, 2026-10-06), and five separate command pairs are exposed",
      model.pages == ("camera", "aiming", "orbit_camera", "loot", "dynamic_camera", "commands")
      and model.page == "camera"
      and list(model.options) == ["third_person", "shoulder_left", "shoulder_smooth", "orbit_smooth", "shoulder_seconds", "fov", "third_person_ads", "orbit",
                                  "orbit_distance", "extended_loot", "loot_reach", "speed_fov", "speed_fov_gain",
                                  "speed_fov_seconds", "action_framing", "action_framing_strength", "camera_motion",
                                  "camera_motion_strength"]
      and set(model.camera_options) == set(model.options)
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
original_path, original_save = mod.settings_file, mod.save_settings
original_disk = original_path.read_bytes()
# An opaque custom writer cannot prove that disk survived, so compensation must retry.
def opaque_failure():
    raise OSError("synthetic persistence failure")
mod.settings_file, mod.save_settings = None, opaque_failure
check("failed preference save keeps the prior page", not model.change_page("camera") and Model(mod).page == "commands")
check("failed value save keeps the prior FOV", not model.write({"fov": 135}) and settings.fov.value == 125)
mod.settings_file, mod.save_settings = original_path, original_save
check("failed compensation keeps later writes blocked", model.transaction.pending)
check("blocked writes leave disk and FOV unchanged", original_path.read_bytes() == original_disk
      and settings.fov.value == 125)
model.transaction.clock = lambda: model.transaction.retry_after + 1
check("successful compensation unlocks writes", model.advance() == "failed" and not model.transaction.pending)
settings.zoom.option.value = 450
check("command reset leaves zoom and FOV alone", model.default_commands()
      and settings.zoom.distance() == 450 and settings.fov.value == 125)
model.assign_command("zoom_out", "keyboard", "H")
check("global restore also resets distance and commands", model.restore()
      and settings.zoom.distance() == 300 and settings.fov.value == 110
      and settings.commands.option("zoom_out_key").value is None
      and [option.identifier for option, _ in model._undo].count("orbit_distance") == 1)
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

# A camera mod of another protocol loaded first, as an Apex Movement older than this file: the switch refuses.
mod.disable()
legacy = types.ModuleType("_apex_camera_runtime_v2")
legacy.protocol, legacy.runtime = 2, object()
sys.modules["_apex_camera_runtime_v2"] = legacy
refused = Model(mod)
check("a camera mod of another version refuses the switch and leaves the mod off",
      refused.toggle_enabled() is False and not mod.is_enabled)
check("the window then says which mods to update instead of a failed save",
      refused.toggle_notice == "camera_outdated")
check("the cause of the refusal is written in the log",
      state["errors"][-1] == "[Third Person & FOV] could not switch the mod on: "
                             "IncompatibleState: incompatible shared camera state")
del sys.modules["_apex_camera_runtime_v2"]
check("once the other mod is gone the switch works again", refused.toggle_enabled() and mod.is_enabled)
mod.disable()
shared.reset_for_tests()
print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
