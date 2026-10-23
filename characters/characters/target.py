"""Whom an enemy targets, and the hunter imposed as its target: It Follows imposes the hunter on each enemy of the
horde, imposes him again once the game has cleared him, and clears what it imposed when it lets the enemy go.

Both go through GbxTargetingFunctionLibrary as the enemy research did in game: GetPrimaryTarget since 2026-09-28,
AISetScriptedTarget and AIClearScriptedTarget in séance 31. TargetPatch, live and live_status are the research's
(mods/perso/apex_probe/source/apex_brain_target_patch.py), which the trials loaded (docs/RUN/sondes/run_zone_target.py);
It Follows keeps its own copy (decision 45). The patch never replaces another script's target and never clears one it
did not set.
"""

from typing import Any, Callable

import unrealsdk

LIBRARY = "GbxTargetingFunctionLibrary"
MAX_TEXT = 40
# The library's default object, through a weak pointer as every game object It Follows keeps (teams.py, ground.py):
# asked twice an enemy a second, 240 times with 120 enemies, it was looked for by name each time (audit of 15 October
# 2026).
_held: dict[str, Any] = {"library": None}


def live(actor: Any) -> bool:
    return live_status(actor) == "alive"


def live_status(actor: Any) -> str:
    """alive, or why not: expired, dead, health_unknown (the game does not say it with a bool), root_missing, or which
    read raised. Only a sure alive passes, and the reason is kept for the stops that come early."""
    if actor is None:
        return "expired"
    try:
        dead = actor.HealthState.bCurrentlyDead
    except Exception:
        return "health_read_failed"
    if dead is True:
        return "dead"
    if dead is not False:
        return "health_unknown"
    try:
        return "alive" if actor.RootComponent is not None else "root_missing"
    except Exception:
        return "root_read_failed"


class TargetPatch:
    """The hunter imposed on one enemy, owned until restored. actor_ref and player_ref give the characters or None
    (weak pointers); library gives the targeting library's default object."""

    def __init__(self, actor_ref: Callable[[], Any], player_ref: Callable[[], Any],
                 library: Callable[[], Any]) -> None:
        self.actor_ref, self.player_ref, self.library = actor_ref, player_ref, library
        self.pending = False

    def read(self) -> str:
        """The enemy's imposed target: none, player or other; actor_expired or actor_inactive when it cannot be
        asked."""
        actor = self.actor_ref()
        if actor is None:
            return "actor_expired"
        if not live(actor):
            return "actor_inactive"
        target = self.library().AIGetScriptedTarget(AIActor=actor)
        if target is None:
            return "none"
        player = self.player_ref()
        if player is not None and target._get_address() == player._get_address():
            return "player"
        return "other"

    def apply(self) -> None:
        """Imposes the hunter, without the game's restrictions. ValueError when already applied, when the enemy has an
        imposed target already, when the hunter is not alive, or when the write is not read back."""
        if self.pending or self.read() != "none" or not live(self.player_ref()):
            raise ValueError("Target baseline unavailable")
        # Owned before the call: a setter that writes then raises must still be cleared by restore().
        self.pending = True
        self.library().AISetScriptedTarget(AIActor=self.actor_ref(), TargetActor=self.player_ref(),
                                           bApplyRestrictions=False)
        if not self.verify():
            raise ValueError("Target write not confirmed")

    def verify(self) -> bool:
        return self.pending and self.read() == "player"

    def restore(self) -> str:
        """Clears the hunter if he is still the imposed target, and says how it ended: restored, already_original,
        superseded, actor_expired; inactive when never applied; actor_inactive_retry_stop leaves it owned, to try again.
        ValueError, still owned, when the clearing is not read back."""
        if not self.pending:
            return "inactive"
        state = self.read()
        if state == "actor_inactive":
            return "actor_inactive_retry_stop"
        if state == "player":
            self.library().AIClearScriptedTarget(AIActor=self.actor_ref())
            if self.read() != "none":
                raise ValueError("Target cleanup not confirmed")
            result = "restored"
        else:
            # Never clear another script's replacement, or call an expired actor.
            result = {"none": "already_original", "other": "superseded", "actor_expired": "actor_expired"}[state]
        self.pending = False
        return result


def library() -> Any:
    pointer = _held["library"]
    found = pointer() if pointer is not None else None
    if found is None:
        found = unrealsdk.find_class(LIBRARY).ClassDefaultObject
        _held["library"] = unrealsdk.unreal.WeakPointer(found)
    return found


def same(a: Any, b: Any) -> bool:
    """The comparison TargetPatch uses in game: two wrappers of one object share its address."""
    try:
        return a is not None and b is not None and a._get_address() == b._get_address()
    except Exception:
        return False


def aimed_at(actor: Any, player: Any) -> tuple[str, Any]:
    """aimed(), and the target itself when it is someone else than the player, else None: after trial 6e's vehicle
    ride, the enemies targeted another character and the trial could only tell its class. The target is valid for
    this read only."""
    try:
        found = library().GetPrimaryTarget(AIActor=actor)
    except Exception:
        return "unavailable", None
    if found is None:
        return "none", None
    if same(found, player):
        return "player", None
    try:
        kind = str(found.Class.Name)[:MAX_TEXT]
    except Exception:
        kind = "unreadable"
    return f"other:{kind}", found


def aimed(actor: Any, player: Any) -> str:
    """Nobody while the enemy rests, the player, or other:<its class> for anything else: after the hunter's vehicle
    rides of trial 6a, the enemies targeted something else and the trial could not say what."""
    return aimed_at(actor, player)[0]


def primary(actor: Any, player: Any) -> str:
    """Nobody while the enemy rests, the player or another character in a fight."""
    return aimed(actor, player).split(":", 1)[0]


def imposed(actor_ref: Any, player_ref: Any) -> TargetPatch:
    """The owner of the hunter imposed on one enemy: read(), apply(), verify(), restore()."""
    return TargetPatch(actor_ref, player_ref, library)


def release(patch: Any, body_reused: bool, announce: Callable[[], None]) -> str:
    """Clears the imposed target when the enemy is let go, announcing the call first; never on a body the game
    reuses, where no call is made, as in the enemy research."""
    if patch is None or not patch.pending:
        return "inactive"
    if body_reused:
        return "not_needed"
    try:
        if patch.read() == "player":
            announce()
        return patch.restore()
    except Exception as error:
        return f"clear_error:{type(error).__name__}"
