"""Send one thrown object from the hunter's left hand to the point under the crosshair: thrown_from_hand.py says which
object and when, thrown_aim.py does the arithmetic."""

import math
from typing import Any

from .camera_motion import view_axes
from .thrown_aim import angle_deg, born_as_throw, target, turned

# At its birth the body's left hand is the most advanced, 63 cm ahead of the hunter: it throws, as in first person.
HAND_SOCKETS = ("FX_L_Hand", "L_Hand")
# The sight line of the trial: what the crosshair meets within 100 m, the hunter and the object ignored.
SIGHT_CM = 10000.0
SIGHT_RADIUS = 1.0
CAMERA_CHANNEL = 2


def vector(value: Any) -> tuple:
    result = float(value.X), float(value.Y), float(value.Z)
    if not all(math.isfinite(part) for part in result):
        raise ValueError("invalid throw vector")
    return result


class ThrowSender:
    def __init__(self, sdk: Any, kismet: Any) -> None:
        self.sdk, self.kismet = sdk, kismet

    def send(self, pc: Any, pawn: Any, obj: Any) -> tuple:
        """(True, what was done) once the object is in the hand and relaunched; (False, why) when it is left as the
        game made it."""
        manager = pc.PlayerCameraManager
        camera = vector(manager.GetCameraLocation())
        rotation = manager.GetCameraRotation()
        forward = view_axes(float(rotation.Pitch), float(rotation.Yaw))[0]
        start, velocity = vector(obj.K2_GetActorLocation()), vector(obj.GetVelocity())
        hand = self._hand(pawn.Mesh)
        if hand is None:
            return False, "no_hand"
        if not born_as_throw(start, camera, forward, hand):
            return False, "not_a_throw"
        distance = self._sight(pawn, obj, camera, forward)
        launch = turned(velocity, start, hand, target(camera, forward, distance))
        if launch is None:
            return False, "too_close"
        answer = obj.K2_SetActorLocation(self._make(hand), False, self.sdk.make_struct("HitResult"), True)
        # The SDK answers a function with out parameters as (value, outs...).
        if (answer[0] if isinstance(answer, tuple) and answer else answer) is not True:
            return False, "move_refused"
        obj.MovementComponent.Velocity = self._make(launch)
        reach = "none" if distance is None else f"{distance:.0f}"
        return True, (f"hand_cm={math.dist(start, hand):.0f} turn_deg={angle_deg(velocity, launch):.1f}"
                      f" crosshair_cm={reach}")

    def _hand(self, mesh: Any) -> tuple | None:
        for socket in HAND_SOCKETS:
            if mesh.DoesSocketExist(socket):
                return vector(mesh.GetSocketLocation(socket))
        return None

    def _sight(self, pawn: Any, obj: Any, camera: tuple, forward: tuple) -> float | None:
        """How far the crosshair's line meets something (None: nothing within SIGHT_CM)."""
        end = tuple(c + f * SIGHT_CM for c, f in zip(camera, forward))
        answer = self.kismet.SphereTraceSingle(
            pawn, self._make(camera), self._make(end), SIGHT_RADIUS, CAMERA_CHANNEL, True, [pawn, obj], 0,
            self.sdk.make_struct("HitResult"), True, self.sdk.make_struct("LinearColor"),
            self.sdk.make_struct("LinearColor"), 0.0)
        if not isinstance(answer, tuple) or not 2 <= len(answer) <= 3 or type(answer[0]) is not bool:
            raise ValueError("invalid sight result")
        if not answer[0]:
            return None
        distance = float(answer[-1].Distance)
        if not math.isfinite(distance) or not 0.0 <= distance <= SIGHT_CM:
            raise ValueError("invalid sight contact")
        return distance

    def _make(self, point: tuple) -> Any:
        return self.sdk.make_struct("Vector", X=point[0], Y=point[1], Z=point[2])
