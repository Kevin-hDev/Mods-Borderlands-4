"""Tests the way into the mod's window: choosing the mod in the SDK's menu opens it once, Close goes back to the
list of mods, and a window that cannot be had leaves the SDK's own settings page."""

import pathlib
import sys
from types import ModuleType, SimpleNamespace as NS

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
# The window's own modules, which nothing else in the mod's tests loads: one that no longer imports fails here.
from benefix_ohm_attack import (control_console_handoff, control_console_keys, control_timer_native,  # noqa: E402,F401
                                control_window, control_window_cleanup, control_window_clock, control_window_hooks,
                                panel_entry, panel_open, report)

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Mod:
    def iter_display_options(self):
        yield "the SDK's own option"


class ModScreen:
    def __init__(self, current):
        self.mod = current


# The SDK's console menu, as far as the way in reads it: a stack of screens, the mod's page on top of the list.
console = ModuleType("console_mod_menu")
screens = ModuleType("console_mod_menu.screens")
screen_mod = ModuleType("console_mod_menu.screens.mod")
screen_mod.ModScreen = ModScreen
console.screens = screens
sys.modules.update({console.__name__: console, screens.__name__: screens, screen_mod.__name__: screen_mod})
events: list = []
home = NS(draw=lambda: events.append("the list of mods drawn"))
screens.pop_screen = lambda: screens.screen_stack.pop()


def started(**asked) -> None:
    events.append(asked)
    control_window._active = NS(form=NS(keep_when_disabled=True), handoff=NS(redraw=None), closed=False)


real_start, control_window.start = control_window.start, started
mod = Mod()
screens.screen_stack = [home, ModScreen(mod)]
panel_open.install(mod)
panel_open.install(mod)
check("choosing the mod's page opens the window, asked to go back to the menu, and still lists the SDK's options",
      list(mod.iter_display_options()) == ["the SDK's own option"] and events == [{"return_to_menu": True}])
check("the window is opened once per page, however often the page is drawn",
      list(mod.iter_display_options()) == ["the SDK's own option"] and len(events) == 1)
check("the window open is the one the attack asks about", control_window.active())
control_window._active.handoff.redraw()
check("Close goes back to the list of mods", screens.screen_stack == [home] and events[-1] == "the list of mods drawn")

report.reset()
control_window._active = None
other = Mod()
panel_open.install(other)
screens.screen_stack = [home, ModScreen(other)]


def refused(**asked) -> None:
    raise RuntimeError("the game refuses the window")


control_window.start = refused
errors = len(state["errors"])
check("a window that cannot be opened leaves the SDK's own page, with its options",
      list(other.iter_display_options()) == ["the SDK's own option"] and screens.screen_stack[-1].mod is other)
check("and says so once, in words a player can read",
      state["errors"][errors:] == ["[Benefix Ohm Attack] Custom menu unavailable. Console settings remain available."])

# The real opening never raises: what stops it is written in the log by the window itself, and nothing is open.
report.reset()
quiet = Mod()
panel_open.install(quiet)
screens.screen_stack = [home, ModScreen(quiet)]
calls: list = []
control_window.start = lambda **asked: calls.append(asked)
errors = len(state["errors"])
check("a window that did not open, without raising, leaves the SDK's page and adds no error of the mod's own",
      list(quiet.iter_display_options()) == ["the SDK's own option"] and calls == [{"return_to_menu": True}]
      and len(state["errors"]) == errors and screens.screen_stack[-1].mod is quiet)

lone = Mod()
panel_open.install(lone)
screens.screen_stack = [ModScreen(lone)]
calls.clear()
check("a page that is not on top of the list of mods opens nothing, and that is no error",
      list(lone.iter_display_options()) == ["the SDK's own option"] and calls == []
      and len(state["errors"]) == errors and control_window._active is None)
foreign = Mod()
screens.screen_stack = [home, ModScreen(foreign)]
check("another mod's page on top of the list is never taken for this one's",
      list(lone.iter_display_options()) == ["the SDK's own option"] and calls == [] and len(state["errors"]) == errors)
control_window.start = real_start

# After Close, the list of mods is drawn again; a drawing that fails once may be asked again.
control_window._active = None
again = Mod()
panel_open.install(again)
screens.screen_stack = [home, ModScreen(again)]
control_window.start = started
list(again.iter_display_options())
redraw = control_window._active.handoff.redraw
draws: list = []


def draw_failing_once() -> None:
    draws.append(1)
    if len(draws) == 1:
        raise RuntimeError("the drawing failed")


home.draw = draw_failing_once
try:
    redraw()
    check("a drawing of the list that fails is not hidden", False)
except RuntimeError:
    check("a drawing of the list that fails is not hidden", screens.screen_stack == [home])
redraw()
check("asked again, the list is drawn, and the page is not popped twice", draws == [1, 1] and screens.screen_stack == [home])
control_window.start = real_start
control_window._active = None

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
