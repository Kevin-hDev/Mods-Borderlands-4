"""The body faces where the hunter runs, in third person (Kevin, 2026-10-09).

Off sprint, the game keeps the body facing the camera and plays its side runs; Kevin wants the body to face the run
on every side. Trials 1 to 6 (docs/investigations/apex_movement/animation/2026-10-09-corps-gauche-droite.md) turned
the actor's yaw just before each update of its animation: the body turns toward the run at TURN_RATE, slides included,
then back to the camera once the hunter aims, glides or leaves the ground and the air, and is handed back to the game.
An action turns it back to the crosshair at ACTION_TURN_RATE (body_actions.py). A hunter who stops stays turned where
he stopped while the camera turns around him (Kevin, 2026-10-09: « c'est exactement ça qu'il nous faudrait »), until
he acts, aims or runs again; stopped facing the camera, he is the game's.

At 180 degrees (Kevin's second mode), a run behind the hunter's sides leaves the body facing the camera, and the game
plays its own backward run.
"""

import math
from typing import Any, Callable

# A quarter turn in an eighth of a second: quick enough to follow a key press, without a visible snap.
TURN_RATE = 720.0
# Kevin wants the hunter to turn back quickly when he acts (2026-10-09): a half turn in an eighth of a second.
ACTION_TURN_RATE = 1440.0
# A pause or a loading screen between two updates must not turn the body in one jump.
MAX_STEP_S = 0.1
# Walking and falling: the body faces the run on the ground and through a jump; climbing and other modes are the game's.
MODES = (1, 3)
# Below this the hunter is starting or stopping, and his body shows neither running nor standing yet.
MIN_SPEED = 100.0
STILL = "still"
# At 180 degrees: halfway between a side run (90) and a back diagonal (135), so eight keyboard directions split
# cleanly; a stick held near it keeps its side for HYSTERESIS degrees, so the body never swings back and forth.
BACK_LIMIT = 112.5
HYSTERESIS = 10.0


def heading(x: float, y: float) -> float:
    """World direction of a horizontal vector, 0 to 360, the way Unreal measures yaw."""
    return math.degrees(math.atan2(y, x)) % 360


def signed_gap(direction: float, reference: float) -> float:
    """Where direction sits seen from reference, -180 to 180: positive to the right, as Unreal's yaw turns."""
    gap = (direction - reference + 180.0) % 360.0 - 180.0
    return 180.0 if gap == -180.0 else gap


def turned(offset: float, goal: float, most: float) -> float:
    """offset moved toward goal by at most `most` degrees, the short way round, -180 to 180."""
    gap = signed_gap(goal, offset)
    if abs(gap) <= most:
        return signed_gap(goal, 0.0)
    return signed_gap(offset + math.copysign(most, gap), 0.0)


def aiming(character: Any) -> bool:
    """The test player_sample.py uses."""
    zoom = character.ZoomState
    return bool(zoom.bWantsToZoom) or getattr(zoom.State, "name", str(zoom.State)) != "NotZoomed"


class BodyFacing:
    def __init__(self, make_rotator: Callable[[float, float, float], Any]) -> None:
        self.make_rotator = make_rotator
        self.holding = False
        self.offset = 0.0  # the body's yaw from the view, while held
        self.behind = False  # at 180 degrees: the run is behind the sides
        self.kept_yaw: float | None = None  # the body's world yaw while the hunter stands still
        self.last_ns: int | None = None

    def run_gap(self, character: Any, anim: Any, view: float, full_turn: bool) -> float | str | None:
        """Where the hunter runs, seen from the camera; STILL when he stands; None when the body should face the
        camera."""
        movement = character.CharacterMovement
        if movement.MovementMode not in MODES or anim.bIsGliding or aiming(character):
            return None
        velocity = movement.Velocity
        if math.hypot(velocity.X, velocity.Y) < MIN_SPEED:
            return STILL
        gap = signed_gap(heading(velocity.X, velocity.Y), view)
        if full_turn:
            self.behind = False
            return gap
        limit = BACK_LIMIT - HYSTERESIS if self.behind else BACK_LIMIT + HYSTERESIS
        self.behind = abs(gap) > limit
        return None if self.behind else gap

    def step(self, character: Any, anim: Any, pose: Any, acting: bool, full_turn: bool, now_ns: int) -> bool:
        """Turns the body a step toward its goal before the animation reads it; whether the body is still held."""
        step_s = 0.0 if self.last_ns is None else min((now_ns - self.last_ns) / 1e9, MAX_STEP_S)
        self.last_ns = now_ns
        controller = character.Controller
        if controller is None:
            return self.holding
        view = float(controller.GetControlRotation().Yaw)
        run = None if acting else self.run_gap(character, anim, view, full_turn)
        still = run == STILL
        if (run is None or still) and not self.holding:
            return False
        if not still:
            self.kept_yaw = None
        body = character.K2_GetActorRotation()
        if not self.holding:
            # From where the game left the body: in sprint it has already turned it toward the stick.
            self.holding, self.offset = True, signed_gap(float(body.Yaw), view)
        if still:
            if self.kept_yaw is None:
                self.kept_yaw = (view + self.offset) % 360.0
            self.offset = signed_gap(self.kept_yaw, view)
        else:
            goal = 0.0 if run is None else run
            self.offset = turned(self.offset, goal, (ACTION_TURN_RATE if acting else TURN_RATE) * step_s)
        rotation = self.make_rotator(float(body.Pitch), (view + self.offset) % 360.0, float(body.Roll))
        character.K2_SetActorRotation(rotation, False)
        pose.apply(anim, self.offset, None if run is None or still else signed_gap(run, self.offset))
        if (run is None or still) and self.offset == 0.0:
            self.release(anim, pose)
        return self.holding

    def release(self, anim: Any, pose: Any) -> None:
        """The body is the game's again: the chest's twist goes back to the game's."""
        self.holding, self.offset, self.behind, self.kept_yaw = False, 0.0, False, None
        pose.restore(anim)
