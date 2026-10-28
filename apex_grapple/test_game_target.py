"""Tests the mod's grapple point: placed under the aim, sent away to spare the punch, never fatal."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import game_target  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Point:
    """A grapple point as the game spawns one: it moves, and it can be destroyed."""

    def __init__(self) -> None:
        self.Name = "GrapplePoint_1"
        self.at, self.destroyed = None, False

    def K2_SetActorLocation(self, where, sweep, hit, teleport):
        self.at = (where.X, where.Y, where.Z)

    def K2_DestroyActor(self):
        self.destroyed = True


class Statics:
    def __init__(self) -> None:
        self.spawned, self.finished = [], []

    # Both take the scale rule Unreal 5 added, and require it, as the game does. Verified on
    # 2026-09-21: "missing 1 required positional argument: 'TransformScaleMethod'". A fake that did
    # not require it let that very call through the tests and cost a whole session.
    def BeginDeferredActorSpawnFromClass(self, context, kind, where, handling, owner, TransformScaleMethod):
        point = Point()
        self.spawned.append((kind, handling, TransformScaleMethod))
        return point, where

    def FinishSpawningActor(self, actor, where, TransformScaleMethod):
        if not isinstance(actor, Point):
            raise TypeError("FinishSpawningActor expects an actor, not an output tuple")
        self.finished.append(actor)
        return actor, where


statics = Statics()
state["extra_classes"] = {"GameplayStatics": types.SimpleNamespace(ClassDefaultObject=statics),
                          "GrapplePoint": "GrapplePointClass"}
player = sdk_stubs.FakeCharacter()


def fresh() -> None:
    game_target.reset()
    statics.spawned.clear()
    statics.finished.clear()
    state["misc"].clear()
    state["errors"].clear()


fresh()
game_target.follow(player, (100.0, 200.0, 300.0))
check("a point is spawned where the mod would grapple", len(statics.spawned) == 1)
check("of the game's own grapple point class", statics.spawned[0][0] == "GrapplePointClass")
# A point on a wall overlaps the wall: any rule but "always spawn" would refuse to place it.
check("and always placed, even overlapping the wall", statics.spawned[0][1] == game_target.ALWAYS_SPAWN)
check("its spawning is finished", len(statics.finished) == 1)
check("with the scale rule Unreal 5 requires", statics.spawned[0][2] == game_target.MULTIPLY_WITH_ROOT)
check("and the game has a point to grapple to", game_target.ready())
held = game_target._held()
check("it sits on the aimed spot", held.at == (100.0, 200.0, 300.0))
check("its placement is written once", sum("grapple point is placed" in l for l in state["misc"]) == 1)

game_target.follow(player, (500.0, 0.0, 0.0))
check("it follows the aim without a second spawn", len(statics.spawned) == 1 and held.at == (500.0, 0.0, 0.0))

# Where the mod would punch, the point goes away, so the key still punches (Kevin, 2026-09-20).
game_target.follow(player, None)
check("with nothing to grapple it is sent far out of every range", held.at == game_target.AWAY)
check("and the game has no point to grapple to, so the key punches", not game_target.ready())
check("the mod knows its own point", game_target.mine(held))
check("and no other", not game_target.mine(Point()))
check("a ray can be told to pass through it", game_target.held_list() == [held])

fresh()
game_target.follow(player, None)
check("nothing to grapple and no point yet spawns nothing", not statics.spawned)
check("and there is nothing for a ray to pass through", game_target.held_list() == [])

fresh()
game_target.follow(player, (1.0, 1.0, 1.0))
point = game_target._held()
game_target.remove()
check("removing it destroys it", point.destroyed)
check("and forgets it", game_target._held() is None)

# Nothing here may cost a grapple: a failure switches the point off once and says so.
fresh()
state["extra_classes"] = {}
game_target.follow(player, (1.0, 1.0, 1.0))
check("a game with no grapple point class says so", any("switched off" in l for l in state["errors"]))
check("and there is then no point for the game, so the mod's own grapple runs", not game_target.ready())
state["errors"].clear()
game_target.follow(player, (2.0, 2.0, 2.0))
check("and stays quiet after, rather than repeating", not state["errors"])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
