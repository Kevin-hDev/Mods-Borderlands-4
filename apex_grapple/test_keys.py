"""Tests grapple input and jump-to-release without spending the release press as a jump."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from unrealsdk.hooks import Block  # noqa: E402

from apex_grapple import control_config, game_target, game_grapple, game, keys, settings  # noqa: E402

# These tests describe the mod's own grapple. The prototype that hands every press to the game is
# switched off here and tested on its own at the end.
game_grapple.ON = False

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class FakeRope:
    """Answers as the real rope does, and writes down what it was asked."""

    def __init__(self) -> None:
        self.takes_key = True
        self.holds = False
        self.fired = 0
        self.native_actions = []
        self.released = 0
        self.raises = False

    def fire(self, character, now_ns, native_action=True):
        if self.raises:
            raise RuntimeError("the trace failed")
        self.fired += 1
        self.native_actions.append(native_action)
        return self.takes_key

    def key_up(self, now_ns):
        self.released += 1

    def let_go(self, reason, now_ns):
        self.holds = False

    def reset(self):
        self.holds = False


def press(key: str):
    return state["keybinds"][key](sdk_stubs.event("IE_Pressed"))


def release(key: str):
    return state["keybinds"][key](sdk_stubs.event("IE_Released"))


player = sdk_stubs.FakeCharacter()
state["pc"] = sdk_stubs.player(player, state["mappings"])
game.refresh(0, at_once=True)
rope = FakeRope()

check("binding answers yes when the game names a grapple key", keys.bind(state["mappings"], rope))
check("every grapple key is bound", "V" in state["keybinds"] and "Gamepad_RightThumbstick" in state["keybinds"])
check("and every jump key too", "SpaceBar" in state["keybinds"])
check("the keys are said to be bound", keys.is_bound())
check("and they match the game's list", keys.matches(state["mappings"]))

check("a press that grapples is kept from the game", press("V") is Block)
check("the rope was asked", rope.fired == 1)
check("the game's native grapple key is identified", rope.native_actions[-1] is True)
check("its release is kept too, so the game never sees half a press", release("V") is Block)
check("and the rope was told the key came up", rope.released == 1)

rope.takes_key = False
check("a press that does not grapple goes to the game, which punches", press("V") is None)
check("and so does its release", release("V") is None)

rope.raises = True
check("a press that fails goes to the game rather than being swallowed", press("V") is None)
check("the failure is written once", any("grapple key passed to the game" in line for line in state["errors"]))
rope.raises = False

check("jump is free while nothing holds", press("SpaceBar") is None)
check("and its release too", release("SpaceBar") is None)
rope.holds = True
check("jump releases without spending a jump", press("SpaceBar") is Block and not rope.holds)
check("its release is kept as well", release("SpaceBar") is Block)
settings.block_jump.value = False
rope.holds = True
check("option off releases and passes jump to the game", press("SpaceBar") is None and not rope.holds)
settings.block_jump.value = True
rope.holds = False

# A key set to both must grapple: blocking it as a jump would swallow the grapple press itself.
keys.unbind()
both = [sdk_stubs.mapping("Action_Grapple", "V"), sdk_stubs.mapping("Action_Jump_HoldToGlide", "V")]
keys.bind(both, rope)
rope.takes_key, rope.holds = True, True
check("a key that does both belongs to the grapple", press("V") is Block and rope.fired > 0)
release("V")

keys.unbind()

original_groups = control_config.groups
control_config.groups = lambda mappings: (("G",), ("Gamepad_RightThumbstick",))
keys.bind(state["mappings"], rope)
check("a custom keyboard key still starts the mod's grapple", press("G") is Block)
check("the custom key is not mistaken for the game's melee action", rope.native_actions[-1] is False)
release("G")
keys.unbind()
control_config.groups = original_groups

check("unbinding takes every key back", not state["keybinds"])
check("and says so", not keys.is_bound())
check("a game that names no grapple key binds nothing",
      not keys.bind([sdk_stubs.mapping("Action_Reload", "R")], rope))
check("not even the jump, which would then be blocked with no way to grapple", "R" not in state["keybinds"])

keys.bind(state["mappings"], rope)
check("a changed key list no longer matches", not keys.matches([sdk_stubs.mapping("Action_Grapple", "B")]))
keys.unbind()

game.forget()
keys.bind(state["mappings"], rope)
state["pc"] = None
game.refresh(0, at_once=True)
check("with the player gone, a press is handed straight to the game", press("V") is None)
keys.unbind()

# The prototype: every press goes to the game, which grapples to the mod's point with its own rope.
state["pc"] = sdk_stubs.player(player, state["mappings"])
game.refresh(0, at_once=True)
keys.bind(state["mappings"], rope)
game_grapple.ON = True
game_target.ready = lambda: True
rope.fired = 0
check("with the prototype on and its point placed, a press goes to the game", press("V") is None)
check("and the mod's own rope is not asked at all", rope.fired == 0)
check("its release goes to the game too", release("V") is None)

# The point could not be placed: 0.10.0 then left the player with no grapple at all (2026-09-21).
game_target.ready = lambda: False
rope.fired = 0
check("with no point placed, the mod's own grapple runs as before", press("V") is Block)
check("and the mod's rope is asked", rope.fired == 1)
release("V")
game_grapple.ON = False
keys.unbind()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
