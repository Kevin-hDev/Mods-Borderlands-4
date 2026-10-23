"""Tests trial 187's level played (companion_levels.py): 4, 7, 9 and 12 times the hunter's health, God's shield alone
filled again after 45 s; the normal mode's level while It Follows has it on; Bandit's in the Horde, with neither on,
without It Follows, for a level the table lacks or a read that fails, each why said; the game's module found by its
name; It Follows' real session.py at the frontier, only its modes faked. And what It Follows gives a companion
(given): the level's health and shield wait, said with why; its card's shield of 30 % or none, its speed and its
outfit; back 45 s after a death; the level played now when none is given."""

import pathlib
import sys
import types
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()
from it_follows import companion_choices, session  # noqa: E402
from it_follows import companion_levels as module  # noqa: E402
from it_follows.characters.companions.tuning import Tuning  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Session:
    """It Follows' session.py as the probe reads it: the normal mode on with its level, or None; a run going or not."""

    def __init__(self, normal: object = None, run: object = False) -> None:
        self.normal, self.run = normal, run

    def normal_live(self) -> object:
        if isinstance(self.normal, Exception):
            raise self.normal
        return self.normal

    def running(self) -> object:
        return self.run


def live(level: object) -> object:
    return types.SimpleNamespace(level=level, playing=True)


check("decisions 37 and 38: 4, 7, 9 and 12 times, God's shield alone filled again, after 45 s", module.LEVELS == {
      "Bandit": (4.0, None), "Senior": (7.0, None), "Predator": (9.0, None), "God": (12.0, 45.0)})
levels_spec = util.spec_from_file_location("levels_under_test", HERE / "it_follows" / "normal" / "levels.py")
normal_levels = util.module_from_spec(levels_spec)
levels_spec.loader.exec_module(normal_levels)
check("each of the normal mode's levels has its companions' values, God's included (decision 153)",
      list(module.LEVELS) == list(normal_levels.LEVELS))
check("Bandit outside the normal mode (Kevin: « toujours Bandit »); It Follows' module as the game names it",
      module.OUTSIDE == "Bandit" and module.SESSION == "it_follows.session")
check("a level: its name, why, times and wait", module.level("God", "normal") == ("God", "normal", 12.0, 45.0)
      and module.level("God", "normal").times == 12.0 and module.level("Senior", "x").refill_after_s is None)
for name in ("Bandit", "Senior", "Predator", "God"):
    check(f"the normal mode on at {name}: its level", module.played(Session(live(name)))
          == module.level(name, "normal"))
check("on, waiting for a game: its level still", module.played(Session(types.SimpleNamespace(
      level="Senior", playing=False))) == module.level("Senior", "normal"))
check("a Horde run: Bandit", module.played(Session(None, True)) == module.level("Bandit", "horde"))
check("nothing on: Bandit", module.played(Session(None, False)) == module.level("Bandit", "off"))
check("running() other than True: off", module.played(Session(None, 1)).why == "off")
check("a level the table lacks: Bandit, its name said, cut", module.played(Session(live("X" * 90))) == module.level(
      "Bandit", "unknown:" + "X" * 40))
check("a read that fails: Bandit, why said", module.played(Session(RuntimeError("boom"))) == module.level(
      "Bandit", "unread:RuntimeError"))
check("a level unreadable: Bandit, why said", module.played(Session(types.SimpleNamespace())).why
      == "unread:AttributeError")
check("running() failing: Bandit, why said", module.played(types.SimpleNamespace(
      normal_live=lambda: None, running=lambda: 1 / 0)).why == "unread:ZeroDivisionError")

sys.modules.pop(module.SESSION, None)
check("It Follows not loaded: Bandit", module.played() == module.level("Bandit", "no_it_follows"))
sys.modules[module.SESSION] = Session(live("Predator"))
check("the game's module found by its name", module.played() == module.level("Predator", "normal"))
# It Follows' real session.py, imported from its package, the game's SDK faked: normal_live() and running() as they
# are, and found by the name the game loads it under.
sys.modules[module.SESSION] = session

check("It Follows' session found by its name", sys.modules[module.SESSION] is session
      and module.played() == module.level("Bandit", "off"))
check("It Follows' session, nothing on: Bandit, off", module.played(session) == module.level("Bandit", "off"))
session._state["run"] = object()
check("It Follows' session, a run going: Bandit, horde", module.played(session) == module.level("Bandit", "horde"))
session._state["run"] = None
session._state["normal"] = types.SimpleNamespace(settings=types.SimpleNamespace(level=types.SimpleNamespace(
    name="Predator")), playing=lambda: True)
check("It Follows' session, the normal mode on at Predator: Predator", module.played(session) == module.level(
      "Predator", "normal"))

Choice = companion_choices.Choice
check("a shield of 30 % of their health (decision 37), back 45 s after a death (decision 23)",
      module.SHIELD_SHARE == 0.3 and module.BACK_AFTER_S == 45.0)
check("given at Predator: 9 times, never filled again; the card's shield, +30 %, the player's colours, said why",
      module.given(Choice(True, "+30%", "player"), module.level("Predator", "normal")) == Tuning(
          9.0, 0.3, None, 1.3, 45.0, "player", ("Predator", "normal")))
check("given at God: filled again after 45 s; the card's shield off: none; speed off; his own outfit",
      module.given(Choice(False, "Off", "own"), module.level("God", "normal")) == Tuning(
          12.0, 0.0, 45.0, 1.0, 45.0, "own", ("God", "normal")))
check("no level given: the one played now (the normal mode at Predator)", module.given(Choice()) == Tuning(
      9.0, 0.3, None, 1.2, 45.0, "own", ("Predator", "normal")))
session._state["normal"] = None
check("no level given, nothing on: Bandit, off", module.given(Choice()).said == ("Bandit", "off")
      and module.given(Choice()).times == 4.0)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
