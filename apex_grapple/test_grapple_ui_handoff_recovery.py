"""A failed console return resumes without losing or repeating completed steps."""

from ui_test_loader import load


Handoff = load("control_console_handoff").Handoff
CONSOLE = 0xC0


class Native:
    def __init__(self, fail_on_tap=0):
        self.fail_on_tap = fail_on_tap
        self.attempts = 0
        self.taps = []

    def check_target(self):
        return True

    def tap(self, key):
        self.attempts += 1
        if self.attempts == self.fail_on_tap:
            raise RuntimeError("temporary input failure")
        self.taps.append(key)


redraws = []


def redraw_once_failed():
    redraws.append(1)
    if len(redraws) == 1:
        raise RuntimeError("temporary redraw failure")


native = Native()
handoff = Handoff(native, CONSOLE, 0, redraw_once_failed)
assert handoff.restore() is False, "a transfer in progress must not report restoration"
handoff.phase = "ready"
try:
    handoff.restore()
except RuntimeError:
    pass
else:
    raise AssertionError("a failed redraw must reach the cleanup retry")
assert handoff.restore() is True
assert redraws == [1, 1] and native.taps == [CONSOLE, CONSOLE]
assert handoff.restore() is True and native.taps == [CONSOLE, CONSOLE]

native = Native(fail_on_tap=2)
redraws = []
handoff = Handoff(native, CONSOLE, 0, lambda: redraws.append(1))
handoff.phase = "ready"
try:
    handoff.restore()
except RuntimeError:
    pass
else:
    raise AssertionError("a failed second press must reach the cleanup retry")
assert handoff.restore() is True
assert redraws == [1] and native.taps == [CONSOLE, CONSOLE]
print("OK | console return retries redraw and only unfinished key presses")
