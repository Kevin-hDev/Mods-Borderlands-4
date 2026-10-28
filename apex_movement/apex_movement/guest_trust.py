"""Co-op: when a host takes a guest's place from the guest's own game instead of correcting it.

The host replays each move of a guest with Apex's values at its own frames, and lands a little off: corrected, a guest
was put back on the ground just after a slide jump, one jump in two even with its slide seen from the first frame, and
pulled back after every climb the host ended before the guest (trial 6, docs/coop/2026-10-17-saccades-restantes.md,
verified in both copies). With the engine's two switches below on, the host's copy of a climbing guest followed the
guest's place exactly (same trial). Kevin chose them for the climb (« L'invité décide »), then for the slide and the
climb up to the landing, jump included (« Glissade et grimpe », 2026-10-18). Accepted limit: meanwhile an explosion on
the host's side cannot push the guest.
"""

from typing import Any

from . import game

SWITCHES = {"bIgnoreClientMovementErrorChecksAndCorrection": True, "bServerAcceptClientAuthoritativePosition": True}
# A guest who has not stood on the ground since (a fall out of the world, a teleport by the host in mid-air) gets the
# host's corrections back after this long. Estimate, not measured: room for a jump and a glide after it.
LONGEST_NS = 10_000_000_000


def until_landing(guest: Any, key: str, active: bool) -> dict[str, Any]:
    """The switches from a frame where a movement's gesture is under way (`active`) until the guest stands on the
    ground again, and at most LONGEST_NS after the gesture's last frame. `key` is that movement's own entry in the
    guest's memo, so a slide and a climb keep separate windows."""
    if active:
        guest.memo[key] = guest.now_ns
        return dict(SWITCHES)
    last = guest.memo.get(key)
    if last is None:
        return {}
    if game.is_on_ground(guest.character.CharacterMovement) or guest.now_ns - last > LONGEST_NS:
        del guest.memo[key]
        return {}
    return dict(SWITCHES)
