"""Tests when a key asks for the weapon to be put away: once at the press, or once when held long enough."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


heirloom_stubs.install()

from apex_heirloom.key_press import HOLD, LATE_S, PRESS, KeyWatch  # noqa: E402

HOLD_S = 0.4

watch = KeyWatch()
check("press mode: the press asks at once", watch.event("IE_Pressed", 1.0, PRESS) is True)
check("press mode: a frame asks nothing more", watch.tick(2.0, PRESS, HOLD_S) is False)
check("press mode: the key's repeats ask nothing", watch.event("IE_Repeat", 1.5, PRESS) is False)
check("press mode: the release asks nothing", watch.event("IE_Released", 2.0, PRESS) is False)

watch = KeyWatch()
check("hold mode: the press asks nothing yet", watch.event("IE_Pressed", 1.0, HOLD) is False)
check("hold mode: held less than the hold time, nothing", watch.tick(1.3, HOLD, HOLD_S) is False)
check("hold mode: held the hold time, it asks", watch.tick(1.41, HOLD, HOLD_S) is True)
check("hold mode: held on, it asks only once", watch.tick(1.6, HOLD, HOLD_S) is False)
watch.event("IE_Released", 1.7, HOLD)
check("hold mode: released, nothing more", watch.tick(2.5, HOLD, HOLD_S) is False)

watch = KeyWatch()
watch.event("IE_Pressed", 1.0, HOLD)
watch.event("IE_Released", 1.2, HOLD)
check("hold mode: a short press asks nothing (Square reloads on it)", watch.tick(1.5, HOLD, HOLD_S) is False)

watch = KeyWatch()
watch.event("IE_Pressed", 1.0, HOLD)
watch.event("IE_Repeat", 1.3, HOLD)
check("hold mode: the key's repeats do not restart the count", watch.tick(1.41, HOLD, HOLD_S) is True)

watch = KeyWatch()
watch.event("IE_Pressed", 1.0, HOLD)
watch.event("IE_Pressed", 5.0, HOLD)
check("a press after a missed release starts afresh", watch.tick(5.2, HOLD, HOLD_S) is False)
check("... and asks once held again long enough", watch.tick(5.4, HOLD, HOLD_S) is True)

watch = KeyWatch()
watch.event("IE_Pressed", 1.0, HOLD)
check("a first frame long after the hold time asks nothing (the release may have been missed)",
      watch.tick(1.0 + HOLD_S + LATE_S + 0.1, HOLD, HOLD_S) is False)
check("... and the key is forgotten", watch.pending() is False)

watch = KeyWatch()
watch.event("IE_Pressed", 1.0, HOLD)
check("a key held toward the hold time is pending", watch.pending() is True)
watch.forget()
check("forgotten, it is no longer pending", watch.pending() is False)
check("forgotten, it asks nothing", watch.tick(1.5, HOLD, HOLD_S) is False)

watch = KeyWatch()
watch.event("IE_Pressed", 1.0, PRESS)
check("press mode: nothing is pending after the press", watch.pending() is False)

watch = KeyWatch()
watch.event("IE_Pressed", 1.0, PRESS)
watch.event("IE_Released", 1.1, PRESS)
check("press mode: a mouse button's second quick click, a double click, asks again",
      watch.event("IE_DoubleClick", 1.2, PRESS) is True)
watch = KeyWatch()
watch.event("IE_Pressed", 1.0, HOLD)
watch.event("IE_Released", 1.1, HOLD)
watch.event("IE_DoubleClick", 1.2, HOLD)
check("hold mode: a double click held on asks once the hold time is reached", watch.tick(1.61, HOLD, HOLD_S) is True)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
