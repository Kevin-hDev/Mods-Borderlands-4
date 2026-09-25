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

ok = runtime.calls[0][0:2] == ("register", "third_person_fov")
ok = ok and runtime.calls[0][2] == 150
ok = ok and runtime.calls[1][0:3] == ("prepare", "third_person_fov", False)
ok = ok and runtime.calls[2] == ("tick", state["pc"], 42)
ok = ok and toggle is True and settings.third_person.value is True

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
