"""It Follows' catch-up: an enemy of the horde left far behind is brought back onto the hunter's own way, out of his
sight (decision 23), at the distances of the level the player chose (decision 47).

Why (docs/RUN/enquetes/2026-10-10-camps-qui-suivent.md): beyond 300 m or so, trial 6f's cats mostly stood still or ran
on the spot, even with the lent zone and the imposed target, for a cause not found; Kevin accepted, as a help only,
that such an enemy be brought closer at once where he does not see it. Its new place is on the hunter's own way, where
he stood seconds before: ground he crossed, behind him. K2_TeleportTo, the engine's teleport that looks for a free spot
around the one asked, was called 48 times on six cats in trial 6h without a crash, 47 of them landing where asked.
Trial 6i brings them closer and sooner (docs/RUN/enquetes/2026-10-10-horde-serree.md); trial 6j keeps bringing them
back while the hunter drives (decision 27, docs/RUN/enquetes/2026-10-11-horde-pendant-les-trajets.md); trial 6l puts
them on the ground found under his way (ground.py), never where he swam (decision 28), and brings back one stuck still
near him too (docs/RUN/enquetes/2026-10-11-horde-sur-la-terre.md). Trial 6m looks farther back along his way, then on
a ring around him out of his sight, since in trial 6l every place was refused once his way behind lay over water.
Trial 6n traces the ring from high above him and farther out, since in trial 6m the shore stood 5 to 13 m above his
vehicle on the sea, above where the trace began. Trial 6z bis serves first the enemies that waited longest, five a
second (decision 42): in trial 6z, served in the list's own order three a second, the first twelve were brought back
11 to 31 times each and the 15 copies drawn last 1 to 6 times, standing still far behind the rest of the time.
Each enemy brought back goes the next offset of the level's spread farther (decision 66, spread.py), so that those of
one second do not land in one group; one put farther is due again only that much farther, or it would be brought back
again at once. So is a copy the spread has born farther than far_m, up to 65 m behind him: due only the level's margin
past where it joined.
"""

from collections import deque
import math
from typing import Any, Callable

import unrealsdk

from . import reads

# Places in one second, each farther along the hunter's way than the one before by SPACING_M, so that the enemies
# brought back together do not land on each other: Kevin, 13 October 2026, after trial 6z, where three a second left
# the copies behind: « on va tester 5 par seconde ». The last place, 16 m past the level's, still lies within its far_m,
# and within an enemy's own once the spread put it farther.
PLACES = 5
SPACING_M = 4.0
# Out of his sight: a game's view is narrower than 180 degrees, so farther than 90 from where he looks is out of it;
# both where the enemy stands and where it goes.
HIDDEN_DEG = 90.0
# At most once per enemy in this long: one that cannot keep up is not moved every second. Trial 6h's cats, 7 m/s
# against the hunter's 9 to 15 on foot, fell behind again within seconds of being brought back, and waited 10 s.
EVERY_S = 5.0
# Faster than this the hunter drives: no enemy runs that fast (trial 6h: 10 m/s at most, the hunter 16 on foot).
DRIVING_M_S = 20.0
# While he drives, an enemy is brought back this often instead: trial 6i's cats, left to wait until he slowed, were 200
# to 550 m behind by then, where the game no longer moves them, and he looked their way while waiting for them, which
# forbids bringing them back. Behind him while he drives, they are out of his sight; at 30 m/s, 2 s keeps them within
# 100 m or so, where they still run (decision 27).
DRIVING_EVERY_S = 2.0
# The hunter's way, a point a sample: a minute.
TRAIL_POINTS = 60
# Farther than reads.JUMP_M from the last point of his way, the hunter's place jumped (a death, a fast travel): his old
# way then lies far away, and places would be searched between his new place and the old one.
JUMP_M = reads.JUMP_M
# Where nothing can be walked on at that place, farther back along his way by this much, in turn (trial 6k). Trial 6l's
# 10 and 20 m mostly lay over the lake he had just crossed: no place taken in the whole trial. Trial 6m went up to 80 m
# farther, past which the cats mostly stood still anyway (trial 6f).
FARTHER_M = (0.0, 10.0, 20.0, 40.0, 60.0, 80.0)
# Then on a ring around him, as far as the place, at these angles from where he looks, all out of his sight: leaving a
# lake, the shore beside him is ground though his way behind is water.
RING_DEG = (180.0, 140.0, 220.0, 110.0, 250.0)
# Then on rings this much farther out (trial 6n): on the sea, the nearest shore lay farther than 38 m (trial 6m).
RING_FARTHER_M = (0.0, 30.0, 60.0)
# A ring point is traced from this far above the hunter: trial 6m's shore stood 5 to 13 m above his vehicle on the
# sea, while the trace began 1 m above him, inside the ground, and met nothing.
RING_UP_CM = 2000.0
# A ring point this near a point of his way where he swam is refused, as his way is (decision 28).
SWUM_NEAR_M = 15.0
# Traces in one second, for all enemies together: one enemy may trace 21 times; a search that found nothing is not
# made again for the next enemy in that second (said as_before), since it would find the same. Sixteen a place, as
# when three places had 48.
TRACES_PER_SAMPLE = 16 * PLACES
# Trial 6l: an enemy that has not moved STUCK_MOVE_M in STUCK_S, farther than STUCK_NEAR_M from the hunter, is brought
# back as if far. Trial 6j's cats stuck above water stood 13 to 16 m from him for about 40 s, never due; one that
# reached him stands closer, or moves around him.
STUCK_S = 5.0
STUCK_MOVE_M = 1.0
STUCK_NEAR_M = 10.0


class CatchUp:
    """The hunter's way, where he looks, and the enemies brought back. announce(call, log, **fields) notes a call
    before it happens; ground (ground.GroundTrace) says where an enemy can stand under a point. An enemy goes behind_m
    from the hunter on his way, the level's (decision 47), once farther than far_m from him, even one coming back by
    itself: trial 6h brought back only those that had not closed 10 m in 5 s past 60 m, and its cats took 20 to 40 s to
    come back after each ride. spread (spread.Spread) moves each place by its next offset."""

    def __init__(self, announce: Callable[..., None], ground: Any, behind_m: float, far_m: float, spread: Any) -> None:
        self.announce, self.ground, self.spread = announce, ground, spread
        # The places of one second, in metres from the hunter, nearest first.
        self.behind = tuple(behind_m + SPACING_M * index for index in range(PLACES))
        self.far_m = far_m
        # How much farther than its place an enemy may fall before it is due: 20 m at every level (levels.py).
        self.margin_m = far_m - behind_m
        # Each enemy's own far_m once the spread put it farther than the level's places.
        self.far_of: dict[str, float] = {}
        # Where each enemy last moved from, and since when it has stood there.
        self.still: dict[str, tuple[tuple, float]] = {}
        # Each point of his way, and whether he swam there.
        self.trail: deque = deque(maxlen=TRAIL_POINTS)
        self.last: dict[str, float] = {}
        self.view: float | None = None
        self.walked_at: float | None = None
        self.hunter_m_s: float | None = None
        self.given = 0
        self.traces_left = TRACES_PER_SAMPLE
        # The places searched in vain this second, by how many enemies were given a place before and the offset.
        self.vain: set[tuple[int, float]] = set()
        # Since the last status line: what each search said, and the traces made, the ground trace's own count; a
        # trace cost 0.14 ms in trials 6q to 8b, and up to TRACES_PER_SAMPLE a second, a share never written down.
        self.said: dict[str, int] = {}
        self.traces_seen = ground.calls

    def walk(self, here: tuple | None, pc: Any, now: float, swimming: bool = False) -> None:
        """Once a sample, before the enemies: where the hunter stands and whether he swims, how fast he went since the
        last place known, and where he looks. A place farther than JUMP_M from the last point of his way forgets the
        way, no speed taken."""
        self.hunter_m_s = None
        if here is not None:
            if self.trail and math.dist(self.trail[-1][0], here) > JUMP_M * 100.0:
                self.trail.clear()
            elif self.trail and self.walked_at is not None and now > self.walked_at:
                self.hunter_m_s = math.dist(self.trail[-1][0], here) / 100.0 / (now - self.walked_at)
            self.trail.append((here, swimming))
            self.walked_at = now
        try:
            self.view = float(pc.GetControlRotation().Yaw)
        except Exception:
            self.view = None
        self.given = 0
        self.traces_left = TRACES_PER_SAMPLE
        self.vain.clear()

    def queue(self, chasers: list) -> list:
        """The enemies in the order the places of a second go to them: those never brought back first, then the one
        brought back longest ago; among equals, as listed."""
        return sorted(chasers, key=lambda chaser: self.last.get(chaser.name, -math.inf))

    def consider(self, name: str, mover: Any, at: tuple | None, here: tuple | None, to_player: float | None,
                 now: float) -> dict | None:
        """Brings the enemy back once it is due and a place out of sight is found. None when it is not due; else
        catch_up says moved, refused, call_failed:<error>, in_sight, no_place or later, with the place when one was
        found, where it came from (way or ring), what the trace met there, driving while the hunter drives, and stuck
        for one brought back for standing still; refused lists why each place tried before was not taken (as_before when
        the same search found nothing this second), water_met what each place refused for water met."""
        driving = self.hunter_m_s is not None and self.hunter_m_s > DRIVING_M_S
        stuck = self._stuck(name, at, to_player, now)
        far = self.beyond(name, to_player)
        if not (far or stuck) or now - self.last.get(name, -math.inf) < (DRIVING_EVERY_S if driving else EVERY_S):
            return None
        line = self._bring(name, mover, at, here, now)
        outcome = str(line.get("catch_up"))
        self.said[outcome] = self.said.get(outcome, 0) + 1
        if stuck and not far:
            line["stuck"] = True
        return {**line, "driving": True} if driving else line

    def beyond(self, name: str, to_player: float | None) -> bool:
        """Whether the enemy stands farther than the catch-up brings it back from (decision 97 lets it go there)."""
        return to_player is not None and to_player > self.far_of.get(name, self.far_m)

    def gauge(self) -> dict:
        """What the searches said and the traces made since the last time asked, then forgotten; broken with its error
        once a trace failed, which ends the catch-up's traces for the run."""
        traces, self.traces_seen = self.ground.calls - self.traces_seen, self.ground.calls
        said = {**self.said, "traces": traces}
        if self.ground.broken is not None:
            said["broken"] = self.ground.broken
        self.said = {}
        return said

    def arrived(self, name: str, metres: float | None) -> None:
        """A copy born behind the hunter joins the horde metres from him: due only once the margin farther, never
        before far_m."""
        if metres is not None:
            self.far_of[name] = max(self.far_m, metres + self.margin_m)

    def forget(self, name: str) -> None:
        """Drops what is kept of an enemy let go: a run may last an hour or more, its enemies coming and going."""
        self.last.pop(name, None)
        self.still.pop(name, None)
        self.far_of.pop(name, None)

    def _stuck(self, name: str, at: tuple | None, to_player: float | None, now: float) -> bool:
        if at is None:
            self.still.pop(name, None)
            return False
        since = self.still.get(name)
        if since is None or math.dist(since[0], at) > STUCK_MOVE_M * 100.0:
            self.still[name] = (at, now)
            return False
        return now - since[1] >= STUCK_S and to_player is not None and to_player > STUCK_NEAR_M

    def _bring(self, name: str, mover: Any, at: tuple | None, here: tuple | None, now: float) -> dict:
        if self.view is None or here is None or at is None or not self._hidden(at, here):
            return {"catch_up": "in_sight"}
        if self.given >= PLACES:
            return {"catch_up": "later"}
        offset = self.spread.next()
        if (self.given, offset) in self.vain:
            return {"catch_up": "no_place", "refused": ["as_before"]}
        refused: list[str] = []
        water_met: list[str] = []
        line = {"catch_up": "no_place"}
        for source, way, swum in self._places(here, offset):
            if swum:
                refused.append("swum")
                continue
            if not self._hidden(way, here):
                refused.append("in_sight")
                continue
            if self.traces_left <= 0:
                refused.append("budget")
                break
            self.traces_left -= 1
            said, spot, met = self.ground.ground(name, mover, way, *([RING_UP_CM] if source == "ring" else []))
            if spot is None:
                refused.append(said)
                if said == "water" and met:
                    water_met.append(met)
                if said.startswith("call_failed"):
                    break
                continue
            if not self._hidden(spot, here):
                refused.append("in_sight")
                continue
            self.given += 1
            self.last[name] = now
            self.far_of[name] = self.far_m + max(0.0, offset)
            line = {"catch_up": self._teleport(name, mover, spot, here), "from": source, "spot": reads.spot(spot),
                    "way": reads.spot(way), "met": met}
            break
        else:
            self.vain.add((self.given, offset))
        if refused:
            line["refused"] = refused
        if water_met:
            line["water_met"] = water_met
        return line

    def _places(self, here: tuple, offset: float):
        """Where an enemy may go, in turn: points back along the hunter's way, offset farther, then on the ring around
        him; each with whether he swam there."""
        behind_m = self.behind[self.given] + offset
        for farther_m in FARTHER_M:
            found = self._spot(here, (behind_m + farther_m) * 100.0)
            if found is None:
                break
            yield ("way", *found)
        swum = [point for point, wet in self.trail if wet]
        for farther_m in RING_FARTHER_M:
            reach = (behind_m + farther_m) * 100.0
            for angle in RING_DEG:
                bearing = math.radians(self.view + angle)
                point = (here[0] + reach * math.cos(bearing), here[1] + reach * math.sin(bearing), here[2])
                yield "ring", point, any(math.dist(point[:2], wet[:2]) < SWUM_NEAR_M * 100.0 for wet in swum)

    def _hidden(self, point: tuple, here: tuple) -> bool:
        dx, dy = point[0] - here[0], point[1] - here[1]
        if dx == 0.0 and dy == 0.0:
            return False
        bearing = math.degrees(math.atan2(dy, dx))
        return abs((bearing - self.view + 180.0) % 360.0 - 180.0) > HIDDEN_DEG

    def _spot(self, here: tuple, behind_cm: float) -> tuple[tuple, bool] | None:
        """Walking back the hunter's way, the first point behind_cm from where he stands, between two of its points,
        and whether he swam at either."""
        newer, wet = here, False
        for older, older_wet in reversed(self.trail):
            if math.dist(older, here) >= behind_cm:
                low, high = 0.0, 1.0
                for _ in range(20):
                    middle = (low + high) / 2.0
                    if math.dist(_between(newer, older, middle), here) < behind_cm:
                        low = middle
                    else:
                        high = middle
                return _between(newer, older, high), wet or older_wet
            newer, wet = older, older_wet
        return None

    def _teleport(self, name: str, mover: Any, spot: tuple, here: tuple) -> str:
        """Teleports the enemy onto spot, facing the hunter, the call announced first; up to PLACES a second, so not
        written to the log (report.py)."""
        yaw = math.degrees(math.atan2(here[1] - spot[1], here[0] - spot[0]))
        self.announce("K2_TeleportTo", log=False, on=name)
        try:
            done = mover.K2_TeleportTo(
                DestLocation=unrealsdk.make_struct("Vector", X=spot[0], Y=spot[1], Z=spot[2]),
                DestRotation=unrealsdk.make_struct("Rotator", Pitch=0.0, Yaw=yaw, Roll=0.0))
        except Exception as error:
            return f"call_failed:{type(error).__name__}"
        return "moved" if done else "refused"


def _between(a: tuple, b: tuple, share: float) -> tuple:
    return tuple(start + (end - start) * share for start, end in zip(a, b))
