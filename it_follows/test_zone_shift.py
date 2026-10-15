"""Tests the zone moved onto a point and put back: every parameter of K2_SetWorldLocation passed by name, no sweep,
teleported; the move announced before its call and read back, within 1 m of the point; a zone that does not move says
so and is still put back; a failing move raises with the zone counted as moved; put back only once moved, without the
zone nothing called, one that did not get back tried again. A whole actor is read, moved and put back the same way with
the actor's functions."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import zone_fixture  # noqa: E402

fixture = zone_fixture.Fixture(state)
journal = fixture.journal

from it_follows import zone_shift  # noqa: E402

fails: list[str] = []
HOME = (1000.0, 2000.0, 300.0)
POINT = (5000.0, 0.0, 100.0)


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def mark(word: str = "announced") -> object:
    return lambda: journal.append(word)


def fresh() -> tuple:
    journal.clear()
    zone = fixture.zone("camp", HOME)
    return zone_shift.Shift(zone), zone


try:
    shift, zone = fresh()
    check("the zone's place is noted before anything moves", shift.home == HOME and not shift.moved
          and shift.where() == HOME)
    moved = shift.place(POINT, mark())
    check("the zone is moved onto the point, announced first, and read back there",
          moved == "moved" and zone.at == POINT and journal == ["announced", ("move", "camp", 5000.0)]
          and shift.where() == POINT)
    check("no sweep, a HitResult for the out parameter, teleported",
          zone.calls == [{"sweep": False, "hit": "HitResult", "teleport": True}])
    check("the zone is put back where it stood, announced first",
          shift.put_back(mark("announced back")) == "restored" and zone.at == HOME
          and journal[-2:] == ["announced back", ("move", "camp", 1000.0)] and not shift.moved)
    check("a zone put back is not moved again", shift.put_back(mark()) == "inactive"
          and sum(entry[0] == "move" for entry in journal if isinstance(entry, tuple)) == 2)

    shift, zone = fresh()
    check("a zone never moved is not put back", shift.put_back(mark()) == "inactive" and journal == [])
    zone.stuck = True
    check("a zone that does not move says so", shift.place(POINT, mark()) == "not_moved" and shift.moved)
    check("it is still put back, and says it stood where it was", shift.put_back(mark()) == "restored")

    shift, zone = fresh()
    zone.offset_cm = 100.0
    check("a zone read back within 1 m of the point counts as moved", shift.place(POINT, mark()) == "moved")
    zone.offset_cm = 150.0
    check("farther than that, it does not", shift.place(POINT, mark()) == "not_moved")

    shift, zone = fresh()
    check("without the point nothing moves", shift.place(None, mark()) == "unavailable" and journal == [])
    zone.freed = True
    check("without the zone nothing moves, and it has no place", shift.place((0.0, 0.0, 0.0), mark()) == "unavailable"
          and journal == [] and not shift.moved and shift.where() is None)
    unread = zone_shift.Shift(fixture.zone("unread", (float("nan"), 0.0, 0.0)))
    check("a zone whose place could not be read has nowhere to go back to, and is not moved",
          unread.home is None and unread.place(POINT, mark()) == "unavailable" and journal == []
          and not unread.moved)

    shift, zone = fresh()
    zone.fail = True
    try:
        shift.place(POINT, mark())
        raised = False
    except RuntimeError:
        raised = True
    check("a failing move raises to the run, announced first, the zone counted as moved",
          raised and shift.moved and journal == ["announced", ("move", "camp", 5000.0)])
    check("putting it back says its error", shift.put_back(mark()) == "restore_error:RuntimeError" and shift.moved)
    zone.fail = False
    check("once the call works again, it is put back", shift.put_back(mark()) == "restored" and zone.at == HOME)

    shift, zone = fresh()
    shift.place(POINT, mark())
    zone.stuck = True
    check("a zone that does not get back says so, still counted as moved",
          shift.put_back(mark()) == "restore_failed" and shift.moved and zone.at == POINT)
    zone.stuck = False
    check("and is tried again next time", shift.put_back(mark()) == "restored" and zone.at == HOME and not shift.moved)

    shift, zone = fresh()
    shift.place(POINT, mark())
    zone.freed = True
    journal.clear()
    check("without the zone nothing is put back", shift.put_back(mark()) == "unavailable" and journal == [])

    journal.clear()
    spawner = fixture.spawner("OakSpawner_Camp", (7000.0, 0.0, 50.0))
    moved_actor = zone_shift.Shift(spawner, actor=True)
    check("trial 6h: an actor's place is read with the actor's function",
          moved_actor.home == (7000.0, 0.0, 50.0) and moved_actor.where() == (7000.0, 0.0, 50.0))
    check("an actor is moved by K2_SetActorLocation, no sweep, teleported, and read back there",
          moved_actor.place((0.0, 0.0, 0.0), mark()) == "moved" and spawner.at == (0.0, 0.0, 0.0)
          and journal == ["announced", ("move", "OakSpawner_Camp", 0.0)]
          and spawner.calls == [{"sweep": False, "hit": "HitResult", "teleport": True}]
          and moved_actor.where() == (0.0, 0.0, 0.0))
    check("and put back where it stood",
          moved_actor.put_back(mark()) == "restored" and spawner.at == (7000.0, 0.0, 50.0))
    spawner.freed = True
    check("an actor gone has no place", moved_actor.where() is None)
    check("each is read by its own function: a zone read as an actor, or an actor as a zone, has no place",
          zone_shift.Shift(fixture.zone("z", HOME), actor=True).home is None
          and zone_shift.Shift(fixture.spawner("s", HOME)).home is None)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
