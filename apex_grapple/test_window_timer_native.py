"""Native timer failure paths retain callbacks and never run work on another thread."""

import ctypes
import os
from types import SimpleNamespace as NS
from ui_test_loader import load


class Function:
    def __init__(self, body):
        self.body = body

    def __call__(self, *args):
        return self.body(*args)


events = []
api = NS(SetTimer=Function(lambda *args: 17), KillTimer=Function(lambda *args: 1),
         GetForegroundWindow=Function(lambda: 5),
         GetWindowThreadProcessId=Function(lambda window, pid: setattr(pid._obj, "value", os.getpid()) or 42))
kernel = NS(GetCurrentThreadId=Function(lambda: 42))
ctypes.WinDLL = lambda name, **kwargs: api if name == "user32" else kernel
ctypes.WINFUNCTYPE = lambda *args: lambda callback: callback
native = load("control_timer_native").NativeTimer()
pointer = native.callback
native.start(lambda: events.append("tick"))
native.invoke(None, 0x113, 16, 0)
assert not events
native.invoke(None, 0x113, 17, 0)
assert events == ["tick"] and native.available()
api.GetWindowThreadProcessId.body = lambda *args: 99
assert not native.available()
api.KillTimer.body = lambda *args: 0
try:
    native.stop()
except RuntimeError:
    pass
else:
    raise AssertionError("A failed timer cancellation must remain visible")
assert native.timer == 17 and native.callback is pointer
api.KillTimer.body = lambda *args: 1
native.stop()
native.invoke(None, 0x113, 17, 0)
assert events == ["tick"] and native.timer == 0 and native.callback is pointer
api.SetTimer.body = lambda *args: 0
try:
    native.start(lambda: events.append("unexpected"))
except RuntimeError:
    pass
else:
    raise AssertionError("Timer creation failure must abort opening")
assert native.target is None
api.SetTimer.body = lambda *args: 18
native.start(lambda: events.append("wrong thread"))
kernel.GetCurrentThreadId.body = lambda: 99
native.invoke(None, 0x113, 18, 0)
assert events == ["tick"] and native.error == "RuntimeError" and native.target is None
print("OK | native ABI setup, cancellation failure, stale messages and wrong-thread refusal")
