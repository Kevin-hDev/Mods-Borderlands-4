"""Tests how the window names a run (panel_words.py): a level by its place, Level 1 to Level 5, in a button and in a
sentence, in English and in French, a level the mod no longer has by its number; a time limit as its button; when a run
began, today, yesterday or a date, in the player's local time, in each language; how it ended."""

import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import panel_words as words  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def moment(day: int, hour: int, minute: int) -> int:
    return int(time.mktime((2026, 10, day, hour, minute, 0, 0, 0, -1)))


try:
    check("a level by its place, in a button", words.level(25, "EN") == "LEVEL 1" and words.level(100, "FR")
          == "NIVEAU 5")
    check("a level in a sentence", words.level_in_sentence(60, "EN") == "level 3"
          and words.level_in_sentence(60, "FR") == "niveau 3")
    check("a level the mod no longer has, by its number", words.level(120, "EN") == "120"
          and words.level_in_sentence(120, "FR") == "niveau 120")
    check("a time limit as its button", words.limit(1800.0, "FR") == "30 MIN" and words.limit(None, "FR")
          == "ILLIMITÉE" and words.limit(None, "EN") == "UNLIMITED")
    now = moment(14, 18, 0)
    check("today and yesterday", words.when(moment(14, 14, 32), "EN", now) == "TODAY 14:32"
          and words.when(moment(13, 23, 5), "FR", now) == "HIER 23 H 05"
          and words.when(moment(14, 9, 7), "FR", now) == "AUJOURD'HUI 9 H 07")
    check("an older day by its date", words.when(moment(12, 20, 15), "EN", now) == "OCT 12 20:15"
          and words.when(moment(12, 20, 15), "FR", now) == "12 OCT. 20 H 15")
    check("how it ended", words.end("time_up", "FR") == "TEMPS ÉCOULÉ" and words.end("left_game", "EN")
          == "GAME LEFT")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
