"""Tests the shared first-person lookup: the arms found among many, the socket list."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402
from heirloom_stubs import sdk_stubs  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


state = heirloom_stubs.install()
from apex_heirloom import apex_first_person as fp  # noqa: E402


def arms_for(owner: object, name: str = "FirstPersonArms", answers: bool = True):
    """An animation instance and the mesh it belongs to, as the game presents them."""
    instance = types.SimpleNamespace()
    mesh = types.SimpleNamespace(Name=name, Outer=owner, GetAnimInstance=lambda: instance if answers else None)
    instance.Outer = mesh
    return instance, mesh


character = object()
stranger = object()
body, _ = arms_for(character, name="Body")
other, _ = arms_for(stranger)
mine, my_mesh = arms_for(character)
state["all"]["/Script/Engine.AnimInstance"] = [body, other, mine]

check("the player's own arms are picked out of the level's instances", fp.mesh(character) is my_mesh)
check("no character means no arms", fp.mesh(None) is None)

state["all"]["/Script/Engine.AnimInstance"] = [arms_for(character, answers=False)[0]]
check("a mesh that answers with another instance is refused", fp.mesh(character) is None)

my_mesh.GetAllSocketNames = lambda: ["FX_L_Hand_Grapple", "FX_R_Hand"]
check("the arms hand over their anchors", fp.sockets(my_mesh) == ["FX_L_Hand_Grapple", "FX_R_Hand"])
my_mesh.GetAllSocketNames = lambda: [f"Bone_{i}" for i in range(325)] + ["R_Hand_Object"]
check("an anchor past the 325 bones of Kevin's arms is still listed", "R_Hand_Object" in fp.sockets(my_mesh))
my_mesh.GetAllSocketNames = lambda: (f"Bone_{i}" for i in range(10**6))
check("an endless list is cut", len(fp.sockets(my_mesh)) == fp.MAX_SOCKETS)
my_mesh.GetAllSocketNames = lambda: (_ for _ in ()).throw(RuntimeError("refused"))
check("a refused list costs nothing", fp.sockets(my_mesh) == [])
del my_mesh.GetAllSocketNames
check("arms that cannot list their anchors say nothing", fp.sockets(my_mesh) == [])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
