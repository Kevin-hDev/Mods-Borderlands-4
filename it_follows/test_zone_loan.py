"""Tests the zone lent to an enemy and given back: which zone it holds by path; the loan announced before its call and
read back; a lent zone already gone is never passed on; the own zone given back only while the lent one is still held,
never on a reused body, without the enemy or its zone; a give-back that does not take, or fails, says so; an enemy lent
the zone it holds (trial 6i), or holding none (trial 6r)."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import zone_fixture  # noqa: E402

fixture = zone_fixture.Fixture(state)
journal = fixture.journal

from it_follows import zone_loan  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def mark(word: str = "announced") -> object:
    return lambda: journal.append(word)


def sets() -> int:
    return sum(entry[0] == "set" for entry in journal if isinstance(entry, tuple))


own = fixture.zone("home", (18000.0, 0.0, 0.0))
lent = fixture.zone("camp", (2000.0, 0.0, 0.0))
other = fixture.zone("else", (0.0, 0.0, 0.0))


def lent_to() -> tuple:
    """The lent zone as the hunter zone hands it: its weak pointer and its path."""
    return sdk_stubs.FakeWeak(lent), lent.path


def new_loan() -> tuple:
    journal.clear()
    for zone in (own, lent, other):
        zone.freed = False
    enemy = fixture.enemy("cat", own)
    return zone_loan.Loan(fixture.seen("cat", own, enemy), *lent_to()), enemy


try:
    loan, enemy = new_loan()
    check("the loan knows both zones", loan.target() is lent and loan.own() is own and loan.home == "own")
    check("the zone held reads none, target, own or other",
          [loan.held(zone) for zone in (None, lent, own, other)] == ["none", "target", "own", "other"])
    taken = loan.lend(enemy, mark())
    check("the loan is announced before its call, then read back",
          taken == "target" and enemy.zone is lent and journal == ["announced", ("set", "cat", "camp")])
    check("the own zone is given back while the lent one is held, announced first",
          loan.give_back(enemy, False, mark("announced back")) == "restored" and enemy.zone is own
          and journal[-2:] == ["announced back", ("set", "cat", "home")])
    check("an enemy back home is left as it is", loan.give_back(enemy, False, mark()) == "already_home" and sets() == 2)
    enemy.zone = other
    check("a zone the game gave meanwhile is not undone", loan.give_back(enemy, False, mark()) == "left_alone"
          and enemy.zone is other and sets() == 2)

    loan, enemy = new_loan()
    lent.freed = True
    check("a lent zone already gone is never passed on", loan.lend(enemy, mark()) == "unavailable"
          and journal == [] and enemy.zone is own)

    loan, enemy = new_loan()
    enemy.refuse = True
    check("a zone the enemy did not take reads its own", loan.lend(enemy, mark()) == "own")

    loan, enemy = new_loan()
    enemy.fail = True
    try:
        loan.lend(enemy, mark())
        raised = False
    except RuntimeError:
        raised = True
    check("a failing loan call raises to the run, announced first", raised and journal[0] == "announced")

    loan, enemy = new_loan()
    loan.lend(enemy, mark())
    journal.clear()
    check("nothing is given back on a body the game reuses",
          loan.give_back(enemy, True, mark()) == "not_needed" and journal == [] and enemy.zone is lent)
    check("without the enemy nothing is given back", loan.give_back(None, False, mark()) == "unavailable"
          and journal == [])
    own.freed = True
    check("without the own zone nothing is given back", loan.give_back(enemy, False, mark()) == "unavailable"
          and enemy.zone is lent and journal == [])
    own.freed = False
    enemy.refuse = True
    check("a give-back that does not take says so", loan.give_back(enemy, False, mark()) == "restore_failed"
          and enemy.zone is lent)
    enemy.refuse, enemy.fail = False, True
    check("a failing give-back says its error", loan.give_back(enemy, False, mark()) == "restore_error:RuntimeError")

    journal.clear()
    enemy = fixture.enemy("cat", lent)
    loan = zone_loan.Loan(fixture.seen("cat", lent, enemy), *lent_to())
    check("trial 6i: an enemy lent the zone it holds is lent nothing, no call, and reads the lent zone",
          loan.lend(enemy, mark()) == "target" and journal == [])
    check("and is given nothing back, no call", loan.give_back(enemy, False, mark()) == "its_own"
          and journal == [] and enemy.zone is lent)
    check("on a body the game reuses, nothing either", loan.give_back(enemy, True, mark()) == "not_needed")

    journal.clear()
    enemy = fixture.enemy("bat", None)
    loan = zone_loan.Loan(fixture.seen("bat", None, enemy), *lent_to())
    check("trial 6r: an enemy without a zone is lent the zone, announced first",
          loan.homeless and loan.home == "none" and loan.lend(enemy, mark()) == "target"
          and journal == ["announced", ("set", "bat", "camp")])
    check("and given back none, announced first, as the game had it",
          loan.give_back(enemy, False, mark("announced back")) == "restored" and enemy.zone is None
          and journal[-2:] == ["announced back", ("set", "bat", None)])
    check("back without a zone, it is left as it is", loan.give_back(enemy, False, mark()) == "already_home"
          and sets() == 2)
    enemy.zone = lent
    enemy.refuse = True
    check("a give-back of none that does not take says so", loan.give_back(enemy, False, mark()) == "restore_failed")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
