"""Whether a vehicle has ground under it: one trace straight down from a little above its origin.

The vehicle's origin sat 22 above the flat ground it drove on (sessions 3 to 9); jumps rose 343 to 652. Channel 2 and
the call are Apex Movement's wall_sense recipe, verified in game; the vehicle itself is ignored by the trace.
"""

from typing import Any

import unrealsdk

TRACE_UP = 50.0
GROUND_REACH = 250.0
TRACE_CHANNEL = 2

_library: Any = None


def on_ground(vehicle: Any) -> bool:
    global _library
    if _library is None:
        _library = unrealsdk.find_class("KismetSystemLibrary").ClassDefaultObject
    where = vehicle.K2_GetActorLocation()
    start = unrealsdk.make_struct("Vector", X=where.X, Y=where.Y, Z=where.Z + TRACE_UP)
    end = unrealsdk.make_struct("Vector", X=where.X, Y=where.Y, Z=where.Z - GROUND_REACH)
    hit, _ignored, _result = _library.LineTraceSingle(
        vehicle, start, end, TRACE_CHANNEL, False, [], 0, unrealsdk.make_struct("HitResult"), True,
        unrealsdk.make_struct("LinearColor"), unrealsdk.make_struct("LinearColor"), 0.0,
    )
    return bool(hit)
