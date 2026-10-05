"""Camera collision geometry, recovery and bounded diagnostics."""
from .generated_ads import CAMERA_MAX_COORDINATE as MAX_COORDINATE
RADIUS = 10.0
MIN_RADIUS = 1.0
VOLUME_RECHECKS = 2
# Kevin accepted at most 1 mm TOTAL separation, not 1 mm per retry (engine units are cm).
MAX_CONTACT_RELAXATION = 0.1
CONTACT_TOLERANCE = MAX_CONTACT_RELAXATION / VOLUME_RECHECKS
# Centered 0.2 mm sweep contains the endpoint sphere without relying on stationary overlap queries.
ENDPOINT_PROBE_HALF_LENGTH = 0.01
VISIBILITY_STEPS = 6
VISIBILITY_PATH_STEPS = 16
VISIBILITY_SAMPLE_SPACING = 4.0
VISIBILITY_CACHE_SIZE = 32
VISIBILITY_INWARD_SPEED = 160.0
RELEASE_MARGIN = 1.0
UPPER_BODY_FRACTION = 0.75
MARGIN = 2.0
TRACE_CHANNEL = 1
MAX_LENGTH = 100_000.0
MIN_LENGTH = 1.0e-6
RETURN_SPEED = 12.0
VISIBILITY_DELAY = 0.2
MAX_DELTA = 0.1
from .diagnostics_config import INCIDENT_PERIOD_NS, STATUS_PERIOD_NS
POSITION_FAILURE = "Camera collision unavailable; native position retained"
STATUS_LINE = ("camera collision frames={frames} blocked={blocked} errors={errors} "
               "max_us={max_us:.0f} mean_us={mean_us:.1f}")
