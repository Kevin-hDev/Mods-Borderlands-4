"""Puts the frame's clock to sleep while nobody drives, and wakes it when the game says a player changed body.

Why (docs/performance/enquetes/2026-10-24-cout-vehicle-driving.md, item 14): on foot the clock woke Python at every
animation update, over a thousand times a second in a Horde, only to see whether someone got in.

The signals were seen at each entry in game, 2026-10-25: PlayerController:ClientRestart in every role (solo, the host
for itself and for each guest's controller, the guest for itself), Controller:OnRep_Pawn on a guest's game, and the
OnStartedDriving of the Echo4 script every character carries. Three, so one missed or renamed by a patch leaves the
others. A signal does not always come with the new body (a guest's first ClientRestart still has the character): it
opens a window in which the frame looks for itself. Leaving needs no signal: awake while anyone drives, the frame sees
it.

The clock is mods_base's hook of frame.py, which mods_base enables and disables with the mod; the signals' hook goes
with the mod too, so an asleep clock is never woken while the mod is off. Disabling the clock from inside its own call
is done as the performance probes end themselves from their own hook (docs/performance/sondes/run_perf_bench.py).
"""

import time
from typing import Any

from mods_base import hook
from unrealsdk.hooks import Type

from . import report

ECHO4_STARTED = ("/Game/PlayerCharacters/_Shared/GBXScripts/Script_Echo4.Script_Echo4_C"
                 ":GbxActorScriptEvt__VehicleScriptEvents_OnStartedDriving")
MS = 1_000_000
# A guest's second ClientRestart, the one with the vehicle, came 66 ms after the first in game; two seconds also cover
# a slow frame or a loading hitch.
WINDOW_NS = 2_000 * MS

_clock: Any = None
_asleep = False
_until_ns = 0


def watch(clock: Any) -> None:
    """The clock to put to sleep and wake: frame.py's hook."""
    global _clock
    _clock = clock


def settle(now_ns: int, busy: bool) -> None:
    """After each frame: kept while anyone drives and for the window after the last signal or drive, then asleep."""
    global _asleep, _until_ns
    if busy:
        # A frame came, so the clock runs, whatever woke it.
        _asleep = False
        _until_ns = max(_until_ns, now_ns + WINDOW_NS)
        return
    if _asleep or now_ns < _until_ns:
        return
    _asleep = True
    _clock.disable()
    report.note("asleep: nobody drives")


def wake_at(now_ns: int, cause: str) -> None:
    global _asleep, _until_ns
    _until_ns = max(_until_ns, now_ns + WINDOW_NS)
    if _asleep:
        _asleep = False
        _clock.enable()
        report.note(f"woken by {cause}")


def reset() -> None:
    """The mod switched off: mods_base enables the clock again with the mod, awake."""
    global _asleep, _until_ns
    _asleep = False
    _until_ns = 0


def _cause(func: Any) -> str:
    try:
        return str(func.func.Name)
    except Exception:
        # The name is only said in the log: the clock wakes all the same.
        return "a signal of the game"


@hook(ECHO4_STARTED, Type.POST)
@hook("/Script/Engine.Controller:OnRep_Pawn", Type.POST)
@hook("/Script/Engine.PlayerController:ClientRestart", Type.POST, hook_identifier=f"{__package__}:wake")
def woken(_obj: Any, _args: Any, _ret: Any, func: Any) -> None:
    try:
        wake_at(time.perf_counter_ns(), _cause(func))
    except Exception as exc:
        report.error_once(f"wake:{type(exc).__name__}", f"a wake-up of the frame failed: {exc!r}")
