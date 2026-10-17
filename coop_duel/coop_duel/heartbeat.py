"""The frame hook that beats the duel: any animation update calls it, many times a frame, and the duel acts once per
duel.STEP_S (the same hook the duel's trials ran on the host, trials 4 to 8). Without a duel it only takes the score's
message off the screen once shown long enough."""

from typing import Any

from mods_base import hook
from unrealsdk.hooks import Type

from . import duel, report

HOOK_PATH = "/Script/Engine.AnimInstance:BlueprintUpdateAnimation"


@hook(HOOK_PATH, Type.POST, hook_identifier=f"{__package__}:heartbeat")
def tick(_obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    try:
        duel.beat(duel.clock())
    except Exception as error:
        report.error_once(f"tick:{type(error).__name__}", f"a duel beat was cut short ({type(error).__name__})")
