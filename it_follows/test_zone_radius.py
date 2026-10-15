"""Tests the writer of the lent zone's combat radius: the radius written and read back, the one the zone had said, and
written back once; never over a radius the game changed meanwhile, nor on another zone; a radius outside 1 m to 1 km,
asked or found on the zone, refused before anything is written; a write the game does not keep undone and refused; a
second write refused while the first holds; a write back that fails, or a zone that cannot be read, said so."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import zone_radius  # noqa: E402
from it_follows.zone_radius import TerritoryRadiusPatch  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def territory(path: str = "/Game/Test.Territory", radius: object = 5200.0) -> object:
    target = types.SimpleNamespace(settings=types.SimpleNamespace(CombatTerritory=types.SimpleNamespace(Radius=radius)))
    target._path_name = lambda: path
    return target


def radius(target: object) -> object:
    return target.settings.CombatTerritory.Radius


def refused(error: type, act: object) -> bool:
    try:
        act()
    except error:
        return True
    return False


class Area:
    """A combat area whose writes the game may turn down: past keep_cm it keeps keep_cm; from the fail_from-th write on,
    the write raises."""

    def __init__(self, value: float, keep_cm: float = math.inf, fail_from: int = 0) -> None:
        self.value, self.keep_cm, self.fail_from, self.writes = value, keep_cm, fail_from, 0

    @property
    def Radius(self) -> float:
        return self.value

    @Radius.setter
    def Radius(self, value: float) -> None:
        self.writes += 1
        if self.fail_from and self.writes >= self.fail_from:
            raise RuntimeError("refused")
        self.value = min(value, self.keep_cm)


try:
    target, patch = territory(), TerritoryRadiusPatch(60000.0)
    check("the radius is written, read back, and the one the zone had said",
          patch.apply(target) == 5200.0 and radius(target) == 60000.0
          and patch.saved == ("/Game/Test.Territory", 5200.0))
    check("the zone's own radius is written back", patch.restore(target) == "restored" and radius(target) == 5200.0)
    check("only once", patch.restore(target) == "inactive" and radius(target) == 5200.0)
    check("nothing written, nothing to write back", TerritoryRadiusPatch(60000.0).restore(territory()) == "inactive")

    target, patch = territory(), TerritoryRadiusPatch(60000.0)
    patch.apply(target)
    target.settings.CombatTerritory.Radius = 70000.0
    check("a radius the game changed meanwhile is left as the game set it",
          patch.restore(target) == "ownership_lost" and radius(target) == 70000.0)

    target, patch = territory(), TerritoryRadiusPatch(60000.0)
    patch.apply(target)
    elsewhere = territory("/Game/Other.Territory", 60000.0)
    check("another zone is never written back, even holding the radius written",
          patch.restore(elsewhere) == "different_territory" and radius(elsewhere) == 60000.0
          and radius(target) == 60000.0)

    target, patch = territory(), TerritoryRadiusPatch(60000.0)
    patch.apply(target)
    check("a second write while the first holds is refused, the radius left as written",
          refused(RuntimeError, lambda: patch.apply(target)) and radius(target) == 60000.0)
    check("a zone that cannot be read when written back says so", patch.restore(None) == "unavailable")

    check("a radius asked that is not a number, or outside 1 m to 1 km, is refused",
          refused(ValueError, lambda: TerritoryRadiusPatch(float("nan")))
          and refused(ValueError, lambda: TerritoryRadiusPatch(2_000_000.0))
          and refused(ValueError, lambda: TerritoryRadiusPatch(100_001.0))
          and refused(ValueError, lambda: TerritoryRadiusPatch(99.0)))
    check("1 m and 1 km are taken", TerritoryRadiusPatch(100.0).target == zone_radius.MIN_RADIUS_CM
          and TerritoryRadiusPatch(100_000.0).target == zone_radius.MAX_RADIUS_CM)
    for found in (-1.0, 0.0, 99.0, 100_001.0):
        target, patch = territory(radius=found), TerritoryRadiusPatch(60000.0)
        check(f"a zone found with a radius of {found} cm is refused, nothing written",
              refused(ValueError, lambda: patch.apply(target)) and radius(target) == found and patch.saved is None)
    for label, target in (("not finite", territory(radius=math.inf)), ("not a number", territory(radius="x")),
                          ("unreadable", types.SimpleNamespace(settings=None, _path_name=lambda: "/Game/T.T"))):
        check(f"a zone whose radius is {label} is refused through reads.zone_radius_cm",
              refused(ValueError, lambda: TerritoryRadiusPatch(60000.0).apply(target)))
    nameless = territory()
    del nameless._path_name
    check("a zone without a path is refused, nothing written",
          refused(ValueError, lambda: TerritoryRadiusPatch(60000.0).apply(nameless)) and radius(nameless) == 5200.0)

    target = territory()
    target.settings.CombatTerritory = Area(5200.0, keep_cm=50000.0)
    patch = TerritoryRadiusPatch(60000.0)
    check("a write the game does not keep is refused, the zone's own radius written back first",
          refused(RuntimeError, lambda: patch.apply(target)) and radius(target) == 5200.0 and patch.saved is None
          and patch.restore(target) == "inactive")

    target = territory()
    target.settings.CombatTerritory = Area(5200.0, fail_from=2)
    patch = TerritoryRadiusPatch(60000.0)
    patch.apply(target)
    check("a write back that fails says so", patch.restore(target) == "restore_failed" and radius(target) == 60000.0)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
