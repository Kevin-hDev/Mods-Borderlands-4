"""The game's beat: one call a frame, taken from the first-person arms' own animation update.

That update runs once a frame (heirloom probes, verified in game), in third person too: 30 shots were fired from
that view on 2026-10-01 (docs/attaque-rayon/enquetes/2026-10-01-troisieme-personne.md).
"""

import time
from typing import Any

from mods_base import hook
from unrealsdk.hooks import Type

from . import attack

ARMS_UPDATE = "/Game/PlayerCharacters/_Shared/Animation/BPAnim_Player_1st.BPAnim_Player_1st_C:BlueprintUpdateAnimation"


# The identifier carries the package's own name, so this hook never replaces another mod's.
@hook(ARMS_UPDATE, Type.POST, hook_identifier=f"{__package__}:frame")
def tick(_obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    attack.on_frame(time.perf_counter())
