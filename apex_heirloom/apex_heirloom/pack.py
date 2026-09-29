"""Which parts of Apex Heirloom this file runs, and the name it wears in the game's mod list.

The sources build the full mod, both parts. The build tool (borderlands_4/outils/build_heirloom_files.py) writes a
different pack.py into each separate file, so a player can download the holster alone, as Tidy Weapons, or the
heirloom alone, as Heirloom (Kevin, 2026-09-27, before the 1.0.0 went on Nexus: « Les fabriquer d'abord », « Juste
Heirloom »). As Apex Movement's separate files: the same code in every file, these lines only differ.

Named apart from Apex Movement's pack.py (CARRIES, carries) on purpose: its family check takes any loaded module with
those names for one of its own files, and would read the full heirloom as running every movement.
"""

NAME = "Apex Heirloom"
# The parts this file runs, by their switches' identifiers (parts.py). Empty means both: the full mod.
PARTS: tuple[str, ...] = ()


def runs(part: str) -> bool:
    return not PARTS or part in PARTS
