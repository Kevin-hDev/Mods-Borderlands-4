"""Movement opens once from its own SDK menu and keeps native options as fallback."""

import sys
from types import ModuleType, SimpleNamespace as NS

import movement_ui_fixture

movement_ui_fixture.install()

from apex_movement import panel_entry, panel_open, control_window


class Mod:
    def iter_display_options(self):
        yield "native option"


mod = Mod()
console = ModuleType("console_mod_menu")
screens = ModuleType("console_mod_menu.screens")
screen_mod = ModuleType("console_mod_menu.screens.mod")


class ModScreen:
    def __init__(self, current):
        self.mod = current


screen_mod.ModScreen = ModScreen
sys.modules[console.__name__] = console
sys.modules[screens.__name__] = screens
sys.modules[screen_mod.__name__] = screen_mod
console.screens = screens
events = []
home = NS(draw=lambda: events.append("home"))
page = ModScreen(mod)
screens.screen_stack = [home, page]
screens.pop_screen = lambda: screens.screen_stack.pop()


def start(**kwargs):
    events.append(kwargs)
    control_window._active = NS(form=NS(keep_when_disabled=True), handoff=NS(redraw=None))


control_window.start = start
panel_open.install(mod)
assert list(mod.iter_display_options()) == ["native option"]
assert events == [{"return_to_menu": True}]
assert list(mod.iter_display_options()) == ["native option"] and len(events) == 1
control_window._active.handoff.redraw()
assert screens.screen_stack == [home] and events[-1] == "home"

draw_attempts = []
original_draw = home.draw
def draw_once_failed():
    draw_attempts.append(1)
    if len(draw_attempts) == 1:
        raise RuntimeError("temporary drawing failure")
    original_draw()
home.draw = draw_once_failed
second_page = ModScreen(mod)
screens.screen_stack.append(second_page)
panel_entry.open_page(mod)
redraw = control_window._active.handoff.redraw
try:
    redraw()
except RuntimeError:
    pass
else:
    raise AssertionError("the first redraw should fail after popping")
assert screens.screen_stack == [home]
redraw()
assert draw_attempts == [1, 1] and events[-1] == "home"
print("OK | Movement menu opens once, keeps SDK fallback and returns to mod list")
