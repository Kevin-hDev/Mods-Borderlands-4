"""Tests hold mode: a held press grapples, a tap on the melee key gives the game its punch back, the rest is unchanged."""

import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from unrealsdk.hooks import Block  # noqa: E402

from apex_grapple import control_config, game, game_grapple, key_hold, keys, melee_press, session, settings  # noqa: E402

game_grapple.ON = False
fails: list[str] = []
SECOND = 1_000_000_000


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class FakeRope:
    def __init__(self) -> None:
        self.takes_key, self.busy, self.holds = True, False, False
        self.fired, self.released = [], 0

    def fire(self, character, now_ns, native_action=True, held=False):
        self.fired.append((now_ns, native_action, held))
        return self.takes_key

    def key_up(self, now_ns):
        self.released += 1

    def let_go(self, reason, now_ns):
        self.holds = False

    def reset(self):
        self.holds = False


def press(key):
    return state["keybinds"][key](sdk_stubs.event("IE_Pressed"))


def release(key):
    return state["keybinds"][key](sdk_stubs.event("IE_Released"))


def tick_after(seconds):
    key_hold.tick(rope, player, key_hold._pressed_ns + int(seconds * SECOND))


def injected():
    return [str(action.Name) for _, _, action, _, _, _ in state["injections"]]


player = sdk_stubs.FakeCharacter()
state["pc"] = sdk_stubs.player(player, state["mappings"])
state["subsystems"] = [sdk_stubs.types.SimpleNamespace(Outer=object()),
                       sdk_stubs.types.SimpleNamespace(Outer=state["pc"].Player)]
game.refresh(0, at_once=True)
rope = FakeRope()
keys.bind(state["mappings"], rope)

check("both switches are off by default, so nothing waits",
      settings.keyboard_hold.default_value is False and settings.controller_hold.default_value is False)
check("the hold time is Kevin's 0.4 s, from 0.2 to 1 s",
      (settings.hold_time.default_value, settings.hold_time.min_value, settings.hold_time.max_value) == (0.4, 0.2, 1.0))
check("switches off, R3 grapples at once as before", press("Gamepad_RightThumbstick") is Block and len(rope.fired) == 1)
release("Gamepad_RightThumbstick")

settings.controller_hold.value = True
rope.fired.clear()
rope.released = 0
check("controller switch on, R3 is kept from the game", press("Gamepad_RightThumbstick") is Block)
check("and waits: no shot yet", not rope.fired and key_hold.pending())
tick_after(0.39)
check("not before the hold time", not rope.fired)
check("a tap's release is kept too, the game never sees half a press", release("Gamepad_RightThumbstick") is Block)
check("a tap gives the game the melee action back", injected() == ["Action_Melee"])
_, target, _, value, modifiers, triggers = state["injections"][0]
check("on the local player's subsystem, a full press for one frame, with no extra rules",
      target.Outer is state["pc"].Player and value.X == 1.0 and modifiers == [] and triggers == [])
check("a tap never fires the rope nor lets it go", not rope.fired and rope.released == 0 and not key_hold.pending())
check("and the log says what the tap gave", any("tap on Gamepad_RightThumbstick: gave the game Action_Melee" in line
                                                for line in state["misc"]))

state["injections"].clear()
press("Gamepad_RightThumbstick")
tick_after(0.4)
check("held for the hold time, the rope fires", len(rope.fired) == 1 and not key_hold.pending())
check("as a shot fired by a hold, whose release keeps the pull", rope.fired[0][2] is True and rope.fired[0][1] is True)
check("a held press gives the game nothing", not state["injections"])
check("its release reaches the rope", release("Gamepad_RightThumbstick") is Block and rope.released == 1)

rope.fired.clear()
rope.takes_key = False
press("Gamepad_RightThumbstick")
tick_after(0.5)
check("a held shot the rope refuses gives the game its melee action", injected() == ["Action_Melee"])
release("Gamepad_RightThumbstick")
check("and its release gives nothing more", injected() == ["Action_Melee"])
rope.takes_key = True

state["injections"].clear()
rope.fired.clear()
check("the keyboard keeps its own switch: V still grapples at once", press("V") is Block and len(rope.fired) == 1)
release("V")

rope.fired.clear()
rope.busy = True
check("a press during a shot calls it off at once", press("Gamepad_RightThumbstick") is Block and len(rope.fired) == 1)
release("Gamepad_RightThumbstick")
rope.busy = False

rope.fired.clear()
settings.controller_hold.value = "yes"
check("a malformed switch keeps the press at once", press("Gamepad_RightThumbstick") is Block and len(rope.fired) == 1)
release("Gamepad_RightThumbstick")
settings.controller_hold.value = True

press("Gamepad_RightThumbstick")
state["pc"].bShowMouseCursor = True
keys.observe(time.perf_counter_ns())
check("a menu opened during a hold forgets it, its release may never come", not key_hold.pending())
state["pc"].bShowMouseCursor = False
release("Gamepad_RightThumbstick")
check("and a later release gives nothing", not state["injections"])

press("Gamepad_RightThumbstick")
session.reset(rope)
check("a session reset forgets a held press", not key_hold.pending())
release("Gamepad_RightThumbstick")

rope.fired.clear()
press("Gamepad_RightThumbstick")
settings.controller_hold.value = False
tick_after(0.01)
check("a switch turned off during a hold fires at once", len(rope.fired) == 1 and not key_hold.pending())
release("Gamepad_RightThumbstick")
keys.unbind()

# A key of the player's own carries no grapple action in the game's list: its tap gives nothing back.
settings.keyboard_hold.value = True
original_groups = control_config.groups
control_config.groups = lambda mappings: (("G",), ("MouseScrollUp",))
keys.bind(state["mappings"], rope)
rope.fired.clear()
press("G")
release("G")
check("a tap on a key of the player's own does nothing", not rope.fired and not state["injections"])
check("a wheel notch has no release, so it never waits", press("MouseScrollUp") is Block and len(rope.fired) == 1)
keys.unbind()
control_config.groups = original_groups
settings.keyboard_hold.value = False

scans = state["find_all_calls"].count("/Script/EnhancedInput.EnhancedInputLocalPlayerSubsystem")
check("the subsystem is looked up once per controller", scans == 1)
state["subsystems"] = []
melee_press.forget()
check("no subsystem, no press, and nothing breaks", melee_press.press("V") == [])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
