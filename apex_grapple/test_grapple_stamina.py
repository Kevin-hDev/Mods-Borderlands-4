"""Tests what the traversal reserve changes for a shot: it costs, or it does not fire and the key is kept."""

import sys

from grapple_fixture import check, fails, fresh, grapple, settings, state  # noqa: F401
import stamina_fixture
from apex_grapple import report, stamina

library = stamina_fixture.install(stamina)


def shot(cost: float, left: float) -> tuple:
    """A fresh rope, a reserve at `left`, one press: (key taken, hook away, what the game was asked to take)."""
    settings.stamina_cost.value = cost
    library.value, library.taken = left, []
    player, rope = fresh(on_ground=False)
    taken = rope.fire(player, 0)
    return taken, rope.state == grapple.FLYING, list(library.taken)


check("a full reserve fires and pays its share", shot(33.0, 100.0) == (True, True, [-33.0]))
check("the last third still fires", shot(33.0, 33.0) == (True, True, [-33.0]))
check("too little keeps the key and fires nothing, so the key does not punch instead",
      shot(33.0, 32.0) == (True, False, []))
check("an empty reserve fires nothing", shot(33.0, 0.0) == (True, False, []))
check("at no cost a shot fires on an empty reserve and takes nothing", shot(0.0, 0.0) == (True, True, []))
check("the refusal is written in the log, once per press",
      sum("not enough stamina" in line for line in state["misc"]) == 2)

library.failing = True
state["errors"].clear()
check("a reserve the game will not read never blocks a shot", shot(33.0, 100.0) == (True, True, []))
check("and the failure is said once", len(state["errors"]) == 1)

settings.stamina_cost.value = settings.stamina_cost.default_value
report.reset()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
