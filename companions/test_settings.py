"""Tests Companions' settings (settings.py): the five of the SETTINGS page with spec-compagnons.md's starting values,
ranges and steps (decision 67), each a whole number; the refill's slider starting at NEVER, its left end; the bars off
at first; the team and the outfits hidden and empty at first."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from companions import settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def shape(option) -> tuple:
    return option.identifier, option.value, option.min_value, option.max_value, option.step, option.is_integer


check("health: ×4 at first, ×1 to ×20 by 1", shape(settings.health) == ("health_times", 4, 1, 20, 1, True))
check("shield: 30 % at first, 0 to 100 % by 10", shape(settings.shield) == ("shield_percent", 30, 0, 100, 10, True))
check("refill: never at first, never or 5 to 120 s by 5", shape(settings.refill) == (
      "shield_refill_s", 0, 0, 120, 5, True) and settings.NEVER == 0)
check("speed: +20 % at first, 0 to +50 % by 10", shape(settings.speed) == ("speed_percent", 20, 0, 50, 10, True))
check("back after death: 45 s at first, 10 to 120 s by 5", shape(settings.back) == (
      "back_after_s", 45, 10, 120, 5, True))
check("the five in the page's order", settings.TEAM == [settings.health, settings.shield, settings.refill,
                                                         settings.speed, settings.back])
check("each with its words", all(option.display_name and option.description for option in settings.TEAM))
check("the bars off at first, under It Follows' name for them", settings.bars.identifier == "companion_bars"
      and settings.bars.value is False)
check("the version of what is kept, then the team and the outfits, hidden, empty at first (review of 23 October "
      "2026: a version written from the first save)", [(option.identifier, option.value, option.is_hidden)
      for option in settings.HIDDEN] == [("companions_saved_version", 1, True), ("companions_team", [], True),
                                         ("companions_outfits", {}, True)])

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
