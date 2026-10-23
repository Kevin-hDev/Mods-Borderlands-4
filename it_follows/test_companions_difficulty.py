"""Tests trial 187's level played (difficulty.py): 4, 7, 9 and 12 times the hunter's health, God's shield alone
filled again after 45 s; the normal mode's level while It Follows has it on; Bandit's in the Horde, with neither on,
without It Follows, for a level the table lacks or a read that fails, each why said; the game's module found by its
name; It Follows' real session.py at the frontier, only its modes faked."""

import pathlib
import sys
import types
from importlib import util

HERE = pathlib.Path(__file__).resolve().parent
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


spec = util.spec_from_file_location("difficulty_under_test", HERE / "it_follows" / "companions" / "difficulty.py")
module = util.module_from_spec(spec)
spec.loader.exec_module(module)


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
del sys.modules[module.SESSION]

# It Follows' real session.py, imported from its package, the game's SDK faked: normal_live() and running() as they
# are, and found by the name the game loads it under.
sys.path.insert(0, str(HERE))
import sdk_stubs  # noqa: E402

sdk_stubs.install()
from it_follows import session  # noqa: E402

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

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
