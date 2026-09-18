"""Keeps one movement from running in two installed files of this pack at once.

Several separate files can be installed side by side (Kevin, 2026-09-18), because no two movements write the same
game value. What must not happen is the same movement running twice — the full pack next to a separate file, or the
same file under two names. Both copies would write one field each frame and each would believe it owns the game's
original value, so whichever stopped last would put back what the other had already written.

A file that would run a movement another switched-on file already runs does not switch on, and says so.
"""

import sys
from typing import Any

from mods_base import Mod

from . import movements, pack, report

# A sibling is any module that carries this same pack.py: it has these three names and nothing else does.
MARKS = ("NAME", "CARRIES", "carries")


def _running(this_package: str) -> list[tuple[str, Any]]:
    """Every other switched-on file of this family, by package name. Read from a copy: modules load while we walk.

    Switched on, not merely installed: a file the player turned off runs nothing, and refusing because of it kept the
    only file actually wanted off for good (review, 2026-09-18).
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


def clash(this_package: str, carried: list[str]) -> str:
    """The first switched-on sibling running one of these movements, and which ones; empty when there is none."""
    for name, sibling in _running(this_package):
        shared = [movement for movement in carried if sibling.carries(movement)]
        if shared:
            return f"{sibling.NAME} ({name}) already runs {', '.join(shared)}"
    return ""


def carried() -> list[str]:
    return [movement.name for movement in movements.MOVEMENTS if pack.carries(movement.name)]


class FamilyMod(Mod):
    """A mod that checks for a clash before switching on, rather than switching off again after.

    mods_base switches a mod on from its settings file while build_mod is still running (mod_factory.py:149, then
    settings.py:71), before the module's own `mod` exists: a refusal from on_enable raised NameError with the hooks
    already on, and the movement ran twice (review, 2026-09-18). Refusing here also leaves the settings file as it
    was, so once the other file is gone the next launch switches this one on again.
    """

    def enable(self) -> None:
        if not self.is_enabled:
            found = clash(__package__, carried())
            if found:
                report.warning(f"{found}: {pack.NAME} stays off; turn one of the two off, or remove it")
                return
        super().enable()
