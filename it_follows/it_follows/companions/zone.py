"""A companion's own combat zone, set on the hunter each time he walks away, widened while it follows, then put back.

Trial 135 of docs/renforts: the zone moves, the game leaves it there, but the zone alone does not bring the character,
as It Follows' trial 3b found; hence the walks (walk.py). A zone is a scene component, read with
K2_GetComponentLocation and moved with K2_SetWorldLocation, no sweep, teleported (It Follows' hunter_zone.py,
zone_shift.py). Trial 140 widens its combat radius to RADIUS_M while the follow lasts, with It Follows' writer
(zone_radius.py, trial 6p), so that the enemies around the hunter stand in it. A character's zone is owned by the
spawner it was born of (trial 164), which is how a companion just born is found (choose.py); zone_of reads that owner
with GetOwner, the read every trial since 164 used.
"""

import math
from typing import Any, Callable

import unrealsdk

FOLLOW_S = 2.0
FOLLOW_M = 5.0
# Trial 6g of It Follows: a zone the game moves away reads far from where it was put a second later.
HELD_M = 5.0
# A zone read back within 1 m of the point asked counts as moved (it_follows/zone_shift.py).
PLACED_CM = 100.0
RADIUS_M = 40.0
MAX_TEXT = 160


def zone_of(actor: Any) -> tuple[Any, str]:
    """The character's combat zone and how it reads: its class, name and owner; or why it cannot be read."""
    try:
        zone = actor.GetTerritory()
    except Exception as error:
        return None, f"error:{type(error).__name__}:{str(error)[:MAX_TEXT]}"
    if zone is None:
        return None, "none"
    try:
        holder = zone.GetOwner()
        held_by = "none" if holder is None else f"{holder.Class.Name}:{holder.Name}"
    except Exception as error:
        held_by = f"error:{type(error).__name__}"
    return zone, f"{zone.Class.Name}:{zone.Name} owned by {held_by}"[:MAX_TEXT]


def point(zone: Any) -> tuple[float, float, float] | None:
    try:
        where = zone.K2_GetComponentLocation()
        found = (float(where.X), float(where.Y), float(where.Z))
    except Exception:
        return None
    return found if all(math.isfinite(value) for value in found) else None


class ZoneOnHunter:
    """One zone, where it stood (home), and what following the hunter did to it; note(text) says a call before it is
    made."""

    def __init__(self, zone: Any, note: Callable[[str], None]) -> None:
        self.zone, self.note = unrealsdk.unreal.WeakPointer(zone), note
        self.home = point(zone)
        self.followed_at: float | None = None
        self.put_at: tuple | None = None
        self.moves = self.refused = self.in_row = self.away = 0
        self.radius: Any = None

    def _move(self, zone: Any, at: tuple, why: str) -> bool:
        self.note(f"about to call K2_SetWorldLocation on the zone ({why})")
        make = unrealsdk.make_struct
        zone.K2_SetWorldLocation(NewLocation=make("Vector", X=at[0], Y=at[1], Z=at[2]), bSweep=False,
                                 SweepHitResult=make("HitResult"), bTeleport=True)
        reached = point(zone)
        return reached is not None and math.dist(reached, at) <= PLACED_CM

    def follow(self, here: tuple | None, now: float) -> tuple[str, tuple | None]:
        """Sets the zone on the hunter once he is FOLLOW_M away, at most every FOLLOW_S; says what it did (waiting,
        kept, moved, not_moved) and where the zone stands then. A zone found away from where it was put is counted
        (away). A failing call raises."""
        zone = self.zone()
        centre = point(zone) if zone is not None else None
        if self.put_at is not None and centre is not None and math.dist(centre, self.put_at) / 100.0 > HELD_M:
            self.away += 1
        if zone is None or here is None or (self.followed_at is not None and now - self.followed_at < FOLLOW_S):
            return "waiting", centre
        if centre is not None and math.dist(centre, here) / 100.0 <= FOLLOW_M:
            return "kept", centre
        self.followed_at, self.put_at = now, here
        took = self._move(zone, here, "follow")
        self.moves += 1
        self.refused += not took
        self.in_row = 0 if took else self.in_row + 1
        return ("moved" if took else "not_moved"), point(zone)

    def widen(self, patches: Any) -> str:
        """Its combat radius made RADIUS_M with patches, It Follows' zone_radius module; says the radius it had."""
        zone = self.zone()
        if zone is None:
            return "unavailable"
        self.radius = patches.TerritoryRadiusPatch(RADIUS_M * 100.0)
        self.note(f"about to write the zone's combat radius {RADIUS_M} m")
        try:
            before = self.radius.apply(zone)
        except Exception as error:
            self.radius = None
            return f"failed:{type(error).__name__}"
        return f"{round(before / 100.0, 1)}->{RADIUS_M}"

    def narrow(self) -> str:
        """Its own combat radius written back, once, if the one written is still there."""
        patch, self.radius = self.radius, None
        zone = self.zone()
        if patch is None:
            return "not_widened"
        if zone is None:
            return "unavailable"
        self.note("about to write the zone's own combat radius back")
        try:
            return str(patch.restore(zone))
        except Exception as error:
            return f"failed:{type(error).__name__}"

    def put_back(self) -> str:
        """Puts the zone back where it stood, once it was moved."""
        if self.put_at is None:
            return "never_moved"
        zone = self.zone()
        if zone is None or self.home is None:
            return "unavailable"
        try:
            return "restored" if self._move(zone, self.home, "back") else "restore_failed"
        except Exception as error:
            return f"restore_error:{type(error).__name__}"
