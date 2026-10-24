"""Tests what a census does after its first part (normal/arrivals.py): an enemy waiting holds weak pointers only, its
other fields kept; met with its objects of now while the game says it alive; gone, dead or unsaid, it is not met; its
zone freed, it is met without it; a part does the new first, nearest first, then the held, one at least, until
PART_S passed; a new start replaces what the last left; clear leaves nothing."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows.normal import arrivals  # noqa: E402
from it_follows.seen import Seen  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def body(name: str, dead: object = False) -> types.SimpleNamespace:
    return types.SimpleNamespace(Name=name, freed=False, HealthState=types.SimpleNamespace(bCurrentlyDead=dead))


def seen(actor: object, zone: object = None) -> Seen:
    return Seen(actor, actor.Name, "Char_Enemy", zone, "/Game/Zone" if zone is not None else "", (0.0, 0.0, 0.0),
                40.0, (100.0, 0.0, 0.0))


try:
    area = types.SimpleNamespace(freed=False)
    one = body("Char_One")
    waiting = arrivals.Waiting.of(seen(one, area))
    check("waiting: weak pointers only, its other fields kept", waiting.seen.actor is None and waiting.seen.zone is None
          and waiting.seen.name == "Char_One" and waiting.seen.radius_m == 40.0 and waiting.actor() is one)
    now = waiting.now()
    check("met with its objects of now", now.actor is one and now.zone is area and now.zone_path == "/Game/Zone")
    area.freed = True
    check("its zone freed: met without it", waiting.now().zone is None and waiting.now().actor is one)
    for label, change in (("dead", lambda: setattr(one.HealthState, "bCurrentlyDead", True)),
                          ("its death unsaid", lambda: setattr(one.HealthState, "bCurrentlyDead", None)),
                          ("gone", lambda: setattr(one, "freed", True))):
        one = body("Char_One")
        waiting = arrivals.Waiting.of(seen(one))
        change()
        check(f"{label}: not met", waiting.now() is None)

    done: list[str] = []
    clock = {"now": 0.0}

    def arrive(found: Seen) -> None:
        done.append(f"met:{found.name}")
        clock["now"] += 0.002

    def keep(held: str) -> None:
        done.append(f"kept:{held}")
        clock["now"] += 0.001

    parts = arrivals.Arrivals(arrive, keep, lambda: clock["now"])
    check("nothing yet: nothing pending", not parts.pending())
    dead = body("Char_Dead", True)
    parts.start([seen(body("Char_Near")), seen(dead), seen(body("Char_Far"))], ["Char_Held_1", "Char_Held_2"])
    parts.part()
    check("a part: one at least, until PART_S passed (3 ms)", done == ["met:Char_Near", "met:Char_Far"]
          and parts.gone == 1 and parts.pending())
    parts.part()
    check("the new first, then the held", done[2:] == ["kept:Char_Held_1", "kept:Char_Held_2"] and not parts.pending())
    clock["now"] = 0.0
    done.clear()
    slow = arrivals.Arrivals(lambda found: (done.append(found.name), clock.__setitem__("now", clock["now"] + 0.01)),
                             keep, lambda: clock["now"])
    slow.start([seen(body("Char_Slow_1")), seen(body("Char_Slow_2"))], [])
    slow.part()
    check("one longer than PART_S: alone in its part", done == ["Char_Slow_1"] and slow.pending())
    slow.start([seen(body("Char_Fresh"))], ["Char_Held"])
    check("a new start replaces what the last left", len(slow.waiting) == 1 and list(slow.held) == ["Char_Held"]
          and slow.gone == 0)
    slow.clear()
    check("cleared: nothing pending", not slow.pending())
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
