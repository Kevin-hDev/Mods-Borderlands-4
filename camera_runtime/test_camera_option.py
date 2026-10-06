"""Visible camera choices are committed only by their runtime transaction."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


class BoolOption:
    def __init__(self, identifier, value, **_kwargs):
        self.identifier = identifier
        self.value = value
        self.default_value = value
        self.mod = None
        self.on_change_anytime = None

    def __setattr__(self, name, value):
        if name == "value" and getattr(self, "on_change_anytime", None) is not None:
            self.on_change_anytime(self, value)
        super().__setattr__(name, value)


mods_base = types.ModuleType("mods_base")
mods_base.BoolOption = BoolOption
sys.modules["mods_base"] = mods_base

from apex_camera_runtime.camera_option import CameraBoolOption  # noqa: E402

fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


calls = []
def accept(value):
    calls.append(value)
    return True


option = CameraBoolOption("orbit", False, route=accept)
option.mod = types.SimpleNamespace(is_enabled=False)
option.value = True
check("settings loading while disabled establishes the saved value",
      option.value is True and calls == [])
option.mod.is_enabled = True
option.value = False
check("a live menu request is routed without changing the saved value",
      option.value is True and calls == [False] and option.camera_status == "pending")
option.commit(False)
check("the runtime confirmation commits without routing again",
      option.value is False and calls == [False] and option.camera_status == "confirmed")
option.value = "false"
check("an invalid menu value is refused at the boundary",
      option.value is False and calls == [False])

refused = CameraBoolOption("shoulder", False, route=lambda _value: False)
refused.mod = types.SimpleNamespace(is_enabled=True)
refused.value = True
check("a non-elected menu owner reports refusal without changing its value",
      refused.value is False and refused.camera_status == "refused")

ready = [False]
waiting = CameraBoolOption(
    "orbit", False, route=accept, ready=lambda: ready[0])
waiting.mod = types.SimpleNamespace(is_enabled=True)
waiting.value = True
check("a live camera choice waits until its runtime is ready",
      waiting.value is False and waiting.camera_status == "waiting")
ready[0] = True
waiting.value = True
check("the same choice routes once the runtime becomes ready",
      waiting.value is False and waiting.camera_status == "pending")

cancelled = []
cancellable = CameraBoolOption(
    "orbit", False, route=lambda _value: True,
    cancel=lambda: cancelled.append(True) or True)
cancellable.mod = types.SimpleNamespace(is_enabled=True)
cancellable.value = True
check("a pending native request can be cancelled before its menu closes",
      cancellable.cancel_pending() and cancelled == [True]
      and cancellable.value is False and cancellable.camera_status == "refused")

from apex_camera_runtime.camera_option import BaseViewOption

locked = [True]
base = BaseViewOption('third_person', False, locked=lambda: locked[0])
base.mod = types.SimpleNamespace(is_enabled=True)
try:
    base.value = True
except ValueError:
    pass
check('Orbit locks the SDK base view without changing its saved value', base.value is False and base.locked)
locked[0] = False
base.value = True
check('the SDK base view becomes editable after Orbit ends', base.value is True and not base.locked)
locked[0] = True
base.commit(False)
check('runtime rollback uses a non-routed base commit', base.value is False)
base.mod.is_enabled = False
base.value = True
check('disabled settings loading is not blocked', base.value is True)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
