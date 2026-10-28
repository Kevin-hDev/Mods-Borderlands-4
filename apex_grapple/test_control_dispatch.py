"""Custom combinations use the production callbacks and leave the other device alone."""

import control_fixture as f
from apex_grapple import game, keys, session
from unrealsdk.hooks import Block


class Rope:
    holds = False
    def __init__(self):
        self.fires = 0
        self.releases = 0
    def fire(self, character, now, native_action=True):
        self.fires += 1
        return True
    def key_up(self, now):
        self.releases += 1
    def reset(self):
        self.holds = False


player = f.sdk_stubs.FakeCharacter()
f.state["pc"] = f.sdk_stubs.player(player, f.state["mappings"])
rope = Rope()
game.refresh(0, at_once=True)
session.refresh(0, rope, at_once=True)
device = f.config.DEVICES[0]
device.mode.value = f.config.DOUBLE
device.first.value, device.second.value = "LeftControl", "ThumbMouseButton2"
assert keys.bind(f.state["mappings"], rope)
assert "V" not in f.state["keybinds"] and "Gamepad_RightThumbstick" in f.state["keybinds"]


def event(key, name="IE_Pressed"):
    return f.state["keybinds"][key](f.sdk_stubs.event(name))


assert event("LeftControl") is None and rope.fires == 0
assert event("ThumbMouseButton2") is Block and rope.fires == 1
assert event("ThumbMouseButton2", "IE_Repeat") is Block and rope.fires == 1
assert event("LeftControl", "IE_Released") is None and rope.releases == 1
assert event("ThumbMouseButton2", "IE_Released") is Block and rope.releases == 1
assert event("ThumbMouseButton2") is None
assert event("LeftControl") is Block and rope.fires == 2
event("LeftControl", "IE_Released")
event("ThumbMouseButton2", "IE_Released")
assert event("Gamepad_RightThumbstick") is Block and rope.fires == 3
event("Gamepad_RightThumbstick", "IE_Released")

event("LeftControl")
session.reset(rope)
assert event("ThumbMouseButton2") is None and rope.fires == 3
event("LeftControl", "IE_Released")
event("ThumbMouseButton2", "IE_Released")

# A missed release while a menu suppresses input cannot complete a later chord.
event("LeftControl")
f.state["pc"].bShowMouseCursor = True
keys.observe(1)
f.state["pc"].bShowMouseCursor = False
assert event("ThumbMouseButton2") is None and rope.fires == 3
event("ThumbMouseButton2", "IE_Released")
event("LeftControl", "IE_Released")
event("LeftControl")
keys.observe(f.config.INPUT_GAP_NS + 2)
assert event("ThumbMouseButton2") is None and rope.fires == 3
event("ThumbMouseButton2", "IE_Released")
event("LeftControl", "IE_Released")

# While a native selector owns input, the gameplay callbacks must leave it alone.
from apex_grapple import control_window
previous_active = control_window.active
control_window.active = lambda: True
assert event("LeftControl") is None and event("ThumbMouseButton2") is None
assert event("SpaceBar") is None and rope.fires == 3
control_window.active = previous_active
assert event("ThumbMouseButton2") is None  # No stale chord was started in the window.
keys.unbind()
print("OK | both devices, both chord orders, repeats, reset and native UI input isolation")
