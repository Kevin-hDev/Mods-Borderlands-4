"""Tests the camps It Follows puts to work in a run: nothing is made without the camps' kit or the hunter's look; the
lent zone's camp is made apart, behind the hunter opposite to his look, facing him, the call written to the log first;
its zone, found among the game's zones by its owner, is lent as a Seen that walks nowhere; without it, or when the camp
is refused, no copy is asked; each enemy within NEAR_M whose kind the game knows gets a copy, on a ring of RING_M around
that point, each ring moved along the hunter's back by the level's spread (decision 66), each laid on the ground under
its point, from UP_CM above to DOWN_CM below, the hunter as context; points over water, with no ground or on a character
(decision 72) are left out, counted by why, and as many are asked as the camps' room and the ground allow, free camps
first; each ask turns the ring; the game's limit is lifted at the first ask; the camps handed an enemy, and the lent
zone's, are It Follows'; the asking stops at the first refusal or error, said; the status is the camps', with the
limit's state; the search for the zone keeps to its limits; the killed are asked again the same way. On It Follows' own
camps and limit, with report.py's lines: each near enemy handed a camp of its own, every call written before it is made,
and the next run, with the same camps, takes the free ones again."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
sys.modules["unrealsdk"].make_struct = lambda name, **fields: types.SimpleNamespace(struct_name=name, **fields)

from it_follows import budget, camps, copies, levels, report, spread  # noqa: E402
from it_follows.seen import Seen  # noqa: E402
import wave_fixture as fake  # noqa: E402
from wave_fixture import events  # noqa: E402

clock = [0.0]
copies.time = camps.time = types.SimpleNamespace(monotonic=lambda: clock[0])
camps.FGbxDefPtr = fake.DefPtr
fake.record_log()
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


behaviour: dict = {}


class FakeCamps:
    """camps.Camps as copies.py sees it: its kit, its free camps and room, a camp made at each place asked, refusals
    when told."""

    def __init__(self) -> None:
        self.made_count = 0
        # The session's names of the camps put to work, as camps.Camps keeps them.
        self.mine: set[str] = set()

    def kit(self) -> object:
        events.append(("kit",))
        return behaviour["kit"]

    def knows(self, kind: str) -> bool:
        return kind in ("Char_CatYoung", "Char_BatBasic")

    def made(self, kit: object, point: tuple, yaw: float, character: object) -> object:
        events.append(("made", point, yaw))
        return behaviour["host"]

    def survey(self) -> object:
        events.append(("survey",))
        return types.SimpleNamespace(free=list(behaviour["free"]), busy=behaviour["busy"],
                                     pending=behaviour["pending"], stuck=behaviour["stuck"])

    def room(self, survey: object) -> int:
        return behaviour["room"]

    def place(self, kit: object, free: list, point: tuple, yaw: float, character: object) -> object:
        events.append(("place", point, yaw, len(free)))
        if behaviour["place"] == "raise":
            raise RuntimeError("bad")
        if behaviour["place"] is None:
            return None
        if free:
            return free.pop(0)
        self.made_count += 1
        return object(), fake.Spawner(name=f"OakSpawner_Copy{self.made_count}")

    def hand(self, kit: object, camp: object, spawner: object, kind: str) -> str | None:
        events.append(("hand", spawner.Name, kind))
        return behaviour["hand"].pop(0) if behaviour["hand"] else None

    def status(self) -> dict:
        return {"camps": 2, "alive": 1, "gone": 0, "failed": 0}


class FakeBudget:
    def __init__(self) -> None:
        self.said = "untouched"

    def lift(self) -> str:
        events.append(("lift",))
        self.said = "lifted"
        return self.said

    def restore(self) -> str:
        events.append(("restore",))
        return "given_back"


class SlowZone(fake.Zone):
    """A zone whose owner takes longer than READ_S to read."""

    @property
    def Outer(self) -> object:
        clock[0] += copies.READ_S + 0.1
        return None

    @Outer.setter
    def Outer(self, value: object) -> None:
        pass


def seen(name: str, x_m: float | None, definition: str = "Char_CatYoung") -> Seen:
    return Seen(object(), name, definition, None, "", None, 0.0, None if x_m is None else (x_m * 100.0, 0.0, 0.0))


look = types.SimpleNamespace(GetControlRotation=lambda: types.SimpleNamespace(Yaw=0.0))
here = (0.0, 0.0, 0.0)
hunter = object()
crowd = [seen("cat", 20.0), seen("bat", 60.0, "Char_BatBasic"), seen("odd", 80.0, "Char_Odd"),
         seen("far", 200.0), seen("lost", None), seen("blank", 30.0, "")]
ours = fake.Spawner(name="OakSpawner_2147000001")
own_zone = fake.Zone(ours)
middle = (-copies.BEHIND_M * 100.0, 0.0, 0.0)
# No spread: each ring around middle itself.
FLAT = ((100, 0.0),)


def reset(water: tuple = (), no_ground: tuple = (), not_world: tuple = (), **fields: object) -> tuple:
    events.clear()
    behaviour.update(kit=object(), host=ours, free=[], room=50, place="make", hand=[], busy=0, pending=0, stuck=0)
    behaviour.update(fields)
    state["all"]["GbxTerritoryComponent"] = [fake.Zone(fake.Spawner(name="OakSpawner_UAID_Game")), own_zone]
    ground = fake.Ground(water, no_ground, not_world)
    return copies.Copies(report.announce, FakeCamps(), ground, FakeBudget(), spread.Spread(FLAT)), ground


def took(name: str) -> list[tuple]:
    return [entry for entry in events if entry[0] == name]


def close(a: tuple, b: tuple) -> bool:
    return all(abs(x - y) < 1e-6 for x, y in zip(a, b))


def line(**fields: object) -> tuple:
    return "log", {"event": "call", "run": 0, "call": "run_camps", **fields}


try:
    run, ground = reset(kit="find_class(OakSpawner):KeyError")
    check("without the camps' kit nothing is made nor written",
          run.ask(crowd, hunter, look, here, 120) == (None, {"made": "no_kit:find_class(OakSpawner):KeyError"})
          and events == [("kit",)])
    run, ground = reset()
    check("without the hunter's look nothing is made",
          run.ask(crowd, hunter, object(), here, 120) == (None, {"made": "no_look:AttributeError"})
          and events == [("kit",)])
    run, ground = reset(host=None)
    check("the camp refused: no copy is asked",
          run.ask(crowd, hunter, look, here, 120) == (None, {"made": "camp_refused"}) and not took("place")
          and not took("lift"))
    run, ground = reset()
    state["all"]["GbxTerritoryComponent"] = [fake.Zone(fake.Spawner(name="OakSpawner_UAID_Game"))]
    check("a camp whose zone is not found: no copy is asked, the camp said, and it is It Follows'",
          run.ask(crowd, hunter, look, here, 120) == (None, {"made": "no_camp_zone", "camp": "OakSpawner_2147000001"})
          and not took("place") and run.ours("OakSpawner_2147000001"))
    run, ground = reset()
    own_zone.settings = types.SimpleNamespace()
    check("a camp whose zone's radius cannot be read: no copy is asked",
          run.ask(crowd, hunter, look, here, 120) == (None, {"made": "camp_zone_radius_unreadable",
                                                        "camp": "OakSpawner_2147000001"})
          and not took("place"))
    own_zone.settings = types.SimpleNamespace(CombatTerritory=types.SimpleNamespace(Radius=1500.0))

    run, ground = reset()
    host, said = run.ask(crowd, hunter, look, here, 120)
    made = took("made")[0]
    check("the lent zone's camp is made apart BEHIND_M behind the hunter, opposite to his look, facing him, after the "
          "call is written to the log",
          close(made[1], middle) and abs(made[2]) < 1e-6
          and events[:3] == [("kit",), line(near=3, at=[-40.0, 0.0, 0.0]), made])
    check("its zone is lent as a Seen: the zone found by its owner, a camp's that holds no enemy and walks nowhere",
          host == Seen(actor=None, name="own_camp", definition="", zone=own_zone, zone_path=own_zone._path_name(),
                       centre=(-4000.0, 0.0, 0.0), radius_m=15.0, at=None, walks=False))
    check("each enemy within NEAR_M whose kind the game knows gets a copy, handed its kind, the limit lifted first",
          [entry[1:] for entry in took("hand")] == [("OakSpawner_Copy1", "Char_CatYoung"),
                                                    ("OakSpawner_Copy2", "Char_BatBasic")]
          and events.index(("lift",)) < events.index(took("place")[0]))
    points = [asked[2] for asked in ground.asked]
    check("on a ring of RING_M around the point behind the hunter, each point laid on the ground under it, from UP_CM "
          "above to DOWN_CM below, the hunter as context",
          len(points) == 2 and all(abs(math.dist(point, middle) - copies.RING_M * 100.0) < 1e-6 for point in points)
          and all(asked[:2] == ("camp", hunter) and asked[3:] == (copies.UP_CM, copies.DOWN_CM)
                  for asked in ground.asked)
          and [close(entry[1], (point[0], point[1], point[2] - 500.0)) for entry, point in zip(took("place"), points)]
          == [True, True])
    check("each copy's camp faces the hunter",
          all(abs(entry[2] - math.degrees(math.atan2(-entry[1][1], -entry[1][0]))) < 1e-6 for entry in took("place")))
    check("what was made is said: the near, the unknown kinds, the free camps, the copies alive, the room, the spots, "
          "the asked, the handed",
          said == {"made": "done", "camp": "OakSpawner_2147000001", "zone": own_zone._path_name(), "near": 3,
                   "unknown": 1, "free": 0, "taken_back": 0, "alive": 0, "room": 50, "spots": 2, "asked": 2,
                   "handed": 2, "at": [-40.0, 0.0, 0.0], "took_ms": 0.0})
    check("the zone's camp and the copies' are It Follows', the game's are not",
          run.ours("OakSpawner_2147000001") and run.ours("OakSpawner_Copy1") and run.ours("OakSpawner_Copy2")
          and not run.ours("OakSpawner_UAID_Game") and not run.ours(None))
    check("the kinds known are the camps'", run.knows("Char_CatYoung") and not run.knows("Char_Odd"))
    check("the status is the camps', with the limit's state",
          run.status() == {"camps": 2, "alive": 1, "gone": 0, "failed": 0, "budget": "lifted"})
    check("the stop gives the limit back", run.put_back() == "given_back" and events[-1] == ("restore",))
    run, ground = reset()
    run.ask(crowd, hunter, types.SimpleNamespace(GetControlRotation=lambda: types.SimpleNamespace(Yaw=90.0)), here, 120)
    made = took("made")[0]
    check("whatever the hunter's look, the lent zone's camp is made behind him, facing him",
          close(made[1], (0.0, -copies.BEHIND_M * 100.0, 0.0)) and abs(made[2] - 90.0) < 1e-6)
    run, ground = reset()
    said = run.ask([seen("edge", 150.0), seen("past", 150.1)], hunter, look, here, 120)[1]
    check("an enemy 150 m away is near, one 10 cm farther is not", said["near"] == 1 and said["asked"] == 1)

    run, ground = reset(room=1)
    check("only as many copies as the camps have room for",
          run.ask(crowd, hunter, look, here, 120)[1]["asked"] == 1 and len(ground.asked) == 1)
    run, ground = reset()
    check("decision 96: no more copies than the horde has room for",
          run.ask(crowd, hunter, look, here, 1)[1]["asked"] == 1 and len(ground.asked) == 1
          and run.ask(crowd, hunter, look, here, 0)[1]["asked"] == 0)
    run, ground = reset(room=0)
    host, said = run.ask(crowd, hunter, look, here, 120)
    no_room = host is not None and said["asked"] == 0 and ground.asked == [] and not took("lift")
    run, ground = reset()
    host, said = run.ask([seen("far", 200.0)], hunter, look, here, 120)
    check("no room, or nobody near: no copy is asked, nothing traced, the limit untouched, the zone still lent",
          no_room and host is not None and said["near"] == 0 and said["handed"] == 0 and ground.asked == []
          and not took("lift"))

    run, ground = reset(water=(0,), no_ground=(1,))
    killed = [("cat2", "Char_CatYoung"), ("bat2", "Char_BatBasic"), ("cat3", "Char_CatYoung")]
    run.ask([], hunter, look, here, 120)
    events.clear()
    said = run.again(killed, hunter, look, here)
    check("trial 8c: points over water or with no ground are left out; only as many are asked as the ground allows, "
          "the first killed first",
          said == {"again": "done", "free": 0, "taken_back": 0, "alive": 0, "room": 50, "spots": 1, "asked": 1,
                   "handed": 1, "left_out": {"water": 1, "no_ground": 1}, "at": [-40.0, 0.0, 0.0],
                   "took_ms": 0.0}
          and [entry[2] for entry in took("hand")] == ["Char_CatYoung"])
    check("trial 8a: the killed are asked again behind the hunter, the call written to the log first",
          events[:2] == [("kit",), line(again=3, at=[-40.0, 0.0, 0.0])])
    run, ground = reset(not_world=(1,))
    said = run.again(killed, hunter, look, here)
    check("decision 72: a point whose trace met a character is left out, said",
          said["spots"] == 2 and said["asked"] == 2 and said["left_out"] == {"not_world": 1})
    run, ground = reset(water=(0, 1, 2))
    said = run.again(killed, hunter, look, here)
    check("no ground at all on the ring: nobody asked, the limit untouched",
          said["spots"] == 0 and said["asked"] == 0 and said["handed"] == 0 and not took("lift"))

    run, ground = reset(busy=3, pending=1, stuck=2)
    said = run.again(killed, hunter, look, here)
    check("the copies alive are said, their camps busy or handed one lately, and hold nobody back (decision 65); the "
          "stuck camps taken back are said (trial 14)",
          said["alive"] == 4 and said["room"] == 50 and said["handed"] == 3 and said["taken_back"] == 2)

    run, ground = reset()
    run.again(killed[:2], hunter, look, here)
    first_ring = [asked[2] for asked in ground.asked]
    ground.asked.clear()
    run.again(killed[:2], hunter, look, here)
    turned = ground.asked[0][2]
    check("each ask turns the ring by the golden angle, so that asks at one place do not reuse its spots",
          close(first_ring[0], (middle[0] + copies.RING_M * 100.0, 0.0, 0.0))
          and math.isclose(math.atan2(turned[1] - middle[1], turned[0] - middle[0]), copies.TURN_RAD))

    run, ground = reset()
    run.spread = spread.Spread(levels.SPREAD)
    run.again([(f"cat{number}", "Char_CatYoung") for number in range(10)], hunter, look, here)
    rings = [asked[2] for asked in ground.asked]
    centres = [(point[0] - math.cos(2.0 * math.pi * index / 10) * copies.RING_M * 100.0,
                point[1] - math.sin(2.0 * math.pi * index / 10) * copies.RING_M * 100.0)
               for index, point in enumerate(rings)]
    check("decision 66: each one's ring moved along the hunter's back by the next offset of Kevin's spread: six at "
          "40 m, two at 50, one at 55, one at 35",
          len(centres) == 10 and all(math.isclose(y, 0.0, abs_tol=1e-6) for _x, y in centres)
          and [round(-x / 100.0, 6) for x, _y in centres] == [40.0, 50.0, 40.0, 40.0, 55.0, 40.0, 35.0, 40.0, 50.0,
                                                              40.0])

    free_camp = (object(), fake.Spawner(name="OakSpawner_Free"))
    run, ground = reset(free=[free_camp])
    said = run.again(killed[:2], hunter, look, here)
    check("the free camps are offered first",
          [entry[1] for entry in took("hand")] == ["OakSpawner_Free", "OakSpawner_Copy1"] and said["free"] == 1
          and took("place")[0][3] == 1 and run.ours("OakSpawner_Free"))
    run, ground = reset(hand=[None, "PushActorDef:RuntimeError"])
    said = run.again(killed, hunter, look, here)
    check("the asking stops at the first refusal, said, the ones before it handed",
          said["asked"] == 3 and said["handed"] == 1 and said["refusal"] == "PushActorDef:RuntimeError"
          and len(took("hand")) == 2 and not run.ours("OakSpawner_Copy2"))
    run, ground = reset(place=None)
    check("a camp that cannot be placed stops it too",
          run.again(killed, hunter, look, here)["refusal"] == "camp_refused")
    run, ground = reset(place="raise")
    check("and so does an error, said with its kind",
          run.again(killed, hunter, look, here)["refusal"] == "error:RuntimeError")
    check("without the hunter's look nobody is asked again",
          reset()[0].again(killed, hunter, object(), here) == {"again": "no_look:AttributeError", "handed": 0})
    check("without the camps' kit nobody is asked again",
          reset(kit="find_class(OakSpawner):KeyError")[0].again(killed, hunter, look, here)
          == {"again": "no_kit:find_class(OakSpawner):KeyError", "handed": 0})

    run, ground = reset()
    state["all"]["GbxTerritoryComponent"] = [SlowZone(None), fake.Zone(fake.Spawner(name="x")), own_zone]
    check("the search for the zone keeps to READ_S",
          run.ask(crowd, hunter, look, here, 120)[1]["made"] == "no_camp_zone")
    clock[0] = 0.0
    run, ground = reset()
    copies.MAX_ZONES = 1
    check("and to MAX_ZONES", run.ask(crowd, hunter, look, here, 120)[1]["made"] == "no_camp_zone")
    copies.MAX_ZONES = 5000
    check("behind: opposite to the look, at the same height",
          [round(value, 6) for value in copies.behind((0.0, 0.0, 50.0), 90.0)]
          == [0.0, -copies.BEHIND_M * 100.0, 50.0])
    check("facing: the yaw from a point towards another",
          round(copies.facing((0.0, 0.0, 0.0), (0.0, 100.0, 0.0)), 6) == 90.0)

    events.clear()
    statics = fake.Statics(zones=[])
    state["all"]["GbxTerritoryComponent"] = statics.zones
    def_type, _spawner_class, _library = fake.give_kit(state, statics, ["Char_PsychoBasic_Male"])
    settings = fake.Settings()
    fake.play(settings)
    own = camps.Camps(report.announce, 200)
    first_run = copies.Copies(report.announce, own, fake.Ground(), budget.Budget(report.announce),
                              spread.Spread(FLAT))
    psychos = [seen(f"Char_PsychoBasic_Male_{number}", 10.0 * number, "Char_PsychoBasic_Male") for number in (1, 2, 3)]
    host, said = first_run.ask(psychos, hunter, look, here, 120)
    taking = [camp.pointer() for camp in own.pool]
    steps = ("SetSpawnerEnabled", "PushActorDef", "ResetSpawner")
    handed = [entry for entry in events if entry[0] in steps]
    check("on It Follows' own camps and limit, with report.py's lines as in game: the lent zone's camp made apart; "
          "each near enemy handed a camp of its own, enabled, its kind pushed typed, started again; every call written "
          "to the log before it is made; all of them It Follows'",
          host.zone is statics.zones[0] and len(taking) == 3 and host.zone.Outer not in taking
          and said["made"] == "done" and said["asked"] == 3 and said["handed"] == 3 and "refusal" not in said
          and [entry[:2] for entry in handed] == [(call, spawner.Name) for spawner in taking for call in steps]
          and all(entry[2:] == ("RUN", entry[3], True) and entry[3].name == "Char_PsychoBasic_Male"
                  and entry[3].kind is def_type for entry in handed if entry[0] == "PushActorDef")
          and all(spawner.SpawnerComponent.SpawnDetails.bCritical for spawner in taking)
          and settings.bDisableSpawnBudget is True and fake.announced_first(events)
          and all(first_run.ours(spawner.Name) for spawner in (host.zone.Outer, *taking)))
    check("each birth owed by its camp, with its kind, until it joins the horde",
          first_run.owed == {spawner.Name: "Char_PsychoBasic_Male" for spawner in taking})
    first_run.joined(taking[0].Name)
    check("joined, owed no more", taking[0].Name not in first_run.owed and len(first_run.owed) == 2)
    first_host = host.zone.Outer.Name
    first_run.put_back()
    clock[0] = camps.PENDING_S
    events.clear()
    next_run = copies.Copies(report.announce, own, fake.Ground(), budget.Budget(report.announce),
                              spread.Spread(FLAT))
    check("before the next run puts any to work, the camps of the first are the mod's to it too",
          next_run.ours(first_host) and all(next_run.ours(spawner.Name) for spawner in taking)
          and not next_run.ours("OakSpawner_UAID_Game"))
    host, said = next_run.ask(psychos[:2], hunter, look, here, 120)
    check("the next run, with the same camps: the enemy list not read again, the camps whose enemy died moved and "
          "handed again, none made but the lent zone's, the limit lifted again, every call written first",
          said["free"] == 3 and said["handed"] == 2 and len(own.pool) == 3
          and not took("GetEnemiesActorDefStrings") and len(took("BeginDeferredActorSpawnFromClass")) == 1
          and [entry[1] for entry in took("K2_SetActorLocation")] == [spawner.Name for spawner in taking[:2]]
          and settings.bDisableSpawnBudget is True and fake.announced_first(events))
    check("a run owes nothing for an earlier run's births: never asked again as that run's kinds",
          set(next_run.owed) == {spawner.Name for spawner in taking[:2]})
    surveyed = len(took("HaveAllDied"))
    check("nothing lost while the births are pending", next_run.unseen() == [])
    clock[0] += camps.PENDING_S
    again = next_run.again([("Char_Cat_9", "Char_CatYoung")], hunter, look, here)
    lost = next_run.unseen()
    read = len(took("HaveAllDied"))
    check("births whose camp is free again before they joined the horde: their kinds given, once, the camps read, "
          "one whose camp was handed again first among them",
          again["handed"] == 1 and lost == ["Char_PsychoBasic_Male"] * 2
          and list(next_run.owed.values()) == ["Char_CatYoung"] and read > surveyed)
    clock[0] += camps.PENDING_S
    check("the birth handed meanwhile, its camp free again, given in its turn", next_run.unseen() == ["Char_CatYoung"])
    read = len(took("HaveAllDied"))
    check("nothing owed: the camps are not even read", next_run.unseen() == [] and len(took("HaveAllDied")) == read)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
