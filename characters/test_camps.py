"""Tests It Follows' own camps: the kit looked up at each ask and the game's enemy list read once, a missing piece said
with the call that gave nothing or raised; a camp made at a point, turned to a yaw, through a deferred spawn, kept out
of the pool when made apart; the survey forgets the camps the game took, counts those handed less than PENDING_S ago as
pending, those whose enemy HaveAllDied(InternalAndExternal) says died as free, and those handed STUCK_S ago or more with
none of their enemies alive, counted as stuck; the others busy, a read that raises counting busy; the room is the free
camps and those still to be made under most; a free camp moved where asked, made movable first, one that does not move
or lands too far left aside, else a new one made, none past most and none kept that the game refused; an enemy handed
with its requests critical and never to come back on their own (trial 218), the spawner enabled, the definition pushed
typed with the game's definition type and the camp started again, in that order, the steps after a refused one never
made; details the game will not take noted, the enemy asked all the same; refused up to the push the camp is free
again, after it busy; the status counts the camps holding their enemy, those gone and the reads that fail. Every call
but the status's is written by report.py before it is made."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
sys.modules["unrealsdk"].make_struct = lambda name, **fields: types.SimpleNamespace(struct_name=name, **fields)

from characters import camp_kit, camps, report  # noqa: E402
import wave_fixture as fake  # noqa: E402
from wave_fixture import events  # noqa: E402

clock = [100.0]
camps.time = types.SimpleNamespace(monotonic=lambda: clock[0])
camps.FGbxDefPtr = fake.DefPtr
fake.record_log()
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def calls() -> list[str]:
    """The calls report.py wrote before making them, in order."""
    return [line["call"] for line in fake.lines() if line["event"] == "call"]


def named(call: str) -> list[tuple]:
    return [entry for entry in events if entry[0] == call]


class Locked:
    """Spawn details the game will not let be written."""

    bCritical = bOverrideCritical = bOverrideRespawnStyle = False
    RespawnStyle = sdk_stubs.RespawnStyle.Timed

    def __setattr__(self, name: str, value: object) -> None:
        raise RuntimeError("read only")


def refusals() -> list[dict]:
    return [line for line in fake.lines() if line["event"] == "spawn_details_refused"]


try:
    statics = fake.Statics()
    def_type, spawner_class, library = fake.give_kit(state, statics, ["Char_CatYoung", "Char_BatBasic"])
    hunter = object()
    own = camps.Camps(report.announce, 3)

    kit = own.kit()
    check("the kit is the game's definition type, the spawner class and the statics, its lookups, the SDK's own "
          "searches, not written to the log; the enemy list, a call to the game, written before it is made",
          kit == camp_kit.Kit(def_type, spawner_class, statics) and calls() == ["GetEnemiesActorDefStrings"]
          and fake.announced_first(events))
    check("the kinds of the game's enemy list are known", own.knows("Char_CatYoung") and not own.knows("Char_Odd"))
    events.clear()
    own.kit()
    check("the enemy list is read once", named("GetEnemiesActorDefStrings") == [] and calls() == [])
    del state["classes"]["OakSpawner"]
    check("a piece the game does not give says which call raised", own.kit() == "find_class(OakSpawner):KeyError")
    state["classes"]["OakSpawner"] = None
    check("or which gave nothing", own.kit() == "find_class(OakSpawner):none")
    state["classes"]["OakSpawner"] = spawner_class
    library.names = None
    fresh = camps.Camps(report.announce, 3)
    check("an enemy list that cannot be read is said too, and nothing is known",
          fresh.kit() == "GetEnemiesActorDefStrings:none" and not fresh.knows("Char_CatYoung"))
    library.names = RuntimeError("no list")
    check("or that raises, said with its error", fresh.kit() == "GetEnemiesActorDefStrings:RuntimeError")
    library.names = ["Char_CatYoung", "Char_BatBasic"]
    check("and it is read again at the next ask", fresh.kit() == kit and fresh.knows("Char_BatBasic"))
    camp_kit.MAX_DEFINITIONS = 1
    fresh = camps.Camps(report.announce, 3)
    fresh.kit()
    camp_kit.MAX_DEFINITIONS = 4096
    check("never more than MAX_DEFINITIONS kinds read",
          fresh.knows("Char_CatYoung") and not fresh.knows("Char_BatBasic"))

    events.clear()
    host = own.made(kit, (100.0, 200.0, 300.0), 90.0, hunter)
    where = host.where
    check("a camp made apart: a deferred spawn at the point, always spawned, scaled with its root, the hunter as "
          "context, each call written to the log before it is made, the second naming the camp; kept out of the pool",
          named("BeginDeferredActorSpawnFromClass") == [("BeginDeferredActorSpawnFromClass", hunter, spawner_class, 1,
                                                         None, 1)]
          and named("FinishSpawningActor") == [("FinishSpawningActor", host.Name, 1)]
          and where.struct_name == "Transform"
          and (where.Translation.X, where.Translation.Y, where.Translation.Z) == (100.0, 200.0, 300.0)
          and (where.Scale3D.X, where.Scale3D.Y, where.Scale3D.Z) == (1.0, 1.0, 1.0)
          and calls() == ["BeginDeferredActorSpawnFromClass", "FinishSpawningActor"]
          and fake.lines()[-1]["on"] == host.Name and fake.announced_first(events) and own.pool == [])
    check("turned to the yaw asked", math.isclose(where.Rotation.Z, math.sin(math.radians(45.0)))
          and math.isclose(where.Rotation.W, math.cos(math.radians(45.0))) and where.Rotation.X == 0.0
          and where.Rotation.Y == 0.0)
    statics.refuse_begin = True
    check("a spawn the game refuses makes no camp", own.made(kit, (0.0, 0.0, 0.0), 0.0, hunter) is None)
    statics.refuse_begin, statics.refuse_finish = False, True
    check("nor does a spawn it cannot finish", own.made(kit, (0.0, 0.0, 0.0), 0.0, hunter) is None)
    statics.refuse_finish = False

    survey = own.survey()
    check("no camp yet: nothing free, the room is most", survey == camps.Survey([], 0, 0) and own.room(survey) == 3)
    placed = own.place(kit, [], (500.0, 0.0, 0.0), 0.0, hunter)
    check("no free camp: a new one made at the point, kept in the pool", placed is not None and own.pool == [placed[0]]
          and placed[1].at == (500.0, 0.0, 0.0) and placed[0].pointer() is placed[1])
    first = placed
    statics.refuse_begin = True
    refused = own.place(kit, [], (550.0, 0.0, 0.0), 0.0, hunter)
    statics.refuse_begin, statics.refuse_finish = False, True
    unfinished = own.place(kit, [], (560.0, 0.0, 0.0), 0.0, hunter)
    statics.refuse_finish = False
    check("a camp the game refuses to make, or to finish, is not kept", refused is None and unfinished is None
          and own.pool == [first[0]])

    events.clear()
    said = own.hand(kit, *first, "Char_CatYoung")
    component = first[1].SpawnerComponent
    pushes = named("PushActorDef")
    check("an enemy handed: its requests critical, the spawner enabled, the definition pushed typed with the game's "
          "definition type, destroying what it held, then started again, in that order",
          said is None and component.SpawnDetails.bCritical is True and component.SpawnDetails.bOverrideCritical is True
          and [entry[0] for entry in events if entry[0] != "log"] == ["SetSpawnerEnabled", "PushActorDef",
                                                                      "ResetSpawner"]
          and named("SetSpawnerEnabled") == [("SetSpawnerEnabled", first[1].Name, True)]
          and named("ResetSpawner") == [("ResetSpawner", first[1].Name, True)]
          and pushes[0][2] == camps.REASON == "RUN" and pushes[0][3].name == "Char_CatYoung"
          and pushes[0][3].kind is def_type and pushes[0][4] is True
          and first[0].kind == "Char_CatYoung" and first[0].handed_at == 100.0)
    check("trial 218: its requests never to come back on their own, the game's Timed bearing it again some 20 minutes "
          "after losing it", component.SpawnDetails.bOverrideRespawnStyle is True
          and component.SpawnDetails.RespawnStyle is sdk_stubs.RespawnStyle.Never)
    check("its requests made critical and never to come back first; each step written to the log before it is made, "
          "with the camp and the definition; nothing refused",
          calls() == ["SpawnDetails critical", "SpawnDetails never respawn", "SetSpawnerEnabled", "PushActorDef",
                      "ResetSpawner"]
          and fake.lines()[0] == {"event": "call", "run": 0, "call": "SpawnDetails critical", "on": first[1].Name}
          and fake.lines()[1] == {"event": "call", "run": 0, "call": "SpawnDetails never respawn",
                                  "on": first[1].Name}
          and fake.lines()[3] == {"event": "call", "run": 0, "call": "PushActorDef", "on": first[1].Name,
                                  "definition": "Char_CatYoung"}
          and fake.announced_first(events) and refusals() == [])

    second = own.place(kit, [], (600.0, 0.0, 0.0), 0.0, hunter)
    own.hand(kit, *second, "Char_BatBasic")
    clock[0] = 100.0 + camps.PENDING_S - 0.1
    events.clear()
    survey = own.survey()
    check("a camp handed less than PENDING_S ago is pending, not read; the survey written to the log once",
          survey == camps.Survey([], 0, 2) and named("HaveAllDied") == []
          and fake.lines() == [{"event": "call", "run": 0, "call": "HaveAllDied", "camps": 2}])
    clock[0] = 100.0 + camps.PENDING_S
    second[1].SpawnerComponent.died = False
    events.clear()
    survey = own.survey()
    check("then a camp whose enemy HaveAllDied(InternalAndExternal) says died is free, the others busy",
          survey.free == [first] and survey.busy == 1 and survey.pending == 0
          and named("HaveAllDied") == [("HaveAllDied", first[1].Name, 2), ("HaveAllDied", second[1].Name, 2)]
          and fake.announced_first(events))
    second[1].SpawnerComponent.died = RuntimeError("no read")
    check("a read that raises counts busy", own.survey().busy == 1)
    second[1].SpawnerComponent.died = 1
    check("and so does any answer but True", own.survey().busy == 1)
    check("the room: the free camps and those still to be made under most", own.room(survey) == 1 + 1)
    second[1].SpawnerComponent.died = False
    clock[0] = 100.0 + camps.STUCK_S - 0.1
    events.clear()
    check("trial 14: within STUCK_S of its hand, a camp whose enemy's death is not said stays busy, its enemies not "
          "counted", own.survey().busy == 1 and named("GetNumAliveActors") == [])
    clock[0] = 100.0 + camps.STUCK_S
    second[1].SpawnerComponent.alive = 1
    check("past it, one whose enemy is alive stays busy", own.survey().busy == 1)
    second[1].SpawnerComponent.alive = 0
    events.clear()
    taken = own.survey()
    check("and one with none of its enemies alive is taken back: free, counted as stuck, its enemies counted "
          "InternalAndExternal",
          taken.free == [first, second] and taken.busy == 0 and taken.stuck == 1
          and named("GetNumAliveActors") == [("GetNumAliveActors", second[1].Name, 2)])
    second[1].SpawnerComponent.alive = RuntimeError("no count")
    check("a count that raises keeps it busy", own.survey().busy == 1 and own.survey().stuck == 0)
    second[1].SpawnerComponent.alive, second[1].SpawnerComponent.died = 0, 1
    clock[0] = 100.0 + camps.PENDING_S

    events.clear()
    moved = own.place(kit, list(survey.free), (900.0, 50.0, 10.0), 0.0, hunter)
    check("a free camp is taken before any is made: made movable, written to the log before it is made, teleported "
          "without sweep, the move not written, as those of the camps that follow the hunter, read back",
          moved == first and first[1].at == (900.0, 50.0, 10.0) and named("SetMobility") == [("SetMobility",
                                                                                            first[1].Name, 2)]
          and named("K2_SetActorLocation") == [("K2_SetActorLocation", first[1].Name, False, "HitResult", True)]
          and len(own.pool) == 2 and calls() == ["SetMobility"]
          and fake.announced_first([entry for entry in events if entry[0] != "K2_SetActorLocation"]))
    events.clear()
    own.place(kit, [first], (950.0, 50.0, 10.0), 0.0, hunter)
    check("a camp already movable is not made so again", named("SetMobility") == [])
    first[1].sticks = True
    third = own.place(kit, [first], (1500.0, 0.0, 0.0), 0.0, hunter)
    first[1].sticks = False
    check("a free camp that does not move is left aside, and a new one made",
          third is not None and third[1] is not first[1] and len(own.pool) == 3 and third[1].at == (1500.0, 0.0, 0.0))
    first[1].off_cm = 110.0
    landed_far = own.place(kit, [first], (980.0, 50.0, 10.0), 0.0, hunter)
    first[1].off_cm = 90.0
    landed_near = own.place(kit, [first], (960.0, 50.0, 10.0), 0.0, hunter)
    first[1].off_cm = 0.0
    check("one that lands farther than MOVED_M from the place asked has not moved, and none is made past most; within "
          "MOVED_M it has", landed_far is None and landed_near == first and len(own.pool) == 3)
    stuck = fake.Spawner()
    stuck.RootComponent = fake.Root(stuck.Name, stays=True)
    check("nor one whose root stays fixed, and none past most",
          len(own.pool) == 3 and own.place(kit, [(camps.Camp(stuck), stuck)], (0.0, 0.0, 0.0), 0.0, hunter) is None
          and len(own.pool) == 3)
    rootless = fake.Spawner()
    rootless.RootComponent = None
    check("nor one without a root",
          own.place(kit, [(camps.Camp(rootless), rootless)], (0.0, 0.0, 0.0), 0.0, hunter) is None)

    steps = ("SetSpawnerEnabled", "PushActorDef", "ResetSpawner")
    for index, step in enumerate(steps):
        third[1].SpawnerComponent.fails = {step}
        events.clear()
        said = own.hand(kit, *third, "Char_CatYoung")
        after_push = step == "ResetSpawner"
        check(f"{step} refused: said with its error, the steps after it never made, the camp "
              f"{'busy' if after_push else 'free again'}",
              said == f"{step}:RuntimeError" and (third[0].handed_at is not None) is after_push
              and [entry[0] for entry in events if entry[0] != "log"] == list(steps[:index + 1]))
    third[1].SpawnerComponent.fails = set()
    third[1].SpawnerComponent.SpawnDetails = Locked()
    events.clear()
    check("requests that cannot be made critical nor kept from coming back: the enemy asked all the same, each "
          "refusal noted with its error and the camp",
          own.hand(kit, *third, "Char_CatYoung") is None and named("ResetSpawner") == [("ResetSpawner", third[1].Name,
                                                                                         True)]
          and refusals() == [
              {"event": "spawn_details_refused", "run": 0, "detail": "SpawnDetails critical",
               "why": "SpawnDetails critical:RuntimeError", "on": third[1].Name},
              {"event": "spawn_details_refused", "run": 0, "detail": "SpawnDetails never respawn",
               "why": "SpawnDetails never respawn:RuntimeError", "on": third[1].Name}])
    renamed = sdk_stubs.spawn_details()
    renamed.RespawnStyle = sdk_stubs.enum.IntEnum("ERespawnStyle", ["Timed", "Level"])(1)
    third[1].SpawnerComponent.SpawnDetails = renamed
    events.clear()
    check("a game whose choices no longer hold Never: refused and noted, nothing of it written, its requests "
          "critical, the enemy asked all the same", own.hand(kit, *third, "Char_CatYoung") is None
          and renamed.bCritical is True and renamed.bOverrideRespawnStyle is False
          and [line["why"] for line in refusals()] == ["SpawnDetails never respawn:KeyError"])

    first[1].SpawnerComponent.alive = 1
    second[1].SpawnerComponent.alive = RuntimeError("no count")
    fake.free(third[1])
    events.clear()
    check("the status counts the camps holding their enemy, those gone and the reads that fail; its calls, made at "
          "each status, are not written to the log",
          own.status() == {"camps": 3, "alive": 1, "pending": 0, "free": 0, "stuck": 0, "gone": 1, "failed": 1}
          and fake.lines() == [] and ("GetNumAliveActors", second[1].Name, 2) in events)
    first[1].SpawnerComponent.alive = 0
    second[1].SpawnerComponent.alive, second[1].SpawnerComponent.died = 0, True
    check("trial 8e: a camp handed long ago without an enemy alive is free once HaveAllDied says its enemy died",
          own.status() == {"camps": 3, "alive": 0, "pending": 0, "free": 2, "stuck": 0, "gone": 1, "failed": 0})
    stuck_counts = []
    for answer in (False, None, 1):
        second[1].SpawnerComponent.died = answer
        stuck_counts.append(own.status())
    check("and stuck when it says anything else, as the survey reads it",
          stuck_counts == [{"camps": 3, "alive": 0, "pending": 0, "free": 1, "stuck": 1, "gone": 1, "failed": 0}] * 3)
    first[0].handed_at = clock[0] - 1.0
    second[1].SpawnerComponent.died = RuntimeError("no read")
    events.clear()
    check("one handed less than PENDING_S ago is pending, not read; a HaveAllDied that raises counts as failed",
          own.status() == {"camps": 3, "alive": 0, "pending": 1, "free": 0, "stuck": 0, "gone": 1, "failed": 1}
          and named("HaveAllDied") == [("HaveAllDied", second[1].Name, 2)])
    own.survey()
    check("the survey forgets the camps the game took", len(own.pool) == 2 and third[0] not in own.pool)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
