"""Tests trial 175's staggers taken away (calm.py): on a living companion, Flinch, Stagger and Launch locked,
with
the game's enum values, under our reason, Block true, each call said first; the values trial 88 listed when the SDK has
no enum; never Ragdoll; a dead one, or one whose death cannot be read, left alone."""

import pathlib
import sys
import types
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


calls: list[tuple] = []
notes: list[str] = []
state["classes"]["OakHitReactionBlueprintLibrary"] = types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
    LockHitReactions=lambda AIActor, type, reason, Block: calls.append((AIActor.Name, type, reason, Block))))
state["enums"] = {"ELockedHitReaction": types.SimpleNamespace(All="E0", Flinch="E1", Stagger="E2", Launch="E3",
                                                               Ragdoll="E4", Melee="E5")}

spec = util.spec_from_file_location("follow_calm_under_test", HERE / "it_follows" / "companions" / "calm.py")
calm = util.module_from_spec(spec)
spec.loader.exec_module(calm)


def companion(name: str, dead: object = False) -> object:
    return types.SimpleNamespace(Name=name, HealthState=types.SimpleNamespace(bCurrentlyDead=dead))


check("a living companion: Flinch, Stagger and Launch locked, said first", calm.calm(
      companion("Crankus_1"), notes.append) == ["Flinch", "Stagger", "Launch"]
      and calls == [("Crankus_1", "E1", "RenfortsCompanion", True), ("Crankus_1", "E2", "RenfortsCompanion", True),
                    ("Crankus_1", "E3", "RenfortsCompanion", True)]
      and notes == ["about to call LockHitReactions(Flinch) on Crankus_1",
                    "about to call LockHitReactions(Stagger) on Crankus_1",
                    "about to call LockHitReactions(Launch) on Crankus_1"])
check("never a ragdoll", not any(call[1] == "E4" for call in calls))
calls.clear()
del state["enums"]["ELockedHitReaction"]
calm.calm(companion("Lemmy_1"), notes.append)
check("no enum to hand: the values trial 88 listed", [call[1] for call in calls] == [1, 2, 3])
calls.clear()
check("a dead one left alone", calm.calm(companion("Frame_1", dead=True), notes.append) == "dead" and calls == [])
check("one whose death cannot be read left alone", calm.calm(types.SimpleNamespace(Name="Odd_1"), notes.append)
      == "dead" and calls == [])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
