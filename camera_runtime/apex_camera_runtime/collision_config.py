"""Camera guard geometry, sweep volume and bounded diagnostics."""
from .generated_ads import CAMERA_MAX_COORDINATE as MAX_COORDINATE
RADIUS = 10.0
MIN_RADIUS = 1.0
VOLUME_RECHECKS = 2
# Kevin accepted at most 1 mm TOTAL separation, not 1 mm per retry (engine units are cm).
MAX_CONTACT_RELAXATION = 0.1
CONTACT_TOLERANCE = MAX_CONTACT_RELAXATION / VOLUME_RECHECKS
MARGIN = 2.0
TRACE_CHANNEL = 1
MAX_LENGTH = 100_000.0
MIN_LENGTH = 1.0e-6
from .diagnostics_config import INCIDENT_PERIOD_NS, STATUS_PERIOD_NS
POSITION_FAILURE = "Camera collision unavailable; native position retained"
# Getting into a vehicle, the game's camera folds onto the hunter's head for one frame, the camera guard refuses it, and
# the game then pauses about 0.1 s on that frame (docs/third_person_fov/camera/enquetes/2026-10-08-saccade-vehicule.md).
# A failure this soon after a resolved frame keeps that frame's camera instead; Kevin chose this on 2026-10-08.
HOLD_NS = 200_000_000
HELD_FAILURE = "Camera collision unavailable; previous position held"
# That folded camera stands 0 cm across from the hunter and 71 cm above its centre, on all six entries measured
# (docs/third_person_fov/camera/releves/: 2026-10-08-saccade-vehicule/sonde-1.txt and
# 2026-10-08-sauts-camera/sonde-vehicule-garde-1.txt); it often only touches the vehicle, so nothing else tells it
# apart. In play the game's arm keeps the camera off the hunter's head: the closest measured is 74 cm from its centre
# (2026-10-08-sauts-camera/sonde-1.txt), across distance not recorded. A frame wrongly caught only keeps the last good
# camera, for HOLD_NS at most (cm).
FOLD_ACROSS_CM = 5.0
FOLD_REACH_CM = 100.0
# The refusals the collision files raise themselves: only these reasons reach the log, never another error's text,
# which could carry internal details. Kevin, 2026-10-08: the vehicle jolt investigation needs to know which one fires
# (docs/third_person_fov/camera/enquetes/2026-10-08-saccade-vehicule.md); test_collision_diagnostics.py keeps this
# list in step with the raise sites.
KNOWN_REFUSALS = frozenset((
    "Invalid collision identity", "Camera collision identity unavailable", "invalid collision point",
    "invalid collision segment", "invalid collision contact", "invalid collision result",
    "invalid initial collision depth", "camera folded onto the hunter"))
STATUS_LINE = ("camera collision frames={frames} errors={errors} "
               "max_us={max_us:.0f} mean_us={mean_us:.1f}")
