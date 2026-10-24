"""The camera units after the animation update share one SDK hook; every other hook passes straight through."""

import pathlib
import sys
import types
from collections import namedtuple

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime import frame_hooks  # noqa: E402
from apex_camera_runtime.frame_hooks import FRAME, IDENTIFIER, FrameHooks  # noqa: E402
from apex_camera_runtime.free_look import FreeLook  # noqa: E402
from apex_camera_runtime.vehicle_framing import VehicleFraming  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Sdk:
    """The SDK's hooks module: one callback per (path, kind, identifier)."""
    Type = types.SimpleNamespace(PRE="PRE", POST="POST")
    Block = object()

    def __init__(self):
        self.items = {}

    def add_hook(self, path, kind, identifier, callback):
        self.items[(path, kind, identifier)] = callback

    def remove_hook(self, path, kind, identifier):
        del self.items[(path, kind, identifier)]

    def has_hook(self, path, kind, identifier):
        return (path, kind, identifier) in self.items


sdk, lines, calls = Sdk(), [], []
hooks = FrameHooks(sdk, lines.append)
hooks.add_hook(FRAME, hooks.Type.POST, "offset", lambda *args: calls.append("offset"))
hooks.add_hook(FRAME, hooks.Type.POST, "free_look", lambda *args: calls.append("free_look"))
check("two units after the animation update: one SDK hook", list(sdk.items) == [(FRAME, "POST", IDENTIFIER)])
check("each unit still sees its own hook", hooks.has_hook(FRAME, hooks.Type.POST, "offset")
      and not hooks.has_hook(FRAME, hooks.Type.POST, "vehicle"))
sdk.items[(FRAME, "POST", IDENTIFIER)]("anim", None, None, None)
check("one update reaches every unit, in the order they asked", calls == ["offset", "free_look"])

hooks.remove_hook(FRAME, hooks.Type.POST, "offset")
check("one unit gone: the SDK hook stays for the other", (FRAME, "POST", IDENTIFIER) in sdk.items)
hooks.remove_hook(FRAME, hooks.Type.POST, "free_look")
check("the last unit gone: the SDK hook goes too", sdk.items == {})

hooks.add_hook(FRAME, hooks.Type.PRE, "omni", print)
hooks.add_hook("/Script/Engine.PlayerController:ClientSetCameraMode", hooks.Type.PRE, "transitions", print)
check("a hook before the update, or on another function, is the SDK's own",
      (FRAME, "PRE", "omni") in sdk.items and hooks.has_hook(FRAME, hooks.Type.PRE, "omni")
      and ("/Script/Engine.PlayerController:ClientSetCameraMode", "PRE", "transitions") in sdk.items)
hooks.remove_hook(FRAME, hooks.Type.PRE, "omni")
check("and is removed from the SDK", (FRAME, "PRE", "omni") not in sdk.items)
check("the SDK's other names pass through", hooks.Block is Sdk.Block)

calls.clear()


def broken(*_args):
    raise RuntimeError("unit failed")


hooks.add_hook(FRAME, hooks.Type.POST, "broken", broken)
hooks.add_hook(FRAME, hooks.Type.POST, "after", lambda *args: calls.append("after"))
hooks.dispatch("anim", None, None, None)
check("a unit that raises is told and the others still run",
      calls == ["after"] and len(lines) == 1 and "broken hook failed" in lines[0] and "unit failed" in lines[0])

calls.clear()
hooks.remove_hook(FRAME, hooks.Type.POST, "broken")
hooks.add_hook(FRAME, hooks.Type.POST, "stopper",
               lambda *args: (calls.append("stopper"), hooks.remove_hook(FRAME, hooks.Type.POST, "after")))
hooks.callbacks = {"stopper": hooks.callbacks["stopper"], "after": hooks.callbacks["after"]}
hooks.dispatch("anim", None, None, None)
check("a unit removed by another during the update is not called", calls == ["stopper"])

shared_sdk = Sdk()
shared = FrameHooks(shared_sdk, lines.append)
pc = types.SimpleNamespace(Pawn=None)
vehicle = VehicleFraming(lambda: (shared, lambda possibly_loading: pc, lambda item: (lambda: item), id,
                                  lambda: 0, lines.append))
vehicle.sync(types.SimpleNamespace(dynamic_camera=lambda: (1.0, 1.0)))
Values = namedtuple("Values", "keys holds hold_s")
look = FreeLook(lambda: (None, None, shared, lambda possibly_loading=False: pc, lambda: 0, lines.append, id))
look.sync(types.SimpleNamespace(free_look=lambda: Values(("A",), (True,), 0.2)))
check("Free Look and the framing at the wheel, both on: the SDK holds one hook after the update",
      list(shared_sdk.items) == [(FRAME, "POST", IDENTIFIER)] and set(shared.callbacks) == {
          "apex_camera_runtime:vehicle_framing", "apex_camera_runtime:free_look"})
vehicle.sync(types.SimpleNamespace(dynamic_camera=lambda: (0.0, 0.0)))
look.sync(types.SimpleNamespace(free_look=lambda: None))
check("both off: none left", shared_sdk.items == {} and shared.callbacks == {})

frame_hooks._front = None
sys.modules["unrealsdk"] = types.SimpleNamespace(logging=types.SimpleNamespace(error=lines.append))
first = frame_hooks.front(sdk)
check("every unit of a copy gets the same front", frame_hooks.front(sdk) is first and first.hooks is sdk)
del sys.modules["unrealsdk"]

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
