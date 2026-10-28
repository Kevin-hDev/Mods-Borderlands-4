"""Tests the guard between the files of Apex Heirloom: a file refuses to switch on while another switched-on file runs
one of its parts, and says which; a file switched off, running other parts, the package's own submodules, Apex
Movement's files and this file itself never keep it off."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

state = heirloom_stubs.install()
from apex_heirloom import family, mod  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def sibling(name: str, parts: tuple[str, ...], on: bool = True, marks: bool = True) -> types.ModuleType:
    """A loaded file of this family, as the SDK imports one: its pack.py and its mod."""
    module = types.ModuleType(name)
    names = {"NAME": name.replace("_", " ").title()}
    if marks:
        names.update(PARTS=parts, runs=lambda part: not parts or part in parts)
    else:  # Apex Movement's pack.py: its own names for the same idea
        names.update(CARRIES=parts, carries=lambda part: True)
    module.pack = types.SimpleNamespace(**names)
    module.mod = types.SimpleNamespace(is_enabled=on)
    sys.modules[name] = module
    return module


both = ["heirloom", "holster"]
check("alone, nothing keeps it off", family.clash("apex_heirloom", both) == "" and family.blocked() == "")
# Marked on rather than switched on and off: switching off takes our list back from the game's arms, not in this test.
mod.is_enabled = True
check("switched on, this file is not its own sibling", family.clash("apex_heirloom", both) == "")
mod.is_enabled = False

sibling("tidy_weapons", ("holster",))
check("a switched-on file running one of its parts keeps it off, and is named with that part",
      family.clash("apex_heirloom", both) == "Tidy Weapons (tidy_weapons) already runs holster"
      and family.blocked() == "Tidy Weapons (tidy_weapons) already runs holster")
check("a file running only other parts does not", family.clash("heirloom", ["heirloom"]) == "")
sys.modules["tidy_weapons"].mod.is_enabled = False
check("switched off, it does not either", family.blocked() == "")
del sys.modules["tidy_weapons"]

sibling("other_mod.sub", ("holster",))
sibling("apex_movement", (), marks=False)
check("a package's own submodule and Apex Movement's files are not of this family", family.blocked() == "")
del sys.modules["other_mod.sub"], sys.modules["apex_movement"]

sibling("heirloom", ("heirloom",))
mod.enable()
check("refused, it stays off and says why, under its name",
      not mod.is_enabled and state["warnings"][-1] == "[Apex Heirloom] Heirloom (heirloom) already runs heirloom: "
      "Apex Heirloom stays off; turn one of the two off, or remove it")
del sys.modules["heirloom"]
mod.enable()
check("that file gone, it switches on", mod.is_enabled)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
