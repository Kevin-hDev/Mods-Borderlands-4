"""Console commands finish before suspension; restore is bounded and preserves menu context."""

from ui_test_loader import load
from types import SimpleNamespace as NS

module = load("control_console_handoff")
api = vars(module)
events = []


class Native:
    def check_target(self):
        events.append("target")

    def tap(self, key):
        events.append(key)


handoff = api["Handoff"](Native(), 0xC0, 0, lambda: events.append("redraw"))
assert not handoff.advance(1) and not events
handoff.restore()
assert not events
assert not handoff.advance(api["COMMAND_RETURN_NS"])
assert events == [0x1B]
assert not handoff.advance(api["COMMAND_RETURN_NS"] + 1)
assert handoff.advance(api["COMMAND_RETURN_NS"] + api["MESSAGE_DRAIN_NS"])
handoff.restore()
assert events[-3:] == ["redraw", 0xC0, 0xC0]
count = len(events)
handoff.restore()
assert len(events) == count
for name in ("Escape", "Alt+F4", "Tilde;exit", None):
    try:
        module.keys.configured_key(name)
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported console key accepted")
print("OK | deferred handoff, no premature restore, menu redraw, exactly one restore")

select = api["select_console_key"]
assert select([NS(KeyName="F8")]) == 0x77
assert select([NS(KeyName="Gamepad_Special_Right"), NS(KeyName="Insert")]) == 0x2D
assert select([NS(KeyName="Tilde"), NS(KeyName="F8")]) == module.keys.TILDE
for keys in ([], [NS(KeyName="Unknown")], [NS(KeyName="F8")] * 17):
    try:
        select(keys)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid console configuration accepted")
print("OK | configured key priority, supported alternative, bounded console key list")
