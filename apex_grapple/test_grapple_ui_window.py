"""Manual closure and context cleanup do not cancel normal key capture; Escape closes as the Close button does,
once released, never during a key choice nor when the form keeps the window open; a focus the game took comes
back to the window."""

from ui_test_loader import load
import sys
from types import ModuleType, SimpleNamespace as NS

events = []
sdk = ModuleType("unrealsdk")
sdk.logging = NS(info=events.append)
sdk.hooks = NS(remove_hook=lambda *args: events.append("unhook"),
               has_hook=lambda *args: False, Type=NS(POST=1))
sdk.commands = NS(remove_command=lambda *args: events.append("uncommand"), has_command=lambda *args: False)
sdk.find_enum = lambda name: NS(Default=0, DoNotLock=0)
sys.modules["unrealsdk"] = sdk
base = ModuleType("mods_base")
sys.modules["mods_base"] = base
character = NS()
pc = NS(bShowMouseCursor=True, CurrentMouseCursor=0, OakCharacter=character)
base.get_pc = lambda **kwargs: pc
import ui_clock_fixture
ui_clock_fixture.install(sdk)
window = load("control_window")
escape = load("control_escape")


class Keyboard:
    """The fake user32 every session reads Escape from: nothing pressed unless a check says so."""
    held = pressed = False

    def GetAsyncKeyState(self, key):
        assert key == escape.VK_ESCAPE
        answer = (escape.DOWN if self.held else 0) | (escape.PRESSED if self.pressed else 0)
        self.pressed = False
        return answer


keyboard = Keyboard()
escape.user32 = lambda: keyboard


def session(frontend=False):
    events.clear()
    pc.bShowMouseCursor = True
    pc.OakCharacter = None if frontend else character
    root = NS(RemoveFromParent=lambda: events.append("removed"),
              GetIsSelectingKey=lambda: False, SetKeyboardFocus=lambda: events.append("focus"),
              HasKeyboardFocus=lambda: False, HasFocusedDescendants=lambda: True)
    library = NS(SetInputMode_GameOnly=lambda *args: events.append("game_input"),
                 SetInputMode_GameAndUIEx=lambda *args: events.append("menu_input"),
                 SetInputMode_UIOnlyEx=lambda *args: events.append("ui_input"))
    form = NS(widgets={"first": lambda: root}, poll=lambda: False,
              selecting=lambda: root.GetIsSelectingKey(), escape=lambda: events.append("form_escape") or True)
    bindings = NS(ready=lambda: True)
    item = window.Session(lambda: pc, lambda: root, lambda: library, False,
                          form, bindings, lambda: None if frontend else character)
    item.hooked = item.commanded = item.input_changed = True
    window._active = item
    return item, root


item, root = session()
window.start(return_to_menu=True)
assert window.active() and any("already_open" in event for event in events)
window.cancel()
assert item.closed and not window.active()
count = len(events)
window.cancel()
assert len(events) == count

item, root = session(frontend=True)
item.poll(1)
assert not item.closed
item.close("button")
assert "menu_input" in events and "game_input" not in events

item, root = session(frontend=True)
pc.OakCharacter = character
item.poll(1)
assert item.closed and any("closed=session_changed" in event for event in events)
assert "menu_input" not in events and "game_input" not in events

item, root = session()
item.character = lambda: None
pc.OakCharacter = None
item.poll(1)
assert item.closed and "game_input" not in events

item, root = session()
for attempt in range(8):
    pc.bShowMouseCursor = False
    item.poll(attempt * window.POLL_NS + 1)
assert not item.closed and "ui_input" not in events
assert len([x for x in events if "cursor_visible_restored" in x]) <= 3

item, root = session()
pc.bShowMouseCursor = False
root.GetIsSelectingKey = lambda: True
item.poll(1)
assert not item.closed and "ui_input" not in events
assert pc.bShowMouseCursor is False
root.GetIsSelectingKey = lambda: False
item.poll(window.POLL_NS + 1)
assert not item.closed  # Escape ends capture, not the whole panel.

item, root = session()
root.HasFocusedDescendants = lambda: False  # The game took the focus (Kevin, 2026-10-06).
item.poll(1)
assert "ui_input" not in events  # A focus just given may land a frame later.
item.poll(window.POLL_NS + 1)
assert not item.closed and "ui_input" in events and "focus" in events
assert any("focus_restored=1" in x for x in events)

item, root = session()
item.poll(120_000_000_000)
assert not item.closed  # No arbitrary 30-second expiry anymore.
item.form.poll = lambda: True
item.poll(121_000_000_000)
assert item.closed and pc.bShowMouseCursor is False
assert all(event in events for event in ("removed", "game_input", "unhook", "uncommand"))
count = len(events)
item.close("again")
assert len(events) == count

item, root = session()
item.selector = lambda: None
item.poll(1)
assert item.closed and any("closed=window_gone" in x for x in events)

item, root = session()
window.get_pc = lambda **kwargs: NS()
item.poll(1)
assert item.closed and "game_input" not in events
window.get_pc = lambda **kwargs: pc

item, root = session()
pc.OakCharacter = NS(other=True)
item.poll(1)
assert item.closed and any("closed=session_changed" in x for x in events)

item, root = session()
item.bindings.ready = lambda: False
item.poll(1)
assert item.closed and any("closed=mod_disabled" in x for x in events)

item, root = session()
item.input_changed = False
item.handoff = NS(advance=lambda now: False, restore=lambda: events.append("menu_restored"))
item.poll(1)
assert "ui_input" not in events
item.handoff.advance = lambda now: True
item.poll(window.POLL_NS + 1)
assert "ui_input" in events
item.form.poll = lambda: True
item.poll(2 * window.POLL_NS + 1)
assert item.closed and events.index("game_input") < events.index("menu_restored")


def fail():
    raise RuntimeError("private detail")


item, root = session()
item.form.poll = fail
item.tick(None, None, None, None)
assert item.closed and "game_input" in events
assert any("poll_error" in x for x in events) and not any("private detail" in x for x in events)

item, root = session()
root.RemoveFromParent = fail
item.close("cancelled")
assert "game_input" in events and "uncommand" in events
assert item.hooked  # Retain the callback briefly to retry removing the failed root.
assert any("cleanup_error" in x for x in events)

cls = NS(_find=lambda method: NS(_properties=lambda: iter(NS(Name=x) for x in
         ("Widget", "slot", "ReturnValue"))))
window.require_signature(cls, "AddWidget", ("Widget", "slot", "ReturnValue"))
try:
    window.require_signature(cls, "AddWidget", ("Widget", "Slot", "ReturnValue"))
except ValueError:
    pass
else:
    raise AssertionError("Mismatched metadata must block construction")

registered = {"callback": object()}
sdk.hooks.has_hook = lambda *args: "callback" in registered
sdk.hooks.remove_hook = lambda *args: registered.pop("callback", None)
sdk.hooks.add_hook = lambda *args: registered.update(callback=args[-1])
callback = lambda *args: None
assert window.install_listener(callback) and registered["callback"] is callback

def turns(item, start, count):
    for turn in range(start, start + count):
        item.poll(turn * window.POLL_NS + 1)


item, root = session()
keyboard.held = True
turns(item, 0, 3)
assert not item.closed and "form_escape" not in events  # Never while the key is down.
keyboard.held = False
turns(item, 3, 1)
assert not item.closed  # The release turn: the key may still reach the game.
turns(item, 4, 1)
assert item.closed and "form_escape" in events and any("escape_released=true" in x for x in events)
assert any("closed=button" in x for x in events)  # The Close button's way out, back to the mods list.

item, root = session()
item.form.escape = lambda: events.append("form_escape") or False
keyboard.pressed = True
turns(item, 0, 3)
assert not item.closed and "form_escape" in events  # The form keeps it open, as when Close cannot save.

item, root = session()
root.GetIsSelectingKey = lambda: True
keyboard.held = True
turns(item, 0, 2)
root.GetIsSelectingKey = lambda: False  # Escape cancelled the key choice in its field.
turns(item, 2, 2)
keyboard.held = False
turns(item, 4, 3)
assert not item.closed and "form_escape" not in events

item, root = session()
keyboard.pressed = True
item.form.poll = lambda: True
turns(item, 0, 1)
assert item.closed and "form_escape" not in events  # A click on Close in the same turn closes at once.
print("OK | manual close, no expiry, cursor, focus, capture, travel, disable, error cleanup and Escape")
