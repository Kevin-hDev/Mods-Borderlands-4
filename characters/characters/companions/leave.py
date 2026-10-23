"""A companion taken out of the world when its follow ends otherwise than by its death (decision 59 of docs/renforts,
Kevin, 22 October 2026: at STOP « Ils disparaissent »): before, a team stopped left its companions standing where they
were, unfollowed, with their health and shield, and each start and stop left up to eight more (trial 197).

By GbxDestroyActor(False), the call that took a living enemy born of our spawner out of the world without a crash
(docs/spawn-boss, trial 6 of 5 October 2026, verified in game once), never the engine's K2_DestroyActor, after which
the game crashed (19 h 44 the same day). Its spawner is not touched: it is never destroyed (camps.py), and the
companions' camps take it back as free once none of its characters lives (camps.STUCK_S). A dead one is left to the
game, which takes it away itself; a gone one has nothing left to take.
"""

from typing import Any, Callable

MAX_TEXT = 120


def leave(actor: Any, name: str, announce: Callable[..., None]) -> str:
    """The companion taken out of the world: "removed", "gone" when the game holds it no longer, or why the call
    failed. The call is written before it is made: the SDK log outlives a crash."""
    if actor is None:
        return "gone"
    announce("GbxDestroyActor", on=name)
    try:
        actor.GbxDestroyActor(False)
    except Exception as error:
        return f"failed:{type(error).__name__}:{str(error)[:MAX_TEXT]}"
    return "removed"
