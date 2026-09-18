"""Tests the guard between files of the same pack: siblings are found, and only a shared movement is a clash."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_movement import family  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def sibling(package: str, name: str, carries: tuple[str, ...]) -> None:
    """A loaded file of the same pack, as the game would have it in sys.modules."""
    pack = types.SimpleNamespace(NAME=name, CARRIES=carries,
                                 carries=lambda movement, c=carries: not c or movement in c)
    sys.modules[package] = types.SimpleNamespace(pack=pack)


# The real package is loaded here by the import above, and it carries everything: it would clash with every check
# below, correctly. Set aside so the test plays the siblings it means to.
real = sys.modules.pop("apex_movement")

check("alone, nothing clashes", family.clash("apex_slides", ["Slides"]) == "")

sibling("apex_dash", "Apex Dash", ("Dash",))
check("a sibling carrying another movement is no clash", family.clash("apex_slides", ["Slides"]) == "")

sibling("apex_slides_copy", "Apex Slides", ("Slides",))
clash = family.clash("apex_slides", ["Slides"])
check("a sibling carrying the same movement is a clash", clash != "")
check("the clash names the other file and the movement",
      "Apex Slides" in clash and "apex_slides_copy" in clash and "Slides" in clash)

check("a file does not clash with itself", family.clash("apex_slides_copy", ["Slides"]) == "")

sibling("apex_movement_full", "Apex Movement", ())
check("the full pack clashes with every separate file", family.clash("apex_dash", ["Dash"]) != "")

del sys.modules["apex_movement_full"], sys.modules["apex_slides_copy"]
check("once the other file is gone, nothing clashes", family.clash("apex_slides", ["Slides"]) == "")

sys.modules["not_ours"] = types.SimpleNamespace(pack=types.SimpleNamespace(NAME="Something else"))
check("a module with a pack of its own but not ours is ignored", family.clash("apex_slides", ["Slides"]) == "")

sys.modules["mods_base.something"] = types.SimpleNamespace(pack=types.SimpleNamespace(
    NAME="Apex Slides", CARRIES=("Slides",), carries=lambda movement: True))
check("a submodule is not taken for a file of the pack", family.clash("apex_slides", ["Slides"]) == "")

sys.modules["apex_movement"] = real
check("the real full pack is found once it is back", family.clash("apex_slides", ["Slides"]) != "")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
