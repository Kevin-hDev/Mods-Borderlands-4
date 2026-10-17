"""One character's wall climb: the moment it judges, the rules, the push up the wall and the jumps it gives back.

Split from wall_climb.py on 2026-10-17 so that a co-op host can climb each guest itself. The climb writes a vertical
speed every frame on the climbing character, on its own machine only: the host, which decides where every character
is, computed the guest falling and pulled them back down ("le chasseur fait des mini grimpes, saccade et tombe",
docs/coop/2026-10-16-essai-recopie.md). What only the player has, the arms' animation, the hoist press, the refusal
lines and the mantle hold, stays in wall_climb.py.
"""

import math
from typing import Any, Callable

from . import air_jumps, climb_aim, climb_rules, game, settings, wall_choice, wall_sense

# The measure's lean into the wall, which kept the character touching it all the way up.
INTO_WALL = 100.0
NS_PER_S = 1_000_000_000


def limits(character: Any) -> climb_rules.Limits:
    distance = 2.0 * game.half_height(character) * float(settings.climb_height.value) / 100.0
    return climb_rules.Limits(distance=distance, delay_ns=int(float(settings.reclimb_delay.value) * NS_PER_S),
                              lean_deg=float(settings.climb_lean.value), speed=float(settings.climb_speed.value))


def remote_stick(character: Any) -> tuple[float, float]:
    """A guest's move stick as the host knows it: the acceleration the guest's moves carry, over the most it can be.

    On the host the input a guest pushes reads zero every time, while the acceleration is filled: 24 000 long with the
    stick pushed, the air strafe's MaxAcceleration, and zero with it let go (959 readings, 2026-10-17, verified in game,
    releves/coop/2026-10-17-grimpe-invite).
    """
    movement = character.CharacterMovement
    most = float(movement.MaxAcceleration)
    if most <= 0.0:
        return 0.0, 0.0
    acceleration = movement.GetCurrentAcceleration()
    x, y = float(acceleration.X) / most, float(acceleration.Y) / most
    length = math.hypot(x, y)
    return (x / length, y / length) if length > 1.0 else (x, y)


def moment(character: Any, now_ns: int, stick: tuple[float, float]) -> climb_rules.Moment:
    movement = character.CharacterMovement
    in_air = game.is_in_air(movement)
    yaw = game.view_yaw(character)
    # Traces in the air only: on the ground no climb can start or go on.
    walls = (wall_sense.walls_ahead(character, yaw, game.half_height(character))
             if in_air and yaw is not None else [])
    high = [wall for wall, share in zip(walls, wall_sense.hit_heights(walls)) if share >= climb_aim.HIGH_FROM]
    location = character.K2_GetActorLocation()
    return climb_rules.Moment(
        now_ns=now_ns, in_air=in_air, on_ground=game.is_on_ground(movement),
        game_move=game.in_controlled_move(movement), mantling=game.is_mantling(movement),
        near_game_climb=game.is_near_game_climb(movement),
        x=float(location.X), y=float(location.Y), z=float(location.Z),
        jumps=game.jump_count(character), stick_x=stick[0], stick_y=stick[1], view_yaw=yaw,
        wall=wall_choice.best_wall(walls), hits=len(walls),
        high_wall=wall_choice.best_wall(high) is not None,
    )


class Climber:
    def __init__(self, say: Callable[[str], None]) -> None:
        self.rules = climb_rules.Rules()
        self.jumps = air_jumps.JumpBudget(say)
        # The fullest lean of the climb under way, told at its end: the only way a log shows a diagonal was climbed.
        self.max_lean = 0.0
        self.last_ns = 0

    def step(self, character: Any, now_ns: int, stick: tuple[float, float]
             ) -> tuple[climb_rules.Moment, climb_rules.Limits, climb_rules.Step]:
        """Judges this frame and, while climbing, pushes the character up the wall."""
        self.last_ns = now_ns
        seen = moment(character, now_ns, stick)
        bounds = limits(character)
        step = self.rules.step(seen, bounds)
        if step.event == "start":
            self.max_lean = 0.0
            self.jumps.climb_started(character, now_ns)
        if step.climbing:
            self._push(character, seen, bounds)
        return seen, bounds, step

    def _push(self, character: Any, seen: climb_rules.Moment, bounds: climb_rules.Limits) -> None:
        wall = seen.wall
        lean = climb_aim.lean_degrees(seen.stick_x, seen.stick_y, wall, bounds.lean_deg)
        self.max_lean = max(self.max_lean, abs(lean))
        side_x, side_y, up = climb_aim.climb_direction(lean, wall)
        movement = character.CharacterMovement
        # Never slower than the rise already under way: a climb starting on the frame a jump leaves the ground used to
        # replace 912 with the climb speed, which turned a sprint jump into a hop (Kevin, 2026-09-17).
        rise = max(up * bounds.speed, float(movement.Velocity.Z))
        game.set_velocity(movement, wall.into_x * INTO_WALL + side_x * bounds.speed,
                          wall.into_y * INTO_WALL + side_y * bounds.speed, rise)

    def after_rules(self, character: Any, now_ns: int) -> None:
        """After the rules read the jump count: a jump given back before them would hide the jump that ends a climb."""
        given = self.jumps.update(character, now_ns)
        if given is not None:
            self.rules.jumps_given_back(given)
