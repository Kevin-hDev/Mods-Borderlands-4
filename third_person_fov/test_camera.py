"""The mini pack is a client of the shared camera runtime, below Apex Movement and above Omni Sprint."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
RUNTIME = HERE.parent.parent / "camera_runtime" / "source"
sys.path[:0] = [str(HERE), str(RUNTIME)]

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
state["settings_exists"] = True

from third_person_fov import camera, settings  # noqa: E402
from apex_camera_runtime.arbitration import Arbiter, Client  # noqa: E402


class Runtime:
    def __init__(self):
        self.calls = []
        self.refuse_stop = False
        self.active = "third_person_fov"
        self.accept_menu = True

    def register(self, *args):
        self.calls.append(("register", *args))

    def prepare_third_person(self, *args):
        self.calls.append(("prepare", *args[:2]))
        return None

    def tick(self, *args):
        self.calls.append(("tick", *args))

    def toggle_third_person(self, owner):
        self.calls.append(("toggle", owner))
        settings.set_third_person(not settings.third_person_enabled())
        return True

    def toggle_shoulder(self, owner):
        self.calls.append(("shoulder", owner))
        if owner != self.active:
            return False
        settings.set_shoulder_left(not settings.shoulder_left_enabled())
        return True

    def toggle_orbit(self, owner):
        self.calls.append(("orbit", owner))
        if owner != self.active:
            return False
        settings.set_orbit(not settings.orbit_enabled())
        return True

    def set_shoulder(self, owner, left):
        self.calls.append(("shoulder_menu", owner, left))
        if owner != self.active or not self.accept_menu:
            return False
        settings.set_shoulder_left(left)
        return True

    def set_orbit(self, owner, enabled):
        self.calls.append(("orbit_menu", owner, enabled))
        if owner != self.active or not self.accept_menu:
            return False
        settings.set_orbit(enabled)
        return True

    def camera_ready(self, owner):
        return owner == self.active

    def unregister(self, owner):
        self.calls.append(("unregister", owner))
        if self.refuse_stop:
            raise RuntimeError("stop refused")


runtime = Runtime()
camera.shared = lambda: runtime
camera.start()
state["pc"] = object()
camera.on_frame(42)
settings.third_person.mod = sdk_stubs.FakeMod(state)
toggle = camera.toggle_third_person()
settings.shoulder_left.mod = sdk_stubs.FakeMod(state)
settings.orbit.mod = sdk_stubs.FakeMod(state)
shoulder = camera.toggle_shoulder()
orbit = camera.toggle_orbit()

ok = runtime.calls[0][0:2] == ("register", "third_person_fov")
ok = ok and runtime.calls[0][2] == 150
ok = ok and runtime.calls[1][0:3] == ("prepare", "third_person_fov", False)
ok = ok and runtime.calls[2] == ("tick", state["pc"], 42)
ok = ok and toggle is True and settings.third_person.value is True
ok = ok and shoulder is True and settings.shoulder_left.value is True
ok = ok and orbit is True and settings.orbit.value is True
state["mods"][0].is_enabled = True
settings.shoulder_left.mod = state["mods"][0]
settings.orbit.mod = state["mods"][0]
settings.shoulder_left.value = False
settings.orbit.value = False
ok = ok and runtime.calls[-2:] == [("shoulder_menu", "third_person_fov", False),
                                   ("orbit_menu", "third_person_fov", False)]
ok = ok and settings.shoulder_left.value is False and settings.orbit.value is False
runtime.accept_menu = False
settings.shoulder_left.value = True
settings.orbit.value = True
ok = ok and settings.shoulder_left.value is False and settings.orbit.value is False
runtime.active = "apex_movement"
ok = ok and not camera.toggle_shoulder() and not camera.toggle_orbit()
ok = ok and settings.shoulder_left.value is False and settings.orbit.value is False

arbiter = Arbiter()
for owner, priority in (("omni_sprint", 100), ("apex_movement", 200),
                        ("third_person_fov", camera.PRIORITY)):
    arbiter.register(Client(owner, priority, object()), camera.PROTOCOL)
owners = [arbiter.active().owner]
arbiter.unregister("apex_movement")
owners.append(arbiter.active().owner)
arbiter.unregister("third_person_fov")
owners.append(arbiter.active().owner)
ok = ok and owners == ["apex_movement", "third_person_fov", "omni_sprint"]

runtime.refuse_stop = True
try:
    camera.stop()
except RuntimeError:
    pass
ok = ok and camera._registered is False

print("RESULTAT:", "TOUS LES TESTS PASSENT" if ok else "1 ECHEC(S)")
raise SystemExit(0 if ok else 1)
