"""Tests the pause the window holds (game_pause.py): nothing paused out of a game; a game already paused left as it is;
the game paused and read back, held with its world; held once; given back and read back; a world gone leaves nothing to
give back; a game that keeps its pause is tried again; a game that refuses the pause, or a call that raises, leaves
the window open over the running game, said; nothing held, nothing to give back; the watch: a game found running
under the window paused again, said once a pause, looked at once a second, counted at the release, never raising; the
release says what the world's clocks did under the window."""

import json
import pathlib
import sys
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import mods_base  # noqa: E402
from it_follows import game_pause, report  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def line() -> dict:
    return json.loads(state["info"][-1][len(report.PREFIX) + 1:])


def said() -> str:
    return line()["outcome"]


class Statics:
    """GameplayStatics as the pause asks it: whether the game is paused, and pausing or resuming it."""

    def __init__(self) -> None:
        self.paused, self.refuses, self.keeps, self.raises = False, False, False, False
        self.times = {"GetTimeSeconds": 100.0, "GetUnpausedTimeSeconds": 200.0, "GetRealTimeSeconds": 300.0}

    def __getattr__(self, name: str):
        if name in self.__dict__.get("times", {}):
            return lambda _context: self.times[name]
        raise AttributeError(name)

    def IsGamePaused(self, _context: object) -> tuple:
        if self.raises:
            raise RuntimeError("statics")
        return (self.paused,)

    def SetGamePaused(self, _context: object, paused: bool) -> None:
        if not (paused and self.refuses) and not (not paused and self.keeps):
            self.paused = paused


statics = Statics()
state["classes"][game_pause.STATICS] = SimpleNamespace(ClassDefaultObject=statics)
world = SimpleNamespace()
mods_base.ENGINE.GameViewport.World = world
real = [0.0]
game_pause.real_s = lambda: real[0]

try:
    check("out of a game: nothing paused", game_pause.hold() is False and said() == "not_in_game")
    state["pc"] = SimpleNamespace(OakCharacter=object())
    statics.paused = True
    check("a game already paused: left as it is, never resumed here", game_pause.hold() is False
          and said() == "paused_already" and game_pause.release() is True and statics.paused)
    statics.paused = False
    check("the game paused, read back, held", game_pause.hold() is True and statics.paused and game_pause.holding()
          and said() == "held")
    check("held once", game_pause.hold() is True)
    statics.keeps = True
    check("a game that keeps its pause: tried again", game_pause.release() is False and game_pause.holding()
          and said() == "kept_by_game")
    statics.keeps = False
    check("given back, read back", game_pause.release() is True and not statics.paused and not game_pause.holding()
          and said() == "released")
    check("nothing held, nothing to give back", game_pause.release() is True)
    game_pause.hold()
    game_pause._held["world"] = lambda: None
    check("its world gone: nothing to give back", game_pause.release() is True and said() == "world_gone")
    statics.paused, statics.refuses = False, True
    check("a game that refuses the pause: the window over the running game, said", game_pause.hold() is False
          and not game_pause.holding() and said() == "refused")
    statics.refuses, statics.raises = False, True
    check("a call that raises: said, nothing held", game_pause.hold() is False and not game_pause.holding()
          and said() == "failed")
    statics.raises = False

    lines = len(state["info"])
    game_pause.watch()
    check("the watch: nothing held, nothing looked at", len(state["info"]) == lines)
    check("the pause held for the watch", game_pause.hold() is True)
    statics.paused = False
    real[0] += 0.5
    game_pause.watch()
    check("the watch looks once a second, not at each poll", not statics.paused)
    real[0] += 0.6
    game_pause.watch()
    check("a game found running under the window: paused again, said", statics.paused and said() == "lost")
    statics.paused = False
    real[0] += 1.0
    lines = len(state["info"])
    game_pause.watch()
    check("found running again: paused again, not said again", statics.paused and len(state["info"]) == lines)
    statics.times = {"GetTimeSeconds": 100.5, "GetUnpausedTimeSeconds": 212.0, "GetRealTimeSeconds": 312.25}
    released = game_pause.release() is True and line()
    check("the release says what each of the world's clocks did under the window, and how often it ran",
          released and released["world_s"] == 0.5 and released["unpaused_s"] == 12.0
          and released["real_s"] == 12.25 and released["lost"] == 2)
    game_pause.hold()
    statics.raises = True
    real[0] += 2.0
    game_pause.watch()
    check("a watch whose read raises: said once as an error, never raising", state["errors"][-1:]
          and "pause" in state["errors"][-1])
    statics.raises = False
    game_pause.release()
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
