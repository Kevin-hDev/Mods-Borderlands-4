"""Tests the words shown: the time played as minutes and seconds, cut, hours past an hour, nothing below nothing; the
bar in English and in French; English for a language the mod does not have."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

from it_follows import texts  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


try:
    check("minutes and seconds", texts.clock(0.0) == "00:00" and texts.clock(277.9) == "04:37")
    check("past an hour, the hours first", texts.clock(3725.0) == "1:02:05")
    check("a time below nothing reads as nothing", texts.clock(-4.0) == "00:00")
    check("the bar in English, the horde that follows before the time", texts.bar(texts.ENGLISH, 12, 1, 37, 277.9)
          == "KILLS 12   DEATHS 1   HORDE 37   04:37")
    check("the bar in French", texts.bar(texts.FRENCH, 12, 1, 37, 277.9) == "TUÉS 12   MORTS 1   HORDE 37   04:37")
    check("English for a language the mod does not have", texts.bar("Klingon", 0, 0, 0, 0.0)
          == "KILLS 0   DEATHS 0   HORDE 0   00:00")
    check("the two languages, English first", texts.LANGUAGES == (texts.ENGLISH, texts.FRENCH))
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
