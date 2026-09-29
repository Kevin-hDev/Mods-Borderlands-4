"""Keeps one part of Apex Heirloom from running in two installed files at once: the full mod next to Tidy Weapons or
Heirloom, or the same file under two names.

Tidy Weapons and Heirloom run side by side, as the full mod runs both parts. The same part twice must not: two holsters
would put the weapon away twice on one press, and two heirlooms would hang two knives in the hand. The Nexus page asks
the player not to install both, and this check holds when the page is not read.

A file that would run a part another switched-on file already runs does not switch on, and says so. As Apex Movement's
family.py, from which it is taken.
"""

import sys
from typing import Any

from mods_base import Mod
from unrealsdk import logging

from . import pack, parts

# A sibling is any module that carries this same pack.py: it has these three names, and Apex Movement's does not.
MARKS = ("NAME", "PARTS", "runs")


def _running(this_package: str) -> list[tuple[str, Any]]:
    """Every other switched-on file of this family, by package name. Read from a copy: modules load while we walk.

    Switched on, not merely installed: a file the player turned off runs nothing (Apex Movement's review, 2026-09-18).
    """
    found = []
    for name, module in list(sys.modules.items()):
        if name == this_package or "." in name:
            continue
        sibling = getattr(module, "pack", None)
        if sibling is None or not all(hasattr(sibling, mark) for mark in MARKS):
            continue
        if getattr(getattr(module, "mod", None), "is_enabled", False):
            found.append((name, sibling))
    return found


def clash(this_package: str, parts: list[str]) -> str:
    """The first switched-on sibling running one of these parts, and which ones; empty when there is none."""
    for name, sibling in _running(this_package):
        shared = [part for part in parts if sibling.runs(part)]
        if shared:
            return f"{sibling.NAME} ({name}) already runs {', '.join(shared)}"
    return ""


def blocked() -> str:
    """Why this file cannot switch on now, empty when it can: the window says it, rather than a failed save."""
    return clash(__package__, [part.switch.identifier for part in parts.PARTS])


class FamilyMod(Mod):
    """A mod that checks for a clash before switching on, rather than switching off again after.

    mods_base switches a mod on from its settings file while build_mod is still running, before the module's own `mod`
    exists: refusing here, as Apex Movement does, also leaves the settings file as it was, so once the other file is
    gone the next launch switches this one on again.
    """

    def enable(self) -> None:
        if not self.is_enabled:
            found = blocked()
            if found:
                logging.warning(f"[{pack.NAME}] {found}: {pack.NAME} stays off; turn one of the two off, or remove it")
                return
        super().enable()
