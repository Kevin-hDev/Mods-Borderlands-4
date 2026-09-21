"""Full window opening without a pawn, then cleanup back to the title screen or game."""

import sys
import time
from types import ModuleType, SimpleNamespace as NS

from ui_test_loader import load

events, commands, hooks = [], {}, {}
sdk = ModuleType("unrealsdk")
sdk.logging = NS(info=events.append)
sdk.find_enum = lambda name: NS(Default=0, DoNotLock=0)
sdk.unreal = NS(WeakPointer=lambda obj: lambda: obj)
sdk.commands = NS(has_command=lambda name: name in commands,
                  add_command=lambda name, fn: commands.update({name: fn}) or True,
                  remove_command=lambda name: commands.pop(name, None))
sdk.hooks = NS(Type=NS(POST=1), has_hook=lambda path, kind, name: name in hooks,
               add_hook=lambda path, kind, name, fn: hooks.update({name: fn}) or False,
               remove_hook=lambda path, kind, name: hooks.pop(name, None))
signatures = {
    "AddWidget": ("Widget", "slot", "ReturnValue"),
    "SetInputMode_UIOnlyEx": ("PlayerController", "InWidgetToFocus", "InMouseLockMode", "bFlushInput"),
    "SetInputMode_GameOnly": ("PlayerController", "bFlushInput"),
    "SetInputMode_GameAndUIEx": ("PlayerController", "InWidgetToFocus", "InMouseLockMode", "bHideCursorDuringCapture", "bFlushInput"),
}
cls = NS(_find=lambda name: NS(_properties=lambda: (NS(Name=x) for x in signatures[name])))
library = NS(Class=cls, SetInputMode_UIOnlyEx=lambda *args: events.append("ui_input"),
             SetInputMode_GameOnly=lambda *args: events.append("game_input"),
             SetInputMode_GameAndUIEx=lambda *args: events.append("menu_input"))
sdk.find_class = lambda name: cls if name == "GameViewportSubsystem" else NS(ClassDefaultObject=library)
viewport = NS(Name="GameViewportSubsystem_1", AddWidget=lambda *args: events.append("added") or True)
sdk.find_all = lambda cls: iter((viewport,))
sys.modules["unrealsdk"] = sdk
base = ModuleType("mods_base")
state = NS(pc=None)
base.get_pc = lambda **kwargs: state.pc
sys.modules["mods_base"] = base
window = load("control_window")
window.Bindings = lambda: NS(prepare=lambda: True, summary=lambda: "Controls", ready=lambda: True)
window.Form = lambda widgets, bindings: NS(widgets=widgets, poll=lambda: False, selecting=lambda: False)
root = NS(RemoveFromParent=lambda: events.append("removed"))
selector = NS(SetKeyboardFocus=lambda: events.append("focus"))
two = NS(SetIsChecked=lambda value: None)
window.control_view.build_view = lambda *args: (root, {"first": selector, "two": two})
window.control_view.viewport_slot = lambda: NS()
window.control_console_handoff.create = lambda now: NS(advance=lambda now: True,
                                                       restore=lambda: events.append("console_return"))

for pawn, expected in ((None, "menu_input"), (object(), "game_input")):
    events.clear()
    state.pc = NS(OakCharacter=pawn, bShowMouseCursor=True, CurrentMouseCursor=0)
    window.start(return_to_menu=True)
    assert window.active() and len(hooks) == 1 and len(commands) == 1
    session = window._active
    assert session.frontend == (pawn is None)
    session.poll(time.perf_counter_ns())
    assert "ui_input" in events
    session.close("button")
    assert not window.active() and not hooks and not commands
    assert events.index(expected) < events.index("console_return")
    assert state.pc.bShowMouseCursor  # Both started from a console/menu, not hidden gameplay input.

# Missing controllers during loading must not create a widget or take input ownership.
state.pc = None
events.clear()
window.start(return_to_menu=True)
assert not window.active() and "added" not in events and not hooks and not commands
print("OK | no-pawn title screen, game, correct input restoration, and loading guard")
