"""Tests the level's quicker dodges (normal/dodge_speed.py): hooked under its own name, one look every FRAME_GAP_S at
most; a dodge sped up by the level's factor while it lasts, its own time given back at its end; given back after
LONGEST_S even if the state still says dodging, and not taken again until it says otherwise; an enemy out of the list
still given back; an enemy gone forgotten; MAX_HELD at once; a time that cannot be read said once and not retried in
the same dodge; a look that raises ends the mode; the stop gives every time back and unhooks."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from it_follows import frame  # noqa: E402
from it_follows.normal import dodge_speed  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def pawn(name: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(Name=name, freed=False,
                                 AIDodgeState=types.SimpleNamespace(ActiveDodge=types.SimpleNamespace(Action=None)),
                                 CustomTimeDilation=types.SimpleNamespace(BaseValue=1.0, Value=0.8))


def time_of(enemy: types.SimpleNamespace) -> tuple[float, float]:
    return enemy.CustomTimeDilation.BaseValue, enemy.CustomTimeDilation.Value


def weak(*enemies: types.SimpleNamespace) -> dict:
    return {enemy.Name: sdk_stubs.FakeWeak(enemy) for enemy in enemies}


clock = {"now": 100.0}
frame.now = lambda: clock["now"]

try:
    lines: list[tuple[str, dict]] = []
    failures: list[str] = []
    speed = dodge_speed.DodgeSpeed(lambda event, **f: lines.append((event, f)), 3.0, failures.append)
    speed.start()
    check("hooked under its own name", dodge_speed.IDENTIFIER in state["hooks"]
          and dodge_speed.IDENTIFIER not in ("it_follows:run", "it_follows:normal"))
    psycho, bandit = pawn("Char_Psycho"), pawn("Char_Bandit")
    speed.follow(weak(psycho, bandit))
    psycho.AIDodgeState.ActiveDodge.Action = "Dodge_Left"
    state["hooks"][dodge_speed.IDENTIFIER].fn()
    check("a dodge sped up three times", time_of(psycho) == (3.0, 2.4000000000000004) and time_of(bandit) == (1.0, 0.8)
          and speed.count == 1)
    clock["now"] += 0.004
    psycho.AIDodgeState.ActiveDodge.Action = None
    state["hooks"][dodge_speed.IDENTIFIER].fn()
    check("within FRAME_GAP_S no look", time_of(psycho)[0] == 3.0)
    clock["now"] += 0.01
    state["hooks"][dodge_speed.IDENTIFIER].fn()
    check("its end: its own time given back", time_of(psycho) == (1.0, 0.8) and speed.held == {})

    bandit.AIDodgeState.ActiveDodge.Action = "Dodge_Back"
    speed.look(200.0)
    speed.look(200.0 + dodge_speed.LONGEST_S + 0.1)
    check("past LONGEST_S given back though still dodging", time_of(bandit) == (1.0, 0.8))
    speed.look(205.0)
    check("and not taken again while the state says so", time_of(bandit) == (1.0, 0.8) and speed.count == 2)
    bandit.AIDodgeState.ActiveDodge.Action = None
    speed.look(206.0)
    bandit.AIDodgeState.ActiveDodge.Action = "Dodge_Right"
    speed.look(207.0)
    check("its state cleared, its next dodge sped up", time_of(bandit)[0] == 3.0 and speed.count == 3)
    speed.follow({})
    bandit.AIDodgeState.ActiveDodge.Action = None
    speed.look(207.2)
    check("out of the list, still given back at its end", time_of(bandit) == (1.0, 0.8) and speed.held == {})

    cat = pawn("Char_Cat")
    speed.follow(weak(cat))
    cat.AIDodgeState.ActiveDodge.Action = "Dodge"
    speed.look(210.0)
    cat.freed = True
    speed.look(210.1)
    check("an enemy gone while held is forgotten", speed.held == {})

    crowd = [pawn(f"Char_{number}") for number in range(dodge_speed.MAX_HELD + 2)]
    for enemy in crowd:
        enemy.AIDodgeState.ActiveDodge.Action = "Dodge"
    speed.follow(weak(*crowd))
    speed.look(220.0)
    check("MAX_HELD at once", len(speed.held) == dodge_speed.MAX_HELD)

    blind = pawn("Char_Blind")
    del blind.CustomTimeDilation
    blind.AIDodgeState.ActiveDodge.Action = "Dodge"
    speed.follow(weak(blind))
    for moment in (230.0, 230.1, 230.2):
        speed.look(moment)
    check("a time that cannot be read: said once, not retried in that dodge",
          [event for event, _ in lines] == ["normal_dodge_speed_failed"] and "Char_Blind" in speed.stuck)

    stopped = speed.stop()
    check("the stop gives every time back and unhooks", stopped["hook"] == "removed" and speed.held == {}
          and all(time_of(enemy) == (1.0, 0.8) for enemy in crowd)
          and dodge_speed.IDENTIFIER not in state["hooks"])
    check("a second stop: inactive", speed.stop()["hook"] == "inactive")

    broken = dodge_speed.DodgeSpeed(lambda event, **f: None, 2.0, failures.append)
    broken.start()
    broken.watched = {"Char_Broken": None}
    clock["now"] += 1.0
    state["hooks"][dodge_speed.IDENTIFIER].fn()
    check("a look that raises ends the mode", failures == ["dodge_error:TypeError"])
    broken.stop()
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
