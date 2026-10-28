"""Tests the time played: the world's time followed second by second; a pause, where it stands still while the real
time runs, left out; a new world counted from its start; a world clock going back in the same world, or unreadable,
timed by the real time for that sample, then the world's again, never its whole time at once; a world never read never
taken for a new one; the controller asked, not the character; the game's own pause and It Follows' window both left out,
though the unpaused time runs on under them, and the window's never taken off twice."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import clock as clock_module, game_pause  # noqa: E402

fails: list[str] = []
world_clock = [50.0]
# The unpaused time runs on through a pause, as the real time does.
unpaused = [500.0]
asked: list = []
unreadable = [False]


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class World:
    """A world: equal only to itself, as the game's objects are."""

    def __init__(self, name: str) -> None:
        self.Name, self.freed = name, False


class Statics:
    """The world's time, the unpaused and real times, and the pause the window holds."""

    def __init__(self) -> None:
        self.paused = False

    def GetTimeSeconds(self, context: object) -> float:
        asked.append(context)
        if unreadable[0]:
            raise RuntimeError("no clock")
        return world_clock[0]

    def GetUnpausedTimeSeconds(self, _context: object) -> float:
        return unpaused[0]

    def GetRealTimeSeconds(self, _context: object) -> float:
        return unpaused[0]

    def IsGamePaused(self, _context: object) -> tuple:
        return (self.paused,)

    def SetGamePaused(self, _context: object, paused: bool) -> None:
        self.paused = paused


state["classes"]["GameplayStatics"] = types.SimpleNamespace(ClassDefaultObject=Statics())
engine = sys.modules["mods_base"].ENGINE
engine.GameViewport.World = World("World_0")
pc = types.SimpleNamespace(Name="OakPlayerController_0", OakCharacter=None)


def close(a: float, b: float) -> bool:
    return abs(a - b) < 1e-9


try:
    clock = clock_module.Clock(pc, 1000.0)
    check("a run begins at nothing played", clock.played == 0.0)
    world_clock[0] = 51.0
    said = clock.tick(pc, 1001.0)
    check("a second of the world is a second played", close(clock.played, 1.0)
          and said == {"real_gap_s": 1.0, "world_gap_s": 1.0, "new_world": False})
    check("the world's time is asked through the controller, which stays while the hunter drives",
          asked and all(context is pc for context in asked))
    world_clock[0] = 51.1
    said = clock.tick(pc, 1011.0)
    check("a pause is left out: 10 s of real time, 0.1 s of the world's", close(clock.played, 1.1)
          and said["real_gap_s"] == 10.0 and said["world_gap_s"] == 0.1)
    engine.GameViewport.World = World("World_1")
    world_clock[0] = 2.0
    said = clock.tick(pc, 1030.0)
    check("a new world counts from its start", close(clock.played, 3.1) and said["new_world"] is True
          and said["world_gap_s"] == 2.0)
    world_clock[0] = 1.0
    said = clock.tick(pc, 1031.0)
    check("a world clock going back in the same world: the real time for that sample", close(clock.played, 4.1)
          and said["world_gap_s"] is None and clock.fallbacks == 1)
    unreadable[0] = True
    clock.tick(pc, 1032.0)
    unreadable[0] = False
    world_clock[0] = 300.0
    clock.tick(pc, 1033.0)
    check("after an unreadable world clock, the real time again, never the world's whole time",
          close(clock.played, 6.1) and clock.fallbacks == 3)
    world_clock[0] = 301.0
    clock.tick(pc, 1034.0)
    check("then the world's time again", close(clock.played, 7.1) and clock.fallbacks == 3)
    holder = engine.GameViewport
    engine.GameViewport = None
    world_clock[0] = 302.0
    clock.tick(pc, 1035.0)
    engine.GameViewport = holder
    world_clock[0] = 303.0
    said = clock.tick(pc, 1036.0)
    check("a world unreadable for a sample is never taken for a new one", close(clock.played, 9.1)
          and said["new_world"] is False)
    engine.GameViewport = None
    world_clock[0] = 304.0
    clock.tick(pc, 1037.0)
    engine.GameViewport = holder
    engine.GameViewport.World = World("World_2")
    world_clock[0] = 5.0
    said = clock.tick(pc, 1038.0)
    check("the world known before an unreadable sample is kept: a new one after it counts from its start",
          close(clock.played, 15.1) and said["new_world"] is True and said["world_gap_s"] == 5.0)

    engine.GameViewport = None
    world_clock[0] = 50.0
    unread = clock_module.Clock(pc, 2000.0)
    engine.GameViewport = holder
    world_clock[0] = 51.0
    said = unread.tick(pc, 2001.0)
    check("a world unread at the start is never taken for a new one at the first sample",
          close(unread.played, 1.0) and said["new_world"] is False)

    world_clock[0] = 51.0
    paused_run = clock_module.Clock(pc, 3000.0)
    world_clock[0], unpaused[0] = 52.0, 501.0
    paused_run.tick(pc, 3001.0)
    unpaused[0] += 142.0
    said = paused_run.tick(pc, 3143.0)
    check("trial 18's 142 s in the game's own pause count none: the world's time stood still",
          close(paused_run.played, 1.0) and said["real_gap_s"] == 142.0 and said["world_gap_s"] == 0.0)
    state["pc"] = types.SimpleNamespace(OakCharacter=object())
    game_pause.hold()
    unpaused[0] += 8.0
    paused_run.tick(pc, 3151.0)
    check("a sample taken while the window holds the pause counts none of it", close(paused_run.played, 1.0))
    unpaused[0] += 4.0
    game_pause.release()
    world_clock[0], unpaused[0] = 53.0, unpaused[0] + 1.0
    paused_run.tick(pc, 3156.0)
    check("the window's pause is never taken off twice: the second after it counts whole",
          game_pause.holding() is False and close(paused_run.played, 2.0))
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
