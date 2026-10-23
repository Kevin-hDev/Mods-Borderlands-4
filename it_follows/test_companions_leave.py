"""Tests a companion taken out of the world (companions/leave.py, decision 59): by GbxDestroyActor(False) only, the
call written before it is made, never the engine's K2_DestroyActor; gone, nothing called; a refused call said."""

import pathlib
import sys
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("leave_under_test", HERE / "it_follows" / "companions" / "leave.py")
module = util.module_from_spec(spec)
spec.loader.exec_module(module)


class Companion:
    def __init__(self, refuse: bool = False) -> None:
        self.calls: list = []
        self.refuse = refuse

    def GbxDestroyActor(self, net_force: bool) -> None:
        if self.refuse:
            raise RuntimeError("refused")
        self.calls.append(("GbxDestroyActor", net_force))

    def K2_DestroyActor(self) -> None:
        self.calls.append(("K2_DestroyActor",))


said: list = []


def announce(call: str, **fields: object) -> None:
    said.append((call, fields))


try:
    one = Companion()
    check("removed by GbxDestroyActor(False), written first", module.leave(one, "Lemmy_1", announce) == "removed"
          and one.calls == [("GbxDestroyActor", False)] and said == [("GbxDestroyActor", {"on": "Lemmy_1"})])
    said.clear()
    check("gone: nothing to remove, nothing called", module.leave(None, "Lemmy_1", announce) == "gone" and said == [])
    refused = Companion(refuse=True)
    check("refused: said, never the engine's K2_DestroyActor (it crashed the game)",
          module.leave(refused, "Lemmy_2", announce) == "failed:RuntimeError:refused" and refused.calls == [])
    long = Companion(refuse=True)
    long.GbxDestroyActor = lambda _force: (_ for _ in ()).throw(ValueError("x" * 500))
    check("a long error cut", len(module.leave(long, "Lemmy_3", announce)) == len("failed:ValueError:") + 120)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
