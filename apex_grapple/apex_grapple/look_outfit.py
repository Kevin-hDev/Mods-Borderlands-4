"""Whether the hunter's outfit covers the hip: then the holster, and the pistol in it, stay hidden under the
clothes.

Kevin, 14 October 2026, after the holster came out through Vex's long coat: « si le chasseur porte une veste ça ne doit
pas dépasser et rester caché ». The holster was fitted on her Premium outfit. Measured on her three bodies, hung as in
the game (docs/apex_grapple/pistolet-grappin/outils/blender_holster_outfits.py, 14 October): her own body's coat,
the part SKPart_DarkSiren_Jacket, crosses it on 2 892 pairs of triangles; her Prison and Premium outfits on none.

The parts worn are read on the body's model, the list of parts the game merges into it (GestaltMeshParts, read in
game in docs/reverse-and-change-hunters, essai 16). The game builds that list again when the outfit changes, on the
same character (essai 17), so it is read each time it matters, never kept. Unreadable, the holster stays hidden:
better missing than through the clothes.
"""

from itertools import islice
from typing import Any

from . import report

COVERING = ("SKPart_DarkSiren_Jacket",)
# Bounded: a hunter's body merges five or six parts.
MAX_PARTS = 32

# What the log last said, so that it speaks only when the outfit changes.
_said: bool | None = None


def covers_hip(character: Any) -> bool:
    global _said
    try:
        parts = [str(part.Name) for part in islice(character.Mesh.GestaltMeshParts, MAX_PARTS)]
    except Exception as error:
        report.error_once("look:outfit", f"the outfit could not be read, the holster stays hidden: {error!r}")
        return True
    covered = any(part in COVERING for part in parts)
    if covered != _said:
        _said = covered
        report.note(f"outfit: {', '.join(parts) or 'no part'}; the holster "
                    + ("stays hidden under it" if covered else "shows on the hip"))
    return covered


def forget() -> None:
    global _said
    _said = None
