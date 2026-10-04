"""The boost's push in the air: while the game boosts a vehicle off the ground, a flat push toward its nose (spec
section 3.6, Kevin's wish of 2026-10-02 and 03, in a jump and in a fall from a height).

The game's own boost already pushes in the air, about six times less than on the ground (session 11). What each choice
answers:
- an impulse adds to the velocity, where a velocity set every frame froze a jump's climb up to 361 m (session 7); an
  impulse times the body's mass, without the velocity-change flag, holds within 4 to 5 frames (session 6, B);
- flat, so that the game keeps its gravity and its vertical speed (Kevin's choice of 2026-10-02);
- up to the boost's top speed, as on the ground (Kevin, 2026-10-03), and never a brake;
- in the air with nothing AIR_REACH under the origin: at the grip's reach a jump only showed for 0.4 s (session 11).
"""

import math
from typing import Any

import unrealsdk

from . import ground

MS = 1_000_000
# The origin sat 22 above flat ground (sessions 3 to 9); jumps rose 343 to 652.
AIR_REACH = 100.0
# BoostMaxSpeed is in miles an hour: 84.641 gave 3 784 by this factor, and 3 782 was measured (session 11).
CM_S_PER_MPH = 44.704
# The grip's clock: a hitch pushes no more than a tenth of a second, a pause nothing.
MAX_STEP_S = 0.1
PAUSE_NS = 500 * MS
REPORT_NS = 5000 * MS


def push(vx: float, vy: float, yaw_deg: float, gain: float, ceiling: float) -> tuple[float, float] | None:
    """The flat velocity to add toward the nose: gain at most, never past the ceiling; None when there is none."""
    if gain <= 0.0 or math.hypot(vx, vy) >= ceiling:
        return None
    nose_x, nose_y = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    along = vx * nose_x + vy * nose_y
    # The largest g with |v + g * nose| = ceiling, a root of g^2 + 2 * along * g + |v|^2 - ceiling^2.
    room = -along + math.sqrt(along * along + ceiling * ceiling - vx * vx - vy * vy)
    gained = min(gain, room)
    return gained * nose_x, gained * nose_y


class AirPush:
    def __init__(self, started_ns: int) -> None:
        self.last_ns = started_ns
        self.report_ns = started_ns
        self.frames = 0
        self.top = 0.0

    def step(self, now_ns: int, vehicle: Any, strength: float) -> tuple[bool, list[str]]:
        """Pushes the vehicle for this frame when it is owed; returns whether it pushed, and the log lines."""
        elapsed = now_ns - self.last_ns
        seconds = 0.0 if elapsed > PAUSE_NS else min(elapsed / 1e9, MAX_STEP_S)
        self.last_ns = now_ns
        lines = self._report(now_ns)
        if strength <= 0.0 or seconds <= 0.0 or not vehicle.OakVehicleMovement.IsBoosting():
            return False, lines
        component = getattr(getattr(vehicle, "DriverPawn", None), "VehicleDriverComponent", None)
        attributes = getattr(component, "VehicleAttributesState", None)
        if attributes is None:
            # The driver may sit down after the vehicle became the pawn (spec section 3.1): no boost to follow yet.
            return False, lines
        mesh = vehicle.Mesh
        velocity = mesh.GetPhysicsLinearVelocity("None")
        added = push(velocity.X, velocity.Y, vehicle.K2_GetActorRotation().Yaw,
                     attributes.BoostMaxAccel.Value * strength * seconds,
                     attributes.BoostMaxSpeed.Value * CM_S_PER_MPH)
        # The trace last: it is the one costly check, and most frames stop before it.
        if added is None or ground.on_ground(vehicle, AIR_REACH):
            return False, lines
        mass = mesh.GetMass()
        mesh.AddImpulse(unrealsdk.make_struct("Vector", X=added[0] * mass, Y=added[1] * mass, Z=0.0), "None", False)
        self.frames += 1
        self.top = max(self.top, math.hypot(velocity.X, velocity.Y))
        return True, lines

    def _report(self, now_ns: int) -> list[str]:
        if now_ns - self.report_ns < REPORT_NS:
            return []
        self.report_ns = now_ns
        if self.frames == 0:
            return []
        line = f"air push frames={self.frames} top_speed={self.top:.0f}"
        self.frames, self.top = 0, 0.0
        return [line]
