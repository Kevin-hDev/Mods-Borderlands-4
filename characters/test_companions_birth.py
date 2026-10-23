"""Tests a companion's birth (companions/birth.py), It Follows' real camps at the frontier, the game faked by the camps'
own fixture: 3 m in front of the hunter where the camera looks, at his height, the camp turned to face him; a new camp
made the first time, its companion handed typed, the camp's name given back; the camp of a companion that died
handed the next one, moved first, no new camp made; no player, no kit, no camp, a hand refused: why, nothing asked."""

import math
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
sys.modules["unrealsdk"].make_struct = lambda name, **fields: types.SimpleNamespace(struct_name=name, **fields)

from characters import camps, report  # noqa: E402
from characters.companions import birth  # noqa: E402
import wave_fixture as fake  # noqa: E402
from wave_fixture import events  # noqa: E402

clock = [100.0]
camps.time = types.SimpleNamespace(monotonic=lambda: clock[0])
camps.FGbxDefPtr = fake.DefPtr
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


hunter = types.SimpleNamespace(K2_GetActorLocation=lambda: types.SimpleNamespace(X=1000.0, Y=2000.0, Z=50.0))
pc = types.SimpleNamespace(OakCharacter=hunter, GetControlRotation=lambda: types.SimpleNamespace(Yaw=90.0))
statics = fake.Statics()
definition_type, _class, _library = fake.give_kit(state, statics, ["Char_CatYoung"])
births = birth.Births(camps.Camps(report.announce, birth.MOST_CAMPS))

check("3 m ahead; 16 camps at most", (birth.AHEAD_CM, birth.MOST_CAMPS) == (300.0, 16))
point, yaw = birth.ahead(hunter, pc)
check("in front where the camera looks, at his height", yaw == 90.0 and math.isclose(point[0], 1000.0, abs_tol=1e-9)
      and math.isclose(point[1], 2300.0) and point[2] == 50.0)
answer = births.ask("Char_MeleeFish_NPC", pc)
made = births.camps.pool[0].pointer()
handed = [entry for entry in events if entry[0] == "PushActorDef"]
check("the first: a new camp there, facing the hunter, its companion handed typed, its name given back", answer == {
      "done": "asked", "spawner": made.Name} and math.isclose(made.at[1], 2300.0) and math.isclose(
      made.where.Rotation.Z, math.sin(math.radians(270.0) / 2.0)) and len(handed) == 1
      and handed[0][3].name == "Char_MeleeFish_NPC" and handed[0][3].kind is definition_type and births.asked == 1)
pc.GetControlRotation = lambda: types.SimpleNamespace(Yaw=0.0)
clock[0] = 105.0
second = births.ask("Char_NPC_Abomination", pc)
check("its camp still pending: a second camp made, turned half a turn from the look, to face the hunter",
      second["spawner"] != made.Name and len(births.camps.pool) == 2 and math.isclose(
          births.camps.pool[1].pointer().where.Rotation.Z, 1.0))
clock[0] = 200.0
made.SpawnerComponent.died = True
events.clear()
again = births.ask("Char_NPC_Abomination", pc)
check("a camp whose companion died: handed the next, moved in front of the hunter first, no new camp", again == {
      "done": "asked", "spawner": made.Name} and len(births.camps.pool) == 2 and math.isclose(made.at[0], 1300.0)
      and any(entry[0] == "K2_SetActorLocation" for entry in events))
check("no player, no character: nothing asked", births.ask("A", None) == {"done": "no_character"}
      and births.ask("A", types.SimpleNamespace(OakCharacter=None)) == {"done": "no_character"} and births.asked == 3)
del state["classes"]["OakSpawner"]
check("no kit: why", births.ask("A", pc) == {"done": "no_kit", "why": "find_class(OakSpawner):KeyError"})
state["classes"]["OakSpawner"] = _class
full = birth.Births(camps.Camps(report.announce, 0))
check("no camp: said", full.ask("A", pc) == {"done": "no_camp"} and full.asked == 0)
clock[0] = 300.0
made.SpawnerComponent.fails = {"PushActorDef"}
other = births.camps.pool[1].pointer()
other.SpawnerComponent.died = False
check("a hand refused: why, not counted", births.ask("A", pc) == {"done": "refused", "why": "PushActorDef:RuntimeError"}
      and births.asked == 3)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
