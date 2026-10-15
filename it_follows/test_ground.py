"""Tests where It Follows puts an enemy brought back (ground): a trace straight down through the point on the hunter's
way, from TRACE_UP_CM above it to DROP_CM below, channel 2, the enemy as world context and ignored, with the game's own
structures; the enemy's centre goes its half height and CLEARANCE_CM above the ground met, HALF_HEIGHT_CM when its
half height cannot be read, read once per enemy until the enemy is forgotten; what was met is said; nothing met says
no_ground; a meeting whose component or material is named water is refused, and one on a character or a projectile
(decision 72); every trace is announced first, written to
the log for the first LOGGED_CALLS only; a failing trace says so, then and on every later point, without tracing again;
trial 8c: traced from as high above and as deep below as asked; the library held through a weak pointer and found
again once the game freed it."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import catch_up_fixture as fixture  # noqa: E402
from it_follows import ground as ground_module  # noqa: E402

fixture.keep_struct_names()
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


events: list[tuple] = []


def announce(call: str, log: bool = True, **fields: object) -> None:
    events.append(("announce", call, fields.get("on"), log))


def install_library() -> fixture.TraceLibrary:
    made = fixture.TraceLibrary(events)
    state["classes"]["KismetSystemLibrary"] = types.SimpleNamespace(ClassDefaultObject=made)
    return made


try:
    game = install_library()
    trace = ground_module.GroundTrace(announce)
    one = fixture.Enemy("cat_a")
    said, place, met = trace.ground("cat_a", one, (100.0, 200.0, 250.0))
    context, start, end, channel, complex_trace, ignored, debug, hit, ignore_self, colour, hit_colour, seconds = (
        game.asked[0])
    check("the ground under the point is found, announced first; the enemy's centre goes its half height and "
          "CLEARANCE_CM above it; what was met is said",
          said == "found" and place == (100.0, 200.0, 40.0 + 60.0 + ground_module.CLEARANCE_CM)
          and met == fixture.LANDSCAPE and events[:2] == [("announce", "LineTraceSingle", "cat_a", True), ("trace",)])
    check("traced straight down from TRACE_UP_CM above to DROP_CM below, channel 2, the enemy as context and ignored",
          context is one and (start.X, start.Y, start.Z) == (100.0, 200.0, 250.0 + ground_module.TRACE_UP_CM)
          and (end.X, end.Y, end.Z) == (100.0, 200.0, 250.0 - ground_module.DROP_CM) and channel == 2
          and complex_trace is False and ignored == [] and debug == 0 and ignore_self is True and seconds == 0.0)
    check("with the game's own structures: two vectors, a hit result, two colours",
          (start.struct_name, end.struct_name, hit.struct_name, colour.struct_name, hit_colour.struct_name)
          == ("Vector", "Vector", "HitResult", "LinearColor", "LinearColor"))
    for _ in range(ground_module.LOGGED_CALLS + 1):
        trace.ground("cat_a", one, (100.0, 200.0, 250.0))
    check("each trace announced, written to the log for the first LOGGED_CALLS only; the half height read once per "
          "enemy", [entry[3] for entry in events if entry[0] == "announce"]
          == [True] * ground_module.LOGGED_CALLS + [False] * 2 and one.reads == 1)

    game.ground_z = 250.0 - ground_module.DROP_CM - 1.0
    check("ground deeper than DROP_CM below the point is not found: no_ground",
          trace.ground("cat_b", fixture.Enemy(), (0.0, 0.0, 250.0)) == ("no_ground", None, None))
    game.ground_z = 250.0 + 1500.0
    check("trial 6n: ground 15 m above the point is met only when traced from higher, as asked",
          trace.ground("cat_b", fixture.Enemy(), (0.0, 0.0, 250.0)) == ("no_ground", None, None)
          and trace.ground("cat_b", fixture.Enemy(), (0.0, 0.0, 250.0), 2000.0)[0] == "found"
          and game.asked[-1][1].Z == 250.0 + 2000.0 and game.asked[-1][2].Z == 250.0 - ground_module.DROP_CM)
    game.ground_z = 250.0 - 1500.0
    check("trial 8c: ground 15 m below the point is met only when traced deeper, as asked",
          trace.ground("cat_b", fixture.Enemy(), (0.0, 0.0, 250.0))[0] == "no_ground"
          and trace.ground("cat_b", fixture.Enemy(), (0.0, 0.0, 250.0), 300.0, 2000.0)[0] == "found"
          and game.asked[-1][1].Z == 250.0 + 300.0 and game.asked[-1][2].Z == 250.0 - 2000.0)
    game.ground_z = math.nan
    check("a ground met at a height that is not a number is not found either",
          trace.ground("cat_b", fixture.Enemy(), (0.0, 0.0, 250.0)) == ("no_ground", None, None))
    game.ground_z = 100.0
    game.component = fixture.Named("/Game/World.WaterBodyLake_3.WaterBodyLakeComponent")
    check("a meeting whose component is named water is refused, said",
          trace.ground("cat_b", fixture.Enemy(), (0.0, 0.0, 250.0))
          == ("water", None, "/Game/World.WaterBodyLake_3.WaterBodyLakeComponent"))
    game.component, game.material = None, fixture.Named("/Game/Physics/PM_Water_Shallow.PM_Water_Shallow")
    check("and so is one whose material is", trace.ground("cat_b", fixture.Enemy(), (0.0, 0.0, 250.0))
          == ("water", None, "/Game/Physics/PM_Water_Shallow.PM_Water_Shallow"))
    game.material = types.SimpleNamespace()
    expected = ("found", (0.0, 0.0, 100.0 + ground_module.HALF_HEIGHT_CM + ground_module.CLEARANCE_CM), None)
    check("what cannot be named is no water; an enemy whose half height cannot be read, or is not a size, goes "
          "HALF_HEIGHT_CM above",
          trace.ground("cat_c", fixture.Enemy(half=RuntimeError("no")), (0.0, 0.0, 250.0)) == expected
          and trace.ground("cat_d", fixture.Enemy(half=0.0), (0.0, 0.0, 250.0)) == expected
          and trace.ground("cat_e", object(), (0.0, 0.0, 250.0)) == expected)

    level = "/Game/Maps/WorldLevels/World_P.World_P:PersistentLevel."
    bodies = [f"{level}Char_BatRanged_2147457227.CollisionBubble", f"{level}Char_CatYoung_2147443725.CharacterMesh",
              f"{level}Proj_PhalanxLootBubbleShield.Shield_Collision"]
    world = [f"{level}Puddle_Fire_2147194024.Collision",
             "/Game/Maps/WorldLevels/World_P/_Generated_/3QVP9J7M8H7UUHVEPFVHFRKWP.World_P:PersistentLevel."
             "StaticMeshActor_UAID_025041000001F33502_1810686322.StaticMeshComponent0",
             "/Game/Maps/WorldLevels/World_P/_Generated_/0MGLPI5F2W3AVCL8QVOVH2PDA.World_P:PersistentLevel."
             "LandscapeStreamingProxy_5FYC46K4SY1XAD9JY327YJY2C_2_5_0.LandscapeHeightfieldCollisionComponent_244"]
    said_on = []
    for path in bodies + world:
        game.component = fixture.Named(path)
        said_on.append(trace.ground("cat_b", fixture.Enemy(), (0.0, 0.0, 250.0))[::2])
    check("decision 72: a meeting on a character or a projectile, as met in trials 6m to 8e, is refused, said; a "
          "puddle, a mesh of the world, the land are ground",
          said_on == [("not_world", path) for path in bodies] + [("found", path) for path in world])
    check("the actor a path names: after the persistent level, even under a component's own part, else the segment "
          "before the component's",
          [ground_module.owner(path) for path in (bodies[0], world[1], f"{bodies[1]}.Body_3", fixture.LANDSCAPE,
                                                  "Lone")]
          == ["Char_BatRanged_2147457227", "StaticMeshActor_UAID_025041000001F33502_1810686322",
              "Char_CatYoung_2147443725", "Landscape_1", ""]
          and ground_module.NOT_WORLD_OWNERS == ("Char_", "Proj_"))

    game.component, game.material = fixture.Named(fixture.LANDSCAPE), None
    tall = fixture.Enemy("cat_f", half=50.0)
    trace.ground("cat_f", tall, (0.0, 0.0, 250.0))
    trace.ground("cat_f", tall, (0.0, 0.0, 250.0))
    kept = set(trace.heights)
    trace.forget("cat_f")
    trace.forget("nobody")
    gone = set(trace.heights)
    tall.half = 80.0
    check("an enemy forgotten has its half height read again the next time; the others are kept",
          tall.reads == 1 and "cat_f" in kept and gone == kept - {"cat_f"}
          and trace.ground("cat_f", tall, (0.0, 0.0, 250.0))[1] == (0.0, 0.0, 100.0 + 80.0
                                                                       + ground_module.CLEARANCE_CM)
          and tall.reads == 2)
    before = len(trace.heights)
    for index in range(10_000):
        trace.ground(f"enemy_{index}", tall, (0.0, 0.0, 250.0))
        trace.forget(f"enemy_{index}")
    check("10 000 enemies traced and let go: the table holds no more than before",
          len(trace.heights) == before and trace.broken is None)

    check("the library's default object is held through a weak pointer",
          isinstance(trace.library, sdk_stubs.FakeWeak) and trace.library() is game)
    game.freed = True
    traced = len(game.asked)
    fresh = install_library()
    check("once the game freed it, it is found again",
          trace.ground("cat_g", fixture.Enemy(), (0.0, 0.0, 250.0))[0] == "found" and len(fresh.asked) == 1
          and len(game.asked) == traced)

    events.clear()
    fresh.raises = RuntimeError("bad")
    first = trace.ground("cat_h", fixture.Enemy(), (0.0, 0.0, 250.0))
    traced = len(fresh.asked)
    check("a failing trace says so, then on every later point, without tracing or announcing again",
          first == ("call_failed:RuntimeError", None, None)
          and trace.ground("cat_i", fixture.Enemy(), (0.0, 0.0, 250.0)) == ("call_failed:RuntimeError", None, None)
          and len(fresh.asked) == traced and [entry[0] for entry in events] == ["announce", "trace"])
    del state["classes"]["KismetSystemLibrary"]
    check("so does a library the game does not have",
          ground_module.GroundTrace(lambda call, **fields: None).ground("cat_j", fixture.Enemy(), (0.0, 0.0, 0.0))
          == ("call_failed:KeyError", None, None))
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
