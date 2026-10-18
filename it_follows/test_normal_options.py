"""Tests the normal mode's settings (normal/options.py): Bandit and the allied enemies off at first, whether the mode is
on kept hidden and off at first, the Hardcore off and its progress on at first; the NORMAL MODE page's rows, those the
mode locks apart from the Hardcore's; the settings read as they stand; a value that is no choice read as its
default."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows.normal import levels, options  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    check("the three levels, Bandit at first", options.level.choices == ["Bandit", "Senior", "Predator"]
          and options.level.value == "Bandit")
    check("the allied enemies off at first", options.allies.value is False)
    check("the mode off at first, kept hidden", options.on.value is False and options.on.is_hidden)
    check("the Hardcore off, its progress on", options.hardcore.value is False and options.progress.value is True)
    check("the faster dodges on at first", options.fast_dodges.value is True)
    check("the shields on at first", options.shields.value is True)
    check("the enemies' speed increased at first, of two choices (decision 121)", options.speed.value == "Increased"
          and options.speed.choices == ["Increased", "Reduced"])
    check("the staggers' switch off at first (decision 135)", options.no_staggers.value is False)
    check("the page's rows: the six the mode locks, the Hardcore's two, then the hidden one",
          options.LOCKED == [options.level, options.allies, options.fast_dodges, options.speed, options.shields,
                             options.no_staggers]
          and options.HARDCORE == [options.hardcore, options.progress]
          and options.PAGE == [*options.LOCKED, *options.HARDCORE] and options.ALL == [*options.PAGE, options.on])
    check("the identifiers apart from the Horde's", [option.identifier for option in options.ALL]
          == ["normal_level", "normal_allies", "normal_fast_dodges", "normal_speed", "normal_shields",
              "normal_no_staggers", "normal_hardcore", "normal_hardcore_progress", "normal_on"])
    check("the defaults read as they stand", options.read() == options.Settings(levels.LEVELS["Bandit"], False))
    options.level.value, options.allies.value, options.fast_dodges.value = "Predator", True, False
    check("each choice gives its value", options.read() == options.Settings(levels.LEVELS["Predator"], True, False))
    options.level.value, options.allies.value, options.fast_dodges.value = "Legend", "yes", "no"
    check("a value that is no choice reads as its default",
          options.read() == options.Settings(levels.LEVELS["Bandit"], False))
    options.level.value, options.shields.value = "Bandit", False
    check("the shields switched off at Bandit: none given", options.read().shields is False)
    for name in ("Senior", "Predator"):
        options.level.value = name
        check(f"at {name}, the shields given whatever the option holds (decision 112)", options.read().shields is True)
    options.level.value, options.shields.value = "Bandit", "no"
    check("a value that is no choice reads as on", options.read().shields is True)
    options.shields.value = True
    for name in ("Senior", "Predator"):
        options.level.value, options.speed.value = name, "Reduced"
        chosen = options.read()
        check(f"at {name}, reduced: the level's run and faster dodges x0.85, said so",
              chosen.level == levels.reduced(levels.LEVELS[name]) and chosen.level.name == name
              and chosen.reduced is True)
        options.speed.value = "Increased"
        check(f"at {name}, increased: the level as it is", options.read().level is levels.LEVELS[name]
              and options.read().reduced is False)
    options.level.value, options.speed.value = "Bandit", "Reduced"
    check("at Bandit, reduced holds nothing: the level as it is", options.read().level is levels.LEVELS["Bandit"]
          and options.read().reduced is False)
    options.level.value, options.speed.value = "Predator", "slow"
    check("a speed that is no choice reads as increased", options.read().level is levels.LEVELS["Predator"]
          and options.read().reduced is False)
    options.speed.value = "Increased"
    for name, staggers in (("Bandit", 0.85), ("Senior", 0.75), ("Predator", 0.5)):
        options.level.value = name
        check(f"at {name}, the staggers x{staggers}", options.read().level.staggers == staggers)
    options.no_staggers.value = True
    for name in ("Bandit", "Senior"):
        options.level.value = name
        check(f"at {name}, no staggers switched on holds nothing", options.read().level is levels.LEVELS[name])
    options.level.value = "Predator"
    check("at Predator, no staggers switched on: zero, the rest of the level as it is",
          options.read().level.staggers == 0.0 and options.read().level.speed == levels.LEVELS["Predator"].speed)
    options.speed.value = "Reduced"
    check("at Predator, reduced and no staggers: both", options.read().level.staggers == 0.0
          and options.read().reduced is True and options.read().level.speed < levels.LEVELS["Predator"].speed)
    options.no_staggers.value, options.speed.value = "yes", "Increased"
    check("a value that is no choice reads as off", options.read().level is levels.LEVELS["Predator"])
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
