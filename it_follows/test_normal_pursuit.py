"""Tests the level's long chase (normal/pursuit.py): an enemy's zone widened to 350 m once for all its camp; a zone
already as wide, and an enemy without a zone, left alone; a zone that cannot be written left to the game; a zone the
game loaded again widened again; the zones held bounded; the stop gives each radius back, a zone gone owes nothing."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows.normal import pursuit  # noqa: E402
from it_follows.seen import Seen  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def zone(path: str, radius_cm: float) -> types.SimpleNamespace:
    return types.SimpleNamespace(settings=types.SimpleNamespace(CombatTerritory=types.SimpleNamespace(
        Radius=radius_cm)), _path_name=lambda: path, freed=False)


def seen(name: str, area: types.SimpleNamespace | None) -> Seen:
    radius_m = area.settings.CombatTerritory.Radius / 100.0 if area is not None else 0.0
    return Seen(None, name, "Char_Enemy", area, area._path_name() if area is not None else "", None, radius_m, None)


def radius(area: types.SimpleNamespace) -> float:
    return area.settings.CombatTerritory.Radius


try:
    announced: list[tuple[str, dict]] = []
    chase = pursuit.Pursuit(lambda call, log=True, **f: announced.append((call, {"log": log, **f})), 350.0)
    camp = zone("/Game/Maps/Zone_Camp", 4000.0)
    check("an enemy's zone widened to 350 m, announced without a line", chase.widen(seen("Char_A", camp)) == "widened"
          and radius(camp) == 35000.0 and announced == [("CombatTerritory.Radius",
                                                         {"log": False, "zone": "/Game/Maps/Zone_Camp"})])
    check("once for all its camp", chase.widen(seen("Char_B", camp)) == "already" and len(announced) == 1)
    wide = zone("/Game/Maps/Zone_Wide", 60000.0)
    check("a zone already as wide left alone", chase.widen(seen("Char_C", wide)) == "wide_enough"
          and radius(wide) == 60000.0)
    check("an enemy without a zone", chase.widen(seen("Char_D", None)) == "no_zone")
    broken = zone("/Game/Maps/Zone_Broken", float("nan"))
    check("a zone that cannot be written left to the game",
          chase.widen(seen("Char_E", broken)).startswith("failed:") and chase.widened() == 1)
    camp.freed = True
    loaded = zone("/Game/Maps/Zone_Camp", 4000.0)
    check("a zone the game loaded again widened again", chase.widen(seen("Char_F", loaded)) == "widened"
          and radius(loaded) == 35000.0 and chase.widened() == 1)
    pursuit.MOST = len(chase.zones)
    check("the zones held bounded", chase.widen(seen("Char_G", zone("/Game/Maps/Zone_New", 4000.0))) == "full")
    loaded.freed = True
    new = zone("/Game/Maps/Zone_New", 4000.0)
    check("a zone the game freed is forgotten, its room given to a new one",
          chase.widen(seen("Char_G", new)) == "widened"
          and "/Game/Maps/Zone_Camp" not in chase.zones and len(chase.zones) == pursuit.MOST)
    other = zone("/Game/Maps/Zone_Other", 3000.0)
    pursuit.MOST = 256
    chase.widen(seen("Char_H", other))
    other.freed = True
    check("the stop: each radius given back, a zone gone owes nothing",
          chase.narrow() == {"restored": 1, "gone": 1} and radius(new) == 4000.0 and chase.zones == {})
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
