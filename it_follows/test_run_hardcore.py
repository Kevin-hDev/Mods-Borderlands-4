"""Tests the Horde's Hardcore (run_hardcore.py, decision 109): 0 % at first; at each step reached the toughness given
the Buff's factor times the step's, the damage taken changed the same way, a line written; nothing done or written
within a step; several steps at once taken as one."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import run_hardcore  # noqa: E402

fails: list[str] = []
calls: list[tuple] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Toughness:
    def harden(self, factor: float) -> None:
        calls.append(("harden", round(factor, 6)))


class Taken:
    def change(self, player: object, factor: float) -> dict:
        calls.append(("change", player, round(factor, 6)))
        return {"base": [1.0, round(factor, 3)]}


try:
    hard = run_hardcore.RunHardcore(Toughness(), Taken(), 1.4, 1.2,
                                    lambda event, **fields: calls.append((event, fields)))
    check("0 % at first", hard.percent == 0)
    hard.keep(99, "hunter")
    check("under 100 kills, nothing", calls == [] and hard.percent == 0)
    hard.keep(100, "hunter")
    check("at 100 kills, 1 %: the enemies to come 1.4 x 1.01, the hunter 1.2 x 1.01, written down",
          calls == [("harden", 1.414), ("change", "hunter", 1.212),
                    ("hardcore_step", {"percent": 1, "kills": 100, "health": 1.414,
                                       "taken": {"base": [1.0, 1.212]}})] and hard.percent == 1)
    calls.clear()
    hard.keep(150, "hunter")
    check("within the step, nothing", calls == [])
    hard.keep(420, "hunter")
    check("several steps at once, one change to 4 %", [call[0] for call in calls] == ["harden", "change",
                                                                                    "hardcore_step"]
          and calls[0] == ("harden", 1.456) and hard.percent == 4)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
