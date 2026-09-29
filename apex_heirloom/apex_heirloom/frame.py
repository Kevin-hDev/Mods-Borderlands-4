"""Counts a held key at each frame of the player's arms, clears in time the weapons flag a skipped lift left set
(restriction.py), and writes the keys in use once the holster has started with all its settings (keys.tell).

The first-person arms' animation, not every animation: it runs once a frame, and only while the arms are animated, on
foot, where there is a weapon to put away. Its frames are verified in game (Holster Your Weapon and the heirloom listen
to it, cosmetics/heirloom/mod/source/apex_holster_follow.py).
"""

import time
from typing import Any

from mods_base import hook
from unrealsdk.hooks import Type

from . import keys, report, restriction

ARMS_FRAME = "/Game/PlayerCharacters/_Shared/Animation/BPAnim_Player_1st.BPAnim_Player_1st_C:BlueprintUpdateAnimation"


@hook(ARMS_FRAME, Type.POST)
def tick(obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    keys.tell()
    restriction.tick(obj)
    if not keys.pending():
        return
    try:
        keys.tick(time.perf_counter())
    except Exception as exc:
        report.error_once("frame", f"held key not counted after an error: {exc!r}")
