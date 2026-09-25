"""The grip: the vehicle's speed follows the way it faces instead of sliding on (spec section 3.3).

Taken from the driving probe session 9 validated (2026-09-18; the probe was removed once this mod was validated):
big turns at full throttle lost 6 to 22 percent of the speed instead of 58 to 100, and jumps in turns fell back. Each
frame the flat velocity is turned toward where the vehicle faces, by GRIP_DEG_PER_S at most, losing the set share of
speed for each degree turned. What each guard answers:
- set every frame in a straight line, the body read back only what was written and the speed froze (session 4): a
  vehicle sliding less than MIN_GAP_DEG off its facing is left to the game;
- an impulse's velocity-change flag is ignored by the game, while a velocity set holds at once (session 6);
- while it writes, the grip reads back its own velocity, so a jump's climb written again never ended, up to 361 m
  (session 7): with no ground under the vehicle, or fast up or down, the grip lets go, and it never writes more than
  MAX_HOLD_NS in a row.
The game's powerslide is left alone: it keeps its own velocity (HoverSetup.PowerslideVelocityPreservation*).
"""

import math
from typing import Any

import unrealsdk

from . import ground

MS = 1_000_000
# The vehicle turned at up to 260-340 degrees a second (session 2): a slower grip would leave it sliding.
GRIP_DEG_PER_S = 360.0
# Below a walking pace the direction of travel means nothing; beyond 120 degrees the vehicle reverses or spins.
MIN_SPEED = 300.0
MAX_ANGLE = 120.0
MIN_GAP_DEG = 2.0
# A hitch must not swing the whole velocity at once.
MAX_STEP_S = 0.1
# Longer than any frame a player drives through: the game stood still (paused), so nothing is owed. The grip switched
# off is followed by rest() instead, however short the time off.
PAUSE_NS = 500 * MS
# Fast up or down means a jump, a fall or a slope: the game's own vertical speed must not be written over.
MAX_VERTICAL = 300.0
# The longest turn in sessions 2 to 9 lasted about a second; a write held longer is let go for REST_NS, the time for
# the body to read the game's velocity again (4 to 5 frames, session 6).
MAX_HOLD_NS = 1500 * MS
REST_NS = 100 * MS
# A summary line now and then shows the grip at work in the log, the one proof a session has.
REPORT_NS = 5000 * MS


def gripped(vx: float, vy: float, facing_deg: float, max_turn_deg: float, loss_per_deg: float) -> tuple[float, float]:
    """The flat velocity turned toward the facing by max_turn_deg at most, losing loss_per_deg for each degree."""
    speed = math.hypot(vx, vy)
    if speed < MIN_SPEED:
        return vx, vy
    moving = math.degrees(math.atan2(vy, vx))
    gap = (facing_deg - moving + 180.0) % 360.0 - 180.0
    if abs(gap) < MIN_GAP_DEG or abs(gap) > MAX_ANGLE:
        return vx, vy
    turn = max(-max_turn_deg, min(max_turn_deg, gap))
    if turn == 0.0:
        # Rebuilt by cos and sin, the same velocity comes back a digit off and would be written for nothing.
        return vx, vy
    heading = math.radians(moving + turn)
    kept = speed * (1.0 - loss_per_deg) ** abs(turn)
    return kept * math.cos(heading), kept * math.sin(heading)


class Grip:
    def __init__(self, started_ns: int) -> None:
        self.last_ns = started_ns
        self.report_ns = started_ns
        self.frames = 0
        self.largest = 0.0
        self.holding_since: int | None = None
        self.rest_until = started_ns

    def step(self, now_ns: int, vehicle: Any, loss_per_deg: float) -> list[str]:
        elapsed = now_ns - self.last_ns
        seconds = 0.0 if elapsed > PAUSE_NS else min(elapsed / 1e9, MAX_STEP_S)
        self.last_ns = now_ns
        lines = self._report(now_ns)
        if getattr(vehicle.OakVehicleMovement.PowerslideInput, "name", "None") != "None":
            return lines
        mesh = vehicle.Mesh
        velocity = mesh.GetPhysicsLinearVelocity("None")
        x, y = gripped(velocity.X, velocity.Y, vehicle.K2_GetActorRotation().Yaw, GRIP_DEG_PER_S * seconds,
                       loss_per_deg)
        # The trace last: it is the one costly check, and most frames stop before it.
        wanted = (x, y) != (velocity.X, velocity.Y) and abs(velocity.Z) <= MAX_VERTICAL and ground.on_ground(vehicle)
        if not self._may_write(now_ns, wanted):
            return lines
        mesh.SetPhysicsLinearVelocity(unrealsdk.make_struct("Vector", X=x, Y=y, Z=velocity.Z), False, "None")
        turn = abs((math.degrees(math.atan2(y, x) - math.atan2(velocity.Y, velocity.X)) + 180.0) % 360.0 - 180.0)
        self.frames += 1
        self.largest = max(self.largest, turn)
        return lines

    def rest(self, now_ns: int) -> None:
        """A frame with the grip switched off: its clock keeps up, so that switched back on, even half a second later,
        it never turns at once what the vehicle slid meanwhile (Kevin's review of 2026-09-25)."""
        self.last_ns = now_ns
        self.holding_since = None

    def _may_write(self, now_ns: int, wanted: bool) -> bool:
        """A write is let through unless one has been held MAX_HOLD_NS in a row, then paused REST_NS."""
        if not wanted or now_ns < self.rest_until:
            self.holding_since = None
            return False
        if self.holding_since is None:
            self.holding_since = now_ns
        elif now_ns - self.holding_since > MAX_HOLD_NS:
            self.holding_since, self.rest_until = None, now_ns + REST_NS
            return False
        return True

    def _report(self, now_ns: int) -> list[str]:
        if now_ns - self.report_ns < REPORT_NS:
            return []
        self.report_ns = now_ns
        if self.frames == 0:
            return []
        line = f"grip frames={self.frames} largest_turn={self.largest:.1f}"
        self.frames, self.largest = 0, 0.0
        return [line]
