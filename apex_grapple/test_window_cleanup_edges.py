"""Cleanup ownership survives disappearing objects, silent refusals and persistent failures."""

import test_window_cleanup_recovery as f

window, sdk, events = f.f.window, f.f.sdk, f.f.events

item, root, registered = f.setup()
original = item.root
item.root = f.fail
item.close("error")
assert "game_input" in events and not registered["command"]
item.root = original
item.close("command")
assert "removed" in events and window._active is None

item, root, registered = f.setup()
original = sdk.commands.remove_command
sdk.commands.remove_command = lambda *args: None  # SDK can refuse without an exception.
item.close("error")
assert window._active is item and item.commanded
sdk.commands.remove_command = original
item.close("command")
assert not registered["command"] and window._active is None

item, root, registered = f.setup()
original = sdk.hooks.remove_hook
sdk.hooks.remove_hook = f.fail
item.close("error")
assert "game_input" in events and window._active is item
sdk.hooks.remove_hook = original
item.close("command")
assert not registered["hook"] and window._active is None

old = item
item, root, registered = f.setup()
old.close("late callback")
assert registered == {"hook": True, "command": True} and window._active is item
item.close("button")

# No owner: never delete an arbitrary command merely because its name matches.
sdk.commands.has_command = lambda *args: True
sdk.commands.remove_command = lambda *args: (_ for _ in ()).throw(AssertionError("Foreign command"))
window.start(return_to_menu=True)
assert window._active is None

item, root, registered = f.setup()
item.form.keep_when_disabled = True
item.same_context = f.fail
window.cancel_for_gameplay()
assert item.closed and "removed" in events and not registered["command"]
item.same_context = lambda pc: False
item.close("command")
assert window._active is None

item, root, registered = f.setup()
item.input_changed = False
item.pc = f.fail
item.close("open_failed")
assert window._active is None and "removed" in events
print("OK | independent native reads, silent SDK refusal, hook retry, old and foreign ownership")
