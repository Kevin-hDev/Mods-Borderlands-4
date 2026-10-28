"""The real console's mod selection enters the panel once and returns to its list."""

import ast
from sdk_test_paths import console_menu_archive
import sys
from types import ModuleType, SimpleNamespace as NS
import zipfile
import control_fixture as f
from apex_grapple import panel_entry, control_window

screens = ModuleType("console_mod_menu.screens")
screen_mod = ModuleType("console_mod_menu.screens.mod")
class ModScreen:
    def __init__(self, mod):
        self.mod = mod
    def handle_option_input(self, line):
        return False
screen_mod.ModScreen = ModScreen
sys.modules[screens.__name__] = screens
sys.modules[screen_mod.__name__] = screen_mod
sys.modules["console_mod_menu"].screens = screens
events = []
home = NS(drawn_mod_list=[object(), f.mod], draw=lambda: events.append("home"))
screens.screen_stack = [home]
screens.pop_screen = lambda: screens.screen_stack.pop()
sdk = console_menu_archive()
with zipfile.ZipFile(sdk) as archive:
    tree = ast.parse(archive.read("console_mod_menu/screens/home.py").decode())
cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "HomeScreen")
method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "handle_input")
namespace = {"handle_standard_command_input": lambda line: False, "ModScreen": ModScreen,
             "push_screen": screens.screen_stack.append}
exec(compile(ast.Module(body=[method], type_ignores=[]), str(sdk), "exec"), namespace)
def start(**kwargs):
    events.append(kwargs)
    control_window._active = NS(form=NS(keep_when_disabled=True), handoff=NS(redraw=None))
control_window.start = start
assert namespace["handle_input"](home, "2")
tuple(f.mod.iter_display_options())
assert events == [{"return_to_menu": True, "full_menu": True}]
tuple(f.mod.iter_display_options())
assert len(events) == 1
control_window._active.handoff.redraw()
assert screens.screen_stack == [home] and events[-1] == "home"
assert namespace["handle_input"](home, "1")
tuple(f.mod.iter_display_options())
assert len(events) == 2  # Another mod is never intercepted.

# A transient drawing failure after popping the page must be safe to retry.
screens.screen_stack[:] = [home]
draw_attempts = []
original_draw = home.draw
def draw_once_failed():
    draw_attempts.append(1)
    if len(draw_attempts) == 1:
        raise RuntimeError("temporary drawing failure")
    original_draw()
home.draw = draw_once_failed
assert namespace["handle_input"](home, "2")
tuple(f.mod.iter_display_options())
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
print("OK | real console mod selection, one opening, return to list, other mods unchanged")
