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
    check("the page's rows: the three the mode locks, the Hardcore's two, then the hidden one",
          options.LOCKED == [options.level, options.allies, options.fast_dodges]
          and options.HARDCORE == [options.hardcore, options.progress]
          and options.PAGE == [*options.LOCKED, *options.HARDCORE] and options.ALL == [*options.PAGE, options.on])
    check("the identifiers apart from the Horde's", [option.identifier for option in options.ALL]
          == ["normal_level", "normal_allies", "normal_fast_dodges", "normal_hardcore", "normal_hardcore_progress",
              "normal_on"])
    check("the defaults read as they stand", options.read() == options.Settings(levels.LEVELS["Bandit"], False))
    options.level.value, options.allies.value, options.fast_dodges.value = "Predator", True, False
    check("each choice gives its value", options.read() == options.Settings(levels.LEVELS["Predator"], True, False))
    options.level.value, options.allies.value, options.fast_dodges.value = "Legend", "yes", "no"
    check("a value that is no choice reads as its default",
          options.read() == options.Settings(levels.LEVELS["Bandit"], False))
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
