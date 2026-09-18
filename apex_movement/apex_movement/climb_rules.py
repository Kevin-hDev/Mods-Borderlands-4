"""The wall climb's rules (phase 2 spec, section 2): when a climb starts, why it does not, when it ends, and the wait
before the next.

Kevin's choices on 2026-09-17: a climb starts with a jump at a wall, the stick pushed toward it and the camera looking
at it; it rises about twice the character's height; the game pulls the player over the top; a climb that ends short
blocks the next one for a little over a second, and landing clears that wait; there is no limit on the number of
climbs. A climb goes where the stick asks, straight up or leaning along the wall up to the lean limit (climb_aim).

Every way a climb can fail to start has its own name, and start_refusal is the only place that decides: the log tells
the player's failed tries apart (Kevin, 2026-09-17, some walls of a structure refusing to be climbed), and a second
list of conditions for the log alone would have drifted from the one that decides. No SDK import, so every rule is
tested without the game.
"""

import math
from dataclasses import dataclass

from .climb_aim import Wall, angle_to_wall, view_angle
from .wall_choice import MIN_WALL_FLAT

# The character's radius (40, measured on 2026-09-17) plus 50: all thirteen pushes of the measure started within it,
# none by mistake.
REACH = 90.0
# The climb leans into the wall, which kept it within 90 during the measure: past this, the wall has ended.
LOST_REACH = 135.0
# Pushed at least halfway (phase 2 spec, 2.1, condition 3): chosen, not measured, to tune in game if needed.
MIN_STICK = 0.5
# Within 45 degrees of the wall (spec 2.1, condition 4; Kevin: "il faut regarder le mur"): chosen, not measured.
START_VIEW_DEG = 45.0
# A stick let go for less than this keeps the climb: in play the stick crosses its centre between two pushes, and
# séance Y ended 14 climbs out of 73 on the stick alone. Long enough to forgive a flick, short enough that letting go
# still stops a climb when the player means it.
STICK_GRACE_NS = 250_000_000
# Wider than at the start, so that a small camera move does not cut a climb (spec, end 12). The stick gets the same:
# pushed forward it turns with the camera, and at 45 it cut climbs before the camera rule (0.8.0 test, no camera end).
KEEP_MARGIN_DEG = 15.0
# The stick's tolerance at a start before the diagonal existed (spec 2.1, condition 3: "à 45° près"). start_angle
# takes the larger of this and the lean limit, and the end rule allows that same angle plus KEEP_MARGIN_DEG.
MIN_START_DEG = 45.0
# A climb rises about 70 in 0.2 s. Under an overhang it rose nothing and hung there while the stick was pushed (0.8.0
# test, three climbs of 2.1 to 4.3 s; Kevin: "le personnage ne chute pas, il reste en haut").
STALL_NS = 200_000_000
# Chosen, not measured (spec, end 12 bis): a seventh of that normal rise.
MIN_PROGRESS = 10.0
# The jump count may update a frame after take-off (apex_jump_track): a rise this early is still the same jump.
JUMP_SETTLE_NS = 50_000_000

MANTLE = "mantle"
LANDED = "landed"
GAME_MOVE = "game_move"
JUMP = "jump"
WALL_LOST = "wall_lost"
STICK = "stick"
CAMERA = "camera"
HEIGHT = "height"
BLOCKED = "blocked"
# Every end short of the top blocks the next climb: otherwise releasing and pushing the stick again, or a dash between
# two climbs, would climb forever (spec, 2.4).
DELAYED = frozenset({GAME_MOVE, JUMP, WALL_LOST, STICK, CAMERA, HEIGHT, BLOCKED})

# Why a climb did not start, in the order they are looked at. REFUSALS holds every one of them: a reason missing from
# it would never be told, and séance Y spent a session on a refusal no line could name.
ON_GROUND = "on_ground"
GAME_MOVE_BUSY = "game_move"
MANTLING = "game_mantle"
GAME_CLIMB = "game_climb"
WAITING = "waiting"
NO_WALL = "no_wall"
TOO_FAR = "too_far"
SLOPE = "slope"
NO_STICK = "no_stick"
LOW_ONLY = "low_only"
# From the most general to the most precise; how far down this list a try got is how close it came to a climb.
REFUSALS = (GAME_MOVE_BUSY, MANTLING, GAME_CLIMB, WAITING, NO_WALL, TOO_FAR, SLOPE, LOW_ONLY, NO_STICK, STICK, CAMERA)


@dataclass(frozen=True)
class Moment:
    now_ns: int
    in_air: bool
    on_ground: bool
    game_move: bool
    mantling: bool
    near_game_climb: bool
    z: float
    jumps: int
    stick_x: float
    stick_y: float
    view_yaw: float | None
    # The surface the climb judges itself on, and how many of the traces met anything at all: a refusal where none did
    # points at a structure the traces go through, one where they all did points at the rules.
    wall: Wall | None
    hits: int
    # Whether a wall was seen at the character's own height or above. A step, a kerb or a stair tread is only seen by
    # the traces below: climbing those stole the jump that was leaving the ground (Kevin, 2026-09-17).
    high_wall: bool


@dataclass(frozen=True)
class Limits:
    height: float
    delay_ns: int
    # Degrees a climb may lean to a side. No default: the slider is its only authority, and a forgotten value here
    # would ignore it in silence.
    lean_deg: float
    # Not read by the rules: it rides here so wall_climb._limits bounds every slider in one place. No default either.
    speed: float


@dataclass(frozen=True)
class Step:
    climbing: bool
    event: str = ""
    rise: float = 0.0
    ms: int = 0


def start_angle(limits: Limits) -> float:
    """How far off the wall the stick may be for a climb to start: the lean limit, never under MIN_START_DEG, so that
    with no lean allowed a stick roughly toward the wall still starts a straight climb."""
    return max(MIN_START_DEG, limits.lean_deg)


def view_angle_allowed(limits: Limits) -> float:
    """How far off the wall the camera may be for a climb to start.

    It follows the diagonal like the stick does: climbing to one side means looking that way, and a camera limit left
    at 45 while the stick reached 60 ended 21 climbs out of 73 on the camera alone (séance Y).
    """
    return max(START_VIEW_DEG, limits.lean_deg)


def longest_climb_ns(limits: Limits) -> int:
    """The longest a climb can live: its height at the slowest rise that escapes BLOCKED, whatever the climb speed."""
    return math.ceil(limits.height / MIN_PROGRESS) * STALL_NS


class Rules:
    def __init__(self) -> None:
        self.start: Moment | None = None
        self.jumps = 0
        self.progress_z = 0.0
        self.progress_ns = 0
        self.blocked_until_ns = 0
        # When the stick first left, so a flick between two pushes does not end a climb.
        self.stick_lost_ns = 0

    def step(self, m: Moment, limits: Limits) -> Step:
        if m.on_ground:
            self.blocked_until_ns = 0
        if self.start is not None:
            reason = self._end_reason(m, limits)
            if not reason:
                return Step(climbing=True)
            start, self.start = self.start, None
            if reason in DELAYED:
                self.blocked_until_ns = m.now_ns + limits.delay_ns
            return Step(climbing=False, event=reason, rise=m.z - start.z, ms=(m.now_ns - start.now_ns) // 1_000_000)
        if not self.start_refusal(m, limits):
            self.start, self.jumps = m, m.jumps
            self.progress_z, self.progress_ns = m.z, m.now_ns
            self.stick_lost_ns = 0
            return Step(climbing=True, event="start")
        return Step(climbing=False)

    def jumps_given_back(self, count: int) -> None:
        """The climb put the jump count back to this: a jump from the wall is one above it, not above the old count."""
        self.jumps = count

    def start_refusal(self, m: Moment, limits: Limits) -> str:
        """Why no climb starts at this moment, or "" when one does. The only place that decides, so that what the log
        says and what the mod does can never disagree."""
        if not m.in_air:
            return ON_GROUND
        if m.game_move:
            return GAME_MOVE_BUSY
        if m.mantling:
            return MANTLING
        if m.near_game_climb:
            return GAME_CLIMB
        if m.now_ns < self.blocked_until_ns:
            return WAITING
        wall = m.wall
        if wall is None:
            return NO_WALL
        if wall.distance > REACH:
            return TOO_FAR
        if wall.flat < MIN_WALL_FLAT:
            return SLOPE
        if not m.high_wall:
            return LOW_ONLY
        if math.hypot(m.stick_x, m.stick_y) < MIN_STICK:
            return NO_STICK
        if angle_to_wall(m.stick_x, m.stick_y, wall) > start_angle(limits):
            return STICK
        if view_angle(m.view_yaw, wall) > view_angle_allowed(limits):
            return CAMERA
        return ""

    def _end_reason(self, m: Moment, limits: Limits) -> str:
        if m.mantling:
            return MANTLE
        if m.on_ground:
            return LANDED
        if not m.in_air or m.game_move:
            return GAME_MOVE
        if m.jumps > self.jumps:
            if m.now_ns - self.start.now_ns >= JUMP_SETTLE_NS:
                return JUMP
            self.jumps = m.jumps
        wall = m.wall
        if wall is None or wall.distance > LOST_REACH or wall.flat < MIN_WALL_FLAT:
            return WALL_LOST
        if view_angle(m.view_yaw, wall) > view_angle_allowed(limits) + KEEP_MARGIN_DEG:
            return CAMERA
        if (math.hypot(m.stick_x, m.stick_y) < MIN_STICK
                or angle_to_wall(m.stick_x, m.stick_y, wall) > start_angle(limits) + KEEP_MARGIN_DEG):
            if self.stick_lost_ns == 0:
                self.stick_lost_ns = m.now_ns
            if m.now_ns - self.stick_lost_ns >= STICK_GRACE_NS:
                return STICK
        else:
            self.stick_lost_ns = 0
        if m.z - self.start.z >= limits.height:
            return HEIGHT
        if m.z >= self.progress_z + MIN_PROGRESS:
            self.progress_z, self.progress_ns = m.z, m.now_ns
        elif m.now_ns - self.progress_ns >= STALL_NS:
            return BLOCKED
        return ""
