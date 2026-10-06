"""Tests the Escape watch with a fake user32 whose read takes the PRESSED bit, as Windows does (taken from Save
Editor's keys tests when the watch became every window's, 2026-10-06): only VK_ESCAPE is read; true once, one read
after the release, never while held; a PRESSED bit alone counts as a press; the close is forgotten once given; a press
during the close's turn waits for its own release; the read made when the watch is built drops a press from before the
window opened, and a key held then is not a release by itself; a press while a key is being chosen, or at the turn
after (the key's field let go of it), never closes, even held long after; an unreadable key gives false, one log line
and no new read; outside Windows, loading user32 is refused."""

import os
import sys
from types import ModuleType, SimpleNamespace as NS

from ui_test_loader import load

events = []
sdk = ModuleType("unrealsdk")
sdk.logging = NS(info=events.append)
sys.modules["unrealsdk"] = sdk
escape = load("control_escape")
ESCAPE = 0x1B
fails = []


def check(label, condition):
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class FakeUser32:
    def __init__(self):
        self.calls, self.held, self.pressed = [], False, False

    def GetAsyncKeyState(self, key):
        self.calls.append(key)
        answer = (0x8000 if self.held else 0) | (1 if self.pressed else 0)
        self.pressed = False
        return answer - 0x10000 if answer & 0x8000 else answer


def reads(watch, count, busy=False):
    return [watch.released(busy) for _ in range(count)]


api = FakeUser32()
watch = escape.EscapeWatch(api)
check("the watch reads Escape once when it is built", api.calls == [ESCAPE])
check("a key never pressed: false, and only VK_ESCAPE is read", reads(watch, 3) == [False] * 3
      and set(api.calls) == {ESCAPE})
api.held = True
check("held gives false at every read, from a negative SHORT as ctypes returns it", reads(watch, 4) == [False] * 4)
api.held = False
check("the read after the release gives false: the window waits one turn", watch.released() is False)
mark = len(events)
check("the next read gives true", watch.released() is True)
check("with one log line", sum("escape_released=true" in event for event in events[mark:]) == 1)
check("then false again, and without a new press it stays false", reads(watch, 3) == [False] * 3)
api.pressed = True
check("a PRESSED bit alone (a tap between two reads) gives false, true, then false", reads(watch, 3)
      == [False, True, False])
api.held = True
watch.released()
api.held = False
watch.released()
api.held = True
check("a new press while the close is pending: nothing closes while it is held", reads(watch, 3) == [False] * 3)
api.held = False
check("and the close comes one turn after that press is released", reads(watch, 3) == [False, True, False])
api.held = True
watch.released()
api.held = False
watch.released()
api.pressed = True
check("a tap while the close is pending waits one more turn", reads(watch, 3) == [False, True, False])

api = FakeUser32()
api.pressed = True
check("an Escape pressed before the window opened never closes it", reads(escape.EscapeWatch(api), 4) == [False] * 4)
api = FakeUser32()
api.held = True
built = escape.EscapeWatch(api)
api.held = False
check("a key held when the window opens is not a release by itself", reads(built, 3) == [False] * 3)

# A key being chosen: Escape cancels the choice in its field, never the window.
api = FakeUser32()
watch = escape.EscapeWatch(api)
api.held = True
check("Escape held while a key is being chosen: false", reads(watch, 2, busy=True) == [False, False])
check("still held once the field let go of it: false", reads(watch, 3) == [False] * 3)
api.held = False
check("released after the choice: the window stays open", reads(watch, 3) == [False] * 3)
watch.released(True)
api.held = True
check("pressed at the turn the field lets go of it (busy at the previous read): false", reads(watch, 2) == [False] * 2)
api.held = False
check("and its release never closes either", reads(watch, 3) == [False] * 3)
watch.released(True)
api.pressed = True
check("a tap seen at the turn after the choice: false, and nothing pending", reads(watch, 3) == [False] * 3)
api.held = True
watch.released()
api.held = False
check("the next Escape, with no key being chosen, closes as usual", reads(watch, 3) == [False, True, False])
api.held = True
watch.released()
api.held = False
watch.released()
check("a key choice starting while a close is pending cancels that close", reads(watch, 2, busy=True) == [False] * 2
      and reads(watch, 2) == [False] * 2)


class BrokenApi:
    calls = 0

    def GetAsyncKeyState(self, key):
        self.calls += 1
        raise OSError("no keyboard")


mark = len(events)
broken_api = BrokenApi()
broken = escape.EscapeWatch(broken_api)
check("an unreadable key: false at every read, the window keeps its Close button", reads(broken, 3) == [False] * 3)
check("and the key is not asked again at every turn", broken_api.calls == 1)
check("one log line, not one per turn, with the error's type and no detail",
      sum("escape_unreadable=OSError" in event for event in events[mark:]) == 1
      and not any("no keyboard" in event for event in events[mark:]))

platform = os.name
os.name = "posix"
try:
    try:
        escape.user32()
    except RuntimeError as error:
        refused = str(error) == "Unsupported platform"
    else:
        refused = False
    mark = len(events)
    unloaded = escape.EscapeWatch()
    lazy = reads(unloaded, 2) == [False, False] and sum("escape_unreadable=RuntimeError" in event
                                                       for event in events[mark:]) == 1
finally:
    os.name = platform
check("outside Windows loading user32 is refused", refused)
check("and a watch built without an api reads nothing and says so once", lazy)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
