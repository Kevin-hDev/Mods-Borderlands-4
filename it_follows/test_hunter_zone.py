"""Tests the zone lent to the horde: moved onto the hunter, then lent to several enemies, each call announced first,
with the enemy's name, and written to the SDK log by It Follows' own announce; a zone not moved or not taken says so; it
follows the hunter at most every FOLLOW_S once he is farther than FOLLOW_M, or at once when asked again, its follow
moves never written to the log; whether it stays where it was put last is read, to HELD_M; a zone the game moved away
is put back onto the hunter, the tries that fail in a row counted, a move counting from 0 again; the zone lost once
gone, after TRIES failed tries in a row or AWAY_SAMPLES samples moved away in a row, the first try of a series written
down, a failing call written and not raised; each enemy given its own zone back once, never on a body the game
reuses; the zone always put back; its combat radius widened and written back once, announced first, never over a
radius the game changed."""

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

from it_follows import hunter_zone  # noqa: E402

fails: list[str] = []
camp = fixture.zone("camp", (2000.0, 0.0, 0.0))
home = fixture.zone("home", (18000.0, 0.0, 0.0))
yard = fixture.zone("yard", (9000.0, 0.0, 0.0))


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def at(x: float) -> tuple:
    return (x, 0.0, 0.0)


def fresh() -> tuple:
    journal.clear()
    camp.at, home.at, yard.at = at(2000.0), at(18000.0), at(9000.0)
    camp.settings.CombatTerritory.Radius = 4000.0
    for zone in (camp, home, yard):
        zone.stuck = zone.fail = zone.freed = False
    first, second = fixture.enemy("cat_a", home), fixture.enemy("cat_b", yard)
    return hunter_zone.HunterZone(fixture.seen("host", camp), fixture.announce), first, second


def seen(enemy: object) -> object:
    return fixture.seen(enemy.name, enemy.home, enemy)


def logged_call() -> dict:
    """The last line written to the SDK log, but the run's number."""
    return {name: value for name, value in fixture.logged().items() if name != "run"}


def moves() -> int:
    return sum(entry[0] == "move" for entry in journal)


try:
    zone, first, second = fresh()
    placed = zone.place(at(0.0), 100.0)
    check("placed: the zone moved onto the hunter, announced first", placed == "moved" and camp.at == at(0.0)
          and journal == [announced("K2_SetWorldLocation", zone="onto_hunter"), ("move", "camp", 0.0)])
    check("the call written to the SDK log by It Follows' own announce",
          logged_call() == {"event": "call", "call": "K2_SetWorldLocation", "zone": "onto_hunter"})
    check("its centre is read where it stands", zone.centre() == at(0.0))
    journal.clear()
    taken = [zone.lend(seen(first)), zone.lend(seen(second))]
    check("lent to two enemies, each call announced first with the enemy's name",
          taken == ["target", "target"] and first.zone is camp and second.zone is camp
          and journal == [announced("SetTerritory", zone="target", on="cat_a"), ("set", "cat_a", "camp"),
                          announced("SetTerritory", zone="target", on="cat_b"), ("set", "cat_b", "camp")]
          and logged_call() == {"event": "call", "call": "SetTerritory", "zone": "target", "on": "cat_b"})
    check("it says which zone a lent enemy holds, and that another was never lent",
          zone.held("cat_a", camp) == "target" and zone.held("cat_a", home) == "own"
          and zone.held("cat_a", None) == "none" and zone.held("cat_a", yard) == "other"
          and zone.held("nobody", camp) == "not_lent")
    journal.clear()
    lines = len(state["info"])
    check("it does not follow before FOLLOW_S", zone.follow(at(5000.0), 101.0) == "waiting" and journal == [])
    check("nor while the hunter stays within FOLLOW_M", zone.follow(at(400.0), 102.0) == "kept" and journal == [])
    check("past FOLLOW_M it moves onto him, announced but never written to the SDK log",
          zone.follow(at(5000.0), 102.5) == "moved" and camp.at == at(5000.0)
          and journal == [announced("K2_SetWorldLocation", False, zone="follow"), ("move", "camp", 5000.0)]
          and len(state["info"]) == lines)
    check("and waits FOLLOW_S before the next move", zone.follow(at(9000.0), 103.0) == "waiting")
    camp.stuck = True
    check("a follow move that does not take says so", zone.follow(at(9000.0), 105.0) == "not_moved")
    camp.stuck = False
    journal.clear()
    check("one enemy given its own zone back, announced with its name",
          zone.give_back("cat_a", first, False) == "restored" and first.zone is home
          and journal == [announced("SetTerritory", zone="own", on="cat_a"), ("set", "cat_a", "home")])
    check("only once", zone.give_back("cat_a", first, False) == "not_lent" and zone.held("cat_a", camp) == "not_lent")
    journal.clear()
    check("nothing called on a body the game reuses, and the loan forgotten",
          zone.give_back("cat_b", second, True) == "not_needed" and journal == [] and zone.loans == {})
    check("the zone put back where it stood, announced first", zone.put_back() == "restored"
          and camp.at == at(2000.0)
          and journal[-2:] == [announced("K2_SetWorldLocation", zone="back"), ("move", "camp", 2000.0)])
    check("once put back it follows no more", zone.follow(at(9000.0), 200.0) == "waiting")

    zone, first, second = fresh()
    first.refuse = True
    check("an enemy that does not take the zone says it holds its own", zone.lend(seen(first)) == "own")
    check("given back then, nothing to do", zone.give_back("cat_a", first, False) == "already_home")
    check("never moved, the zone has nothing to put back", zone.put_back() == "inactive")

    zone, first, second = fresh()
    camp.freed = True
    journal.clear()
    check("review: a zone gone before a census put off is lent to nobody, through the hunter zone's own weak pointer, "
          "none made again from the zone read at the start",
          zone.lend(seen(first)) == "unavailable" and zone.loans["cat_a"].target is zone.shift.zone
          and journal == [] and first.zone is home)
    camp.freed = False

    zone, first, second = fresh()
    first.fail = True
    try:
        zone.lend(seen(first))
        raised = False
    except RuntimeError:
        raised = True
    check("a failing lend raises, and the loan is kept to be given back",
          raised and zone.held("cat_a", home) == "own" and zone.give_back("cat_a", first, False) == "already_home")

    zone, first, second = fresh()
    camp.stuck = True
    placed = zone.place(at(0.0), 100.0)
    journal.clear()
    check("a zone that does not move says so, and putting it back is still tried",
          placed == "not_moved" and zone.put_back() == "restored" and ("move", "camp", 2000.0) in journal)

    zone, first, second = fresh()
    check("trial 6h: before it is put, nobody can say whether the zone stays", zone.stays() is None)
    zone.place(at(0.0), 100.0)
    check("put on the hunter, it stays there", zone.stays() is True)
    camp.at = at(42000.0)
    check("moved back by the game farther than HELD_M, it does not", zone.stays() is False)
    camp.at = at(500.0)
    check("HELD_M from where it was put, it still does", zone.stays() is True)
    camp.at = at(510.0)
    check("a step farther, it does not", zone.stays() is False)
    zone.follow(at(9000.0), 102.5)
    check("followed, it stays where it was put last", camp.at == at(9000.0) and zone.stays() is True)
    journal.clear()
    check("asked again, it moves onto the hunter at once, before FOLLOW_S and within FOLLOW_M",
          zone.follow(at(9200.0), 103.0, again=True) == "moved" and camp.at == at(9200.0)
          and journal == [announced("K2_SetWorldLocation", False, zone="follow"), ("move", "camp", 9200.0)]
          and zone.stays() is True)
    camp.freed = True
    check("a zone gone cannot be read: nobody can say", zone.stays() is None and zone.centre() is None)
    camp.freed = False
    zone.put_back()
    check("put back, nobody can say any more", zone.stays() is None)

    zone, first, second = fresh()
    zone.place(at(0.0), 100.0)
    check("FOLLOW_S after its last move the zone follows, not a moment before",
          zone.follow(at(5000.0), 101.9) == "waiting" and zone.follow(at(5000.0), 102.0) == "moved")
    check("a hunter FOLLOW_M away keeps it where it is, a step farther moves it",
          zone.follow(at(5500.0), 104.0) == "kept" and zone.follow(at(5510.0), 104.0) == "moved")

    zone, first, second = fresh()
    check("replace: before the zone is put, it is kept, nothing called",
          zone.replace(at(0.0), 99.0) == "kept" and journal == [] and zone.failures == 0)
    zone.place(at(0.0), 100.0)
    journal.clear()
    check("a zone that stays where it was put is kept, nothing called",
          zone.replace(at(300.0), 101.0) == "kept" and journal == [] and camp.at == at(0.0))
    camp.at = at(42000.0)
    lines = len(state["info"])
    check("a zone the game moved away is put back onto the hunter, announced first, as place does",
          zone.replace(at(300.0), 102.0) == "moved" and camp.at == at(300.0)
          and journal == [announced("K2_SetWorldLocation", zone="back_on_hunter"), ("move", "camp", 300.0)]
          and zone.failures == 0 and zone.put_at == at(300.0) and zone.stays() is True)
    check("written to the SDK log before the move", len(state["info"]) == lines + 1
          and logged_call() == {"event": "call", "call": "K2_SetWorldLocation", "zone": "back_on_hunter"})
    check("then it waits FOLLOW_S before it follows", zone.follow(at(9000.0), 103.0) == "waiting")
    camp.at = at(42000.0)
    camp.stuck = True
    tries = [zone.replace(at(0.0), 104.0 + step) for step in range(3)]
    check("each try the game does not take counts as a failure, in a row",
          tries == ["not_moved"] * 3 and zone.failures == 3 and camp.at == at(42000.0))
    camp.stuck = False
    check("a move counts them from 0 again", zone.replace(at(0.0), 108.0) == "moved" and zone.failures == 0
          and camp.at == at(0.0))
    camp.at = at(42000.0)
    camp.stuck = True
    zone.replace(at(0.0), 110.0)
    camp.stuck = False
    camp.at = at(200.0)
    journal.clear()
    check("a zone held between two tries is kept, nothing called, the count left as it is",
          zone.replace(at(0.0), 111.0) == "kept" and journal == [] and zone.failures == 1)
    camp.at = at(42000.0)
    check("a hunter whose place cannot be read leaves the zone where it is, a failure too",
          zone.replace(None, 112.0) == "unavailable" and moves() == 0 and zone.failures == 2)

    zone, first, second = fresh()
    zone.place(at(0.0), 100.0)
    camp.at = at(42000.0)
    camp.stuck = True
    zone.replace(at(0.0), 101.0)
    zone.replace(at(0.0), 102.0)
    camp.stuck, camp.fail = False, True
    try:
        zone.replace(at(0.0), 103.0)
        raised = False
    except RuntimeError:
        raised = True
    check("a failing call raises to the run, counted as a failure, the zone counted as moved so that it is put back",
          raised and zone.failures == 3 and zone.shift.moved)
    camp.fail = False
    check("the next try that moves it counts from 0 again", zone.replace(at(0.0), 104.0) == "moved"
          and zone.failures == 0)

    written: list[tuple] = []

    def note(event: str, **fields: object) -> None:
        written.append((event, fields))

    zone, first, second = fresh()
    zone.place(at(0.0), 100.0)
    check("lost: a zone that stays is no reason to stop, nothing written", zone.lost(at(0.0), 101.0, note) is None
          and written == [] and zone.away == 0)
    camp.at = at(42000.0)
    check("one the game moved away is put back, the first try of the series written down",
          zone.lost(at(0.0), 102.0, note) is None and camp.at == at(0.0)
          and written == [("zone_replaced", {"outcome": "moved", "failures": 0})] and zone.away == 1)
    for step in range(hunter_zone.AWAY_SAMPLES - 2):
        camp.at = at(42000.0)
        zone.lost(at(0.0), 103.0 + step, note)
    camp.at = at(42000.0)
    check("moved away AWAY_SAMPLES samples in a row though each try puts it back, it is lost; one line only",
          zone.lost(at(0.0), 120.0, note) == "zone_lost" and len(written) == 1)
    zone, first, second = fresh()
    zone.place(at(0.0), 100.0)
    camp.at = at(42000.0)
    zone.lost(at(0.0), 101.0, note)
    camp.at = at(100.0)
    check("held again, the series counts from 0", zone.lost(at(0.0), 102.0, note) is None and zone.away == 0)
    camp.at, camp.stuck = at(42000.0), True
    outcomes = [zone.lost(at(0.0), 103.0 + step, note) for step in range(hunter_zone.TRIES)]
    check("TRIES tries in a row that leave it elsewhere: lost", outcomes == [None] * (hunter_zone.TRIES - 1)
          + ["zone_lost"])
    camp.stuck, camp.fail = False, True
    written.clear()
    zone, first, second = fresh()
    zone.place(at(0.0), 100.0)
    camp.at, camp.fail = at(42000.0), True
    check("a failing call is written down with its error, not raised", zone.lost(at(0.0), 101.0, note) is None
          and written == [("zone_replaced", {"outcome": "call_failed:RuntimeError", "failures": 1})])
    camp.fail, camp.freed = False, True
    check("a zone gone stops the run", zone.lost(at(0.0), 102.0, note) == "zone_gone")
    camp.freed = False

    zone, first, second = fresh()
    zone.place(at(0.0), 100.0)
    journal.clear()
    check("trial 6p: the zone's combat radius widened, announced first, the radius it had said",
          zone.widen(60000.0) == {"widened": "done", "radius_m_before": 40.0, "radius_m": 600.0}
          and camp.settings.CombatTerritory.Radius == 60000.0
          and journal == [announced("CombatTerritory.Radius", zone="widen", radius_m=600.0)])
    check("its radius read where it stands", zone.radius_m() == 600.0)
    journal.clear()
    check("written back once, announced first", zone.narrow() == "restored"
          and camp.settings.CombatTerritory.Radius == 4000.0
          and journal == [announced("CombatTerritory.Radius", zone="narrow")])
    check("only once", zone.narrow() == "not_widened" and camp.settings.CombatTerritory.Radius == 4000.0)

    zone, first, second = fresh()
    zone.widen(60000.0)
    camp.settings.CombatTerritory.Radius = 2500.0
    check("a radius the game changed meanwhile is left as the game set it",
          zone.narrow() == "ownership_lost" and camp.settings.CombatTerritory.Radius == 2500.0)

    zone, first, second = fresh()
    camp.settings.CombatTerritory.Radius = 0.0
    try:
        zone.widen(60000.0)
        raised = False
    except ValueError:
        raised = True
    check("a radius the writer refuses raises, announced before the write, nothing written, nothing to write back",
          raised and journal == [announced("CombatTerritory.Radius", zone="widen", radius_m=600.0)]
          and camp.settings.CombatTerritory.Radius == 0.0 and zone.narrow() == "inactive")

    zone, first, second = fresh()
    camp.freed = True
    check("a zone the game no longer holds is not widened, its radius not read",
          zone.widen(60000.0) == {"widened": "unavailable"} and zone.radius_m() is None
          and zone.narrow() == "not_widened" and camp.settings.CombatTerritory.Radius == 4000.0)

    zone, first, second = fresh()
    zone.widen(60000.0)
    camp.freed = True
    check("gone before its radius is written back, it says so", zone.narrow() == "unavailable")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
