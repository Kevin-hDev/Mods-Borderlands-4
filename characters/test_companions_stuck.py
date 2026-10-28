"""Tests trial 168's blocked walk (stuck.py), Vex's values: the first place read is no block; moving
MIN_MOVED_M on the ground starts the wait again; less, not blocked before STUCK_S, blocked from then; height left out;
an unread place counts as moving; forget starts afresh."""

import pathlib
import sys
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("follow_stuck_under_test", HERE / "characters" / "companions" / "stuck.py")
stuck_module = util.module_from_spec(spec)
spec.loader.exec_module(stuck_module)

check("Vex's values", stuck_module.MIN_MOVED_M == 1.0 and stuck_module.STUCK_S == 2.0)
stuck = stuck_module.Stuck()
check("the first place: no block", not stuck.blocked((0.0, 0.0, 0.0), 0.0))
check("less than 1 m, before 2 s: not blocked", not stuck.blocked((60.0, 60.0, 0.0), 1.9))
check("from 2 s: blocked", stuck.blocked((60.0, 60.0, 0.0), 2.0))
check("height left out: climbing on the spot is still blocked", stuck.blocked((0.0, 0.0, 500.0), 3.0))
check("moved 1 m: the wait starts again", not stuck.blocked((100.0, 0.0, 0.0), 3.5)
      and not stuck.blocked((100.0, 0.0, 0.0), 5.4) and stuck.blocked((100.0, 0.0, 0.0), 5.5))
check("an unread place: moving", not stuck.blocked(None, 6.0) and not stuck.blocked((100.0, 0.0, 0.0), 6.5)
      and not stuck.blocked((100.0, 0.0, 0.0), 8.4) and stuck.blocked((100.0, 0.0, 0.0), 8.5))
stuck.forget()
check("forgotten: afresh", not stuck.blocked((100.0, 0.0, 0.0), 20.0) and stuck.since == ((100.0, 0.0, 0.0), 20.0))

teleports: list[float] = []


def teleport() -> str:
    teleports.append(1.0)
    return "teleported"


stuck = stuck_module.Stuck()
check("unstick: not walking: near, the wait forgotten, no teleport", stuck.unstick(False, False, (0.0, 0.0, 0.0), 0.0,
      teleport) == "near" and stuck.since is None and teleports == [])
stuck.blocked((0.0, 0.0, 0.0), 0.0)
check("unstick: fighting: near, the wait forgotten", stuck.unstick(True, True, (0.0, 0.0, 0.0), 5.0, teleport)
      == "near" and stuck.since is None and teleports == [])
check("unstick: walking, not blocked yet: near", stuck.unstick(True, False, (0.0, 0.0, 0.0), 10.0, teleport) == "near"
      and stuck.unstick(True, False, (0.0, 0.0, 0.0), 11.9, teleport) == "near" and teleports == [])
check("unstick: walking, blocked 2 s: teleported, said stuck", stuck.unstick(True, False, (0.0, 0.0, 0.0), 12.0,
      teleport) == "stuck:teleported" and teleports == [1.0])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
