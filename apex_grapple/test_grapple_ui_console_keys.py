"""Window messages never target another process, background window or arbitrary key."""

from pathlib import Path
import runpy
from types import SimpleNamespace as NS

api = runpy.run_path(str(Path(__file__).with_name("apex_grapple") / "control_console_keys.py"))
events = []


def driver():
    state = NS(foreground=71, pid=1234, scan=41, fail=None, tilde_vk=0xDE, layout=0x040C040C)

    def owner(_window, pid):
        pid._obj.value = state.pid
        return 1

    def post(*args):
        events.append(args)
        return args[1] != state.fail

    def mapping(code, mode, layout):
        assert layout == state.layout
        if mode == 1:
            assert code == 0x29
            return state.tilde_vk
        assert mode == 4
        return state.scan

    result = api["WindowKeys"].__new__(api["WindowKeys"])
    result.window, result.pid = 71, 1234
    result.api = NS(GetForegroundWindow=lambda: state.foreground,
                    GetWindowThreadProcessId=owner,
                    GetKeyboardLayout=lambda thread: state.layout, MapVirtualKeyExW=mapping,
                    PostMessageW=post)
    events.clear()
    return result, state


native, state = driver()
native.tap(api["TILDE"])
assert len(events) == 2 and all(event[0] == 71 for event in events)
assert [event[2] for event in events] == [0xDE, 0xDE], "French console key must use VK 0xDE"
assert events[1][3] == events[0][3] | api["KEYUP_BITS"]
native, state = driver()
state.tilde_vk, state.layout = 0xC0, 0x04090409
native.tap(api["TILDE"])
assert [event[2] for event in events] == [0xC0, 0xC0]
native, state = driver()
native.tap(api["configured_key"]("F8"))
assert [event[2] for event in events] == [0x77, 0x77]
for name, expected in (("F24", 0x87), ("A", 0x41), ("Zero", 0x30), ("NumPadNine", 0x69)):
    native, state = driver()
    native.tap(api["configured_key"](name))
    assert [event[2] for event in events] == [expected, expected]
native, state = driver()
state.scan = 0xE052
native.tap(api["configured_key"]("Insert"))
assert events[0][2] == 0x2D and events[0][3] == 1 | (0x52 << 16) | (1 << 24)
native, state = driver()
state.scan = 0x52  # Measured Windows mapping can omit E0 even with mode 4.
native.tap(api["configured_key"]("Insert"))
assert events[0][3] & (1 << 24), "Insert must remain extended without a returned prefix"
# Re-read the game's layout on each press, including after a live layout switch.
native, state = driver()
native.tap(api["TILDE"])
state.tilde_vk, state.layout = 0xC0, 0x04090409
native.tap(api["TILDE"])
assert [event[2] for event in events] == [0xDE, 0xDE, 0xC0, 0xC0]
native, state = driver()
state.tilde_vk = 0
try:
    native.tap(api["TILDE"])
except RuntimeError:
    pass
else:
    raise AssertionError("Missing layout mapping accepted")
assert not events
for field, value in (("foreground", 72), ("pid", 9000), ("scan", 0), ("layout", 0),
                     ("scan", 0xE100), ("scan", 0xFF52)):
    native, state = driver()
    setattr(state, field, value)
    try:
        native.tap(api["TILDE"])
    except RuntimeError:
        pass
    else:
        raise AssertionError("Unsafe target accepted")
    assert not events
native, state = driver()
try:
    native.tap(0x73 + 1000)
except ValueError:
    pass
else:
    raise AssertionError("Arbitrary key accepted")
assert not events
native, state = driver()
state.fail = api["WM_KEYDOWN"]
try:
    native.tap(api["TILDE"])
except RuntimeError:
    pass
else:
    raise AssertionError("Failed queue reported success")
assert len(events) == 1
print("OK | layouts, live layout switch, configured keys, extended keys and window safety")
