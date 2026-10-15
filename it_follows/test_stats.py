"""Tests a run's counts: an enemy of the horde found dead is a kill, once; a character seen alive then dead at a later
census is a kill, once, whether or not it ever joined the horde; a dead one never seen alive is none; a body seen
alive again begins a new life; the names remembered are bounded; the hunter's deaths, one a death, an unreadable
second never counting a second one."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import stats as stats_module  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    stats = stats_module.Stats(hunter_dead=False)
    check("a run begins with nothing counted", (stats.kills, stats.deaths) == (0, 0))
    stats.seen_alive({"Char_Cat_1", "Char_Cat_2", "Char_Bat_3"})
    check("an enemy of the horde found dead is a kill", stats.killed("Char_Cat_1") and stats.kills == 1)
    check("found dead again, it is not counted twice", not stats.killed("Char_Cat_1") and stats.kills == 1)
    check("the census reading it dead later does not count it again", stats.seen_dead({"Char_Cat_1"}) == 0
          and stats.kills == 1)
    check("one seen alive then read dead is a kill, though it never joined the horde",
          stats.seen_dead({"Char_Bat_3"}) == 1 and stats.kills == 2)
    check("read dead again, still one", stats.seen_dead({"Char_Bat_3"}) == 0 and stats.kills == 2)
    check("a dead one never seen alive is no kill: it may have died before the run", stats.seen_dead({"Char_Old_9"})
          == 0 and stats.kills == 2)
    stats.seen_alive({"Char_Cat_1"})
    check("a body seen alive again is a new enemy, whose death counts", stats.killed("Char_Cat_1")
          and stats.kills == 3)
    stats.seen_alive({"Char_Bat_3"})
    check("a census sees the new life die too", stats.seen_dead({"Char_Bat_3"}) == 1 and stats.kills == 4)

    bounded = stats_module.Stats()
    bounded.seen_alive({f"Char_E_{index}" for index in range(stats_module.MAX_NAMES + 500)})
    for index in range(stats_module.MAX_NAMES + 500):
        bounded.killed(f"Char_K_{index}")
    check("the names remembered stay bounded", len(bounded._alive) <= stats_module.MAX_NAMES
          and len(bounded._counted) <= stats_module.MAX_NAMES and bounded.kills == stats_module.MAX_NAMES + 500)

    hunter = stats_module.Stats(hunter_dead=False)
    check("alive, no death", not hunter.hunter(False) and hunter.deaths == 0)
    check("read dead: a death", hunter.hunter(True) and hunter.deaths == 1)
    check("still dead the next second: the same death", not hunter.hunter(True) and hunter.deaths == 1)
    check("an unreadable second between two dead ones counts nothing", not hunter.hunter(None)
          and not hunter.hunter(True) and hunter.deaths == 1)
    hunter.hunter(False)
    check("alive again, then dead: a second death", hunter.hunter(True) and hunter.deaths == 2)
    unknown = stats_module.Stats()
    check("the first read dead after nothing known is a death", unknown.hunter(True) and unknown.deaths == 1)
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
