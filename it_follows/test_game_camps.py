"""Tests the game's own camps made critical during a run (decision 64): only those within RANGE_M, It Follows' own and
the class defaults left out, a camp already critical left alone and never given back; the flags written as a struct
given back whole and read back; a camp that cannot be read counted; each camp written once a run, but one the game
loaded again under a held name written again; a pass held to
READ_S and to MAX_HELD; EVERY_S between passes; at the stop each camp's own flags written back, those the game freed
counted; the call written to the log before the camps are written."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import game_camps, report  # noqa: E402
import wave_fixture as fake  # noqa: E402
from wave_fixture import events  # noqa: E402

fake.record_log()
fails: list[str] = []
ORIGINAL = {name: getattr(game_camps, name) for name in ("READ_S", "MAX_HELD")}


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Component:
    """A camp's SpawnerComponent: SpawnDetails read as a copy and taken only when given back whole, as a struct is;
    deaf takes nothing, broken raises."""

    def __init__(self, critical: bool, override: bool, deaf: bool, broken: bool) -> None:
        self.flags, self.deaf, self.broken = (critical, override), deaf, broken
        self.writes = 0

    @property
    def SpawnDetails(self) -> types.SimpleNamespace:
        if self.broken:
            raise RuntimeError("unreadable")
        return types.SimpleNamespace(bCritical=self.flags[0], bOverrideCritical=self.flags[1])

    @SpawnDetails.setter
    def SpawnDetails(self, details: types.SimpleNamespace) -> None:
        self.writes += 1
        if not self.deaf:
            self.flags = (details.bCritical, details.bOverrideCritical)


class Camp:
    def __init__(self, name: str, metres: float, critical: bool = False, override: bool = False, deaf: bool = False,
                 broken: bool = False) -> None:
        self.Name, self.x, self.freed = name, metres * 100.0, False
        self.SpawnerComponent = Component(critical, override, deaf, broken)

    def K2_GetActorLocation(self) -> types.SimpleNamespace:
        return types.SimpleNamespace(X=self.x, Y=0.0, Z=0.0)


def ours(name: str) -> bool:
    return name == "OakSpawner_Ours"


def world(*camps: Camp) -> list:
    state["all"][game_camps.SPAWNER_CLASS] = list(camps)
    return list(camps)


HERE_AT = (0.0, 0.0, 0.0)

try:
    near, far, own, default = (Camp("OakSpawner_Near", 100.0), Camp("OakSpawner_Far", game_camps.RANGE_M + 1.0),
                               Camp("OakSpawner_Ours", 10.0), Camp("Default__OakSpawner", 0.0))
    already, half = Camp("OakSpawner_Already", 50.0, True, True), Camp("OakSpawner_Half", 60.0, True, False)
    deaf, broken = Camp("OakSpawner_Deaf", 70.0, deaf=True), Camp("OakSpawner_Broken", 80.0, broken=True)
    world(near, far, own, default, already, half, deaf, broken)
    camps = game_camps.GameCamps(report.announce, ours)
    events.clear()
    said = camps.wake(HERE_AT, 0.0)
    check("decision 64: the game's camps within RANGE_M made critical, It Follows' own, the far ones and the class "
          "defaults left out; one already critical left alone; one that does not read back, or cannot be read, "
          "counted",
          near.SpawnerComponent.flags == (True, True) and half.SpawnerComponent.flags == (True, True)
          and far.SpawnerComponent.flags == (False, False) and own.SpawnerComponent.flags == (False, False)
          and default.SpawnerComponent.writes == 0 and already.SpawnerComponent.writes == 0
          and {key: said[key] for key in ("read", "made", "already", "ours", "far", "not_read_back", "unreadable",
                                          "held", "stopped")}
          == {"read": 7, "made": 2, "already": 1, "ours": 1, "far": 1, "not_read_back": 1, "unreadable": 1,
              "held": 3, "stopped": "complete"})
    check("the call written to the log first", fake.lines()[0] == {"event": "call", "run": 0,
                                                                  "call": "SpawnDetails critical", "game_camps": 0})
    check("EVERY_S between passes", not camps.due(game_camps.EVERY_S - 0.1) and camps.due(game_camps.EVERY_S))
    near.SpawnerComponent.writes = 0
    later = Camp("OakSpawner_Later", 200.0)
    world(near, far, own, default, already, half, deaf, broken, later)
    said = camps.wake(HERE_AT, game_camps.EVERY_S)
    check("each camp written once a run: those held are not read again; one come near since is made critical",
          near.SpawnerComponent.writes == 0 and later.SpawnerComponent.flags == (True, True)
          and said["read"] == 5 and said["made"] == 1 and said["held"] == 4)
    check("no place for the hunter: nothing read", camps.wake(None, 20.0)["stopped"] == "no_place")
    near.freed = True
    near = Camp("OakSpawner_Near", 100.0)
    world(near, far, own, default, already, half, deaf, broken, later)
    said = camps.wake(HERE_AT, 2 * game_camps.EVERY_S)
    check("trial 14: a camp the game freed and loaded again under the same name is made critical again, said, and is "
          "the one given back",
          near.SpawnerComponent.flags == (True, True) and said["made"] == 1 and said["remade"] == 1
          and said["held"] == 4 and camps.held["OakSpawner_Near"][0]() is near)

    half.freed = True
    deaf.SpawnerComponent.deaf = False
    events.clear()
    back = camps.put_back()
    check("at the stop each camp's own flags written back, one the game freed counted, the call written first",
          back == {"restored": 3, "gone": 1, "failed": 0} and near.SpawnerComponent.flags == (False, False)
          and deaf.SpawnerComponent.flags == (False, False) and later.SpawnerComponent.flags == (False, False)
          and already.SpawnerComponent.flags == (True, True) and camps.held == {}
          and fake.lines() == [{"event": "call", "run": 0, "call": "SpawnDetails given back", "game_camps": 4}])
    events.clear()
    check("nothing held, nothing written", camps.put_back() == {"restored": 0, "gone": 0, "failed": 0}
          and events == [])

    stuck = Camp("OakSpawner_Stuck", 10.0)
    world(stuck)
    camps = game_camps.GameCamps(report.announce, ours)
    camps.wake(HERE_AT, 0.0)
    stuck.SpawnerComponent.broken = True
    check("a camp that cannot be written back is counted", camps.put_back() == {"restored": 0, "gone": 0,
                                                                                 "failed": 1})

    world(*[Camp(f"OakSpawner_{number}", 10.0) for number in range(3)])
    game_camps.MAX_HELD = 2
    camps = game_camps.GameCamps(report.announce, ours)
    said = camps.wake(HERE_AT, 0.0)
    check("no more than MAX_HELD camps held at once", said["held"] == 2 and said["stopped"] == "held_limit")
    held = [name for name in camps.held]
    left = next(camp for camp in state["all"]["Spawner"] if camp.Name == held[0])
    left.freed = True
    said = camps.wake(HERE_AT, 20.0)
    check("a camp the game freed is forgotten, its room given to a new one", said["stopped"] == "complete"
          and said["held"] == 2 and held[0] not in camps.held and "OakSpawner_2" in camps.held)
    game_camps.MAX_HELD = ORIGINAL["MAX_HELD"]
    world(*[Camp(f"OakSpawner_{number}", 10.0) for number in range(3)])
    clock = iter([0.0, 0.0, game_camps.READ_S + 0.01, 1.0, 1.0])
    game_camps.time = types.SimpleNamespace(monotonic=lambda: next(clock))
    camps = game_camps.GameCamps(report.announce, ours)
    said = camps.wake(HERE_AT, 0.0)
    check("a pass stops at READ_S, the rest left for the next", said["stopped"] == "time_limit" and said["held"] == 1)
except Exception as error:
    check(f"exception {type(error).__name__}: {error}", False)

print(f"RESULTAT: {'TOUS LES TESTS PASSENT' if not fails else f'{len(fails)} ECHEC(S)'}")
sys.exit(1 if fails else 0)
