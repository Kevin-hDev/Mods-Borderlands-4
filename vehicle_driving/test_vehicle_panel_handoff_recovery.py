"""The standalone Vehicle Driving menu retries an interrupted console return."""

from types import SimpleNamespace as NS

import sdk_stubs


sdk_stubs.install()

import unrealsdk  # noqa: E402

from vehicle_driving import control_console_handoff, control_window_cleanup  # noqa: E402


unrealsdk.logging.info = lambda _message: None
events = []


class Native:
    def check_target(self):
        return True

    def tap(self, key):
        events.append(key)


def redraw():
    events.append("redraw")
    if events.count("redraw") == 1:
        raise RuntimeError("temporary redraw failure")


handoff = control_console_handoff.Handoff(Native(), 0xC0, 0, redraw)
pc = object()
session = NS(input_changed=True, pc=lambda: pc, same_context=lambda current: current is pc,
             handoff=handoff, hooked=False)
cleanup = control_window_cleanup.Cleanup(session, "button")
cleanup.done.update(("root", "input", "cursor", "shape", "command"))

assert cleanup.advance(0, explicit=True) is False
assert cleanup.advance(handoff.next_step) is False
assert cleanup.advance(handoff.next_step) is False
assert events == [0x1B, "redraw"]
assert cleanup.advance(cleanup.next_try) is True
assert events == [0x1B, "redraw", "redraw", 0xC0, 0xC0]
print("OK | Vehicle Driving retries a failed console redraw and returns to the menu")
print("RESULTAT: TOUS LES TESTS PASSENT")
