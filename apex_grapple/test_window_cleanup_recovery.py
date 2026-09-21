"""A closing panel must release independent resources and recover transient SDK failures."""

import test_grapple_ui_window as f


def fail(*args, **kwargs):
    raise RuntimeError("injected failure")


def setup(frontend=False):
    item, root = f.session(frontend)
    registered = {"hook": True, "command": True}
    def remove(kind):
        registered[kind] = False
        f.events.append("unhook" if kind == "hook" else "uncommand")
    f.sdk.hooks.remove_hook = lambda *args: remove("hook")
    f.sdk.hooks.has_hook = lambda *args: registered["hook"]
    f.sdk.commands.remove_command = lambda *args: remove("command")
    f.sdk.commands.has_command = lambda *args: registered["command"]
    return item, root, registered


item, root, registered = setup()
original = item.same_context
item.same_context = fail
item.close("error")
assert "removed" in f.events and not registered["command"]
assert registered["hook"]  # The owned callback drives bounded recovery.
item.same_context = original
item.poll(f.window.time.perf_counter_ns() + 1_000_000_000)
assert "game_input" in f.events and not registered["hook"]
assert f.window._active is None

item, root, registered = setup()
library = item.library()
library.SetInputMode_GameOnly = fail
item.close("error")
assert "removed" in f.events and "game_input" not in f.events
library.SetInputMode_GameOnly = lambda *args: f.events.append("game_input")
item.close("command")  # An explicit request may retry immediately.
assert "game_input" in f.events and f.window._active is None

item, root, registered = setup()
remove = f.sdk.commands.remove_command
f.sdk.commands.remove_command = fail
item.close("error")
assert registered["command"] and f.window._active is item
f.sdk.commands.remove_command = remove
f.window.get_pc = lambda **kwargs: None  # Stop opening after successful preflight recovery.
f.window.start(return_to_menu=True)
assert not registered["command"] and f.window._active is None
f.window.get_pc = lambda **kwargs: f.pc

item, root, registered = setup()
item.library().SetInputMode_GameOnly = fail
item.close("error")
f.pc.OakCharacter = object()
item.close("command")
assert "game_input" not in f.events and f.window._active is None

item, root, registered = setup(frontend=True)
item.close("button")
assert "menu_input" in f.events and "game_input" not in f.events

item, root, registered = setup()
attempts = []
def persistent_failure(*args):
    attempts.append(1)
    raise RuntimeError("persistent")
item.library().SetInputMode_GameOnly = persistent_failure
item.close("error")
start = f.window.time.perf_counter_ns()
for now in range(1, 100):
    item.poll(start + now * 1_000_000_000)
assert 1 < len(attempts) <= 4 and not registered["hook"]
assert f.window._active is item  # Do not discard the owner of unfinished input cleanup.
item.library().SetInputMode_GameOnly = lambda *args: f.events.append("game_input")
item.close("command")
assert f.window._active is None and "game_input" in f.events
print("OK | isolated cleanup, bounded recovery, retained ownership, reopen and world-change safety")
