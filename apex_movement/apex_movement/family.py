"""Finds the other files of this pack already loaded, and the movements two of them would both run.

Several separate files can be installed side by side (Kevin, 2026-09-18), because no two movements write the same
game value. What must not happen is the same movement running twice — the full pack next to a separate file, or the
same file under two names. Both copies would write one field each frame and each would believe it owns the game's
original value, so whichever stopped last would put back what the other had already written.

A file that finds one of its movements already running says so and stays off, rather than fighting for the field.
"""

import sys
from typing import Any

# A sibling is any module that carries this same pack.py: it has these three names and nothing else does.
MARKS = ("NAME", "CARRIES", "carries")


def _packs(this_package: str) -> list[tuple[str, Any]]:
    """Every other loaded package of this family, by name. Read from a copy: modules load while we walk."""
    found = []
    for name, module in list(sys.modules.items()):
        if name == this_package or "." in name:
            continue
        pack = getattr(module, "pack", None)
        if pack is not None and all(hasattr(pack, mark) for mark in MARKS):
            found.append((name, pack))
    return found


def clash(this_package: str, carried: list[str]) -> str:
    """The first sibling running one of these movements, and which ones; empty when there is none."""
    for name, pack in _packs(this_package):
        shared = [movement for movement in carried if pack.carries(movement)]
        if shared:
            return f"{pack.NAME} ({name}) already runs {', '.join(shared)}"
    return ""
