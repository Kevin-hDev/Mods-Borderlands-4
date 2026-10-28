"""Give the game's valid contextual grapple target priority before starting an Apex shot."""

from . import game, game_target, report, settings

TRAVEL_POINT = "GrapplePoint"
READ_FAILURE = "native interaction could not be checked; input passed to the game"


def has_priority() -> bool | None:
    """None means unavailable targeting; False must also bypass the old proximity heuristic."""
    try:
        pc = game.controller()
        strategy = getattr(pc, "GrappleTargetingStrategy", None) if pc is not None else None
        if strategy is None:
            return None
        target = strategy.BestValidTarget.Grappleable
        if target is None or game_target.mine(target):
            return False
        # Only ordinary travel pads follow the optional native movement preference.
        # Other targets perform gameplay actions that must remain available with either setting.
        if str(target.Class.Name) == TRAVEL_POINT and not bool(settings.keep_game_grapple.value):
            return False
        # Follow the same native validity as the indicator. Narrowing only the
        # action cone made an indicated interaction fail away from the crosshair.
        return True
    except Exception:
        # A failed read must not steal a quest action; the next press tries again.
        report.error_once("native_interaction:read", READ_FAILURE)
        return True
