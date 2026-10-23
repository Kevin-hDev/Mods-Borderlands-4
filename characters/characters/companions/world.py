"""What the companions read of the world: It Follows' own reads (reads.py), under the names the follow uses, and the
game's attitude of the hunter toward a character, which It Follows never needed (its enemies are all hostile).

The attitude is GbxTeamFunctionLibrary.GetAttitudeTowards(player, actor), the call the trials read companions and
enemies with since trial 126 of docs/renforts (verified in game: hostile for enemies, friendly for the companions,
docs/spawn-boss/enquetes/2026-10-11-equipes-des-ennemis.md). Nothing is written.
"""

from typing import Any

import unrealsdk

from .. import reads

TEAMS = "GbxTeamFunctionLibrary"
MAX_TEXT = 60

place = reads.point
metres = reads.metres
dead = reads.dead
definition = reads.definition
mode = reads.mode


def hunter(pc: Any) -> Any:
    """What the hunter is now: his vehicle while he drives, his character otherwise; None without a player."""
    return (getattr(pc, "Pawn", None) or getattr(pc, "OakCharacter", None)) if pc is not None else None


def attitude(player: Any, actor: Any) -> str:
    """The game's attitude of the player toward the character, such as hostile or friendly; why when unread."""
    try:
        answer = unrealsdk.find_class(TEAMS).ClassDefaultObject.GetAttitudeTowards(player, actor)
    except Exception as error:
        return f"unread:{type(error).__name__}"
    name = getattr(answer, "name", None)
    return str(name) if isinstance(name, str) else str(answer)[:MAX_TEXT]
