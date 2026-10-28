"""A single paused-game clock owns the active Apex panel and rejects stale work."""

from ui_test_loader import load

module = load("control_window_clock")


class Native:
    def __init__(self):
        self.timer = 0
        self.foreground = True

    def check_thread(self):
        return None

    def available(self):
        return self.foreground

    def start(self, callback):
        self.callback, self.timer = callback, 19

    def stop(self):
        self.timer = 0


native = Native()
clock = module.Clock(native)
events = []


def cancel_a():
    events.append("cancel_a")
    clock.stop("a")
    clock.release("a")


clock.claim("a", cancel_a)


def tick(*args):
    events.append("tick")
    clock.dispatch()  # Nested message dispatch must never re-enter the panel.


clock.start("a", tick)
clock.dispatch()
assert events == ["tick"]
native.foreground = False
clock.dispatch()
assert events == ["tick"]
native.foreground = True
clock.claim("b", lambda: None)
assert events == ["tick", "cancel_a"] and clock.owner == "b"
clock.start("b", lambda *args: events.append("b"))
clock.stop("a")
clock.release("a")
assert native.timer == 19 and clock.owner == "b"
clock.dispatch()
assert events[-1] == "b"
try:
    clock.claim("c", lambda: None)
except RuntimeError:
    pass
else:
    raise AssertionError("Unfinished cleanup must block another panel")
assert clock.owner == "b"
clock.stop("b")
clock.release("b")
assert clock.owner is None

clock.claim("a", cancel_a)
clock.start("a", lambda *args: (_ for _ in ()).throw(RuntimeError("failure")))
clock.dispatch()
assert native.timer == 0 and clock.owner is None
print("OK | exclusive panels, reentrancy, background focus, stale stop and failed callback")
