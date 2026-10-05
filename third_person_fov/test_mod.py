"""The autonomous host has the exact name, one shortcut and a clean lifecycle."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
RUNTIME = HERE.parent.parent / "camera_runtime" / "source"
sys.path[:0] = [str(HERE), str(RUNTIME)]

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
calls = []
fake_camera = types.ModuleType("third_person_fov.camera")
fake_camera.start = lambda: calls.append("start")
fake_camera.stop = lambda: calls.append("stop")
fake_camera.toggle_third_person = lambda: calls.append("toggle") or True
fake_camera.toggle_shoulder = lambda: calls.append("shoulder") or True
fake_camera.toggle_orbit = lambda: calls.append("orbit") or True
sys.modules["third_person_fov.camera"] = fake_camera

import third_person_fov  # noqa: E402

mod = third_person_fov.mod
ok = third_person_fov.__version__ == "1.1.2"
ok = ok and mod.kwargs["name"] == "Third Person & FOV" and mod.is_enabled
ok = ok and calls == ["start"] and set(state["keybinds"]) == {"P", "Six", "Seven"}
state["keybinds"]["P"]()
state["keybinds"]["Six"]()
state["keybinds"]["Seven"]()
ok = ok and calls[-3:] == ["toggle", "shoulder", "orbit"]
mod.disable()
ok = ok and calls[-1] == "stop" and not state["keybinds"]

print("RESULTAT:", "TOUS LES TESTS PASSENT" if ok else "1 ECHEC(S)")
raise SystemExit(0 if ok else 1)
