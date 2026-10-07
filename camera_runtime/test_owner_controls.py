"""Only the elected 200→150→100 camera owner may change its persisted controls."""

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
        self.left = False
        self.orbit = False

    def third_person_enabled(self):
        return True

    def orbit_enabled(self):
        return self.orbit

    def shoulder_left(self):
        return self.left

    def set_orbit(self, value):
        self.orbit = value

    def set_shoulder_left(self, value):
        self.left = value

    def note(self, _message):
        pass


class Third:
    def shoulder_available(self):
        return True

    def undo_auto_shoulder(self, _settings):
        return False

    def set_shoulder(self, settings, left):
        settings.set_shoulder_left(left)
        return True

    def orbit_available(self):
        return True

    def toggle_orbit(self, settings, _now_ns):
        settings.set_orbit(not settings.orbit_enabled())
        return True

    def set_orbit(self, settings, enabled, _now_ns):
        settings.set_orbit(enabled)
        return True

    def clock(self):
        return 1

    def stop(self):
        pass


runtime = CameraRuntime(Fov(), Third())
owners = {name: Settings() for name in ("omni_sprint", "third_person_fov", "apex_movement")}
for name, priority in (("omni_sprint", 100), ("third_person_fov", 150), ("apex_movement", 200)):
    runtime.register(name, priority, owners[name])
    check(f"ascending election reaches {name}", runtime.arbiter.active().owner == name)
    for candidate in owners:
        before = owners[candidate].left
        changed = runtime.toggle_shoulder(candidate)
        check(f"only {name} changes while elected over {candidate}",
              changed is (candidate == name)
              and owners[candidate].left is (not before if candidate == name else before))

for leaving, expected in (("apex_movement", "third_person_fov"),
                          ("third_person_fov", "omni_sprint")):
    runtime.unregister(leaving)
    check(f"descending election returns to {expected}", runtime.arbiter.active().owner == expected)
    before = {name: item.orbit for name, item in owners.items()}
    for candidate in owners:
        changed = runtime.toggle_orbit(candidate)
        check(f"only {expected} changes Orbit over {candidate}",
              changed is (candidate == expected)
              and owners[candidate].orbit is
              (not before[candidate] if candidate == expected else before[candidate]))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
