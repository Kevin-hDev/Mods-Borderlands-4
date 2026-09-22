"""A shot must pay before starting, including the first read of an empty pool."""

import sys

from grapple_fixture import check, fails, fresh, settings, state
import stamina_fixture
from apex_grapple import report, stamina

pool = stamina_fixture.install(stamina)
settings.stamina_cost.value = 33


def fire_with(left):
    player, rope = fresh(on_ground=False)
    pool.value = left
    pool.taken.clear()
    state["audio_calls"].clear()
    accepted = rope.fire(player, 0)
    return accepted, rope


stamina.forget()
accepted, rope = fire_with(0)
check("cold empty reserve keeps the key without firing", accepted and not rope.busy)
check("cold empty reserve starts no effects and charges nothing",
      not state["audio_calls"] and not pool.taken)

original_adjust = pool.AdjustResourcePoolValue


def refused_write(*args):
    raise RuntimeError("private engine details")


pool.AdjustResourcePoolValue = refused_write
report.reset()
state["errors"].clear()
accepted, rope = fire_with(100)
check("failed charge keeps the key and refuses the shot", accepted and not rope.busy)
check("failed charge starts no sound and changes no reserve",
      not state["audio_calls"] and pool.value == 100 and not pool.taken)
check("failed charge does not expose engine details",
      not any("private engine details" in line for line in state["errors"]))
pool.AdjustResourcePoolValue = original_adjust
accepted, rope = fire_with(100)
check("the next successful charge fires once", accepted and rope.busy and pool.taken == [-33])
rope.reset()

# One value/percentage pair per paid shot, instead of separate eligibility and cost reads.
counts = {"value": 0, "share": 0}
original_value = pool.GetResourcePoolValue
original_share = pool.GetResourcePoolPercent


def read_value(*args):
    counts["value"] += 1
    return original_value(*args)


def read_share(*args):
    counts["share"] += 1
    return original_share(*args)


pool.GetResourcePoolValue = read_value
pool.GetResourcePoolPercent = read_share
accepted, rope = fire_with(100)
check("one reserve snapshot per paid shot", counts == {"value": 1, "share": 1})
check("one debit per paid shot", accepted and rope.busy and pool.taken == [-33])
rope.reset()

pool.failing = True
accepted, rope = fire_with(100)
check("unreadable reserve still allows the shot by design", accepted and rope.busy and not pool.taken)
rope.reset()
pool.failing = False
settings.stamina_cost.value = 0
stamina.forget()
accepted, rope = fire_with(0)
check("zero cost still allows an empty-bar shot", accepted and rope.busy and not pool.taken)
rope.reset()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(bool(fails))
