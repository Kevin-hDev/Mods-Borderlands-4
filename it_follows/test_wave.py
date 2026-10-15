"""Tests It Follows' wave: the camps and the copies made at the start, written down, the run's stop written when none
was made or the making raised; an enemy of the horde killed waits to come back when the camps know its kind, up to
the run's most (decision 96), unless the coming back is off, when it is only counted; one left behind once (decision
97); the killed waiting are asked again together, oldest first, no more than the horde has room for, once EVERY_S at
most, those handed taken off the list and written down when someone was asked or the asking
failed, and the first one the game refused taken off too, counted; nobody is asked while the hunter is dead, as
reads.dead says, unplaced, or within SETTLE_S of a jump of his place, which is watched even while nobody waits; an error
ends the coming back, said once; a killed one comes back once until 5 minutes into the run, then GROWTH times as
often, compounded each minute, the share beyond a whole one carried to the next; the enemies that target the hunter
within RADIUS_M are counted, and the count sets the mode on the level's target and band: growing until the target,
held within the band, none coming back above it until the count is down to the target; each change written down; a
sample writes the count, the mode, the factor and the kinds of the place; the stop gives back what the copies lifted.
Decisions 56 and 68: the killed come back as the kinds met where the hunter stands, written down; where the horde
stands is sorted for the status line. Decision 65: nothing beyond the
count near holds the killed back. Kevin's rule: fewer than two following for 3 s, a group of the place asked, unless
the killed are waiting or do not come back; a birth lost before it joined the horde asked again, counted, owed until
the census draws it. Every line goes through report.py; one block runs the wave on It Follows' own
copies, camps and limit."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
sys.modules["unrealsdk"].make_struct = lambda name, **fields: types.SimpleNamespace(struct_name=name, **fields)

from it_follows import budget, camps, guard, horde, report, spread  # noqa: E402
from it_follows import copies as copies_module  # noqa: E402
from it_follows import wave as wave_module  # noqa: E402
from it_follows.seen import Seen  # noqa: E402
import wave_fixture as fake  # noqa: E402
from wave_fixture import events  # noqa: E402

fake.record_log()
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class FakeCopies:
    """copies.Copies as the wave sees it: its camps hand up to room of the killed asked again, the game refusing the
    one after refused_after when told, or it raises when told."""

    def __init__(self) -> None:
        self.asked: list[tuple] = []
        self.room, self.raises, self.made = 50, False, ("host", {"made": "done"})
        self.refused_after: int | None = None
        # The kinds of births lost before they joined, given once by unseen; the camps said joined.
        self.lost: list[str] = []
        self.joined_camps: list = []
        self.owed_camps: set = set()
        self.most: int | None = None

    def ask(self, crowd: list, character: object, pc: object, here: tuple, most: int) -> tuple:
        self.most = most
        if self.raises:
            raise RuntimeError("no camp")
        return self.made

    def again(self, wanted: list, character: object, pc: object, here: tuple) -> dict:
        self.asked.append((list(wanted), character, pc, here))
        if self.raises:
            raise RuntimeError("no camp")
        asked = min(self.room, len(wanted))
        handed = asked if self.refused_after is None else min(asked, self.refused_after)
        said = {"again": "done", "free": 0, "room": self.room, "asked": asked, "handed": handed}
        return said if handed == asked else {**said, "refusal": "PushActorDef:RuntimeError"}

    def knows(self, kind: str) -> bool:
        return kind != "Char_Odd"

    def ours(self, camp: str | None) -> bool:
        return camp == "OakSpawner_Ours"

    def joined(self, camp: str | None) -> None:
        self.joined_camps.append(camp)

    def owes(self, camp: str | None) -> bool:
        return camp in self.owed_camps

    def owing(self) -> int:
        return len(self.owed_camps)

    def unseen(self) -> list[str]:
        found, self.lost = self.lost, []
        return found

    def status(self) -> dict:
        return {"camps": 2, "alive": 1, "gone": 0, "failed": 0}

    def put_back(self) -> str:
        return "given_back"


# Three of the five levels (levels.py): the smallest, the one verified in game, the largest.
LEVEL_25 = types.SimpleNamespace(target=25, low=23, high=26)
LEVEL_40 = types.SimpleNamespace(target=40, low=36, high=42)
LEVEL_100 = types.SimpleNamespace(target=100, low=90, high=105)
PLACE = "/Game/Maps/WorldLevels/World_P.World_P:PersistentLevel"
HERE_AT = (0.0, 0.0, 0.0)
hunter = types.SimpleNamespace(HealthState=types.SimpleNamespace(bCurrentlyDead=False))


# The run's time played, which the wave's growth counts (clock.py): set before a call that needs a time.
played = [0.0]


def fresh(level: object = LEVEL_40, respawn: bool = True, most: int = horde.CROWD_MAX) -> tuple:
    events.clear()
    played[0] = 0.0
    hunter.HealthState.bCurrentlyDead = False
    copies = FakeCopies()
    return copies, wave_module.Wave(copies, report.note, lambda: played[0], level, respawn, most)


def factor_at(at: float) -> float:
    played[0] = at
    return wave.factor()


def written(event: str, **fields: object) -> dict:
    return {"event": event, "run": 0, **fields}


try:
    copies, wave = fresh()
    check("the start makes the camps and the copies, written down, and gives the zone to lend",
          wave.start([], hunter, "pc", HERE_AT) == "host" and fake.lines() == [written("copies", made="done")])
    copies, wave = fresh()
    copies.made = (None, {"made": "camp_refused"})
    check("none made: written with why, and no stop line: the run writes why it does not start",
          wave.start([], hunter, "pc", HERE_AT) is None
          and fake.lines() == [written("copies", made="camp_refused")])
    copies, wave = fresh()
    copies.raises = True
    check("the making raised: said, nothing raised out",
          wave.start([], hunter, "pc", HERE_AT) is None
          and fake.lines() == [written("copies", made="error:RuntimeError")])
    check("It Follows' camps are the copies'", wave.ours("OakSpawner_Ours") and not wave.ours("OakSpawner_Game"))

    copies, wave = fresh()
    wave.tick(hunter, "pc", HERE_AT, 0.0)
    check("nobody killed: nothing asked, nothing written", copies.asked == [] and fake.lines() == [])
    said = [wave.killed("cat", "Char_CatYoung"), wave.killed("odd", "Char_Odd"),
            wave.killed("bat", "Char_BatBasic")]
    check("a killed enemy waits to come back; one of a kind the camps cannot make does not",
          said == ["waiting", "unknown_kind", "waiting"]
          and wave.waiting == [("cat", "Char_CatYoung"), ("bat", "Char_BatBasic")])
    copies.room = 1
    wave.tick(hunter, "pc", HERE_AT, 0.5)
    check("the killed waiting are asked again together, oldest first, with the hunter, his look and his place",
          copies.asked == [([("cat", "Char_CatYoung"), ("bat", "Char_BatBasic")], hunter, "pc", HERE_AT)])
    check("those handed leave the list, the others wait, written down",
          wave.waiting == [("bat", "Char_BatBasic")]
          and fake.lines() == [written("born_again", again="done", free=0, room=1, asked=1, handed=1, of=["cat"],
                                       kinds=["Char_CatYoung"], refused=[], waiting=1)])
    wave.tick(hunter, "pc", HERE_AT, 0.5 + wave_module.EVERY_S - 0.1)
    check("asked once EVERY_S at most", len(copies.asked) == 1)
    copies.room = 0
    wave.tick(hunter, "pc", HERE_AT, 0.5 + wave_module.EVERY_S)
    check("no room: still waiting, nothing written (the trials wrote it to their own file only)",
          len(copies.asked) == 2 and wave.waiting == [("bat", "Char_BatBasic")] and len(fake.lines()) == 1)
    check("the status adds the coming back to It Follows' camps",
          wave.status() == {"camps": 2, "alive": 1, "gone": 0, "failed": 0, "killed": 3, "born_again": 1,
                            "unknown_kind": 1, "waiting_full": 0, "refused": 0, "waiting": 1, "broken": None,
                            "extra": 0, "held_back": 0, "respawn_off": 0, "unseen": 0, "left_behind": 0,
                            "mode": "grow"})

    copies, wave = fresh()
    for name in ("a", "b", "c"):
        wave.killed(name, "Char_CatYoung")
    copies.refused_after = 1
    wave.tick(hunter, "pc", HERE_AT, 0.0)
    check("the first one the game refused leaves the list, counted, so that it holds back nobody",
          wave.waiting == [("c", "Char_CatYoung")] and fake.lines()[-1]["of"] == ["a"]
          and fake.lines()[-1]["refused"] == ["b"] and fake.lines()[-1]["refusal"] == "PushActorDef:RuntimeError"
          and wave.status()["refused"] == 1 and wave.status()["born_again"] == 1)
    copies.refused_after = None
    wave.tick(hunter, "pc", HERE_AT, wave_module.EVERY_S)
    check("the next ones are asked at the next second",
          wave.waiting == [] and copies.asked[-1][0] == [("c", "Char_CatYoung")])

    copies, wave = fresh()
    wave.killed("cat", "Char_CatYoung")
    hunter.HealthState.bCurrentlyDead = True
    wave.tick(hunter, "pc", HERE_AT, 0.0)
    check("the hunter dead: nobody asked, nothing written (the trials wrote the wait to their own file only)",
          copies.asked == [] and fake.lines() == [])
    hunter.HealthState.bCurrentlyDead = False
    wave.tick(hunter, "pc", None, 1.0)
    check("his place unread: nobody asked", copies.asked == [])
    wave.tick(hunter, "pc", HERE_AT, 2.0)
    check("alive and placed again: asked at once", len(copies.asked) == 1 and wave.waiting == [])
    copies, wave = fresh()
    wave.killed("cat", "Char_CatYoung")
    hunter.HealthState.bCurrentlyDead = 1
    wave.tick(hunter, "pc", HERE_AT, 0.0)
    wave.killed("bat", "Char_BatBasic")
    hunter.HealthState = None
    wave.tick(hunter, "pc", HERE_AT, 1.0)
    hunter.HealthState = types.SimpleNamespace(bCurrentlyDead=False)
    check("a death read as reads.dead reads it: one the game does not say with a bool, or cannot say, holds nobody "
          "back", len(copies.asked) == 2)

    copies, wave = fresh()
    far = (wave_module.JUMP_M * 100.0 + 1.0, 0.0, 0.0)
    wave.tick(hunter, "pc", HERE_AT, 0.0)
    wave.tick(hunter, "pc", far, 1.0)
    wave.killed("cat", "Char_CatYoung")
    wave.tick(hunter, "pc", far, 2.0)
    check("his place jumped farther than JUMP_M in a sample, watched while nobody waited: nobody asked",
          copies.asked == [] and fake.lines() == [])
    wave.tick(hunter, "pc", far, 1.0 + wave_module.SETTLE_S - 0.1)
    check("not before SETTLE_S", copies.asked == [])
    wave.tick(hunter, "pc", far, 1.0 + wave_module.SETTLE_S)
    check("asked once SETTLE_S has passed", len(copies.asked) == 1)
    copies, wave = fresh()
    near = (wave_module.JUMP_M * 100.0 - 1.0, 0.0, 0.0)
    wave.tick(hunter, "pc", HERE_AT, 0.0)
    wave.killed("cat", "Char_CatYoung")
    wave.tick(hunter, "pc", near, 1.0)
    check("a move within JUMP_M in a sample is no jump", len(copies.asked) == 1)

    copies, wave = fresh()
    wave.killed("cat", "Char_CatYoung")
    copies.raises = True
    wave.tick(hunter, "pc", HERE_AT, 0.0)
    wave.killed("bat", "Char_BatBasic")
    wave.tick(hunter, "pc", HERE_AT, 5.0)
    check("an error ends the coming back, said once",
          len(copies.asked) == 1 and wave.broken == "error:RuntimeError"
          and fake.lines() == [written("born_again", again="error:RuntimeError", waiting=1)]
          and wave.status()["broken"] == "error:RuntimeError")

    copies, wave = fresh()
    check("decision 69: as many killed wait as the horde holds, 120 at first", wave.most == horde.CROWD_MAX == 120)
    wave.most = 2
    said = [wave.killed(name, "Char_CatYoung") for name in ("a", "b", "c")]
    check("beyond the most the killed are counted, not kept",
          said == ["waiting", "waiting", "waiting_full"] and len(wave.waiting) == 2
          and wave.status()["waiting_full"] == 1 and wave.status()["killed"] == 3)

    copies, wave = fresh()
    check("decisions 38 and 71: once until 5 minutes into the run, then 14 % more each minute from the sixth, "
          "compounded at each minute begun",
          (wave_module.GROW_FROM_S, wave_module.GROWTH, wave_module.RADIUS_M) == (300.0, 1.14, 50.0)
          and [factor_at(at) for at in (299.9, 300.0, 359.9)] == [1.0, 1.14, 1.14]
          and abs(factor_at(360.0) - 1.2996) < 1e-12 and abs(factor_at(540.0) - 1.14 ** 5) < 1e-12)
    check("counted on the time played, which the wave reads at each call",
          factor_at(299.9) == 1.0 and factor_at(300.0) == 1.14 and factor_at(0.0) == 1.0)
    played[0] = 299.0
    said = [wave.killed(name, "Char_CatYoung") for name in ("a", "b")]
    check("before 5 minutes a killed one comes back once", said == ["waiting", "waiting"] and len(wave.waiting) == 2)
    played[0] = 300.0
    said = [wave.killed(name, "Char_CatYoung") for name in ("c", "d", "e", "f", "g", "m", "n", "o")]
    check("then the share beyond a whole one is carried to the next killed: at 1.14, the eighth comes back twice",
          said == ["waiting"] * 7 + ["waiting_x2"] and wave.waiting[-2:] == [("o", "Char_CatYoung")] * 2
          and len(wave.waiting) == 11 and wave.status()["extra"] == 1)
    played[0] = 360.0
    said = [wave.killed(name, "Char_CatYoung") for name in ("h", "i", "j", "k", "l")]
    check("and at 1.2996 a minute later, compounded, the share carried on: the third of five comes back twice",
          said == ["waiting", "waiting", "waiting_x2", "waiting", "waiting"] and wave.status()["extra"] == 2)

    lines = [{"on": "a", "target": "player", "to_player_m": 10.0},
             {"on": "b", "target": "player", "to_player_m": wave_module.RADIUS_M},
             {"on": "c", "target": "player", "to_player_m": wave_module.RADIUS_M + 0.1},
             {"on": "d", "target": "other:OakCharacter", "to_player_m": 5.0},
             {"on": "e", "target": "player", "to_player_m": None},
             {"on": "f", "ended": "mover_dead"}]
    check("decision 39: counted, the enemies that target the hunter within RADIUS_M", wave_module.near(lines) == 2)
    check("trial 15: where the horde stands, whatever it targets: within RADIUS_M, within ON_WAY_M, farther, "
          "unplaced; a line without a place counted unplaced",
          wave_module.ON_WAY_M == 100.0 and wave_module.where(lines + [{"on": "g", "to_player_m": 100.0},
                                                                   {"on": "h", "to_player_m": 100.1}])
          == {"close": 3, "on_way": 2, "far": 1, "unplaced": 2})

    for level in (LEVEL_25, LEVEL_40, LEVEL_100):
        copies, wave = fresh(level)
        modes = []
        for count in (level.low - 1, level.low, level.target - 1, level.target, level.high, level.high + 1,
                      level.target + 1, level.target, level.low, level.low - 1):
            wave.regulate(count)
            modes.append(wave.mode)
        check(f"level {level.target}: growing until the count reaches the level's target, held within its band, "
              f"reducing above it until the count is down to the target, growing again under the band",
              modes == ["grow", "grow", "grow", "hold", "hold", "reduce", "reduce", "hold", "hold", "grow"])
        check(f"level {level.target}: each change written down, with the count and the level's target",
              [line for line in fake.lines() if line["event"] == "regulated"]
              == [written("regulated", mode="hold", was="grow", near=level.target, target=level.target),
                  written("regulated", mode="reduce", was="hold", near=level.high + 1, target=level.target),
                  written("regulated", mode="hold", was="reduce", near=level.target, target=level.target),
                  written("regulated", mode="grow", was="hold", near=level.low - 1, target=level.target)])

    copies, wave = fresh()
    wave.regulate(LEVEL_40.high + 1)
    played[0] = 300.0
    check("above the band, a killed one does not come back, counted, and nobody alive is touched",
          wave.killed("a", "Char_CatYoung") == "held_back" and wave.waiting == []
          and wave.status()["held_back"] == 1 and wave.status()["killed"] == 1 and wave.status()["mode"] == "reduce")
    wave.regulate(LEVEL_40.target)
    played[0] = 420.0
    said = [wave.killed(name, "Char_CatYoung") for name in ("b", "c", "d", "e", "f")]
    check("within the band, once each, whatever the minute", said == ["waiting"] * 5 and len(wave.waiting) == 5)
    check("an unknown kind is said before the mode", wave.killed("g", "Char_Odd") == "unknown_kind")

    copies, wave = fresh(most=1)
    wave.credit = 0.9
    played[0] = 300.0
    check("a killed one coming back twice past the most waits once",
          wave.killed("a", "Char_CatYoung") == "waiting" and len(wave.waiting) == 1
          and wave.status()["extra"] == 0)

    copies, wave = fresh(most=50)
    wave.start(["a", "b", "c"], hunter, "pc", HERE_AT)
    check("decision 96: the copies at the start no more than the horde has room for", copies.most == 47)
    copies, wave = fresh()
    played[0] = 400.0
    wave.credit = 0.9
    said = [wave.left_behind(), wave.left_behind()]
    check("decision 98: one left behind is counted and never asked again, even while the wave grows",
          said == ["rejoins_near", "rejoins_near"] and wave.waiting == [] and wave.credit == 0.9
          and wave.status()["left_behind"] == 2 and wave.status()["extra"] == 0 and wave.status()["killed"] == 0)
    copies, wave = fresh(most=5)
    wave.tick(hunter, "pc", HERE_AT, 0.0)
    for name in ("a", "b", "c"):
        wave.killed(name, "Char_CatYoung")
    wave.regulate(LEVEL_40.low - 1, 3)
    copies.owed_camps = {"camp_x"}
    wave.tick(hunter, "pc", HERE_AT, 5.0)
    check("decision 96: nobody asked beyond the horde's room, the most less those drawn and the births not joined",
          [len(asked[0]) for asked in copies.asked] == [1] and len(wave.waiting) == 2 and wave.owes("camp_x"))
    copies.owed_camps = {"camp_x", "camp_y"}
    wave.tick(hunter, "pc", HERE_AT, 10.0)
    check("and nobody without room, the killed still waiting", len(copies.asked) == 1 and len(wave.waiting) == 2)

    copies, wave = fresh(respawn=False)
    wave.credit = 0.9
    played[0] = 400.0
    said = [wave.killed("a", "Char_CatYoung"), wave.killed("odd", "Char_Odd")]
    wave.regulate(LEVEL_40.high + 1)
    said.append(wave.killed("b", "Char_CatYoung"))
    wave.tick(hunter, "pc", HERE_AT, 0.0)
    status = wave.status()
    check("decision 44: the coming back off, a killed one is counted and never waits, whatever its kind, the mode or "
          "the minute; nobody is asked",
          said == ["respawn_off"] * 3 and wave.waiting == [] and copies.asked == [] and wave.credit == 0.9
          and {key: status[key] for key in ("killed", "respawn_off", "unknown_kind", "held_back", "extra", "waiting")}
          == {"killed": 3, "respawn_off": 3, "unknown_kind": 0, "held_back": 0, "extra": 0, "waiting": 0})

    copies, wave = fresh()
    wave.killed("a", "Char_CatYoung")
    wave.regulate(12)
    played[0] = 300.0
    check("what a sample writes of the wave: the count near, the mode, the factor, those waiting, the room left, no "
          "kind of the place met yet",
          wave.gauge() == {"near": 12, "mode": "grow", "factor": 1.14, "waiting": 1, "kinds": 0,
                           "met_last": 0, "remembered": 0})
    check("the stop gives back what the copies lifted", wave.put_back() == "given_back")

    copies, wave = fresh()
    met = wave.saw([("shotgun", "Char_SoldierShotgun", f"{PLACE}.OakSpawner_Game.Territory", (2000.0, 0.0, 0.0)),
                    ("cat", "Char_CatYoung", f"{PLACE}.OakSpawner_Ours.Territory", (500.0, 0.0, 0.0)),
                    ("striker", "Char_StrikerBasic", "", (0.0, 3000.0, 0.0))])
    for name in ("a", "b", "c"):
        wave.killed(name, "Char_CatYoung")
    wave.tick(hunter, "pc", HERE_AT, 6.0)
    check("decisions 56 and 68: the killed come back as the kinds met where the hunter stands, in turn, It Follows' "
          "own left out", met == 2 and copies.asked[-1][0] == [("a", "Char_SoldierShotgun"),
                                                               ("b", "Char_StrikerBasic"),
                                                               ("c", "Char_SoldierShotgun")])
    check("the kinds born are written down beside the killed they replace",
          fake.lines()[-1]["of"] == ["a", "b", "c"]
          and fake.lines()[-1]["kinds"] == ["Char_SoldierShotgun", "Char_StrikerBasic", "Char_SoldierShotgun"])
    check("the status says the kinds of the place where the hunter stood at the last sample",
          wave.gauge()["kinds"] == 2 and wave.gauge()["met_last"] == 2)
    for name in ("d", "e"):
        wave.killed(name, "Char_CatYoung")
    wave.tick(hunter, "pc", (40000.0, 0.0, 0.0), 8.0)
    wave.tick(hunter, "pc", (40000.0, 0.0, 0.0), 8.0 + wave_module.SETTLE_S)
    check("decision 68: 400 m from where the game's enemies were met, once the jump settled, the killed come back as "
          "they were",
          copies.asked[-1][0] == [("d", "Char_CatYoung"), ("e", "Char_CatYoung")]
          and wave.gauge()["kinds"] == 0)

    copies, wave = fresh()
    said = [wave.killed(f"k{number}", "Char_CatYoung") for number in range(70)]
    wave.regulate(LEVEL_40.low - 1)
    wave.tick(hunter, "pc", HERE_AT, 0.0)
    check("decision 65: nothing but the count near holds the killed back: 70 wait, all asked together",
          said == ["waiting"] * 70 and len(copies.asked[-1][0]) == 70)

    copies, wave = fresh()
    wave.saw([("cat_1", "Char_CatAdult", PLACE + ".OakSpawner_Game.Territory", HERE_AT)])
    for at in (100.0, 100.0 + guard.WAIT_S):
        wave.regulate(0, 1)
        wave.tick(hunter, "pc", HERE_AT, at)
    group = copies.asked[-1][0] if copies.asked else []
    check("Kevin's rule: fewer than 2 enemies following for 3 s, a group of the place asked as the killed are, "
          "written down",
          len(copies.asked) == 1 and len(group) == guard.GROUP and {kind for _name, kind in group} == {"Char_CatAdult"}
          and [line["asked"] for line in fake.lines() if line["event"] == "guard"] == [guard.GROUP])
    copies, wave = fresh(respawn=False)
    wave.saw([("cat_1", "Char_CatAdult", PLACE + ".OakSpawner_Game.Territory", HERE_AT)])
    copies.lost = ["Char_BatBasic"]
    for at in (100.0, 100.0 + guard.WAIT_S):
        wave.regulate(0, 0)
        wave.tick(hunter, "pc", HERE_AT, at)
    check("the killed not coming back (decision 44): no group, no lost birth asked again",
          copies.asked == [] and copies.lost == ["Char_BatBasic"])
    copies, wave = fresh()
    wave.saw([("cat_1", "Char_CatAdult", PLACE + ".OakSpawner_Game.Territory", HERE_AT)])
    wave.killed("cat", "Char_CatYoung")
    copies.room = 0
    for at in (100.0, 100.0 + guard.WAIT_S):
        wave.regulate(0, 0)
        wave.tick(hunter, "pc", HERE_AT, at)
    check("killed waiting to come back: they come first, no group", wave.waiting == [("cat", "Char_CatYoung")])
    copies, wave = fresh()
    copies.lost = ["Char_BatBasic"]
    wave.regulate(0, 5)
    wave.tick(hunter, "pc", HERE_AT, 100.0)
    check("a birth lost before it joined the horde asked again, counted",
          copies.asked[-1][0] == [("unseen", "Char_BatBasic")] and wave.counts["unseen"] == 1)
    events.clear()
    clock = [0.0]
    camps.time = copies_module.time = types.SimpleNamespace(monotonic=lambda: clock[0])
    camps.FGbxDefPtr = fake.DefPtr
    statics = fake.Statics(zones=[])
    state["all"]["GbxTerritoryComponent"] = statics.zones
    fake.give_kit(state, statics, ["Char_CatYoung"])
    settings = fake.Settings()
    fake.play(settings)
    own = camps.Camps(report.announce, 200)
    chain = copies_module.Copies(report.announce, own, fake.Ground(), budget.Budget(report.announce),
                                 spread.Spread(((100, 0.0),)))
    wave = wave_module.Wave(chain, report.note, lambda: 0.0, LEVEL_40, True)
    look = types.SimpleNamespace(GetControlRotation=lambda: types.SimpleNamespace(Yaw=0.0))
    crowd = [Seen(object(), f"Char_CatYoung_{number}", "Char_CatYoung", None, "", None, 0.0,
                  (1000.0 * number, 0.0, 0.0)) for number in (1, 2)]
    host = wave.start(crowd, hunter, look, HERE_AT)
    made = [line for line in fake.lines() if line["event"] == "copies"]
    check("on It Follows' own copies, camps and limit, through report.py: the lent zone's camp and a copy of each "
          "enemy near made, written down, the limit lifted, every call written first",
          host is not None and host.zone is statics.zones[0] and len(made) == 1 and made[0]["made"] == "done"
          and made[0]["handed"] == 2 and settings.bDisableSpawnBudget is True and fake.announced_first(events))
    owed = list(chain.owed)
    for camp in owed:
        wave.joined(camp)
    check("each birth owed by its camp until the census draws it into the horde", len(owed) == 2 and chain.owed == {})
    wave.regulate(LEVEL_40.high + 3)
    held = wave.killed("Char_CatYoung_1", "Char_CatYoung")
    wave.regulate(LEVEL_40.target)
    clock[0] = camps.PENDING_S
    mark = len(events)
    back = wave.killed("Char_CatYoung_2", "Char_CatYoung")
    wave.tick(hunter, look, HERE_AT, 3.0)
    phase = events[mark:]
    again = [entry[1] for entry in phase if entry[0] == "log" and entry[1]["event"] == "born_again"]
    calls = [entry[0] for entry in phase if entry[0] not in ("log", "HaveAllDied")]
    check("a killed one held back above the band; within it, one comes back on a camp whose enemy died, moved, then "
          "handed its kind, every call written first",
          held == "held_back" and back == "waiting" and wave.waiting == [] and len(again) == 1
          and again[0]["handed"] == 1 and again[0]["free"] == 2 and again[0]["of"] == ["Char_CatYoung_2"]
          and calls == ["SetMobility", "K2_SetActorLocation", "SetSpawnerEnabled", "PushActorDef", "ResetSpawner"]
          and fake.announced_first(phase))
    reborn = list(chain.owed)
    clock[0] += camps.PENDING_S
    wave.tick(hunter, look, HERE_AT, 3.0 + wave_module.UNSEEN_EVERY_S)
    again = [line for line in fake.lines() if line["event"] == "born_again"]
    check("a birth whose camp is free again before it joined the horde is asked again, once, as a kind of the place",
          len(reborn) == 1 and wave.counts["unseen"] == 1 and again[-1]["of"] == ["unseen"]
          and again[-1]["kinds"] == ["Char_CatYoung"] and wave.waiting == [])
    chain_lines = fake.lines()
    check("no line holds a field named log, and only a call's line one named call: the names report.py's lines hold "
          "themselves",
          all("log" not in line and ("call" in line) == (line["event"] == "call") for line in chain_lines)
          and {line["event"] for line in chain_lines} == {"call", "copies", "regulated", "born_again"})
    check("the periodic look for lost births writes no call line: only the askings do",
          sum(1 for line in chain_lines if line.get("call") == "HaveAllDied")
          == sum(1 for line in chain_lines if line["event"] in ("copies", "born_again")))
    check("the stop gives the limit back", wave.put_back() == "given_back" and settings.bDisableSpawnBudget is False)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
