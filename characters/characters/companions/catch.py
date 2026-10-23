"""Reinforcements: a companion left too far is teleported behind the hunter, once he stands on ground.

Since trial 166, the rule of Vex Phase Clones (vex_phase_clones/teleport.py) and Loveless Wyrms
(loveless_wyrms/recall.py), allies brought back to a hunter and verified in game there: behind him, where he faces
away, BEHIND_M from him, one SPREAD_DEG rank each so that companions do not land in one another; at his height,
facing him; nothing while he is in the air, they wait for him to land (Kevin, 20 October 2026, trial 163: « ils
doivent se teleporter au sol quand j'y suis, pas dans les air »). K2_TeleportTo is the engine's teleport that looks
for a free spot around the one asked (It Follows' trial 6h, Vex's T1).

Before, the place was taken on the hunter's past way (trial 138), since trial 164 only where he stood on ground: a
stretch crossed in the air or with his mode unread left a gap in the way, and at trial 166 the only place BEHIND_M
behind him was where the companions had started, 120 m away; they were sent back there every 5 s and never reached him
(releves/2026-10-20-essai-166, 20:18:34 to 20:19:30).

Since trial 168, as Vex's Specters (Kevin, 20 October 2026: « Pour le reste oui c'est ok »): never while the companion
fights (vex_phase_clones/combat.py: a busy clone is never brought back), and a walk blocked on the way is ended by a
teleport to its place behind the hunter, near or far (unstick; vex_phase_clones/walk.py, _unstick).

Since trial 169, a companion fighting beyond FIGHT_TELEPORT_M is teleported all the same (Kevin, 20 October 2026: « au
combat, au dela de 100m ils doivent se teleporter pour se rapprocher »): at trial 168 the fights held them up to 206 m
from the hunter (releves/2026-10-20-essai-168). Vex lets a hunting Specter go up to 150 m (combat.py, HUNT_LIMIT_M).
"""

import math
from typing import Any, Callable

import unrealsdk

TELEPORT_M = 50.0
FIGHT_TELEPORT_M = 100.0
# Loveless Wyrms' 4 m at first; as far as a walk stops since trial 166 (walk.ARRIVAL_M): at 4 m they landed
# against him (Kevin, 20 October 2026: « ils viennent coller le chasseur donc plus d'espace »); 10 m after trial 167
# (« on va passer a 10m »).
BEHIND_M = 10.0
# 180 / 8: the team's eight ranks stand behind him or beside him, never in front, 3.9 m apart on 10 m.
SPREAD_DEG = 22.5
EVERY_S = 5.0
# The hunter's movement modes on ground, read in It Follows' trial 6k: on foot MOVE_Walking, driving MOVE_None (his
# vehicle on the road). In the air (MOVE_Falling), climbing (MOVE_Custom), swimming, or unread: the companion waits.
GROUND = ("MOVE_Walking", "MOVE_NavWalking", "MOVE_None")


def facing(actor: Any) -> float | None:
    """Where the hunter (or his vehicle) faces, in degrees; None when it cannot be read."""
    try:
        yaw = float(actor.K2_GetActorRotation().Yaw)
    except Exception:
        return None
    return yaw if math.isfinite(yaw) else None


def fan(rank: int) -> float:
    """Degrees off the spot right behind him for the companion of this rank: 0, then one step each way, then two."""
    step = (rank + 1) // 2
    return SPREAD_DEG * (step if rank % 2 else -step)


def behind(here: tuple, yaw: float, rank: int) -> tuple:
    """The spot of that rank behind the hunter, at his height."""
    angle = math.radians(yaw + 180.0 + fan(rank))
    reach = BEHIND_M * 100.0
    return here[0] + math.cos(angle) * reach, here[1] + math.sin(angle) * reach, here[2]


class CatchUp:
    """The teleports of one companion (actor, its weak pointer), of its rank in the team; note(text) says a call before
    it is made."""

    def __init__(self, actor: Any, name: str, note: Callable[[str], None], rank: int = 0) -> None:
        self.actor, self.name, self.note, self.rank = actor, name, note, rank
        self.at: float | None = None
        self.teleports = self.refused = 0

    def keep(self, here: tuple | None, yaw: float | None, mode: str | None, to_hunter: float | None,
             now: float, fighting: bool = False) -> str:
        """Once a sample: the companion teleported behind the hunter beyond TELEPORT_M, beyond FIGHT_TELEPORT_M while it
        fights. Says what it did. A failing call raises."""
        if here is None or to_hunter is None or to_hunter <= TELEPORT_M:
            return "near"
        if fighting and to_hunter <= FIGHT_TELEPORT_M:
            return "fighting"
        return self.unstick(here, yaw, mode, now)

    def unstick(self, here: tuple | None, yaw: float | None, mode: str | None, now: float) -> str:
        """The companion teleported to its place behind the hunter, once he stands on ground (his movement mode), at
        most every EVERY_S. Says what it did. A failing call raises."""
        if here is None:
            return "no_hunter"
        if mode not in GROUND:
            return "waits_landing"
        if yaw is None:
            return "no_facing"
        if self.at is not None and now - self.at < EVERY_S:
            return "waiting"
        self.at = now
        spot = behind(here, yaw, self.rank)
        towards = math.degrees(math.atan2(here[1] - spot[1], here[0] - spot[0]))
        self.note(f"about to call K2_TeleportTo on {self.name}")
        result = self.actor().K2_TeleportTo(
            DestLocation=unrealsdk.make_struct("Vector", X=spot[0], Y=spot[1], Z=spot[2]),
            DestRotation=unrealsdk.make_struct("Rotator", Pitch=0.0, Yaw=towards, Roll=0.0))
        # Read as Vex Phase Clones reads it: an answer in a tuple would always count as done.
        done = bool(result[0] if isinstance(result, tuple) else result)
        self.teleports += 1
        self.refused += not done
        return "teleported" if done else "refused"
