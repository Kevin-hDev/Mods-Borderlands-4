"""The grapple's model: what one frame adds to the player's velocity while the hook holds.

Numbers in, numbers out. No SDK and no game object reaches this file, so its tests can replay the
Titanfall 2 readings the model was measured on (titanfall_2/docs/investigations/2026-09-18-grappin-titanfall.md).

Two accelerations, and nothing else:

- toward the anchor, constant, 1.8 times the gravity of the moment. It does not fall off with
  distance: a pull measured at 1060 units/s under a gravity of 600 held the same from the first
  frame to the last, whatever the length of the rope.
- along the move stick, about one gravity, in world axes. This is the one that bends the path:
  with the stick released the heading turned 2 degrees over a whole pull, with it held, 49 to 111.

Both stop at a speed, not at a force. The caps are speeds, so they convert between games by the
running speed (260 units/s in Titanfall, 750 here) and not by gravity.

Gravity is applied here, and how much of it is a choice. A rope carries what hangs from it: with a
force alone and nothing else, a shot level with the eyes draws a parabola that meets the floor after
27 to 40 per cent of the way, which is exactly what the game gave (Kevin, 2026-09-20: "a hauteur du
viseur je parcours 40% de la distance et je m'arrete au sol"). `carry` is the share of gravity the
rope holds: at 1 the pull flies straight along the rope, at 0 the player falls as before.
"""

import math

# A frame longer than this is a freeze, a loading screen or a breakpoint, not a frame. Taken at face
# value it would add a whole second of acceleration at once and fire the player out of the level.
LONGEST_STEP_S = 0.1
# Below this the direction of a vector means nothing and normalising it would explode.
TINY = 1e-6


def unit(x: float, y: float, z: float) -> tuple[float, float, float] | None:
    length = math.sqrt(x * x + y * y + z * z)
    if length < TINY:
        return None
    return x / length, y / length, z / length


def toward(position: tuple[float, float, float],
           anchor: tuple[float, float, float]) -> tuple[float, float, float] | None:
    """The way from the player to the anchor; None when they are on the same spot."""
    return unit(anchor[0] - position[0], anchor[1] - position[1], anchor[2] - position[2])


def distance(position: tuple[float, float, float], anchor: tuple[float, float, float]) -> float:
    return math.dist(position, anchor)


def speed_along(velocity: tuple[float, float, float], direction: tuple[float, float, float]) -> float:
    """How fast the player already moves the way `direction` points; negative when moving the other way."""
    return sum(v * d for v, d in zip(velocity, direction))


def push_toward(velocity: tuple[float, float, float], direction: tuple[float, float, float],
                acceleration: float, cap: float, step_s: float) -> tuple[float, float, float]:
    """Accelerates along `direction`, and stops adding once the speed that way reaches `cap`.

    A cap on the speed, not on the force: under the cap the push is whole, at the cap there is none
    at all. The last frame before the cap adds only what is left, so the cap holds at any frame rate.
    """
    already = speed_along(velocity, direction)
    room = cap - already
    if room <= 0.0:
        return velocity
    added = min(acceleration * step_s, room)
    return velocity[0] + direction[0] * added, velocity[1] + direction[1] * added, velocity[2] + direction[2] * added


def step(velocity: tuple[float, float, float],
         position: tuple[float, float, float],
         anchor: tuple[float, float, float],
         stick: tuple[float, float, float],
         gravity: float,
         pull_strength: float,
         pull_cap: float,
         steer_strength: float,
         steer_cap: float,
         carry: float,
         step_s: float) -> tuple[float, float, float]:
    """The velocity to write this frame.

    `stick` is the move input in world axes, already turned by the camera, its length 0 to 1.
    `gravity` is the gravity of the moment, which Apex Movement doubles: the model follows it.
    `pull_cap` is what the pull may reach along the rope, the player's own momentum included — the
    caller adds the speed it had at contact, since the reading caps what the pull *adds*.
    `carry` is the share of gravity the rope holds, 0 to 1.
    """
    step_s = min(max(step_s, 0.0), LONGEST_STEP_S)
    if step_s <= 0.0:
        return velocity
    falling = gravity * (1.0 - min(max(carry, 0.0), 1.0))
    if falling > 0.0:
        velocity = (velocity[0], velocity[1], velocity[2] - falling * step_s)
    rope = toward(position, anchor)
    if rope is not None:
        velocity = push_toward(velocity, rope, gravity * pull_strength, pull_cap, step_s)
    pushed = unit(*stick)
    if pushed is not None:
        # Scaled by how far the stick is pushed: a keyboard always reads fully pushed, a stick half
        # way pushes half as hard, which is what a player feels on the ground.
        lean = min(1.0, math.sqrt(sum(part * part for part in stick)))
        velocity = push_toward(velocity, pushed, gravity * steer_strength * lean, steer_cap, step_s)
    return velocity
