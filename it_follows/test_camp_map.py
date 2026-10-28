"""Tests the camps of the horde's enemies: an enemy's camp is the spawner its own zone is part of, kept once per spawner
by name, cleaned, held through a weak pointer; a zone without a spawner, or whose spawner cannot be read, gives no
camp; a camp forgotten is noted again with an enemy of it; an enemy that left the horde is forgotten, and 10 000 enemies
through the horde leave no more than it holds."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import zone_fixture  # noqa: E402

fixture = zone_fixture.Fixture(state)

from it_follows.camp_map import CampMap  # noqa: E402

fails: list[str] = []
CAMP = "OakSpawner_UAID_04922658D4A7E9B701_2107469469"


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Nameless:
    """A spawner whose name the game cannot give to Python."""

    SpawnerComponent = types.SimpleNamespace()

    @property
    def Name(self) -> str:
        raise RuntimeError("unreadable")


try:
    camps = CampMap()
    camp = fixture.spawner(CAMP, (12345.0, 0.0, 0.0))
    check("an enemy's camp is the spawner its zone is part of, said by its name",
          camps.add("Char_CatYoung_1", fixture.zone_of(camp)) == CAMP
          and camps.add("Char_CatAdult_2", fixture.zone_of(camp)) == CAMP)
    check("two enemies of one camp make one camp", list(camps.spawners) == [CAMP]
          and camps.of == {"Char_CatYoung_1": CAMP, "Char_CatAdult_2": CAMP})
    check("its spawner is held through a weak pointer", camps.spawners[CAMP]() is camp)
    check("a zone without an outer, or whose outer is no spawner, gives no camp",
          camps.add("Char_A", types.SimpleNamespace()) is None
          and camps.add("Char_B", types.SimpleNamespace(Outer=types.SimpleNamespace(Name="PersistentLevel"))) is None
          and "Char_A" not in camps.of and "Char_B" not in camps.of and len(camps.spawners) == 1)
    check("a spawner whose name cannot be read gives no camp",
          camps.add("Char_C", types.SimpleNamespace(Outer=Nameless())) is None and "Char_C" not in camps.of)
    odd = fixture.spawner("Oak\r\nSpawner_" + "x" * 300, (0.0, 0.0, 0.0))
    check("a camp's name is cleaned of line breaks and cut",
          camps.add("Char_D", fixture.zone_of(odd)) == "OakSpawner_" + "x" * 189)
    camp.freed = True
    check("a camp the game no longer holds reads nothing", camps.spawners[CAMP]() is None)
    camp.freed = False

    camps.forget("OakSpawner_" + "x" * 189)
    camps.forget("OakSpawner_Never_Seen")
    forgotten = "OakSpawner_" + "x" * 189 not in camps.spawners and camps.of["Char_D"] == "OakSpawner_" + "x" * 189
    camps.add("Char_D_2", fixture.zone_of(odd))
    check("a camp forgotten is no longer noted, its enemies' camp kept, and noted again with an enemy of it",
          forgotten and "OakSpawner_" + "x" * 189 in camps.spawners and len(camps.spawners) == 2)

    camps.forget_enemy("Char_CatYoung_1")
    check("an enemy that left the horde is forgotten, its camp still noted for the others",
          "Char_CatYoung_1" not in camps.of and camps.of["Char_CatAdult_2"] == CAMP and CAMP in camps.spawners)
    before = dict(camps.of)
    camps.forget_enemy("Char_Nobody")
    check("forgetting an enemy never noted changes nothing", camps.of == before)

    crowd, spawner = CampMap(), fixture.spawner("OakSpawner_Crowd", (0.0, 0.0, 0.0))
    for number in range(10_000):
        crowd.add(f"Char_Cat_{number}", fixture.zone_of(spawner))
        if number >= 25:
            crowd.forget_enemy(f"Char_Cat_{number - 25}")
    check("10 000 enemies through a horde of 25, each forgotten when it leaves: no more than 25 kept",
          len(crowd.of) == 25 and "Char_Cat_9999" in crowd.of and "Char_Cat_9974" not in crowd.of
          and list(crowd.spawners) == ["OakSpawner_Crowd"])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
