"""Tests the window's life in this mod's own copy of it: one window at a time, every way it closes, and what closing
gives back (the widget, the game's input, the cursor, the close command, the timer). The window's widgets are not
built here: a session is made by hand around doubles, as Apex Grapple's own test of the window does, and the real
opening is run as far as its first refusal."""

import pathlib
import sys
from types import SimpleNamespace as NS

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import control_window as window  # noqa: E402
from benefix_ohm_attack import control_window_clock, control_window_hooks  # noqa: E402

fails: list[str] = []
PACKAGE, TAG, COMMAND = "benefix_ohm_attack", "[BenefixOhmUIWindow]", "benefix_ohm_ui_close"
# One list for what the doubles are asked and what the window writes in the log, in the order it happens.
events = state["log"]


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def said(words: str) -> bool:
    return any(isinstance(event, str) and event.startswith(TAG) and words in event for event in events)


class Native:
    """The Windows timer the shared clock drives, without Windows."""

    timer = None

    def check_thread(self) -> None:
        pass

    def available(self) -> bool:
        return True

    def start(self, callback) -> None:
        self.timer = callback

    def stop(self) -> None:
        self.timer = None


native = Native()
clock = control_window_clock.Clock(native)
control_window_clock.shared = lambda: clock
sdk = sys.modules["unrealsdk"]
sdk.commands = NS(remove_command=lambda name: events.append(f"command removed: {name}"), has_command=lambda name: False)
# Two namespaces with the same fields are equal: each character is told apart by its name.
character = NS(name="the player's character")
pc = NS(bShowMouseCursor=True, CurrentMouseCursor="Arrow", OakCharacter=character)
state["pc"] = pc


def opened(frontend: bool = False):
    """A window as the real opening leaves it: its timer running, its close command registered, the input taken."""
    events.clear()
    pc.bShowMouseCursor, pc.OakCharacter = True, None if frontend else character
    root = NS(RemoveFromParent=lambda: events.append("widget removed"))
    library = NS(SetInputMode_GameOnly=lambda *asked: events.append("input back to the game"),
                 SetInputMode_GameAndUIEx=lambda *asked: events.append("input back to the menu"),
                 SetInputMode_UIOnlyEx=lambda *asked: events.append("input taken"))
    form = NS(focus=lambda: root, poll=lambda: False, selecting=lambda: False)
    item = window.Session(lambda: pc, lambda: root, lambda: library, False, form, NS(ready=lambda: True),
                          lambda: None if frontend else character)
    clock.claim(PACKAGE, window.cancel)
    item.claimed = True
    item.hooked = control_window_hooks.install_listener(item.tick)
    item.commanded = item.input_changed = True
    window._active = item
    return item, root


def released() -> bool:
    return not window.active() and window._active is None and native.timer is None and clock.owner is None


check("nothing is open at first", not window.active())
item, root = opened()
check("an open window is active, its timer running under the mod's own name",
      window.active() and native.timer is not None and clock.owner == PACKAGE)
window.start(return_to_menu=True)
check("asking for the window again opens no second one, and names the mod's close command",
      window._active is item and said(f"already_open=true use_{COMMAND}=true"))

window.cancel()
check("closing gives everything back: the widget, the game's input, the cursor, the close command, the timer",
      item.closed and released() and pc.bShowMouseCursor is False and pc.CurrentMouseCursor == "Arrow"
      and [event for event in events if not event.startswith(TAG)][-3:]
      == ["widget removed", "input back to the game", f"command removed: {COMMAND}"])
check("and says so once, under the mod's own tag", said("closed=cancelled cleanup_ok=True attempt=1"))
count = len(events)
window.cancel()
check("closing twice does nothing more", len(events) == count)

item, root = opened()
item.poll(1)
check("an open window polled with nothing to do stays open", not item.closed and window.active())
item.form.poll = lambda: True
item.poll(window.POLL_NS + 1)
check("the window's own Close button closes it", item.closed and released() and said("closed=button cleanup_ok=True"))

item, root = opened(frontend=True)
item.close("button")
check("on the title screen the input goes back to the menu, not to the game",
      released() and "input back to the menu" in events and "input back to the game" not in events)

item, root = opened()
pc.OakCharacter = NS(name="another character")
item.poll(1)
check("another character (a change of map): the window closes and touches no input that is no longer its own",
      released() and said("closed=session_changed") and "input back to the game" not in events)

item, root = opened()
item.selector = lambda: None
item.poll(1)
check("a window the game has taken away closes", released() and said("closed=window_gone"))

item, root = opened()
item.bindings.ready = lambda: False
item.poll(1)
check("a mod that is no longer ready closes its window", released() and said("closed=mod_disabled"))


def fail():
    raise RuntimeError("a private detail")


item, root = opened()
item.form.poll = fail
item.tick(None, None, None, None)
check("an error while the window is open closes it, and the log names its kind, not its words",
      released() and said("poll_error=RuntimeError") and not any("a private detail" in str(event) for event in events))

item, root = opened()
root.RemoveFromParent = fail
item.close("cancelled")
check("a step of the cleaning that fails is said, the other steps are done, and the timer is kept for another try",
      said("cleanup_error=RuntimeError step=root") and "input back to the game" in events
      and f"command removed: {COMMAND}" in events and item.hooked and native.timer is not None and window._active is item)
root.RemoveFromParent = lambda: events.append("widget removed")
item.close("cancelled")
check("the next try finishes it", released() and "widget removed" in events)

matching = NS(_find=lambda method: NS(_properties=lambda: iter(NS(Name=name) for name in ("Widget", "slot", "ReturnValue"))))
changed = NS(_find=lambda method: NS(_properties=lambda: iter(NS(Name=name) for name in ("Widget", "Slot", "ReturnValue"))))
window.require_signature(matching, "AddWidget", ("Widget", "slot", "ReturnValue"))
try:
    window.require_signature(changed, "AddWidget", ("Widget", "slot", "ReturnValue"))
    check("a function of the game whose parameters have changed is refused", False)
except ValueError:
    check("a function of the game whose parameters have changed is refused", True)

# The real opening, as far as its first refusal: the game's viewport no longer takes a widget the way this window
# knows.
events.clear()
pc.bShowMouseCursor, pc.OakCharacter = False, character
find_class = sdk.find_class
sdk.find_class = lambda name: changed if name == "GameViewportSubsystem" else find_class(name)
window.start()
sdk.find_class = find_class
check("opening on a game whose viewport has changed builds nothing, says where it stopped and leaves nothing behind",
      said("open_error=ValueError stage=preflight") and released() and "input taken" not in events)
events.clear()
state["pc"] = None
window.start()
check("opening with no player to open it for does nothing, said", said("not_ready=true") and released())
state["pc"] = pc

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
