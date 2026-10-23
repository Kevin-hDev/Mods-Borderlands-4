"""Tests Companions' copy of the pause its window holds (game_pause.py, It Follows' module taken by
docs/renforts/outils/menu_window.py, the players counted by It Follows' presence.players taken as it is): out of a
game, nothing paused; a game of several players never paused, said (It Follows' trial 70: a guest left frozen while
the host's window was open); the players unread, a game of one; the game paused, read back, held, then given back.
The whole of the module's behaviour is It Follows' own test of the same module; this one keeps the pieces Companions'
copy changes (review of 23 October 2026: a players' count broken here passed every test)."""

import json
from types import SimpleNamespace

import sdk_stubs

state = sdk_stubs.install()

import mods_base  # noqa: E402
from companions import game_pause, report  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def said() -> dict:
    return json.loads(state["info"][-1][len(report.PREFIX) + 1:])


class Statics:
    """GameplayStatics as the pause asks it."""

    def __init__(self) -> None:
        self.paused = False

    def __getattr__(self, name: str):
        if name.startswith("Get"):
            return lambda _context: 1.0
        raise AttributeError(name)

    def IsGamePaused(self, _context: object) -> tuple:
        return (self.paused,)

    def SetGamePaused(self, _context: object, paused: bool) -> None:
        self.paused = paused


class Unread:
    @property
    def GameState(self) -> object:
        raise RuntimeError("no game state")


statics = Statics()
state["classes"][game_pause.STATICS] = SimpleNamespace(ClassDefaultObject=statics)
world = SimpleNamespace(GameState=SimpleNamespace(PlayerArray=[object()]))
mods_base.ENGINE.GameViewport.World = world

try:
    check("out of a game: nothing paused", game_pause.hold() is False and said()["outcome"] == "not_in_game")
    state["pc"] = SimpleNamespace(OakCharacter=object())
    for count in (2, 4):
        mods_base.ENGINE.GameViewport.World = SimpleNamespace(GameState=SimpleNamespace(PlayerArray=[object()] * count))
        check(f"a game of {count} players: never paused, said", game_pause.hold() is False and not statics.paused
              and said() == {"event": "pause", "run": said()["run"], "outcome": "coop", "players": count})
    mods_base.ENGINE.GameViewport.World = Unread()
    check("the players unread: counted as none", game_pause._players() is None)
    mods_base.ENGINE.GameViewport.World = world
    check("a game of one: paused, read back, held", game_pause.hold() is True and statics.paused
          and game_pause.holding() and said()["outcome"] == "held")
    check("given back with the window", game_pause.release() is True and not statics.paused
          and not game_pause.holding() and said()["outcome"] == "released")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
