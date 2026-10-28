"""Tests whether the main menu shows (companions/main_menu.py, decision 61 of docs/renforts): the menu's station
shown, the menu; hidden, a game; no controller, none found, only the class default, a search or a read failing:
unknown (None), never the menu; why it told nothing kept for the journal, forgotten after a read (review of
23 October 2026)."""

import pathlib
import sys
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("main_menu_under_test", HERE / "characters" / "companions" / "main_menu.py")
module = util.module_from_spec(spec)
spec.loader.exec_module(module)


class Station:
    def __init__(self, hidden: object, name: str = "MainMenuStationObject_UAID_1") -> None:
        self.bHidden, self.Name = hidden, name


class Unreadable:
    Name = "MainMenuStationObject_UAID_2"

    @property
    def bHidden(self) -> bool:
        raise RuntimeError("unreadable")


asked: list = []


def finder(*found: object) -> object:
    def search(class_name: str, pc: object) -> tuple:
        asked.append((class_name, pc))
        return iter(found), "actors"
    return search


def failing(_class_name: str, _pc: object) -> tuple:
    raise RuntimeError("no world")


try:
    pc = object()
    check("the station shown: the menu, asked of the controller by its class",
          module.showing(pc, finder(Station(False))) is True and asked == [("MainMenuStationObject", pc)])
    check("the station hidden: a game", module.showing(pc, finder(Station(True))) is False)
    check("the class default skipped (find_all gives it), the station in the world read",
          module.showing(pc, finder(Station(False, "Default__MainMenuStationObject"), Station(True))) is False)
    check("only the class default: unknown, no station", module.showing(pc, finder(Station(False, "Default__X")))
          is None and module.why() == "no_station")
    check("none found: unknown", module.showing(pc, finder()) is None)
    check("no controller: unknown, nothing asked, said", module.showing(None, finder(Station(False))) is None
          and len(asked) == 5 and module.why() == "no_controller")
    check("a search failing: unknown, its error kept", module.showing(pc, failing) is None
          and module.why() == "failed:RuntimeError:no world")
    check("a read failing: unknown", module.showing(pc, finder(Unreadable())) is None
          and module.why() == "failed:RuntimeError:unreadable")
    check("a read that tells: nothing kept", module.showing(pc, finder(Station(True))) is False
          and module.why() == "")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
