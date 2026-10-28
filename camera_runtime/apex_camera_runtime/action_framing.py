"""Where the camera sits for what the player does (dynamic camera, idea 2): back while running, back and up in the
air, closer when crouched; at the wheel, back with the vehicle's speed.

Game units in the camera's axes (X forward, Z up), added to the game's own placement (ThirdPerson: 256 back, 25 down,
Nexus-Data-camera_mode0.json). These are the trial's values: Kevin, 2026-10-06, « je trouve tes réglages très bien
comme ça pour un par défaut », and for the vehicle « ça me convient ». The strength setting scales them.
"""

from .player_sample import Sample

RUN = (-60.0, 0.0)
AIR = (-40.0, 30.0)
CROUCH = (50.0, 0.0)
# The whole run offset from 0.75 of Kevin's top sprint (1269), the speed FOV's full zone: it follows him as he brakes.
FULL_SPEED = 950.0
# At the wheel the game moves its own camera with speed and boost too (ThirdPersonVehicle's VehicleOffset); ours adds
# to it. Vehicle speeds differ and are not measured: full from 0.75 of the top speed seen in this vehicle, never
# below this floor (Kevin's trial reached 3722).
VEHICLE = (-80.0, 0.0)
VEHICLE_FULL_SHARE = 0.75
VEHICLE_FULL_MIN = 1000.0
SECONDS = 0.6
AIM_SECONDS = 0.25


def action(sample: Sample | None) -> str:
    if sample is None:
        return "none"
    if sample.aiming:
        return "aim"
    if sample.in_air:
        return "air"
    # A slide is crouched too: it counts as running.
    if sample.sprinting or sample.sliding:
        return "run"
    if sample.crouched:
        return "crouch"
    return "rest"


def target(sample: Sample | None, strength: float) -> tuple[float, float]:
    name = action(sample)
    if name == "air":
        values, share = AIR, 1.0
    elif name == "run":
        values, share = RUN, min(1.0, max(0.0, sample.flat_speed / FULL_SPEED))
    elif name == "crouch":
        values, share = CROUCH, 1.0
    else:
        return 0.0, 0.0
    return values[0] * share * strength, values[1] * share * strength


def seconds(sample: Sample | None) -> float:
    return AIM_SECONDS if action(sample) == "aim" else SECONDS


def vehicle_target(speed: float, top: float, strength: float) -> tuple[float, float]:
    share = min(1.0, max(0.0, speed / max(VEHICLE_FULL_MIN, VEHICLE_FULL_SHARE * top)))
    return VEHICLE[0] * share * strength, VEHICLE[1] * share * strength
