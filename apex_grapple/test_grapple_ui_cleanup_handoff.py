"""Closing during console transfer keeps cleanup alive until the menu returns."""

import sys
from types import ModuleType, SimpleNamespace as NS

from ui_test_loader import load


messages = []
sdk = ModuleType("unrealsdk")
sdk.logging = NS(info=messages.append)
sys.modules["unrealsdk"] = sdk

Handoff = load("control_console_handoff").Handoff
module = load("control_window_cleanup")
Cleanup = module.Cleanup
events = []


class Native:
    def check_target(self):
        return True

    def tap(self, key):
        events.append(key)


handoff = Handoff(Native(), 0xC0, 0, lambda: events.append("redraw"))
pc = object()
session = NS(input_changed=True, pc=lambda: pc, same_context=lambda current: current is pc,
             handoff=handoff, hooked=False)
cleanup = Cleanup(session, "button")
cleanup.done.update(("root", "input", "cursor", "shape", "command"))

assert cleanup.advance(0, explicit=True) is False
assert "menu" not in cleanup.done and not events
assert cleanup.advance(handoff.next_step) is False
assert events == [0x1B] and "menu" not in cleanup.done
assert cleanup.advance(handoff.next_step) is True
assert events == [0x1B, "redraw", 0xC0, 0xC0]
assert "menu" in cleanup.done
print("OK | early close finishes console handoff before completing cleanup")
