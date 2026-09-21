"""Tests the rope's two ends: the names tried, the ways of writing, and the refusals kept."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_grapple import rope_ends  # noqa: E402

# The eleven names the game printed on 2026-09-20.
NAMES = ["User.Color Scale", "User.Color", "User.Lifetime", "User.Radius", "User.Width",
         "User.Target", "User.Emissive Scale", "User.OffsetCamera", "User.Delay", "User.Source",
         "User.BeamColor"]

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Effect:
    """The effect as the game hands it over: it takes one name, through one function."""

    def __init__(self, takes: str, through: str = "SetVariablePosition") -> None:
        self.takes, self.written = takes, []
        setattr(self, through, self._put)

    def _put(self, name, value):
        if name != self.takes:
            raise RuntimeError(f"no parameter {name}")
        self.written.append((name, value))


class Library:
    """NiagaraFunctionLibrary: no position setter at all on this build, verified 2026-09-21."""

    def SetNiagaraVariableVec3(self, component, name, value):
        raise RuntimeError(f"{name} is a position, not a vector")


library = Library()

# The name is not known ahead of time: it is read from the effect, which prints it with a User.
# prefix that Niagara's own setter adds again, so both spellings are tried.
check("a name is tried both with and without the prefix",
      set(rope_ends.candidates(["User.Target"], rope_ends.TARGET_WORDS)) == {"User.Target", "Target"})
check("a far end is tried before a colour",
      rope_ends.candidates(["User.Color Scale", "User.Target"], rope_ends.TARGET_WORDS)[0].endswith("Target"))
check("and the two ends never take each other's name",
      not set(rope_ends.candidates(NAMES, rope_ends.TARGET_WORDS))
      & set(rope_ends.candidates(NAMES, rope_ends.SOURCE_WORDS)))
check("a name nothing matches gives nothing to try",
      rope_ends.candidates(["User.Color"], rope_ends.TARGET_WORDS) == ())

PRINTED = "[" + ", ".join("{Name: '" + name + "'}" for name in NAMES) + "]"


def loaded() -> None:
    """The names as the mod gets them in the game: read from the effect, never handed in."""
    rope_ends.reset()
    rope_ends.read_names(types.SimpleNamespace(ExposedParameters=PRINTED))


loaded()
state["misc"].clear()
check("the names are read out of what the effect prints, prefix and spaces kept",
      rope_ends.parameter_names("[{Name: 'User.Beam End'}, {Name: 'User.Color Scale'}]")
      == ["User.Beam End", "User.Color Scale"])
check("an effect that will not print its parameters does not raise",
      rope_ends.read_names(types.SimpleNamespace()) is None)
loaded()
state["misc"].clear()
effect = Effect("User.Target")
found = rope_ends.find(effect, library, rope_ends.TARGET_WORDS, (1.0, 2.0, 3.0), "far end")
check("the name the effect really takes is found", found == "User.Target")
check("and it was written where it was asked", effect.written[-1][1].X == 1.0)
check("what answered is written down", any("takes its far end as" in line for line in state["misc"]))
check("the way of writing is kept", rope_ends._setter == "component.SetVariablePosition")

effect.written.clear()
rope_ends.write(effect, library, "User.Target", (9.0, 0.0, 0.0))
check("writing again goes straight through the way that answered", effect.written[-1][1].X == 9.0)

# A refusal is kept per way of writing, not per name: one kept refusal hid three others and cost a
# whole session on 2026-09-21.
loaded()
blank = types.SimpleNamespace()
check("an effect that takes nothing gives nothing",
      rope_ends.find(blank, library, rope_ends.TARGET_WORDS, (0.0, 0.0, 0.0), "far end") is None)
refused = rope_ends.refusals()
check("every way of writing is named in the refusals",
      all(writer in refused for writer in rope_ends.WRITERS))
check("and a way that does not exist at all says so", "AttributeError" in refused)

# A way of writing that does not exist is abandoned at once: no name will make it work.
loaded()
tried: list[str] = []


class Counting(Effect):
    def _put(self, name, value):
        tried.append(name)
        raise AttributeError("no such function")


rope_ends.find(Counting("never"), library, rope_ends.TARGET_WORDS, (0.0, 0.0, 0.0), "far end")
check("a missing way of writing is dropped after one name, not after every name", len(tried) <= 2)

state["misc"].clear()
rope_ends.tell_writers(Effect("User.Target"), library)
check("what the effect really offers is written", any("what the effect offers" in line for line in state["misc"]))
check("and what the library offers too", any("what the library offers" in line for line in state["misc"]))

rope_ends.reset()
check("a reset forgets the way of writing", rope_ends._setter is None)
check("and the refusals with it", rope_ends.refusals() == "")

point = rope_ends.vector((1.0, 2.0, 3.0))
check("a spot becomes a vector the game understands", (point.X, point.Y, point.Z) == (1.0, 2.0, 3.0))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
