"""Tests the focus watch of an open window (Kevin, 2026-10-06: the window lost its focus to the game like a desktop
window): a focus that stays in the window, on the holder or one of its widgets, is left alone; a focus lost two turns
in a row is given back once, never at the first turn, where a focus just given may not have landed yet; never during a
key choice nor the turn after it, never before the window took the input nor once it is closed; a hidden cursor alone
only shows the cursor again, never takes the focus; each kind of log stops after three lines."""

import sys
from types import ModuleType, SimpleNamespace as NS

from ui_test_loader import load

events = []
sdk = ModuleType("unrealsdk")
sdk.logging = NS(info=events.append)
sdk.find_enum = lambda name: NS(Default="default")
sys.modules["unrealsdk"] = sdk
focus = load("control_window_focus")
failures = []


def check(label, condition):
    if not condition:
        failures.append(label)


class Root:
    holder = descendant = True

    def HasKeyboardFocus(self):
        return self.holder

    def HasFocusedDescendants(self):
        return self.descendant


def window(holder=False, descendant=True):
    root = Root()
    root.holder, root.descendant = holder, descendant
    session = NS(root=lambda: root, pc=lambda: pc, closed=False, input_changed=True, focused=0)
    session.focus = lambda: setattr(session, "focused", session.focused + 1)
    return focus.FocusWatch(), session, root


pc = NS(bShowMouseCursor=True, CurrentMouseCursor="crosshair")

watch, session, root = window()
for _ in range(5):
    watch.keep(session, False)
check("A widget of the window holding the focus is left alone", session.focused == 0)
root.descendant, root.holder = False, True
for _ in range(5):
    watch.keep(session, False)
check("The holder itself holding the focus is left alone (a click on the clear layer)", session.focused == 0)

watch, session, root = window(descendant=False)
watch.keep(session, False)
check("The first turn without focus waits: a focus just given may land a frame later", session.focused == 0)
watch.keep(session, False)
check("The second turn in a row gives the focus back", session.focused == 1)
check("Its log line says so", any("focus_restored=1" in line for line in events))
root.descendant = True
watch.keep(session, False)
root.descendant = False
watch.keep(session, False)
check("A turn with the focus back starts the count again", session.focused == 1)

watch, session, root = window(descendant=False)
for busy in (True, True, False, True, False):
    watch.keep(session, busy)
check("Never during a key choice nor the turn after it: the choice owns the input", session.focused == 0)
watch.keep(session, False)
check("Once the choice is over, a focus still lost comes back", session.focused == 1)

watch, session, root = window(descendant=False)
session.input_changed = False
for _ in range(3):
    watch.keep(session, False)
check("Never before the window took the input (the console still open)", session.focused == 0)
session.input_changed, session.closed = True, True
for _ in range(3):
    watch.keep(session, False)
check("Never once the window is closed: its cleanup gave the input back to the game", session.focused == 0)

events.clear()
watch, session, root = window(descendant=False)
for _ in range(20):
    watch.keep(session, False)
check("A focus taken again and again is given back each second turn", session.focused == 10)
check("Its log stops after three lines", sum("focus_restored=" in line for line in events) == 3)

events.clear()
watch, session, root = window()
pc.bShowMouseCursor = False
watch.keep(session, False)
check("A hidden cursor shows again, in its normal shape", pc.bShowMouseCursor is True and pc.CurrentMouseCursor == "default")
check("A hidden cursor alone never takes the focus (live click trace, 2026-09-21)", session.focused == 0)
for _ in range(6):
    pc.bShowMouseCursor = False
    watch.keep(session, False)
check("The cursor log stops after three lines", sum("cursor_visible_restored=" in line for line in events) == 3)
pc.bShowMouseCursor = False
watch.keep(session, True)
check("The cursor is left to a key choice", pc.bShowMouseCursor is False)

for label in failures:
    print("FAILED |", label)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | focus watch: kept, given back, waits, busy, closed, cursor, logs")
sys.exit(1 if failures else 0)
