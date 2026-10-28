"""Whether a vehicle has ground under it: one trace straight down from a little above its origin.

The vehicle's origin sat 22 above the flat ground it drove on (sessions 3 to 9); jumps rose 343 to 652. Channel 2 and
the call are Apex Movement's wall_sense recipe, verified in game; the vehicle itself is ignored by the trace.
The push in the air looks nearer (air_push.AIR_REACH): at this reach a jump only showed for 0.4 s (session 11).
"""

from typing import Any

import unrealsdk

TRACE_UP = 50.0
GROUND_REACH = 250.0
TRACE_CHANNEL = 2

_library: Any = None
# The trace's result and drawing colours, made once: only inputs to the call, never read back.
_unread: tuple[Any, Any, Any] | None = None


def on_ground(vehicle: Any, reach: float = GROUND_REACH) -> bool:
    global _library, _unread
    if _library is None:
        _library = unrealsdk.find_class("KismetSystemLibrary").ClassDefaultObject
    if _unread is None:
        _unread = (unrealsdk.make_struct("HitResult"), unrealsdk.make_struct("LinearColor"),
                   unrealsdk.make_struct("LinearColor"))
    out_hit, trace_colour, hit_colour = _unread
    where = vehicle.K2_GetActorLocation()
    x, y, z = where.X, where.Y, where.Z
    start = unrealsdk.make_struct("Vector", X=x, Y=y, Z=z + TRACE_UP)
    end = unrealsdk.make_struct("Vector", X=x, Y=y, Z=z - reach)
    hit, _ignored, _result = _library.LineTraceSingle(
        vehicle, start, end, TRACE_CHANNEL, False, [], 0, out_hit, True, trace_colour, hit_colour, 0.0,
    )
    return bool(hit)
