"""What a co-op guest's grapple says to the host, in the one number the game lets a guest send it.

The guest's grapple key never reaches the game, so the host never hears of the rope and puts the guest back on the
ground (verified in game, docs/coop/2026-10-16-essai-deux-avec-mods.md). The game's own ServerSetBestGrappleable
carries a target and a 32-bit number from a guest to the host; sent with no target, its number arrives untouched and
the host shows no error (verified in the logs, docs/coop/2026-10-17-grappin-invite.md, trial 2).

Its two top bits say what the rest is:
- a rope going: which way the hook went from the guest's character, 15 bits across and 15 up, about 1 cm at 60 m; the
  host finds the anchor itself, by the same ray along that way;
- the guest's look (look_code.py), so that every player sees that guest's grapple as the guest chose it.
0 is what the game sends for "no target", so it is never ours; RELEASE says the rope let go.
"""

import math

RELEASE = 1
ROPE, LOOK = 1, 2
KIND_SHIFT = 30
PAYLOAD = (1 << KIND_SHIFT) - 1
TURN = 1 << 15
UP_STEPS = (1 << 15) - 1


def is_ours(target: object, code: int) -> bool:
    """A message of ours: no target, and a number the game never sends without one."""
    return target is None and code != 0


def kind(code: int) -> int:
    return code >> KIND_SHIFT


def encode_rope(direction: tuple[float, float, float]) -> int:
    """`direction` as the number sent: any length."""
    x, y, z = direction
    length = math.sqrt(x * x + y * y + z * z)
    if length <= 0.0:
        raise ValueError("a direction needs a length")
    yaw = math.atan2(y, x)
    pitch = math.asin(max(-1.0, min(1.0, z / length)))
    across = int(round((yaw + math.pi) / (2.0 * math.pi) * TURN)) % TURN
    up = int(round((pitch + math.pi / 2.0) / math.pi * UP_STEPS))
    return (ROPE << KIND_SHIFT) | (across << 15) | up


def decode_rope(code: int) -> tuple[float, float, float]:
    """The way the hook went, as a direction of length 1."""
    across, up = (code >> 15) & (TURN - 1), code & (TURN - 1)
    yaw = across / TURN * 2.0 * math.pi - math.pi
    pitch = up / UP_STEPS * math.pi - math.pi / 2.0
    return math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)


def encode_look(number: int) -> int:
    if not 0 <= number <= PAYLOAD:
        raise ValueError("a look number out of range")
    return (LOOK << KIND_SHIFT) | number


def decode_look(code: int) -> int:
    return code & PAYLOAD
