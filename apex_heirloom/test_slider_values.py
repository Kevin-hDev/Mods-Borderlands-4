"""Tests a slider's value as the mod uses it: within its bounds as it is, out of them the nearest bound, and what is
not a number, or not a number at all, the default."""

import pathlib
import sys
import types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()
from apex_heirloom.slider_values import bounded  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def slider(value: object) -> object:
    return types.SimpleNamespace(value=value, default_value=0.4, min_value=0.2, max_value=1.0)


check("within its bounds, the value as it is", bounded(slider(0.6)) == 0.6 and bounded(slider("0.6")) == 0.6)
check("out of them, the nearest bound", bounded(slider(5)) == 1.0 and bounded(slider(0)) == 0.2
      and bounded(slider(float("inf"))) == 1.0)
check("not a number, the default", bounded(slider("fast")) == 0.4 and bounded(slider(None)) == 0.4
      and bounded(slider(float("nan"))) == 0.4)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
