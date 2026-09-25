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


check("the three public settings keep their exact order",
      [item.identifier for item in settings.OPTIONS if not item.is_hidden] ==
      ["third_person", "third_person_key", "fov"])
check("the standalone pack always applies its FOV while enabled",
      settings.custom_fov_enabled() is True and not hasattr(settings, "custom_fov"))
check("third person stays off by default", settings.third_person.value is False)
check("the shortcut defaults to P and has one visible option",
      settings.third_person_key.default_value == "P"
      and settings.third_person_bind.is_hidden is True
      and settings.third_person_key.is_hidden is False)

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

for raw, expected in ((float("nan"), 110.0), (True, 110.0), (20, 70.0),
                      (200, 150.0), (123, 123.0)):
    settings.fov.value = raw
    check(f"FOV is safe for {raw!r}", settings.fov_value() == expected)

settings.third_person_bind.enable()
for raw in ("Gamepad_FaceButton_Top", "MouseX", "Escape", "Tilde"):
    settings.third_person_key.value = raw
    check(f"{raw} unbinds", settings.third_person_key.value is None
          and raw not in state["keybinds"])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
