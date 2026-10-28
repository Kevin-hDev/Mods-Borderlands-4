"""Test reserve transactions: costs, empty bars, upgrades and SDK failures."""

import sys
import sdk_stubs

state = sdk_stubs.install()
import stamina_fixture
from apex_grapple import report, stamina

fails = []


def check(label, condition):
    print(("OK    " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


library = stamina_fixture.install(stamina)
character = object()
handle = stamina.handle()
check("resource handle uses the native parameter type",
      handle.kind == stamina_fixture.TYPE_HANDLE and handle.name == stamina_fixture.POOL)
before = library.reads
stamina.handle()
check("value handle is reused", library.reads == before)
check("full reserve is read", stamina.reserve(character) == (100, 100))
check("full reserve pays once", stamina.try_spend(character, 33)
      and library.value == 67 and library.taken == [-33])

library.value = 33
library.taken.clear()
check("exact cost is accepted", stamina.try_spend(character, 33)
      and library.value == 0 and library.taken == [-33])
library.value = 32
library.taken.clear()
check("insufficient reserve is not charged", not stamina.try_spend(character, 33) and not library.taken)
library.maximum, library.value = 120, 60
check("upgraded maximum comes from this character", stamina.reserve(character) == (60, 120))
check("cost follows the upgraded maximum", stamina.try_spend(character, 33)
      and abs(library.taken[-1] + 39.6) < 0.001)

library.value = 0
library.taken.clear()
stamina.forget()
check("empty reserve needs no cached maximum", stamina.reserve(character) == (0, 0))
check("first empty read refuses a paid shot", not stamina.try_spend(character, 33) and not library.taken)
before = library.reads
check("zero cost ignores the empty pool", stamina.try_spend(character, 0)
      and not library.taken and library.reads == before)

library.failing = True
state["errors"].clear()
check("unreadable reserve stays permissive", stamina.try_spend(character, 33) and not library.taken)
stamina.try_spend(character, 33)
check("read failure is reported once", len(state["errors"]) == 1
      and "Stamina could not be read" in state["errors"][0])
library.failing = False
library.maximum, library.value = 100, 100
check("a later successful read recovers", stamina.try_spend(character, 33) and library.taken == [-33])

original_adjust = library.AdjustResourcePoolValue
library.taken.clear()
library.value = 100
report.reset()
state["errors"].clear()


def refused(*args):
    raise RuntimeError("private engine details")


library.AdjustResourcePoolValue = refused
check("failed debit refuses permission", not stamina.try_spend(character, 33) and not library.taken)
stamina.try_spend(character, 33)
check("write failure is generic and reported once", len(state["errors"]) == 1
      and "Stamina could not be spent" in state["errors"][0]
      and "private engine details" not in state["errors"][0])
library.AdjustResourcePoolValue = original_adjust
check("a later successful debit recovers", stamina.try_spend(character, 33) and library.taken == [-33])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
