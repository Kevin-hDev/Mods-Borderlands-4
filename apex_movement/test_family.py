"""Tests the guard between files of the same pack: only a switched-on sibling running a shared movement is a clash,
and a clash keeps the file off without touching its settings file."""

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


def sibling(package: str, name: str, carries: tuple[str, ...], on: bool = True) -> None:
    """A loaded file of the same pack, as the game would have it in sys.modules, switched on or off."""
    pack = types.SimpleNamespace(NAME=name, CARRIES=carries,
                                 carries=lambda movement, c=carries: not c or movement in c)
    sys.modules[package] = types.SimpleNamespace(pack=pack, mod=types.SimpleNamespace(is_enabled=on))


# The real package is loaded by the import above and carries everything; set aside so the test plays the siblings it
# means to, and put back at the end.
real = sys.modules.pop("apex_movement")

check("alone, nothing clashes", family.clash("apex_slides", ["Slides"]) == "")

sibling("apex_dash", "Apex Dash", ("Dash",))
check("a sibling running another movement is no clash", family.clash("apex_slides", ["Slides"]) == "")

sibling("apex_slides_copy", "Apex Slides", ("Slides",))
clash = family.clash("apex_slides", ["Slides"])
check("a switched-on sibling running the same movement is a clash", clash != "")
check("the clash names the other file and the movement",
      "Apex Slides" in clash and "apex_slides_copy" in clash and "Slides" in clash)
check("a file does not clash with itself", family.clash("apex_slides_copy", ["Slides"]) == "")

# Installed but switched off by the player: it runs nothing, so it must not keep the wanted file off (review,
# 2026-09-18: the guard looked at what was loaded, not at what was running).
sibling("apex_slides_copy", "Apex Slides", ("Slides",), on=False)
check("a switched-off sibling is no clash", family.clash("apex_slides", ["Slides"]) == "")
sys.modules["apex_mid_import"] = types.SimpleNamespace(pack=types.SimpleNamespace(
    NAME="Apex Slides", CARRIES=("Slides",), carries=lambda movement: True))
check("a sibling whose mod does not exist yet is not running", family.clash("apex_slides", ["Slides"]) == "")
del sys.modules["apex_mid_import"]

sibling("apex_movement_full", "Apex Movement", ())
check("the switched-on full pack clashes with every separate file", family.clash("apex_dash_2", ["Dash"]) != "")
del sys.modules["apex_movement_full"], sys.modules["apex_slides_copy"]
check("once the other file is gone, nothing clashes", family.clash("apex_slides", ["Slides"]) == "")

sys.modules["not_ours"] = types.SimpleNamespace(pack=types.SimpleNamespace(NAME="Something else"),
                                                mod=types.SimpleNamespace(is_enabled=True))
check("a module with a pack of its own but not ours is ignored", family.clash("apex_slides", ["Slides"]) == "")
sys.modules["mods_base.something"] = types.SimpleNamespace(pack=types.SimpleNamespace(
    NAME="Apex Slides", CARRIES=("Slides",), carries=lambda movement: True), mod=types.SimpleNamespace(is_enabled=True))
check("a submodule is not taken for a file of the pack", family.clash("apex_slides", ["Slides"]) == "")

# The mod itself: a clash is checked before anything is switched on, and the settings file is left alone.
guarded = family.FamilyMod(state, name="Apex Movement", on_enable=lambda: state["misc"].append("on_enable ran"))
sibling("apex_dash", "Apex Dash", ("Dash",))
guarded.enable()
check("a clash keeps the file off", guarded.is_enabled is False)
check("before its own start ran", "on_enable ran" not in state["misc"])
check("and says why, naming the other file", any("Apex Dash" in line and "stays off" in line
                                                  for line in state["warnings"]))
check("the settings file keeps what it said, so the file comes back once the other is gone",
      guarded.saved_enabled is None)

sys.modules["apex_dash"].mod.is_enabled = False
guarded.enable()
check("with the other file off, it switches on", guarded.is_enabled is True and "on_enable ran" in state["misc"])

sys.modules["apex_movement"] = real
check("the real full pack, switched off here, is no clash", family.clash("apex_slides", ["Slides"]) == "")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
