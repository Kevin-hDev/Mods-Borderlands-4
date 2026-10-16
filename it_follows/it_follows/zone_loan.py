"""An enemy drawn into the horde lent the zone on the hunter, then given its own back when it leaves the horde.

SetTerritory and GetTerritory are called as trial 2 called them in game, three times without a crash; the game never
took a lent zone back (docs/RUN/enquetes/2026-10-10-zone-pretee.md). An enemy lent the zone it already holds (trial 6i:
the lent zone's own group) is neither lent nor given back anything, a call that would change nothing. An enemy without a
zone (trial 6r) is given back none, as the game had it. Zones are held through weak pointers: the lent one is the
hunter zone's own, never made again from the zone read when the run began, since a census put off to a later image may
come after the game freed it (review of 15 October 2026). Taken from the trials' docs/RUN/sondes/run_zone_loan.py.
"""

from typing import Any, Callable

import unrealsdk

from . import reads
from .seen import Seen
from .target import same


class Loan:
    """One enemy's loan: its own zone and the lent one."""

    def __init__(self, mover: Seen, target: Any, target_path: str) -> None:
        """mover is the enemy that is lent the zone; target the lent zone's weak pointer, target_path its path."""
        self.own_path, self.target_path = mover.zone_path, target_path
        self.homeless = mover.zone is None
        self.home = "none" if self.homeless else "own"
        self.own = unrealsdk.unreal.WeakPointer(mover.zone)
        self.target = target

    def held(self, zone: Any) -> str:
        """Which zone an enemy holds: none, the lent one (target), its own, or another one. The lent zone is known by
        its address first: its path, made anew at each read, was asked of every enemy of the horde each second (audit
        of 16 October 2026)."""
        if zone is None:
            return "none"
        if same(zone, self.target()):
            return "target"
        path = reads.path_of(zone)
        return "target" if path == self.target_path else "own" if path == self.own_path else "other"

    def lend(self, actor: Any, announce: Callable[[], None]) -> str:
        """Lends the zone, the call announced first, and says which zone the enemy holds then; a failing call raises.
        A lent zone already gone is never passed on: SetTerritory(None) would leave the enemy without any."""
        zone = self.target()
        if zone is None:
            return "unavailable"
        if self.own_path == self.target_path:
            return self.held(actor.GetTerritory())
        announce()
        actor.SetTerritory(zone)
        return self.held(actor.GetTerritory())

    def give_back(self, actor: Any, body_reused: bool, announce: Callable[[], None]) -> str:
        """Gives the enemy its own zone back, or none if it had none, if it still holds the lent one; never on a body
        the game reuses."""
        if body_reused:
            return "not_needed"
        if self.own_path == self.target_path:
            return "its_own"
        own = self.own()
        if actor is None or (own is None and not self.homeless):
            return "unavailable"
        try:
            current = self.held(actor.GetTerritory())
            if current != "target":
                return "already_home" if current == self.home else "left_alone"
            announce()
            actor.SetTerritory(own)
            return "restored" if self.held(actor.GetTerritory()) == self.home else "restore_failed"
        except Exception as error:
            return f"restore_error:{type(error).__name__}"
