"""Tests Companions' sliders read from the settings file (companions/slider_option.py, review of 23 October 2026):
a number within the range kept, rounded for an integer slider; null, a list, an object, a word, true, an endless
number or not-a-number: the slider's starting value, said once; a number out of the range: its nearest end, said;
the load never raises, so that a file edited by hand never keeps Companions from loading. The five sliders of the
SETTINGS page are such sliders (settings.py)."""

import math

import sdk_stubs

state = sdk_stubs.install()

from companions import settings  # noqa: E402
from companions.slider_option import BoundedSliderOption  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def loaded(value: object) -> object:
    """A health slider as settings.py makes it, loaded with that value."""
    option = BoundedSliderOption("health_times", 4, 1, 20, 1, True)
    option._from_json(value)
    return option.value


def said(identifier: str = "health_times") -> int:
    return sum(f"saved value of {identifier}" in text for text in state["errors"])


check("the five sliders of the SETTINGS page read so", all(isinstance(option, BoundedSliderOption)
                                                          for option in settings.TEAM))
check("a number within the range: kept, nothing said", loaded(7) == 7 and said() == 0)
check("an integer slider: rounded", loaded(7.6) == 8)
try:
    results = [loaded(value) for value in (None, [5], {"a": 1}, "seven", True, math.inf, -math.inf, math.nan)]
    raised = None
except Exception as error:
    results, raised = [], error
check("null, a list, an object, a word, true, an endless number, not-a-number: never raises, the starting value",
      raised is None and results == [4] * 8)
check("said once in the SDK log, with what the file held", said() == 1 and "(None)" in next(
      text for text in state["errors"] if "saved value of health_times" in text))
refill = BoundedSliderOption("shield_refill_s", 0, 0, 120, 5, True)
refill._from_json(500)
check("out of its range: its nearest end, said", refill.value == 120 and said("shield_refill_s") == 1)
refill._from_json(-3)
check("below it: its other end", refill.value == 0)
steps = []
for value in (3, 2, 7.4):
    refill._from_json(value)
    steps.append(refill.value)
check("between two steps: the nearest step, as the slider shows it and the team applies it (3 s, 5 s)",
      steps == [5, 0, 5])
shield = BoundedSliderOption("shield_percent", 30, 0, 100, 10, True)
shield._from_json(35)
check("a share between two steps too", shield.value in (30, 40))
fine = BoundedSliderOption("fine", 0.5, 0.0, 1.0, 0.1, False)
before = len(state["errors"])
fine._from_json(0.3)
check("a decimal step: a value already on it kept as it is, nothing said", fine.value == 0.3
      and len(state["errors"]) == before)
fine._from_json(0.34)
check("and one between two of its steps brought onto the nearest, without float noise", fine.value == 0.3)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
raise SystemExit(1 if fails else 0)
