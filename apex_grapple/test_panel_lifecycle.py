"""A disabled mod's settings remain available, while world transitions still close them."""

import test_grapple_ui_window as f

item, root = f.session()
item.form.keep_when_disabled = True
f.window.cancel_for_gameplay()
assert not item.closed
item.pc().OakCharacter = object()
f.window.cancel_for_gameplay()
assert item.closed
item, root = f.session(frontend=True)
item.form.keep_when_disabled = True
f.window.cancel_for_gameplay()
assert not item.closed
f.window.cancel()
assert item.closed  # Explicit close is never suppressed.
item, root = f.session()
f.window.cancel_for_gameplay()
assert item.closed  # Legacy controls-only panel keeps the previous policy.
print("OK | settings remain open when disabled; explicit cancel and world changes still close")
