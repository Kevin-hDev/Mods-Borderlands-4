"""Tests what the companions read of the world (companions/world.py): It Follows' own reads under the follow's names;
the hunter, his vehicle while he drives, else his character, None without a player; the attitude toward a character,
the game's answer's name, or its text, or why it is unread."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import reads  # noqa: E402
from it_follows.companions import world  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("It Follows' reads, never copied", (world.place, world.metres, world.dead, world.definition, world.mode) == (
      reads.point, reads.metres, reads.dead, reads.definition, reads.mode))
check("driving: his vehicle", world.hunter(types.SimpleNamespace(Pawn="car", OakCharacter="him")) == "car")
check("on foot: his character", world.hunter(types.SimpleNamespace(Pawn=None, OakCharacter="him")) == "him")
check("no player: none", world.hunter(None) is None)
asked: list = []
state["classes"]["GbxTeamFunctionLibrary"] = types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
    GetAttitudeTowards=lambda player, actor: asked.append((player, actor)) or types.SimpleNamespace(name="hostile")))
check("the attitude's name, the player toward the character", world.attitude("me", "bandit") == "hostile"
      and asked == [("me", "bandit")])
state["classes"]["GbxTeamFunctionLibrary"] = types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
    GetAttitudeTowards=lambda player, actor: "x" * 90))
check("an answer without a name: its text, cut", world.attitude("me", "bandit") == "x" * 60)
state["classes"]["GbxTeamFunctionLibrary"] = types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
    GetAttitudeTowards=lambda player, actor: 1 / 0))
check("a call that fails: why", world.attitude("me", "bandit") == "unread:ZeroDivisionError")
del state["classes"]["GbxTeamFunctionLibrary"]
check("no library: why", world.attitude("me", "bandit") == "unread:KeyError")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
