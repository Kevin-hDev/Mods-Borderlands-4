"""Tests which vehicle the player drives: none before a player, on foot or while loading; the pawn at the wheel."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


sdk_stubs.install()

from vehicle_driving import seat  # noqa: E402

check("before a player exists, no vehicle", seat.driven_vehicle(None) is None)
check("while loading, no pawn and no vehicle", seat.driven_vehicle(types.SimpleNamespace(Pawn=None)) is None)
on_foot = types.SimpleNamespace(Pawn=types.SimpleNamespace(Name="OakCharacter_1"))
check("on foot, no vehicle", seat.driven_vehicle(on_foot) is None)
car = sdk_stubs.Vehicle()
check("at the wheel, the vehicle", seat.driven_vehicle(types.SimpleNamespace(Pawn=car)) is car)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
