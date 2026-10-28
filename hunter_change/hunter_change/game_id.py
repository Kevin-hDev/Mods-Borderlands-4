"""Which saved game is loaded: the player state's ActiveCharGuid, which equals the save's own char_guid and changes
with the game loaded, without a restart (essai 28, 2026-09-28)."""

import re
from typing import Any

WORDS = ("A", "B", "C", "D")
UNSET = "0" * 32
# The id as the save writes it (char_guid) and game_id() returns it: every module that checks an id checks it here.
PATTERN = re.compile(r"[0-9A-F]{32}")


def game_id(player_state: Any) -> str | None:
    """The id as the save writes it, four words in hex; None while unset or unreadable. The game hands each word as a
    signed 32-bit number."""
    try:
        guid = player_state.ActiveCharGuid
        text = "".join(f"{int(getattr(guid, word)) & 0xFFFFFFFF:08X}" for word in WORDS)
    except (AttributeError, TypeError, ValueError):
        return None
    return None if text == UNSET else text
