"""Co-op guest: from its rope to its landing, its game sends the host each move on its own, never two moves made one.

In third person a guest's body went back and forth by about 5 degrees on most frames of a rope: 76 % of them, against
5 % for the host's own ropes and 2 % for the guest off the rope (measured in both copies, trial 11 of
docs/coop/2026-10-17-saccades-restantes.md, and already 40 % before any co-op fix). With the engine's move combining
off in the guest's game, the body followed the run and Kevin saw it tremble no more (trial 12: « non il ne tremble
plus »). Cause supposed, not read in the engine: a move combined with the one before starts again from that one's
rotation, every other frame. The host sends no moves and never had it.

The engine's variable belongs to the whole game: it is read before the first change, and put back as found when the
window ends or the mod stops. Cost: up to twice as many moves sent to the host during a rope.
"""

from typing import Any

import mods_base
import unrealsdk

from . import game, report

VARIABLE = "p.NetEnableMoveCombining"
# A guest who has not stood on the ground since its rope gets its moves combined again after this long, as the host's
# trust in it ends (coop_trust.LONGEST_NS). Estimate, not measured.
LONGEST_NS = 10_000_000_000

# The variable's value found before the first change, while the window is open; None once it is put back.
_kept: int | None = None
_last_ns = 0


def _library() -> Any:
    return unrealsdk.find_class("KismetSystemLibrary").ClassDefaultObject


def _run(context: Any, command: str) -> None:
    _library().ExecuteConsoleCommand(context, command, game.controller())


def step(character: Any, rope_on: bool, now_ns: int) -> None:
    """Every frame on a guest: combining off while its own rope is under way, and up to its first frame on the ground
    after it."""
    global _kept, _last_ns
    if rope_on:
        _last_ns = now_ns
        if _kept is None:
            found = int(_library().GetConsoleVariableIntValue(VARIABLE))
            _run(character, f"{VARIABLE} 0")
            _kept = found
            report.note(f"co-op: moves sent one by one during the rope ({VARIABLE} {found} -> 0)")
        return
    if _kept is not None and (game.is_on_ground(character.CharacterMovement) or now_ns - _last_ns > LONGEST_NS):
        release(character)


def release(character: Any = None) -> None:
    """Puts the variable back as found; at switch-off with no character, through the game's world."""
    global _kept
    if _kept is None:
        return
    kept, _kept = _kept, None
    context = character if character is not None else mods_base.ENGINE.GameViewport.World
    _run(context, f"{VARIABLE} {kept}")
    report.note(f"co-op: moves combined again ({VARIABLE} {kept})")


def reset() -> None:
    """At switch-off: the variable is put back; a failure is said, the rest of the switch-off goes on."""
    try:
        release(game.character())
    except Exception as exc:
        report.error_once("coop_moves", f"the game's move combining could not be put back: {exc!r}")
