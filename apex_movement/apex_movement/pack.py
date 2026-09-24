"""Which movements this file carries, and the name it wears in the game's mod list.

The sources build the full pack. The build tool (build_movement_files.py) writes a different pack.py into each
separate file, so one movement can be downloaded on its own (conception, decision 2) and several installed side by
side (Kevin, 2026-09-18).

Side by side works because the files share nothing at runtime: each carries its own copy of the package under its own
name, so its imports, its frame hook and its settings file are its own, and no two movements write the same game
value (checked by test_movement_rules.py). Only a movement carried twice would collide, which is why a separate file
never repeats one the full pack already installed alongside it would run.
"""

from . import movements

NAME = "Apex Movement"
# The movements this file carries, by name. Empty means all of them, which is the full pack.
CARRIES: tuple[str, ...] = ()


def is_full() -> bool:
    return CARRIES == ()


def carries(movement_name: str) -> bool:
    return not CARRIES or movement_name in CARRIES


def carries_module(module: str) -> bool:
    """Shared modules are in every file; a movement's modules only in the files that carry it."""
    if module in movements.FULL_ONLY:
        return is_full()
    owner = movements.owner(module)
    return owner is None or carries(owner.name)


def carries_group(identifier: str) -> bool:
    """A menu line shows only in the files carrying the movement it belongs to."""
    for movement in movements.MOVEMENTS:
        if identifier in movement.menu_groups:
            return carries(movement.name)
    return True
