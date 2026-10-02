"""Tests the beam's own energy: drained by firing, back after a delay, shut while a key is held with the beam off."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import reserve  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(found: float, wanted: float) -> bool:
    return abs(found - wanted) < 1e-6


energy = reserve.Reserve()
check("the reserve starts full and ready", energy.left == 100.0 and energy.can_fire())
energy.spend(2.0, 20.0)
check("firing drains it", near(energy.left, 60.0) and energy.can_fire())
energy.rest(1.0, 25.0, 2.0, key_held=False)
check("it does not refill before the delay", near(energy.left, 60.0))
energy.rest(1.0, 25.0, 2.0, key_held=False)
check("it refills once the delay has passed", near(energy.left, 85.0))
energy.rest(5.0, 25.0, 2.0, key_held=False)
check("it never holds more than its maximum", energy.left == 100.0)
energy.spend(0.5, 20.0)
energy.rest(1.0, 25.0, 2.0, key_held=False)
check("firing again restarts the delay", near(energy.left, 90.0))

energy.spend(10.0, 20.0)
check("it empties at zero, never under", energy.left == 0.0 and not energy.can_fire())
energy.rest(3.0, 25.0, 2.0, key_held=True)
check("emptied, it refills but stays shut while the key is held", energy.left > 0.0 and not energy.can_fire())
energy.rest(0.1, 25.0, 2.0, key_held=False)
check("letting the key go opens it again", energy.can_fire())

endless = reserve.Reserve()
endless.spend(1000.0, 0.0)
check("a drain of zero never runs out", endless.left == 100.0 and endless.can_fire())
endless.spend(-5.0, 20.0)
endless.rest(-5.0, 25.0, 0.0, key_held=False)
check("a negative time changes nothing", endless.left == 100.0)

low = reserve.Reserve()
low.left = 3.0
check("a shot begins only if the reserve can pay what it is asked; one already lit goes on to the last of the energy",
      not low.can_fire(4.0) and low.can_fire(3.0) and low.can_fire())
full = reserve.Reserve()
full.rest(0.1, 25.0, 2.0, key_held=True)
check("a key held while the beam is off shuts even a full reserve: a shot begins at a press", not full.can_fire())
full.rest(0.1, 25.0, 2.0, key_held=False)
check("until the key is let go", full.can_fire())
empty = reserve.Reserve()
empty.spend(10.0, 20.0)
empty.rest(0.1, 25.0, 2.0, key_held=False)
check("an emptied reserve whose key was let go is open, with nothing to fire", not empty.shut and not empty.can_fire())

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
