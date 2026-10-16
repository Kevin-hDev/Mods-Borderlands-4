"""Tests the camps that follow the hunter, noted in a real CampMap: each camp's spawner, its root made movable first
(announced), is moved onto him and read back; a root that stays static, a spawner gone or a failing call is said and the
others still move; they follow him at most every FOLLOW_S once he is farther than FOLLOW_M, their moves never written to
the SDK log; at the end each moved spawner is put back where it stood, announced. Trial 8b: a camp let go of is no
longer followed, put back nor noted, until it is noted again with an enemy drawn anew. A followed camp of the game no
enemy of the horde comes from any more is put back and let go of, whatever its put back says; a camp still held, or one
It Follows made, is kept; a thousand camps through a long run leave no more than the horde holds. A camp whose last
move took is not read again for its root; one whose move did not take is."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import zone_fixture  # noqa: E402
from zone_fixture import announced  # noqa: E402

fixture = zone_fixture.Fixture(state)
journal = fixture.journal

from it_follows.camp_follow import CampFollow  # noqa: E402
from it_follows.camp_map import CampMap  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def at(x: float) -> tuple:
    return (x, 0.0, 0.0)


def camps_of(*spawners: object) -> CampMap:
    """The camp of one enemy for each spawner, noted as the run notes them."""
    camps = CampMap()
    for spawner in spawners:
        camps.add(f"Char_{spawner.Name}", fixture.zone_of(spawner))
    return camps


def moved_ones() -> list:
    return [entry[1] for entry in journal if entry[0] == "move"]


def logged_call() -> dict:
    """The last line written to the SDK log, but the run's number."""
    return {name: value for name, value in fixture.logged().items() if name != "run"}


def nobody(name: str) -> bool:
    return False


try:
    journal.clear()
    static = fixture.spawner("OakSpawner_Static", at(5000.0), mobility=0)
    movable = fixture.spawner("OakSpawner_Movable", at(9000.0))
    follow = CampFollow(camps_of(static, movable), fixture.announce)
    placed = follow.place(at(0.0), 100.0)
    check("each camp's spawner is moved onto the hunter and read back there",
          placed == {"OakSpawner_Static": "moved", "OakSpawner_Movable": "moved"}
          and static.at == at(0.0) and movable.at == at(0.0))
    check("a static root is made movable first, announced; a movable one is left as it is",
          journal[:2] == [announced("SetMobility", camp="OakSpawner_Static"), ("mobility", "OakSpawner_Static", 2)]
          and sum(entry[0] == "mobility" for entry in journal) == 1)
    check("each move announced before it happens, no sweep, teleported",
          journal[2:4] == [announced("K2_SetActorLocation", False, camp="OakSpawner_Static"),
                           ("move", "OakSpawner_Static", 0.0)]
          and static.calls == [{"sweep": False, "hit": "HitResult", "teleport": True}])
    check("the root made movable is written to the SDK log, the moves are not",
          logged_call() == {"event": "call", "call": "SetMobility", "camp": "OakSpawner_Static"})
    journal.clear()
    check("they do not follow before FOLLOW_S", follow.follow(at(9000.0), 101.0) is None and journal == [])
    check("nor while the hunter stays within FOLLOW_M", follow.follow(at(300.0), 102.0) == {} and journal == [])
    check("past FOLLOW_M each moves back onto him",
          follow.follow(at(9000.0), 104.5) == {"OakSpawner_Static": "moved", "OakSpawner_Movable": "moved"}
          and static.at == at(9000.0) and movable.at == at(9000.0)
          and announced("K2_SetActorLocation", False, camp="OakSpawner_Movable") in journal)
    check("not a moment before FOLLOW_S after the last follow", follow.follow(at(20000.0), 106.4) is None)
    check("FOLLOW_S after, a hunter FOLLOW_M away leaves the camps where they are",
          follow.follow(at(9500.0), 106.5) == {} and static.at == at(9000.0) and movable.at == at(9000.0))
    check("a step farther moves them",
          follow.follow(at(9510.0), 108.5) == {"OakSpawner_Static": "moved", "OakSpawner_Movable": "moved"})
    journal.clear()
    back = follow.put_back()
    check("at the end each is put back where it stood, announced and written to the SDK log",
          back == {"OakSpawner_Static": "restored", "OakSpawner_Movable": "restored"}
          and static.at == at(5000.0) and movable.at == at(9000.0)
          and announced("K2_SetActorLocation", camp="OakSpawner_Static", back=True) in journal
          and logged_call() == {"event": "call", "call": "K2_SetActorLocation", "camp": "OakSpawner_Movable",
                                "back": True})
    check("then it follows no more", follow.follow(at(20000.0), 300.0) is None)

    journal.clear()
    stuck = fixture.spawner("OakSpawner_Stuck", at(5000.0), mobility=0, refuses=True)
    gone = fixture.spawner("OakSpawner_Gone", at(6000.0))
    broken = fixture.spawner("OakSpawner_Broken", at(7000.0))
    fine = fixture.spawner("OakSpawner_Fine", at(8000.0))
    follow = CampFollow(camps_of(stuck, gone, broken, fine), fixture.announce)
    broken.fail = True
    gone.freed = True
    check("a root that stays static, a spawner gone and a failing call are said, the others still moved",
          follow.place(at(0.0), 100.0) == {"OakSpawner_Stuck": "static", "OakSpawner_Gone": "gone",
                                           "OakSpawner_Broken": "call_failed:RuntimeError",
                                           "OakSpawner_Fine": "moved"}
          and stuck.at == at(5000.0) and fine.at == at(0.0) and "OakSpawner_Stuck" not in moved_ones())
    check("a camp tried once is not asked again at the next recruit", follow.place_new(at(0.0)) == {})
    broken.fail = False
    check("a spawner that failed to move is still put back", follow.put_back() == {
        "OakSpawner_Broken": "restored", "OakSpawner_Fine": "restored"} and broken.at == at(7000.0))
    journal.clear()
    kept = fixture.spawner("OakSpawner_Kept", at(5000.0))
    follow = CampFollow(camps_of(kept), fixture.announce)
    read: list[str] = []
    real_movable = follow._movable
    follow._movable = lambda spawner, name: read.append(name) or real_movable(spawner, name)
    follow.place(at(0.0), 100.0)
    check("audit of 16 October: a camp moved once is not read again for its root at the next follow",
          read == ["OakSpawner_Kept"] and follow.follow(at(9000.0), 102.0) == {"OakSpawner_Kept": "moved"}
          and read == ["OakSpawner_Kept"] and kept.at == at(9000.0))
    kept.RootComponent.Mobility = 0
    check("one whose move did not take is read again at the next follow, its root made movable again",
          follow.follow(at(20000.0), 104.0) == {"OakSpawner_Kept": "not_moved"}
          and follow.follow(at(30000.0), 106.0) == {"OakSpawner_Kept": "moved"} and len(read) == 2
          and kept.at == at(30000.0) and ("mobility", "OakSpawner_Kept", 2) in journal)
    follow.release("OakSpawner_Kept")
    check("a camp let go of is forgotten as movable too", not follow.movable)
    nothing = CampFollow(CampMap(), fixture.announce)
    check("without camps nothing moves", nothing.place(at(0.0), 1.0) == {} and nothing.put_back() == {})

    ours, game = fixture.spawner("OakSpawner_Ours", at(5000.0)), fixture.spawner("OakSpawner_Game", at(6000.0))
    camps = camps_of(ours, game)
    follow = CampFollow(camps, fixture.announce)
    follow.place(at(0.0), 100.0)
    follow.release("OakSpawner_Ours")
    ours.at = at(-4000.0)
    journal.clear()
    moved = follow.follow(at(9000.0), 103.0)
    check("trial 8b: a camp let go of is no longer followed nor noted, where it stands; the others still follow",
          moved == {"OakSpawner_Game": "moved"} and ours.at == at(-4000.0) and "OakSpawner_Ours" not in camps.spawners
          and "OakSpawner_Ours" not in moved_ones())
    check("nor put back at the end", follow.put_back() == {"OakSpawner_Game": "restored"} and ours.at == at(-4000.0))
    follow = CampFollow(camps, fixture.announce)
    follow.place(at(0.0), 100.0)
    follow.release("OakSpawner_Game")
    camps.add("Char_Game_2", fixture.zone_of(game))
    check("noted again with an enemy drawn anew, it follows again",
          follow.place_new(at(1000.0)) == {"OakSpawner_Game": "moved"} and game.at == at(1000.0))
    follow.release("OakSpawner_Never_Placed")
    check("letting go of a camp never placed changes nothing", list(follow.shifts) == ["OakSpawner_Game"])

    journal.clear()
    ours = fixture.spawner("OakSpawner_Ours", at(5000.0))
    held = fixture.spawner("OakSpawner_Held", at(6000.0))
    empty = fixture.spawner("OakSpawner_Empty", at(7000.0))
    fixed = fixture.spawner("OakSpawner_Fixed", at(8000.0), mobility=0, refuses=True)
    camps = CampMap()
    for enemy, spawner in (("Char_Ours_1", ours), ("Char_Held_1", held), ("Char_Held_2", held),
                           ("Char_Empty_1", empty), ("Char_Fixed_1", fixed)):
        camps.add(enemy, fixture.zone_of(spawner))
    follow = CampFollow(camps, fixture.announce)
    follow.place(at(0.0), 100.0)
    for enemy in ("Char_Ours_1", "Char_Held_1", "Char_Empty_1", "Char_Fixed_1"):
        camps.forget_enemy(enemy)
    journal.clear()
    done = follow.release_empty({"Char_Held_2", "Char_Fixed_1", "Char_No_Camp"}, lambda name: name == "OakSpawner_Ours")
    check("release_empty: a followed camp of the game no enemy of the horde comes from is put back, announced first",
          done == {"OakSpawner_Empty": "restored"} and empty.at == at(7000.0)
          and journal == [announced("K2_SetActorLocation", camp="OakSpawner_Empty", back=True),
                          ("move", "OakSpawner_Empty", 7000.0)]
          and logged_call() == {"event": "call", "call": "K2_SetActorLocation", "camp": "OakSpawner_Empty",
                                "back": True})
    check("then let go of: no longer followed, tried nor noted",
          "OakSpawner_Empty" not in follow.shifts and "OakSpawner_Empty" not in follow.tried
          and "OakSpawner_Empty" not in camps.spawners)
    check("a camp an enemy of the horde still comes from is kept, on the hunter",
          "OakSpawner_Held" in follow.shifts and held.at == at(0.0) and "OakSpawner_Held" in camps.spawners)
    check("a camp It Follows made is kept for release, even with no enemy in the horde",
          "OakSpawner_Ours" in follow.shifts and ours.at == at(0.0) and "OakSpawner_Ours" in camps.spawners)
    journal.clear()
    check("the camp let go of follows no more, the others still do",
          follow.follow(at(9000.0), 103.0) == {"OakSpawner_Held": "moved", "OakSpawner_Ours": "moved"}
          and empty.at == at(7000.0))
    journal.clear()
    check("with every followed camp still held or made by It Follows, nothing is called",
          follow.release_empty({"Char_Held_2"}, lambda name: name == "OakSpawner_Ours") == {} and journal == [])
    camps.add("Char_Empty_2", fixture.zone_of(empty))
    check("noted again with an enemy drawn anew, the camp follows again",
          follow.place_new(at(9000.0)) == {"OakSpawner_Empty": "moved"} and empty.at == at(9000.0))
    empty.fail = True
    held.freed = True
    check("a camp whose put back fails, or that the game freed, is let go of all the same",
          follow.release_empty(set(), lambda name: name == "OakSpawner_Ours")
          == {"OakSpawner_Held": "unavailable", "OakSpawner_Empty": "restore_error:RuntimeError"}
          and list(follow.shifts) == ["OakSpawner_Ours"] and "OakSpawner_Held" not in camps.spawners
          and "OakSpawner_Empty" not in follow.tried)
    check("nor put back again at the end", follow.put_back() == {"OakSpawner_Ours": "restored"})

    camps = CampMap()
    follow = CampFollow(camps, fixture.announce)
    follow.place(at(0.0), 0.0)
    for number in range(1000):
        spawner = fixture.spawner(f"OakSpawner_{number}", at(number * 100.0))
        camps.add(f"Char_{number}", fixture.zone_of(spawner))
        follow.place_new(at(0.0))
        if number:
            camps.forget_enemy(f"Char_{number - 1}")
        follow.release_empty({f"Char_{number}"}, nobody)
    check("a thousand camps through a long run: only the camp of the horde's one enemy is still held",
          list(follow.shifts) == ["OakSpawner_999"] and follow.tried == {"OakSpawner_999"}
          and list(camps.spawners) == ["OakSpawner_999"] and list(camps.of) == ["Char_999"])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
