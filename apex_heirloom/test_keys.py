"""Tests the two keys: silent until the holster runs, then each puts the weapon away held or pressed as set, never
blocks the game, survives an error; stopped, they are silent again and nothing held is counted."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fake_player  # noqa: E402
import heirloom_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = heirloom_stubs.install()

from apex_heirloom import holster_settings, keys  # noqa: E402

now = [100.0]
keys.clock = lambda: now[0]
keys.keyboard_bind.key = "A"


def press(bind, name: str):
    return bind.callback(fake_player.event(name))


check("the keyboard key is read on every event, held keys included", keys.keyboard_bind.event_filter is None)
check("the controller button is Square by default", keys.controller_bind.key == "Gamepad_FaceButton_Left")
check("the controller button is read on every event", keys.controller_bind.event_filter is None)
check("each bind is hidden and shown once, through its option",
      keys.keyboard_bind.is_hidden and keys.controller_bind.is_hidden
      and keys.keyboard_key.is_hidden is False and keys.controller_key.is_hidden is False)
keys.controller_key.value = "Gamepad_FaceButton_Top"
check("a button changed in the menu reaches the controller's bind", keys.controller_bind.key == "Gamepad_FaceButton_Top")
keys.controller_key.value = "A"
check("a keyboard key is refused on the controller's option, which unbinds it",
      keys.controller_key.value is None and keys.controller_bind.key is None)
keys.controller_key.value = "Gamepad_FaceButton_Left"
keys.keyboard_key.value = "Gamepad_FaceButton_Left"
check("a controller button is refused on the keyboard's option", keys.keyboard_key.value is None)
keys.keyboard_key.value = "A"
check("the keyboard's key back to A", keys.keyboard_bind.key == "A")

pc, character = fake_player.player(fake_player.weapon())
state["pc"] = pc
holster_settings.keyboard_hold.value = True
check("before the holster runs, a key does nothing and nothing is counted",
      press(keys.keyboard_bind, "IE_Pressed") is None and not keys.pending() and not keys.running())
lines = len(state["misc"])
keys.tell()
check("before the holster runs, no keys line is written", len(state["misc"]) == lines)
keys.keyboard_bind.key = "Q"
keys.start()
check("started, the keys listen, each bind on its option's key", keys.running() and keys.keyboard_bind.key == "A")
check("a key event never blocks the game", press(keys.keyboard_bind, "IE_Pressed") is None)
keys.tell()
keys.tell()
check("started, the keys in use are written once",
      [line for line in state["misc"][lines:] if line.startswith("[Tidy Weapons] on: ")]
      == [f"[Tidy Weapons] on: {keys.describe()}"])
check("held toward the hold time, the key is pending", keys.pending() is True)
now[0] += 0.2
keys.tick(now[0])
check("held less than the hold time, the weapon stays", character.calls == [])
now[0] += 0.25
keys.tick(now[0])
check("held the hold time, the weapon is put away", character.calls == [(None, 0, 0, 0, -1)])
check("the log says so, with the key and how it asks",
      state["misc"][-1] == "[Tidy Weapons] weapon put away (keyboard key A, hold)")
check("once asked, nothing is pending", keys.pending() is False)
press(keys.keyboard_bind, "IE_Released")

pc, character = fake_player.player(fake_player.weapon("OakWeapon_2"))
state["pc"] = pc
holster_settings.controller_hold.value = False
check("pressed on the controller, the event does not block the reload", press(keys.controller_bind, "IE_Pressed") is None)
check("pressed, the weapon is put away at once", character.calls == [(None, 0, 0, 0, -1)])
check("the log names the controller button",
      state["misc"][-1] == "[Tidy Weapons] weapon put away (controller key Gamepad_FaceButton_Left, press)")
press(keys.controller_bind, "IE_Released")

pc, character = fake_player.player(None)
state["pc"] = pc
now[0] += 5
press(keys.controller_bind, "IE_Pressed")
check("no weapon in hand, the log says so", state["misc"][-1].startswith("[Tidy Weapons] no weapon in hand"))
press(keys.controller_bind, "IE_Released")

holster_settings.keyboard_hold.value = True
press(keys.keyboard_bind, "IE_Pressed")
keys.stop()
check("stopped, no key is pending, and a key does nothing", keys.pending() is False and not keys.running()
      and press(keys.keyboard_bind, "IE_Pressed") is None and keys.pending() is False)
keys.start()
lines = len(state["misc"])
keys.tell()
check("started again, they are written again", state["misc"][lines:] == [f"[Tidy Weapons] on: {keys.describe()}"])


class Broken:
    @property
    def Pawn(self):
        raise RuntimeError("game gone")


state["pc"] = Broken()
holster_settings.controller_hold.value = False
check("an error inside never blocks the key", press(keys.controller_bind, "IE_Pressed") is None)
check("the error is written once", len(state["errors"]) == 1 and "controller key not followed" in state["errors"][0])
press(keys.controller_bind, "IE_Pressed")
check("the same error is not written again", len(state["errors"]) == 1)

holster_settings.hold_time.value = 0.5
check("the log line gives the keys and settings in use",
      keys.describe() == "keyboard A (hold), controller Gamepad_FaceButton_Left (press), hold 0.50 s")
keys.keyboard_bind.key = None
check("a keyboard key the layout could not give is said", keys.describe().startswith("keyboard no key (hold)"))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
