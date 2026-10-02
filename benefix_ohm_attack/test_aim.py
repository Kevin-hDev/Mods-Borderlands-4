"""Tests where the player aims: the spot the camera's ray meets and who stands there."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import aim  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def near(found, wanted):
    return all(abs(a - b) < 1e-6 for a, b in zip(found, wanted))


pc, character = sdk_stubs.player(state)
check("a level look along yaw 0 points down the X axis",
      near(aim.facing(types.SimpleNamespace(Pitch=0.0, Yaw=0.0)), (1.0, 0.0, 0.0)))
check("a positive pitch looks up", near(aim.facing(types.SimpleNamespace(Pitch=90.0, Yaw=0.0)), (0.0, 0.0, 1.0)))
check("the species is the name without its instance number", aim.species_of(types.SimpleNamespace(Name="Char_Psycho_214")) == "Char_Psycho")
check("a character is an enemy, an ally by name and a wall are not",
      aim.is_enemy("Char_Psycho") and not aim.is_enemy("Char_NPC_Vendor") and not aim.is_enemy("StaticMeshActor"))

sdk_stubs.aim_at(state, None)
sky = aim.look(pc, character, 5000.0)
check("aiming at nothing ends the beam at its reach, on no enemy",
      near(sky.anchor, (5000.0, 0.0, 50.0)) and sky.enemy is None and sky.hit is None)
enemy = sdk_stubs.aim_at(state, "Char_Psycho_214", distance=700.0)
found = aim.look(pc, character, 5000.0)
check("aiming at an enemy ends the beam on it and names it",
      near(found.anchor, (700.0, 0.0, 50.0)) and found.enemy is enemy and found.species == "Char_Psycho"
      and found.hit is state["trace"][1])
check("and says how far it stands; nothing met is no distance", found.distance == 700.0 and sky.distance == 0.0)
far = sdk_stubs.aim_at(state, "Char_Psycho_9", distance=80000.0)
check("an enemy 800 metres away is a target when the reach allows it",
      aim.look(pc, character, 100000.0).enemy is far and state["traced"][-1].X == 100000.0)
sdk_stubs.aim_at(state, "Char_NPC_Vendor_3")
check("an ally ends the beam but is no target", aim.look(pc, character, 5000.0).enemy is None)
sdk_stubs.aim_at(state, "StaticMeshActor_12", distance=300.0)
wall = aim.look(pc, character, 5000.0)
check("a wall ends the beam but is no target", near(wall.anchor, (300.0, 0.0, 50.0)) and wall.enemy is None)
state["trace"] = (True, types.SimpleNamespace(HitObjectHandle=types.SimpleNamespace(Actor=character), Distance=10.0))
check("the player himself is no target", aim.look(pc, character, 5000.0).enemy is None)
state["trace"] = (True, types.SimpleNamespace(Distance=10.0))
check("a hit that names nobody is no target", aim.look(pc, character, 5000.0).enemy is None)

ray = state["rays"][-1]
check("the ray is the player's own: his character as the world's context, the channel that meets what blocks him, "
      "simple shapes, nobody set aside by hand, himself ignored",
      ray[0] is character and ray[3] == aim.TRACE_CHANNEL == 2 and ray[4] is False and ray[5] == [] and ray[8] is True)
check("the camera is read in one place: where it is, and its rotation",
      aim.eye(pc)[0] == (0.0, 0.0, 50.0) and aim.eye(pc)[1].Yaw == 0.0)
found = types.SimpleNamespace(Name="Char_Psycho_3")
for label, result in (
        ("its actor", types.SimpleNamespace(Actor=found, Distance=10.0)),
        ("its component's owner", types.SimpleNamespace(Component=types.SimpleNamespace(GetOwner=lambda: found), Distance=10.0)),
        ("its actor, the handle naming nobody",
         types.SimpleNamespace(HitObjectHandle=types.SimpleNamespace(Actor=None), Actor=found, Distance=10.0))):
    state["trace"] = (True, result)
    check(f"a hit that names who was met only by {label} is a target all the same", aim.look(pc, character, 5000.0).enemy is found)
check("a name of any length is cut before it is read",
      len(aim.species_of(types.SimpleNamespace(Name="Char_" + "x" * 500))) == aim.MAX_NAME == 80)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
