"""What a KO does to a player knocked down in a duel, host or guest; duel.py decides when.

Kevin, 16 October 2026: the loser stays KO on the ground 3 s, neither hurting nor hurt, then stands up where he fell
(docs/duel/README.md, décisions). Without the mod, a player knocked down dies about ten seconds later and comes back at
the zone's station, far away (trial 2).

KO: the game's countdown to death paused (PauseDownStateTimer): without it, after six falls in 43 s the host died 0.14 s
after standing up (trial 6), with it eight falls in a row stood up in place (trial 7); then bCanBeDamaged off, the
arena's shield, so that no enemy around hurts him either. Standing up: StopDownState(revived), the reason the game gives
when a teammate stands a player up, the countdown let go, his health and shield refilled to full but not his overshield,
which the duel never gives (trial 3), bCanBeDamaged as before. Verified in game on host and guest, trials 4 to 8.
"""

from typing import Any

import unrealsdk

from . import report

DAMAGE = "DamageStatics"
REASONS, REVIVED = "EExitDownStateReason", "revived"
PAUSE_REASON = "CoopDuelKO"
FULL = 1.0
SKIPPED_LAYER = "Overshield"
# A player holds three health layers (flesh, shield, overshield); the bound keeps a broken list from running long.
MAX_LAYERS = 8


def damage_library() -> Any:
    done, found = report.called(f"find_class({DAMAGE})", lambda: unrealsdk.find_class(DAMAGE).ClassDefaultObject)
    return found if done else None


def protect(label: str, pawn: Any) -> bool:
    """The countdown paused, then bCanBeDamaged off; whether he could be hurt before, True when unreadable, the
    engine's default, so that he is never left unhurtable."""
    report.called(f"PauseDownStateTimer({label}, True)", lambda: pawn.PauseDownStateTimer(True, PAUSE_REASON))
    done, before = report.called(f"bCanBeDamaged of {label}", lambda: bool(pawn.bCanBeDamaged))
    report.called(f"bCanBeDamaged({label}) = False", lambda: setattr(pawn, "bCanBeDamaged", False))
    return before if done else True


def stand_up(damage: Any, label: str, pawn: Any, damageable: bool) -> bool:
    """Stood up in place, health and shield full: whether the game no longer shows him down."""
    done, reason = report.called(f"{REASONS}.{REVIVED}", lambda: getattr(unrealsdk.find_enum(REASONS), REVIVED))
    if done:
        report.called(f"StopDownState({label})", lambda: pawn.StopDownState(reason))
    report.called(f"PauseDownStateTimer({label}, False)", lambda: pawn.PauseDownStateTimer(False, PAUSE_REASON))
    done, kinds = report.called(f"health types of {label}", lambda: [
        slot.HealthType for slot in list(pawn.HealthState.HealthTypeStates)[:MAX_LAYERS]])
    for kind in kinds if done and damage is not None else []:
        if SKIPPED_LAYER in report.shown(kind):
            continue
        report.called(f"RefillHealthPercent({label}, {report.shown(kind)})",
                      lambda kind=kind: damage.RefillHealthPercent(pawn, kind, FULL, FULL))
    report.called(f"bCanBeDamaged({label}) = {damageable}", lambda: setattr(pawn, "bCanBeDamaged", damageable))
    _done, down = report.called(f"InDownState({label})", lambda: pawn.InDownState())
    report.note("stood up", character=label, down_after=report.shown(down))
    return down is False
