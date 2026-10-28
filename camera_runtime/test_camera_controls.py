"""Only the elected and effective third-person owner can change shoulder."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.runtime import CameraRuntime  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Fov:
    def stop(self):
        pass


class Settings:
    def __init__(self):
        self.enabled = True
        self.left = False
        self.orbit = False
        self.toggles = 0

    def third_person_enabled(self):
        return self.enabled

    def orbit_enabled(self):
        return self.orbit

    def shoulder_left(self):
        return self.left


class Third:
    def __init__(self):
        self.available = True
        self.calls = 0
        self.orbit_calls = 0
        self.orbit_ready = True
        self.shoulder_values = []
        self.orbit_values = []
        self.orbit_cancels = 0

    def shoulder_available(self):
        return self.available

    def toggle_shoulder(self, settings):
        self.calls += 1
        settings.toggles += 1
        return True

    def undo_auto_shoulder(self, _settings):
        return False

    def set_shoulder(self, settings, left):
        self.shoulder_values.append(left)
        settings.left = left
        return True

    def orbit_available(self):
        return self.orbit_ready

    def toggle_orbit(self, _settings, now_ns):
        self.orbit_calls += 1
        return now_ns == 123

    def set_orbit(self, settings, enabled, now_ns):
        self.orbit_values.append((enabled, now_ns))
        settings.orbit = enabled
        return True

    def cancel_orbit(self, _settings, now_ns):
        self.orbit_cancels += 1
        return now_ns == 123

    def clock(self):
        return 123

    def stop(self):
        pass


third = Third()
runtime = CameraRuntime(Fov(), third)
omni, apex = Settings(), Settings()
runtime.register("omni", 100, omni)
runtime.register("apex", 200, apex)
check("an inactive owner cannot change shoulder",
      not runtime.toggle_shoulder("omni") and third.calls == 0)
check("an inactive owner cannot report a ready camera",
      not runtime.camera_ready("omni"))
apex.enabled = False
check("disabled third person cannot change shoulder",
      not runtime.toggle_shoulder("apex") and third.calls == 0)
check("a stable Orbit entry is not gated by the third-person preference",
      runtime.camera_ready("apex"))
apex.enabled = True
third.available = False
check("ADS or vehicle state blocks shoulder", not runtime.toggle_shoulder("apex") and third.calls == 0)
third.orbit_ready = False
check("an unstable camera is not ready for a menu transaction",
      not runtime.camera_ready("apex"))
third.orbit_ready = True
check("the elected stable camera is ready for a menu transaction",
      runtime.camera_ready("apex"))
third.available = True
apex.orbit = True
check("a refused saved Orbit still allows the visible ThirdPerson shoulder",
      runtime.set_shoulder("apex", True) and third.shoulder_values == [True] and apex.left)
third.available = False
check("visible Orbit still blocks an invisible shoulder change",
      not runtime.set_shoulder("apex", False) and third.shoulder_values == [True])
third.available = True
apex.orbit = False
check("the elected effective owner changes shoulder once",
      runtime.toggle_shoulder("apex") and third.shoulder_values == [True, False] and not apex.left)
check("the elected menu can request one exact shoulder side",
      runtime.set_shoulder("apex", True) and third.shoulder_values == [True, False, True]
      and apex.left)
check("an inactive menu cannot request a shoulder side",
      not runtime.set_shoulder("omni", False) and third.shoulder_values == [True, False, True])
check("an inactive owner cannot change Orbit",
      not runtime.toggle_orbit("omni") and third.orbit_calls == 0)
apex.enabled = False
check("a stable Orbit entry accepts the first-person base preference",
      runtime.toggle_orbit("apex") and third.orbit_calls == 1)
apex.enabled = True
third.orbit_ready = False
check("an unavailable camera blocks Orbit",
      not runtime.toggle_orbit("apex") and third.orbit_calls == 1)
third.orbit_ready = True
check("the elected effective owner changes Orbit once",
      runtime.toggle_orbit("apex") and third.orbit_calls == 2)
check("the elected menu can request one exact Orbit state",
      runtime.set_orbit("apex", True) and third.orbit_values == [(True, 123)] and apex.orbit)
check("the elected menu can cancel its unfinished Orbit request",
      runtime.cancel_orbit("apex") and third.orbit_cancels == 1)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
