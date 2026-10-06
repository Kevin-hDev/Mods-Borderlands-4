"""The standalone pack exposes the existing camera settings with safe persisted values."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
RUNTIME = HERE.parent.parent / "camera_runtime" / "source"
sys.path[:0] = [str(HERE), str(RUNTIME)]

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from third_person_fov import settings  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("the public settings keep their exact camera order",
      [item.identifier for item in settings.OPTIONS if not item.is_hidden] ==
      ["third_person", "third_person_ads", "third_person_key", "third_person_controller",
       "shoulder_left", "shoulder_smooth", "orbit_smooth", "shoulder_seconds", "shoulder_key", "shoulder_controller",
       "orbit", "orbit_key", "orbit_controller", "zoom_in_key", "zoom_in_controller",
       "zoom_out_key", "zoom_out_controller", "fov", "extended_loot", "loot_reach",
       "speed_fov", "speed_fov_gain", "speed_fov_seconds",
       "action_framing", "action_framing_strength", "camera_motion", "camera_motion_strength"])
check("the standalone pack always applies its FOV while enabled",
      settings.custom_fov_enabled() is True and not hasattr(settings, "custom_fov"))
check("third person stays off by default", settings.third_person.value is False)
check("the shortcut defaults to P and has one visible option",
      settings.third_person_key.default_value == "P"
      and settings.third_person_bind.is_hidden is True
      and settings.third_person_key.is_hidden is False)
check("the new camera choices are off and use Six/Seven",
      settings.shoulder_left.value is False and settings.orbit.value is False
      and settings.shoulder_key.default_value == "Six"
      and settings.orbit_key.default_value == "Seven")

settings.third_person.mod = sdk_stubs.FakeMod(state)
settings.set_third_person(True)
check("third person persists through its one setting",
      settings.third_person.value is True and state["settings_saves"] == 1)
state["refuse_save"] = True
try:
    settings.set_third_person(False)
except RuntimeError:
    pass
check("a refused save restores the visible value", settings.third_person.value is True)
state["refuse_save"] = False

for option, setter in ((settings.shoulder_left, settings.set_shoulder_left),
                       (settings.orbit, settings.set_orbit)):
    option.mod = sdk_stubs.FakeMod(state)
    setter(True)
    state["refuse_save"] = True
    try:
        setter(False)
    except RuntimeError:
        pass
    check(f"{option.identifier} persists and rolls back a refused save", option.value is True)
    state["refuse_save"] = False

for raw, expected in ((float("nan"), 110.0), (True, 110.0), (20, 70.0),
                      (200, 150.0), (123, 123.0)):
    settings.fov.value = raw
    check(f"FOV is safe for {raw!r}", settings.fov_value() == expected)

settings.third_person_bind.enable()
for raw in ("Gamepad_FaceButton_Top", "MouseX", "Escape", "Tilde"):
    settings.third_person_key.value = raw
    check(f"{raw} unbinds", settings.third_person_key.value is None
          and raw not in state["keybinds"])

for bind, option in ((settings.shoulder_bind, settings.shoulder_key),
                     (settings.orbit_bind, settings.orbit_key)):
    bind.enable()
    option.value = "ThumbMouseButton"
    check(f"{option.identifier} accepts a mouse button",
          option.value == "ThumbMouseButton" and "ThumbMouseButton" in state["keybinds"])
    for raw in ("Gamepad_FaceButton_Top", "Escape", "Tilde"):
        option.value = raw
        check(f"{option.identifier} refuses {raw}", option.value is None
              and raw not in state["keybinds"])

check("the shoulder's texts are the runtime's shared ones, its side named in the SDK's text menu",
      settings.shoulder_left.display_name == "Shoulder"
      and (settings.shoulder_left.true_text, settings.shoulder_left.false_text) == ("Left", "Right")
      and settings.orbit.description == "The camera turns freely around the character.")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
