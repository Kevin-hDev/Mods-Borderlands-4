"""Tests the frame loop: the keys kept bound, the rope run once a frame, and an error that stops the pull alone."""

import pathlib
import sys
import types

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
frame.on_frame(sdk_stubs.other_anim(), int(4.5 * SECOND))
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


class CountedLine:
    """A line of the game's key list that counts the mod's reads: each one is a call into the game."""

    def __init__(self, action: str, key: str) -> None:
        self._action = types.SimpleNamespace(Name=action)
        self._key = types.SimpleNamespace(KeyName=key)
        self.reads = 0

    @property
    def Action(self):
        self.reads += 1
        return self._action

    @property
    def Key(self):
        self.reads += 1
        return self._key


counted = [CountedLine("Action_Melee", "V"), CountedLine("Action_Melee", "Gamepad_RightThumbstick"),
           CountedLine("Action_Jump_HoldToGlide", "SpaceBar"), CountedLine("Action_Reload", "R")]
state["pc"] = sdk_stubs.player(player, counted)
frame.on_frame(player.anim, 9 * SECOND)
check("a key list read from the game binds its keys", "V" in state["keybinds"] and "SpaceBar" in state["keybinds"])
for line in counted:
    line.reads = 0
before = len(state["misc"])
frame.on_frame(player.anim, 10 * SECOND)
check("the same list a second later binds nothing again", len(state["misc"]) == before)
# 2026-10-24 review: the check of every second walked the list about eight times, some 50 reads a line in one frame.
check("and reads each line of it once: its action and its key", all(line.reads == 2 for line in counted))

# 2026-10-24 review: alone, every frame asked the game twice whether the player is a co-op guest, looked the network
# role's names up twice, and read the list of players for the grapples of players who are not there.
import mods_base  # noqa: E402  (the test's own, from sdk_stubs)
import unrealsdk  # noqa: E402

frame.on_frame(player.anim, 11 * SECOND)
looked_up: list[str] = []
roles: list[int] = []
viewport_reads: list[int] = []
real_enum, real_engine = unrealsdk.find_enum, mods_base.ENGINE


class CountedEngine:
    @property
    def GameViewport(self):
        viewport_reads.append(1)
        return real_engine.GameViewport


unrealsdk.find_enum = lambda name: (looked_up.append(name), real_enum(name))[1]
player.GetLocalRole = lambda: (roles.append(1), "ROLE_Authority")[1]
mods_base.ENGINE = CountedEngine()
for step in range(1, 4):
    frame.on_frame(player.anim, 11 * SECOND + step * 10_000_000)
unrealsdk.find_enum, mods_base.ENGINE = real_enum, real_engine
del player.GetLocalRole
check("alone, each frame asks the player's network role once", len(roles) == 3)
check("whose names are looked up once for good", len(looked_up) <= 1)
check("and reads no list of players while no other player's grapple is drawn", not viewport_reads)

# 2026-10-24 review: with a rope out, the settings were checked twice a frame, by the frame and again by the rope.
from apex_grapple import settings  # noqa: E402

checks: list[int] = []
real_bounds = settings.keep_in_bounds
settings.keep_in_bounds = lambda: (checks.append(1), real_bounds())[1]
frame.rope.fire(player, 12 * SECOND)
checks.clear()
frame.on_frame(player.anim, 12 * SECOND + 10_000_000)
settings.keep_in_bounds = real_bounds
check("a frame with a rope out checks the settings once", frame.rope.busy and len(checks) == 1)
frame.rope.reset()

# 2026-10-24, Kevin's decision 1: another character's update asked the game for the controller and the character
# before it could be told apart from the player's, enemies included. It now asks nothing while the player's body
# updated in the last 50 ms (played_body.py).
asked: list[int] = []
real_pc = game.get_pc
game.get_pc = lambda **kwargs: (asked.append(1), real_pc(**kwargs))[1]
frame.on_frame(player.anim, 13 * SECOND)
asked.clear()
for _ in range(20):
    frame.on_frame(sdk_stubs.other_anim(), 13 * SECOND + 1_000_000)
check("twenty enemies' updates in the player's frame ask the game nothing", not asked)
frame.on_frame(sdk_stubs.FakeAnim(player.Mesh), 13 * SECOND + 2_000_000)
check("a body on the player's own mesh is still checked", len(asked) > 0)
asked.clear()
frame.on_frame(sdk_stubs.other_anim(), 13 * SECOND + 50_000_000)
check("once the player's body is quiet for 50 ms, any update asks again", len(asked) > 0)
game.get_pc = real_pc

frame.stop()
check("switching off takes the keys back", not keys.is_bound() and not state["keybinds"])
check("and forgets the player", game.character() is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
