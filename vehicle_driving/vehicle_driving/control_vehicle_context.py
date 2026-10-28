"""Vehicle window context includes a driven Pawn when OakCharacter is absent."""
from mods_base import get_pc


def same(session, pc):
    character = session.character()
    return (pc is not None and pc == get_pc(possibly_loading=True)
            and ((session.frontend and getattr(pc, "OakCharacter", None) is None
                  and getattr(pc, "Pawn", None) is None)
                 or (character is not None and getattr(pc, "OakCharacter", None) == character)
                 or (character is None and session.pawn() is not None
                     and getattr(pc, "Pawn", None) == session.pawn())))
