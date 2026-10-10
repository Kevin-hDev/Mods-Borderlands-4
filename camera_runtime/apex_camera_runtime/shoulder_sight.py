"""How far each shoulder's camera sees ahead before a wall (first trial, Kevin, 2026-10-07).

A wall in front of the shoulder hides the view without touching the camera: on Kevin's screenshots the wall filled the
right half of the screen and the reticle sat on it, while the wall check counted the camera clear. So each side also
looks straight ahead, level, from its camera: a level line ignores the floor when the player looks down.

One line caught any thin object: on a wooden bridge, its pillars and railing swapped the shoulder back and forth
(Kevin, 2026-10-08, docs/third_person_fov/camera/releves/2026-10-08-epaule-pont/sdk-essai-2-mesures.log). So each side
looks along three parallel lines across its view, and counts as far as its farthest line sees: a pillar stops one, a
wall all three.

Going up a ramp, the three lines then met the edge of the bridge's floor at the camera's height (SM_Floor_Wood_Plank_A,
upright face, third trial of 2026-10-08, sdk-essai-3-trois-lignes.log). A line that meets something looks again a
little higher: a wall stops both, a step of the floor only the lower one.

Walking straight to a door, the shown shoulder's lines met the wall beside it while the other shoulder looked through
the door: a swap near the wall and a return in the doorway, at each passage (Kevin, 2026-10-08,
docs/third_person_fov/camera/releves/2026-10-08-epaule-porte/sdk-porte-1.log). To a camera a door's edge is a wall's
corner, so before a swap the view alone asks for, one more line looks past the other camera, away from the shown one:
beside a door or a window it meets the same wall, past a corner it sees on.
"""

import math

from .shoulder_auto import BLOCKED, CLEAR

# Distances from the camera (cm), which sits about 2.6 m behind the hunter (dynamic camera trial, 2026-10-06).
# A wall nearer than BLOCKED_CM is in the way: about 2.5 m ahead of the hunter (Kevin, 2026-10-07 second trial: at
# 1.4 m the swap came late). The other side must see past CLEAR_CM to be worth going to; the view counts fully clear
# past SIGHT_CM.
BLOCKED_CM = 510.0
CLEAR_CM = 720.0
SIGHT_CM = 800.0
# Distance to free share, matched to shoulder_auto.py's thresholds: BLOCKED_CM gives BLOCKED, CLEAR_CM gives CLEAR.
SCALE = ((0.0, 0.0), (BLOCKED_CM, BLOCKED), (CLEAR_CM, CLEAR), (SIGHT_CM, 1.0))
RADIUS = 5.0
# TraceTypeQuery2, the engine's Camera channel: characters ignore it, so an enemy ahead is not a wall.
CAMERA_CHANNEL = 2
MAX_NAME = 48
# The side lines stand this far either side of the camera (cm): more than a pillar's width, less than a wall's.
SPREAD_CM = 50.0
# How much higher a stopped line looks again (cm): above a step or a railing, still on a wall.
RISE_CM = 50.0
# How far past the other camera the opening line stands (cm): wider than a door or a window seen from a shoulder.
OPENING_CM = 150.0


def free_share(distance: float) -> float:
    for (near, low), (far, high) in zip(SCALE, SCALE[1:]):
        if distance <= far:
            return low + (high - low) * (distance - near) / (far - near)
    return 1.0


def _name(read) -> str:
    try:
        return str(read())[:MAX_NAME]
    except Exception:
        # Only for the log line: an object without that field is named "?".
        return "?"


def seen(result, distance: float) -> str:
    """What the line met, for the swap's log line: a post and a ramp give the same distance, so the object, its mesh
    and how much its surface faces up (normal Z: 0 for an upright post, near 1 for a floor) tell them apart
    (Kevin, 2026-10-08: swaps on a sloping wooden bridge)."""
    return (f"{distance:.0f} cm on {_name(lambda: result.HitObjectHandle.Actor.Name)}"
            f"/{_name(lambda: result.Component.StaticMesh.Name)} up {_name(lambda: f'{result.ImpactNormal.Z:.2f}')}")


class ShoulderSight:
    def __init__(self, kismet, sdk) -> None:
        self.kismet, self.sdk = kismet, sdk
        # What the farthest line of the last share met, or "clear".
        self.seen = "clear"

    def share(self, actor, start, yaw: float) -> float:
        """Free share of the view ahead of start (free_share), level, along the camera's yaw (degrees): the farthest of
        three lines, the middle one first."""
        angle = math.radians(yaw)
        ahead, side = (math.cos(angle), math.sin(angle)), (-math.sin(angle), math.cos(angle))
        farthest = None
        for offset in (0.0, SPREAD_CM, -SPREAD_CM):
            origin = (start[0] + side[0] * offset, start[1] + side[1] * offset, start[2])
            nearest, met = self._reach(actor, origin, ahead)
            if farthest is None or nearest > farthest:
                farthest, self.seen = nearest, met
            if farthest >= CLEAR_CM:
                # Clear enough for both thresholds: the other lines cannot change the decision.
                break
        return free_share(farthest)

    def opening(self, actor, camera, other, yaw: float) -> float:
        """Free share of the view ahead of one line OPENING_CM past the other camera, on the side away from the
        camera shown: low when the other side only sees through a door or a window."""
        angle = math.radians(yaw)
        side = (-math.sin(angle), math.cos(angle))
        away = 1.0 if (other[0] - camera[0]) * side[0] + (other[1] - camera[1]) * side[1] >= 0 else -1.0
        origin = (other[0] + side[0] * away * OPENING_CM, other[1] + side[1] * away * OPENING_CM, other[2])
        nearest, self.seen = self._reach(actor, origin, (math.cos(angle), math.sin(angle)))
        return free_share(nearest)

    def _reach(self, actor, origin, ahead) -> tuple:
        """How far one line sees and what stopped it: a stopped line looks again RISE_CM higher and keeps the farther."""
        nearest, met = self._line(actor, origin, ahead)
        if nearest < CLEAR_CM:
            higher = self._line(actor, (origin[0], origin[1], origin[2] + RISE_CM), ahead)
            if higher[0] > nearest:
                nearest, met = higher
        return nearest, met

    def _line(self, actor, start, ahead) -> tuple:
        """The nearest contact along one level line (cm, SIGHT_CM when none) and what it met."""
        end = (start[0] + ahead[0] * SIGHT_CM, start[1] + ahead[1] * SIGHT_CM, start[2])
        first = self.sdk.make_struct("Vector", X=start[0], Y=start[1], Z=start[2])
        last = self.sdk.make_struct("Vector", X=end[0], Y=end[1], Z=end[2])
        nearest, met = SIGHT_CM, "clear"
        for detailed in (False, True):
            answer = self.kismet.SphereTraceSingle(
                actor, first, last, RADIUS, CAMERA_CHANNEL, detailed, [actor], 0,
                self.sdk.make_struct("HitResult"), True, self.sdk.make_struct("LinearColor"),
                self.sdk.make_struct("LinearColor"), 0.0)
            if not isinstance(answer, tuple) or not 2 <= len(answer) <= 3 or type(answer[0]) is not bool:
                raise ValueError("invalid sight result")
            if answer[0]:
                distance = float(answer[-1].Distance)
                if not math.isfinite(distance) or not 0 <= distance <= SIGHT_CM:
                    raise ValueError("invalid sight contact")
                if distance < nearest:
                    nearest, met = distance, seen(answer[-1], distance)
        return nearest, met
