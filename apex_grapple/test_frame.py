"""Tests the frame loop: the keys kept bound, the rope run once a frame, and an error that stops the pull alone."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import frame, game, keys  # noqa: E402

fails: list[str] = []
SECOND = 1_000_000_000


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("the hook sits on the animation update, once per frame",
      frame.tick.path == "/Script/Engine.AnimInstance:BlueprintUpdateAnimation")
check("and carries this mod's own name, so it replaces no other mod's",
      frame.tick.identifier == "apex_grapple:frame")

player = sdk_stubs.FakeCharacter()
state["pc"] = sdk_stubs.player(player, state["mappings"])
state["kismet"].hit = (1000.0, "StaticMeshActor")

frame.on_frame(player.anim, SECOND)
check("the first frame binds the keys the game names", keys.is_bound())
check("and writes the game's action list down", any("the game lists" in line for line in state["misc"]))

before = len(state["misc"])
frame.on_frame(player.anim, 2 * SECOND)
check("a frame with the same key list binds nothing again", len(state["misc"]) == before)

state["mappings"][:] = [sdk_stubs.mapping("Action_Grapple", "B")]
frame.on_frame(player.anim, 4 * SECOND)
check("a key list that changed is bound again", "B" in state["keybinds"] and "V" not in state["keybinds"])

# The mod runs on the player's own animation and on nothing else in the level.
frame.rope.fire(player, 4 * SECOND)
frame.on_frame(object(), int(4.5 * SECOND))
check("another animation's frame is not the player's frame", frame.rope.state == "flying")
frame.on_frame(player.anim, int(4.5 * SECOND))
check("the player's own frame runs the rope", frame.rope.holds)


def explode(character, now_ns):
    raise RuntimeError("the velocity could not be written")


held = frame.rope.update
frame.rope.update = explode
frame.on_frame(player.anim, 5 * SECOND)
check("a pull that fails is stopped rather than left writing", not frame.rope.busy)
check("and the failure is written once", any("the pull stopped after an error" in line for line in state["errors"]))
frame.rope.update = held

frame.rope.fire(player, 6 * SECOND)
state["pc"] = sdk_stubs.player(sdk_stubs.FakeCharacter(), state["mappings"])
frame.on_frame(player.anim, 7 * SECOND)
check("a new character takes the old rope with it", not frame.rope.busy)

state["pc"] = None
frame.on_frame(player.anim, 8 * SECOND)
check("no player, nothing done", not frame.rope.busy)

frame.stop()
check("switching off takes the keys back", not keys.is_bound() and not state["keybinds"])
check("and forgets the player", game.character() is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
