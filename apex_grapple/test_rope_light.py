"""Tests lighting the rope: the switch found whatever its shape, and never fatal."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import rope_light  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def fresh() -> None:
    state["misc"].clear()
    state["errors"].clear()


class Beam:
    def __init__(self, lights: bool = True) -> None:
        self.lit, self.lights = [], lights

    def Activate(self, reset: bool = True):
        if not self.lights:
            raise RuntimeError("no switch")
        self.lit.append(reset)


fresh()
beam = Beam()
check("the rope is lit", rope_light.switch_on(beam) is True)
# Reset as it lights: it starts on the two ends written a moment earlier, not on the asset's own.
check("and reset as it lights", beam.lit == [True])
check("nothing is written as an error", not state["errors"])

# A build whose switch takes no argument still gets its rope lit.
fresh()


class OldSwitch:
    def __init__(self) -> None:
        self.lit = []

    def Activate(self, *arguments):
        if arguments:
            raise TypeError("Activate takes no argument on this build")
        self.lit.append(None)


old = OldSwitch()
check("a switch that takes no argument is still found", rope_light.switch_on(old) is True)
check("and it was called bare", old.lit == [None])

fresh()
check("a beam with no switch at all says so", rope_light.switch_on(Beam(lights=False)) is False)
check("once, as an error", sum("could not be lit" in line for line in state["errors"]) == 1)

fresh()
check("a beam that is not an object at all costs nothing",
      rope_light.switch_on(types.SimpleNamespace()) is False)

# The four shields this file carried for one version are gone: the rope stayed active and visible at
# +0.2, +0.4, +0.8 and +1.2 s, and they had made the mod's rope differ from the game's.
check("no shield is taken any more", not hasattr(rope_light, "SHIELDS"))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
