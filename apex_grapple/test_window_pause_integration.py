"""Real Grapple and Movement sessions progress without any animation event."""

import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS

import test_grapple_ui_frontend as f
from ui_test_loader import load


class Native:
    timer = 0

    def check_thread(self):
        return None

    def available(self):
        return True

    def start(self, callback):
        self.callback, self.timer = callback, 9

    def stop(self):
        self.timer = 0


clock_module = load("control_window_clock")
clock = clock_module.Clock(Native())
clock_module.shared = lambda: clock
name = "_movement_pause_test"
package = ModuleType(name)
here = Path(__file__).resolve()
movement_paths = (
    here.parents[2] / "apex_movement/source/apex_movement",
    here.parents[1] / "apex_movement/apex_movement",
)
package.__path__ = [str(next(path for path in movement_paths if path.is_dir()))]
sys.modules[name] = package
movement = importlib.import_module(f"{name}.control_window")
movement.control_window_clock.shared = lambda: clock
factory = ModuleType(f"{name}.panel_factory")
factory.PanelBindings = lambda: NS(prepare=lambda: True, ready=lambda: True)
root = NS(RemoveFromParent=lambda: f.events.append("movement_removed"),
          SetKeyboardFocus=lambda: f.events.append("movement_focus"))
form = NS(focus=lambda: root, poll=lambda: False, selecting=lambda: False)
factory.build = lambda *args: (root, form)
factory.panel_view = NS(viewport_slot=lambda: NS())
sys.modules[factory.__name__] = factory
movement.control_console_handoff.create = f.window.control_console_handoff.create
f.state.pc = NS(OakCharacter=object(), bShowMouseCursor=True, CurrentMouseCursor=0)
f.events.clear()
f.window.start(return_to_menu=True)
first = f.window._active
assert first is not None and first.claimed and clock.owner == f.window.__package__
clock.dispatch()
assert first.input_changed and "ui_input" in f.events

# Selecting the other mod cleans the existing panel without redrawing its old page.
movement.start(return_to_menu=True)
second = movement._active
assert first.closed and f.window._active is None
assert second is not None and clock.owner == name
assert "console_return" not in f.events
clock.dispatch()
assert second.input_changed and "movement_focus" in f.events
form.poll = lambda: True
second.next_poll = 0
clock.dispatch()
assert second.closed and movement._active is None and clock.owner is None
assert clock.native.timer == 0
assert "movement_removed" in f.events and "console_return" in f.events

# A new selection must not retry the previous console page after its stack changed.
def stale_page():
    raise RuntimeError("previous menu page no longer exists")


f.window.start(return_to_menu=True)
pending = f.window._active
clock.dispatch()
pending.handoff.restore = stale_page
pending.close("button")
assert pending.closed and f.window._active is pending and clock.owner is not None
movement.start(return_to_menu=True)
assert f.window._active is None and movement._active is not None
assert pending.cleanup.reason == "cancelled" and clock.owner == name
movement.cancel()
assert movement._active is None and clock.owner is None and clock.native.timer == 0

# Timer construction failure rolls back the added panel and releases ownership.
def fail_start(callback):
    raise RuntimeError("timer failed")

clock.native.start = fail_start
movement.start(return_to_menu=True)
assert movement._active is None and clock.owner is None
print("OK | pause-independent sessions, cross-mod replacement, close and failed-open rollback")
