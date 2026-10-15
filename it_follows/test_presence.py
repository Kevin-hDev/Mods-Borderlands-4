"""Tests whether a game is in play for It Follows (presence.py): no controller, no character; a controller without a
character whose pawn is a vehicle; a pawn that cannot be read being no vehicle; a character in a game of several
players; a character alone, or with a number of players that cannot be read."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import presence  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def players(count: int | None) -> None:
    """The game holds count players; None: the number cannot be read."""
    world = types.SimpleNamespace(GameState=types.SimpleNamespace(PlayerArray=[object()] * count)) if count else None
    sys.modules["mods_base"].ENGINE = types.SimpleNamespace(GameViewport=types.SimpleNamespace(World=world))


def driving(class_name: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(OakCharacter=None,
                                 Pawn=types.SimpleNamespace(Class=types.SimpleNamespace(Name=class_name)))


try:
    hunter = object()
    check("no controller: no character", presence.look() == presence.Seat(None, None, "no_character"))
    state["pc"] = driving("OakVehicle_Outrunner_C")
    check("a controller without a character, driving: in a vehicle", presence.look().why == "in_vehicle"
          and presence.look().player is None)
    state["pc"] = types.SimpleNamespace(OakCharacter=None)
    check("a pawn that cannot be read is no vehicle", presence.look().why == "no_character"
          and presence.in_vehicle(state["pc"]) is False)
    state["pc"] = types.SimpleNamespace(OakCharacter=hunter)
    players(2)
    check("a character in a game of two players: coop, the character said", presence.look().why == "coop"
          and presence.look().player is hunter and presence.players() == 2)
    players(1)
    check("a character alone: a game to play in", presence.look() == presence.Seat(state["pc"], hunter, None))
    players(None)
    check("the number of players unread: a game to play in", presence.players() is None
          and presence.look().why is None)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
