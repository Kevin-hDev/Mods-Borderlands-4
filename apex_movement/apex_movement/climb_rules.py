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

# The character's radius (40, measured on 2026-09-17) plus 50: all thirteen pushes of the measure started within it,
# none by mistake.
REACH = 90.0
# The climb leans into the wall, which kept it within 90 during the measure: past this, the wall has ended.
LOST_REACH = 135.0
MIN_STICK = 0.5
START_VIEW_DEG = 45.0
# A stick let go for less than this keeps the climb: in play the stick crosses its centre between two pushes, and
# séance Y ended 14 climbs out of 73 on the stick alone. Long enough to forgive a flick, short enough that letting go
# still stops a climb when the player means it.
STICK_GRACE_NS = 250_000_000
# A face leaning more than about 45 degrees off upright is a slope to walk on, not a wall to climb.
MIN_WALL_FLAT = 0.7
# Wider than at the start, so that a small camera move does not cut a climb (spec, end 12). The stick gets the same:
# pushed forward it turns with the camera, and at 45 it cut climbs before the camera rule (0.8.0 test, no camera end).
KEEP_MARGIN_DEG = 15.0
# A climb may lean along the wall as far as the stick asks, up to the lean limit (Kevin, 2026-09-17: "que la grimpe ne
# fonctionne pas que tout droit, qu'elle puisse fonctionner en diagonale jusqu'à 60 degrés"). That one angle rules the
# stick everywhere: a climb starts on a stick within it, and ends past it plus the margin. Three separate angles could
# disagree — a lean the start refuses, or an end before the fullest diagonal.
MIN_START_DEG = 45.0
# A climb rises about 70 in 0.2 s. Under an overhang it rose nothing and hung there while the stick was pushed (0.8.0
# test, three climbs of 2.1 to 4.3 s; Kevin: "le personnage ne chute pas, il reste en haut").
STALL_NS = 200_000_000
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
    # The surface the climb judges itself on, and how many of the traces met anything at all: a refusal that says
    # 0 of 3 points at the structure being invisible to the trace, one that says 3 points at the rules.
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


@dataclass(frozen=True)
class Step:
    climbing: bool
    event: str = ""
    rise: float = 0.0
    ms: int = 0


# Two surfaces facing within this of each other are the same wall, seen at two heights: beyond it they are two walls,
# and averaging them would point into neither.
SAME_WALL_COS = 0.7


def best_wall(walls: list[Wall]) -> Wall | None:
    """The surface a climb should judge itself on, out of what the traces met: the nearest one upright enough to be a
    wall, or else the nearest of all, so a refusal can say how far it was and how much it leaned.

    Sorting by uprightness among those within reach cost séance U: rising past REACH left only a bevel two units away,
    the most upright of what was left at 0.53, and the climb ended on a lost wall while the panel stood at 98. Leaning
    surfaces are not candidates at all — that is what the threshold means.
    """
    if not walls:
        return None
    upright = [wall for wall in walls if wall.flat >= MIN_WALL_FLAT]
    if not upright:
        return min(walls, key=lambda wall: wall.distance)
    nearest = min(upright, key=lambda wall: wall.distance)
    # The face of a wall carries bars, bolts and corrugation. Each is upright enough to be picked on its own, and each
    # points its own way, which turns a climb or ends it (Kevin, 2026-09-17: "c'est presque plat, ça devrait être
    # considéré comme du plat"). Averaging the heights that see the same wall smooths them out.
    same = [wall for wall in upright
            if wall.into_x * nearest.into_x + wall.into_y * nearest.into_y >= SAME_WALL_COS]
    return _merged(same)


def _merged(walls: list[Wall]) -> Wall:
    """One wall out of several views of it: the nearest distance, the average way in and way up."""
    if len(walls) == 1:
        return walls[0]
    into_x, into_y = _unit(sum(w.into_x for w in walls), sum(w.into_y for w in walls))
    up_x, up_y, up_z = _unit3(sum(w.up_x for w in walls), sum(w.up_y for w in walls), sum(w.up_z for w in walls))
    return Wall(distance=min(w.distance for w in walls), into_x=into_x, into_y=into_y,
                flat=max(w.flat for w in walls), up_x=up_x, up_y=up_y, up_z=up_z)


def _unit(x: float, y: float) -> tuple[float, float]:
    length = math.hypot(x, y)
    return (x / length, y / length) if length > 1e-6 else (x, y)


def _unit3(x: float, y: float, z: float) -> tuple[float, float, float]:
    length = math.sqrt(x * x + y * y + z * z)
    return (x / length, y / length, z / length) if length > 1e-6 else (0.0, 0.0, 1.0)


def start_angle(limits: Limits) -> float:
    """How far off the wall the stick may be for a climb to start: never under MIN_START_DEG, so that a jump with the
    stick pushed sideways stays a jump even when no lean at all is allowed."""
    return max(MIN_START_DEG, limits.lean_deg)


def view_angle_allowed(limits: Limits) -> float:
    """How far off the wall the camera may be for a climb to start.

    It follows the diagonal like the stick does: climbing to one side means looking that way, and a camera limit left
    at 45 while the stick reached 60 ended 21 climbs out of 73 on the camera alone (séance Y).
    """
    return max(START_VIEW_DEG, limits.lean_deg)


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
