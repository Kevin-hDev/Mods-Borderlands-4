"""Tests the lookup of a game object: taken from memory when held there, loaded from the archives when not."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import game_assets  # noqa: E402

fails: list[str] = []
SHOCK = "/Game/Gear/Weapons/_Shared/Effects/Systems/GenericLaser/NS_Beam_Energy_Shock.NS_Beam_Energy_Shock"


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("an object the game holds in memory is handed back without loading",
      game_assets.load("NiagaraSystem", sdk_stubs.FIRE_BEAM) == "the fire beam" and state["loads"] == [])
check("an object it does not hold is loaded from the archives, then found",
      game_assets.load("NiagaraSystem", SHOCK) == "a loaded beam" and state["loads"] == [SHOCK])
check("the load names the object's class by its full path", state["load_classes"] == ["/Script/Niagara.NiagaraSystem"])
check("once loaded it is not loaded again", game_assets.load("NiagaraSystem", SHOCK) == "a loaded beam" and len(state["loads"]) == 1)

state["in_archives"] = False
try:
    game_assets.load("AnimSequence", "/Game/Nowhere/AS_None.AS_None")
    check("an object the game does not have: ValueError", False)
except ValueError:
    check("an object the game does not have: ValueError", state["load_classes"][-1] == "/Script/Engine.AnimSequence")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
