"""Omni Sprint registers its camera settings at lower priority than Apex Movement."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
RUNTIME = HERE.parent.parent / "camera_runtime" / "source"
sys.path[:0] = [str(HERE), str(RUNTIME)]

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from omni_sprint import camera, settings  # noqa: E402


class Runtime:
    def __init__(self):
        self.registered = []
        self.unregistered = []
        self.ticks = []

    def register(self, *args):
        self.registered.append(args)

    def unregister(self, owner):
        self.unregistered.append(owner)

    def prepare_third_person(self, owner, enabled, setup):
        if not enabled:
            return None
        try:
            setup(self)
        except Exception as error:
            return error
        return None

    def tick(self, pc, now_ns):
        self.ticks.append((pc, now_ns))


runtime = Runtime()
ensured = []
camera.shared = lambda: runtime


def fail_ensure(found):
    ensured.append(found)
    raise RuntimeError("native library blocked")


camera.ensure = fail_ensure
camera.start()
ok = runtime.registered[0][:2] == ("omni_sprint", 100)
ok = ok and settings.third_person.value is False
state["pc"] = sdk_stubs.player(sdk_stubs.BASE)
camera.on_frame(123)
ok = ok and runtime.ticks == [(state["pc"], 123)] and ensured == []
settings.third_person.value = True
try:
    camera.on_frame(456)
except RuntimeError:
    pass
ok = ok and ensured == [runtime] and runtime.ticks[-1] == (state["pc"], 456)
camera.stop()
ok = ok and runtime.unregistered == ["omni_sprint"]

print("RESULTAT:", "TOUS LES TESTS PASSENT" if ok else "1 ECHEC(S)")
sys.exit(0 if ok else 1)
