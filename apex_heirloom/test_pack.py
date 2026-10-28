"""Tests which parts a file runs: the sources build the full mod, both parts under the name Apex Heirloom; a separate
file names its parts; and the names stay apart from Apex Movement's pack.py, whose family check would take this one
for its own."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()
from apex_heirloom import family, heirloom_settings, holster_settings, pack, parts  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


both = (heirloom_settings.heirloom.identifier, holster_settings.holster.identifier)
check("the sources are the full mod, Apex Heirloom, running both parts",
      pack.NAME == "Apex Heirloom" and pack.PARTS == () and all(pack.runs(part) for part in both)
      and parts.PARTS == (parts.HEIRLOOM, parts.HOLSTER))
pack.PARTS = ("holster",)
check("a separate file runs the parts it names, and no other", pack.runs("holster") and not pack.runs("heirloom"))
pack.PARTS = ()
check("its marks are its family's, and none of Apex Movement's (CARRIES, carries)",
      all(hasattr(pack, mark) for mark in family.MARKS)
      and not hasattr(pack, "CARRIES") and not hasattr(pack, "carries"))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
