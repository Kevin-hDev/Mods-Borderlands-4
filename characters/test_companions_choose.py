"""Tests the choice of the character to follow (choose.py): without a spawner, the nearest living one of the
definition within NEAR_M, its zone read; given a spawner, the living one of the definition within NEAR_M whose zone
that spawner owns, even if another stands nearer; none: why, nothing followed; the zone read only for the
definition's living ones near."""

import pathlib
import sys
import types
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("follow_choose_under_test", HERE / "characters" / "companions" / "choose.py")
choose_module = util.module_from_spec(spec)
spec.loader.exec_module(choose_module)

FRAME = "Char_TedioreFrame_NoVacancy_Side"


class Character:
    def __init__(self, name: str, x: float, owner: str | None, definition: str = FRAME, dead: bool = False) -> None:
        self.Name, self.x, self.owner, self.definition, self.dead = name, x, owner, definition, dead


read = types.SimpleNamespace(
    definition=lambda actor: actor.definition, dead=lambda actor: actor.dead, place=lambda actor: (actor.x, 0.0, 0.0),
    metres=lambda a, b: None if a is None or b is None else abs(a[0] - b[0]) / 100.0)
asked: list[str] = []


def zone_of(actor: Character) -> tuple:
    asked.append(actor.Name)
    if actor.owner is None:
        return None, "none"
    return f"zone of {actor.Name}", f"GbxTerritoryComponent:Territory owned by OakSpawner:{actor.owner}"


here = (0.0, 0.0, 0.0)
older = Character("Frame_old", 330.0, "OakSpawner_2147302639")
newer = Character("Frame_new", 1500.0, "OakSpawner_2147290804")
other = Character("Crankus", 100.0, "OakSpawner_2147290804", definition="Char_Crankus")
dead = Character("Frame_dead", 200.0, "OakSpawner_2147290804", dead=True)
far = Character("Frame_far", 6100.0, "OakSpawner_2147290804")
world = [other, dead, older, far, newer]

check("without a spawner: the nearest living one, its zone read", choose_module.choose(
      world, read, zone_of, FRAME, here, None) == (older, "zone of Frame_old",
                                                   "GbxTerritoryComponent:Territory owned by OakSpawner:"
                                                   "OakSpawner_2147302639"))
asked.clear()
check("given its spawner: the one it bore, though an older one stands nearer", choose_module.choose(
      world, read, zone_of, FRAME, here, "OakSpawner_2147290804")[0] is newer)
check("the zone read only for the definition's living ones near", asked == ["Frame_old", "Frame_new"])
check("a spawner's name is matched whole", choose_module.choose(
      world, read, zone_of, FRAME, here, "OakSpawner_214729080")[0] is None)
check("born of a spawner but beyond NEAR_M: none, why", choose_module.choose(
      [far], read, zone_of, FRAME, here, "OakSpawner_2147290804") == (
      None, None, f"no living {FRAME} born of OakSpawner_2147290804 within 60 m"))
check("a living one without a zone: passed over", choose_module.choose(
      [Character("Frame_bare", 100.0, None)], read, zone_of, FRAME, here, "OakSpawner_2147290804")[0] is None)
check("without a spawner and none near: none, why", choose_module.choose(
      [far, dead, other], read, zone_of, FRAME, here, None) == (
      None, None, f"no living {FRAME} within 60 m: spawn it first"))
check("a zone owned by another kind of spawner of that name: passed over", choose_module.choose(
      [Character("Frame_odd", 100.0, None)], read,
      lambda actor: ("zone", "Territory owned by OtherOakSpawner:OakSpawner_2147290804"), FRAME, here,
      "OakSpawner_2147290804")[0] is None)
check("no zone, whatever its text says: passed over", choose_module.choose(
      [Character("Frame_odd", 100.0, None)], read,
      lambda actor: (None, "error:x owned by OakSpawner:OakSpawner_2147290804"), FRAME, here,
      "OakSpawner_2147290804")[0] is None)
check("NEAR_M itself counts", choose_module.nearest([Character("Edge", 6000.0, None)], read, FRAME, here).Name
      == "Edge" and choose_module.born_of([Character("Edge", 6000.0, "OakSpawner_1")], read, zone_of, FRAME, here,
                                          "OakSpawner_1")[0].Name == "Edge")
check("without a spawner: a near one without a zone given with none", choose_module.choose(
      [Character("Frame_bare", 100.0, None)], read, zone_of, FRAME, here, None)[1:] == (None, "none"))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
