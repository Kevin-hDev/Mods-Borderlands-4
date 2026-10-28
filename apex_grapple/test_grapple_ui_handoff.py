"""Console commands finish before suspension; restore is bounded and preserves menu context."""

import sys
from types import ModuleType, SimpleNamespace as NS

from ui_test_loader import load

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
for keys in ([], [NS(KeyName="+")], [NS(KeyName="Unknown")], [NS(KeyName="F8")] * 17):
    assert select(keys) is None, "a console key the window cannot press must not refuse the window"
print("OK | configured key priority, supported alternative, bounded console key list")

events.clear()
handoff = api["Handoff"](Native(), None, 0, lambda: events.append("redraw"))
assert not handoff.advance(api["COMMAND_RETURN_NS"]) and events == [0x1B]
assert handoff.advance(api["COMMAND_RETURN_NS"] + api["MESSAGE_DRAIN_NS"])
assert handoff.restore() is True and handoff.restore() is True
assert events == [0x1B, "target", "target", "redraw"], events
print("OK | unsupported console key: console still closed for the window, menu redrawn, no key pressed after")


class WindowKeys:
    def mapping(self, key):
        assert key == module.keys.TILDE, "only a supported key is mapped"
        return 0xDE, 0x29


def create_with(names):
    logged = []
    sdk = ModuleType("unrealsdk")
    sdk.logging = NS(info=logged.append)
    sdk.find_class = lambda _class: NS(ClassDefaultObject=NS(ConsoleKeys=[NS(KeyName=key) for key in names]))
    console_menu = ModuleType("console_mod_menu")
    console_menu.screens = NS(screen_stack=[NS(draw=lambda: None)])
    saved = {name: sys.modules.get(name) for name in ("unrealsdk", "console_mod_menu")}
    real_keys, module.keys.WindowKeys = module.keys.WindowKeys, WindowKeys
    sys.modules.update(unrealsdk=sdk, console_mod_menu=console_menu)
    try:
        return module.create(0), logged
    finally:
        module.keys.WindowKeys = real_keys
        for name, value in saved.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value


# A player's console key '+' refused every mod window at its preflight (Nexus report, 2026-10-06).
handoff, logged = create_with(["+"])
assert handoff.console_key is None
assert logged == ["[GrappleUIWindow] console_key_mapping unsupported keys=+ reopen=player"], logged
handoff, logged = create_with(["Tilde"])
assert handoff.console_key == module.keys.TILDE
assert logged == ["[GrappleUIWindow] console_key_mapping vk=0xde scan=0x29"], logged
print("OK | the window opens from the console whatever its key; only a supported key is pressed again")
