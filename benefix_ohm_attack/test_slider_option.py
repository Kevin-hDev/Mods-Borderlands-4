"""Tests a slider's persisted option: whatever the settings file holds, a number within the slider's bounds.

The fake SDK's slider loads as the game's own does (mods_base/options.py, read on 2026-10-01): each value below is
one the audit of that day ran through the real one.
"""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from mods_base import SliderOption  # noqa: E402

from benefix_ohm_attack import report  # noqa: E402
from benefix_ohm_attack.slider_option import BoundedSliderOption  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def damage() -> BoundedSliderOption:
    return BoundedSliderOption("damage", 75, 5, 2000, step=5, is_integer=True)


def loaded(option, text: str):
    """The option's value once the settings file has given it this JSON."""
    option._from_json(json.loads(text))
    return option.value


plain = SliderOption("damage", 75, 5, 2000, step=5, is_integer=True)
check("the SDK's own slider keeps a number out of its range", loaded(plain, "100000000") == 100000000)
try:
    loaded(SliderOption("damage", 75, 5, 2000, step=5, is_integer=True), "null")
    check("and lets a value that is no number raise out of the settings' load", False)
except TypeError:
    check("and lets a value that is no number raise out of the settings' load", True)

check("a saved value within the bounds is kept", loaded(damage(), "150") == 150 and type(loaded(damage(), "150")) is int)
check("above the range, the highest bound", loaded(damage(), "100000000") == 2000)
check("below it, the lowest", loaded(damage(), "-50") == 5)
check("a number written as text is read", loaded(damage(), '"300"') == 300)
for label, text in (("not a number (NaN)", "NaN"), ("text", '"abc"'), ("nothing (null)", "null"), ("a list", "[1]")):
    report.reset()
    check(f"a saved value that is {label}: the default, and the load goes on", loaded(damage(), text) == 75)
check("an endless one: the highest bound, and the load goes on", loaded(damage(), "1e400") == 2000)
errors = len(state["errors"])
report.reset()
loaded(damage(), "null")
loaded(damage(), "null")
check("a value the SDK cannot even read is said once", len(state["errors"]) == errors + 1)

delay = BoundedSliderOption("regen_delay", 2.0, 0.0, 10.0, step=0.5, is_integer=False)
check("a slider that is not a whole number keeps its decimals", loaded(delay, "2.5") == 2.5)
check("and is bounded the same", loaded(delay, "1e9") == 10.0 and loaded(delay, "-3") == 0.0)
check("not a number on it: the default", loaded(delay, "NaN") == 2.0)

for label, text, kept in (("out of the range", "100000000", "2000"), ("endless", "1e400", "2000"),
                          ("nothing", "null", "75")):
    report.reset()
    errors = len(state["errors"])
    loaded(damage(), text)
    check(f"a saved value that is {label} is said as replaced, with what the mod goes on with",
          len(state["errors"]) == errors + 1 and state["errors"][-1].endswith(f"it goes on with {kept}"))
report.reset()
errors = len(state["errors"])
loaded(delay, "NaN")
check("so is not-a-number on a slider with decimals, which the SDK takes without a word",
      len(state["errors"]) == errors + 1 and "regen_delay" in state["errors"][-1])
report.reset()
errors = len(state["errors"])
loaded(damage(), "150")
loaded(delay, "2.5")
check("a saved value within the bounds says nothing", len(state["errors"]) == errors)
loaded(damage(), "null")
loaded(BoundedSliderOption("drain", 20, 0, 100, step=1, is_integer=True), "null")
check("each slider says its own trouble", len(state["errors"]) == errors + 2)
report.reset()
loaded(damage(), "[" + ", ".join(["1"] * 500) + "]")
check("a long value is not copied whole into the log", len(state["errors"][-1]) < 200)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
