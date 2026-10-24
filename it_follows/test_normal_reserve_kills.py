"""Tests the throwaway measure of where the player's kills lie (normal/reserve_kills.py, audit of 24 October 2026, M1):
no kill, nothing asked; each kill told in the world, out of it and met, or out of it and never met, the world asked
once a census; the counts said, then counted afresh; a world that cannot be listed said unread, and never asked
again."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import census  # noqa: E402
from it_follows.normal import reserve_kills  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    asked: list[object] = []
    in_world = [types.SimpleNamespace(Name="Char_Body_InWorld"), types.SimpleNamespace(Name="Char_Alive")]

    def actors_of(WorldContextObject: object, ActorClass: object, OutActors: list) -> tuple:
        asked.append(WorldContextObject)
        return ..., in_world

    state["classes"]["GameplayStatics"] = types.SimpleNamespace(
        ClassDefaultObject=types.SimpleNamespace(GetAllActorsOfClass=actors_of))
    state["classes"][census.CHARACTER_CLASS] = types.SimpleNamespace(Name=census.CHARACTER_CLASS)
    player = object()
    seen = reserve_kills.ReserveKills()
    seen.add([], player, {})
    check("no kill: nothing asked", asked == [] and seen.said() == {"in_world": 0, "out_met": 0, "out_unmet": 0,
                                                                    "unread": 0})
    seen.add(["Char_Body_InWorld", "Char_Met_Reserve", "Char_Unmet_Reserve"], player, {"Char_Met_Reserve": None})
    check("each kill told where its body lay, the world asked once", asked == [player]
          and seen.said() == {"in_world": 1, "out_met": 1, "out_unmet": 1, "unread": 0})
    check("then counted afresh", seen.said() == {"in_world": 0, "out_met": 0, "out_unmet": 0, "unread": 0})
    del state["classes"]["GameplayStatics"]
    seen.add(["Char_Body_InWorld"], player, {})
    seen.add(["Char_Other"], player, {})
    check("a world that cannot be listed: unread, and never asked again",
          seen.broken and seen.said()["unread"] == 2 and len(asked) == 1)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
