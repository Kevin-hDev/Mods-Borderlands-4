"""The grapple gun's shots in progress, and the pieces they are shown with: each rope from the muzzle to its hook.

Two places, each a rope and a hook: a new shot leaves at once while the last one's hook comes back, and the returning
one finishes (docs/apex_grapple/pistolet-grappin/spec-pistolet-grappin.md, section 9, choice 7); a third shot takes
the place of the one let go the longest ago, the nearest to the hand. A place half built when the game refuses a
piece leaves its pieces hidden on the character, gone with it. The pieces are built for the settings in use, and
built again only while no shot is in progress, so a shot keeps the look it left with. They live on the character: a
new character (a level loaded) has none, and the old ones are forgotten, never called. look_play.py is the only
caller; rope_visuals.py owns what a failure here costs. Each shot is told apart by what start() returns: its end, the
hook let go or the rope dropped with the arm, is its own, whatever shot came after (spec-pistolet-grappin.md, 3.3).
"""

import time
from typing import Any

from unrealsdk.unreal import WeakPointer

from . import look_assets, look_hook, look_load, look_rope, look_settings, look_timing, report, rope_motion, settings

PLACES = 2


class _Place:
    def __init__(self, character: Any, look: str, thickness: str, count: int, objects: dict, colour: str) -> None:
        self.rope = look_rope.Rope(character, look, thickness, count, objects, colour)
        self.hook = look_hook.Hook(character, objects)
        self.shot: look_timing.Shot | None = None
        self.slack: str | None = None
        self.size: str | None = None

    def hide(self) -> None:
        self.shot = None
        self.rope.show(0)
        self.hook.hide()

    def destroy(self) -> None:
        try:
            self.rope.destroy()
        finally:
            self.hook.destroy()


_owner: Any = None
_built: tuple | None = None
_places: list[_Place] = []
_current: _Place | None = None
_hand: tuple | None = None


def _wanted() -> tuple[str, str, int, str]:
    """The pieces the settings ask for. The colour builds them again only where it is painted, in C's glow: the
    others take it at each shot."""
    look, thickness = look_settings.rope_look.value, look_settings.rope_thickness.value
    colour = look_settings.rope_colour.value if look_rope.glows(look) else look_assets.COLOUR_AT_FIRST
    return look, thickness, look_rope.count(look, thickness, float(settings.grapple_range.value)), colour


def _mine(character: Any) -> bool:
    return _owner is not None and _owner() is character


def busy() -> bool:
    return any(place.shot is not None for place in _places)


def built() -> bool:
    return bool(_places)


def prepare(character: Any) -> None:
    """The pieces for the settings in use, built on `character` unless they are already, or a shot is in progress.
    look_load.Missing names what the game does not have; any other error of the game propagates."""
    global _owner, _built, _places
    wanted = _wanted()
    if (_mine(character) and _built == wanted) or (_mine(character) and busy()):
        return
    reset()
    look, thickness, count, colour = wanted
    began = time.perf_counter()
    objects = look_load.fetch(look_rope.wanted(look, colour) + look_hook.wanted())
    _owner, _built = WeakPointer(character), wanted
    for _ in range(PLACES):
        _places.append(_Place(character, look, thickness, count, objects, colour))
    report.note(f"grapple gun built: rope {look} at {thickness}, {count} pieces a rope"
                f"{f' and its glow in {colour}' if len(_places[0].rope.strands) > 1 else ''}, "
                f"{PLACES} ropes and hooks, "
                f"in {(time.perf_counter() - began) * 1000:.0f} ms")


def start(character: Any, hand: tuple, anchor: tuple, now_ns: int, flight_s: float) -> look_timing.Shot:
    """A shot leaves: the hook from the muzzle `hand` toward `anchor`, there in `flight_s`, at the settings in use."""
    global _current, _hand
    prepare(character)
    free = [place for place in _places if place.shot is None]
    if free:
        place = free[0]
    else:
        place = min(_places, key=lambda one: one.shot.released_ns if one.shot.released_ns is not None
                    else float("inf"))
        place.hide()
    size = look_settings.hook_size.value
    place.slack, place.size = look_settings.rope_movement.value, size
    place.rope.light(look_assets.ROPE_LIGHTS[look_settings.rope_light.value], look_settings.rope_colour.value,
                     look_settings.glow_face.value)
    place.shot = look_timing.Shot(now_ns, int(flight_s * look_timing.NS_PER_S), tuple(anchor),
                                  look_hook.length(size), look_assets.HOOK_SUNK_CM, float(settings.hook_speed.value))
    _current, _hand = place, tuple(hand)
    return place.shot


def hand() -> tuple | None:
    """The muzzle last seen, where the ropes start."""
    return _hand


def holds(shot: look_timing.Shot) -> bool:
    """Whether that shot's hook is still out: flying, planted or coming back."""
    return any(place.shot is shot for place in _places)


def hold(hand: tuple, now_ns: int) -> None:
    """The pull starts: the hook bites."""
    if _current is not None and _current.shot is not None:
        look_timing.catch(_current.shot, hand, now_ns)


def let_go(shot: look_timing.Shot, now_ns: int) -> None:
    """That shot's hook comes back from where it is, measured from the muzzle last seen."""
    global _current
    for place in _places:
        if place.shot is shot and _hand is not None:
            look_timing.release(shot, _hand, now_ns)
            if place is _current:
                _current = None


def drop(shot: look_timing.Shot) -> None:
    """That shot's rope and hook taken away at once: gone off screen with the arm."""
    global _current
    for place in _places:
        if place.shot is shot:
            if place is _current:
                _current = None
            place.hide()


def tick(character: Any, hand: tuple, now_ns: int) -> None:
    """Each shot in progress shown where its timing puts it; each hook back in the hand ends its shot."""
    global _current, _hand
    if not _mine(character):
        forget()
        return
    _hand = tuple(hand)
    for place in _places:
        if place.shot is None:
            continue
        found = look_timing.where(place.shot, _hand, now_ns)
        if found is None:
            if place is _current:
                _current = None
            place.hide()
            continue
        base, way, phase, since = found
        clock = look_timing.clock_s(place.shot, now_ns)
        place.rope.lay(rope_motion.shape(_hand, base, place.slack, rope_motion.swing(phase, since), clock))
        place.hook.put(base, way, place.size)


def forget() -> None:
    """Drops every piece without calling it: its character is gone, and the pieces with it."""
    global _owner, _built, _places, _current, _hand
    _owner, _built, _places, _current, _hand = None, None, [], None, None


def reset() -> None:
    """Every piece removed at once, on the character that still holds them; forgotten in any case."""
    places, alive = _places, _owner is not None and _owner() is not None
    forget()
    if not alive:
        return
    failed = None
    for place in places:
        try:
            place.destroy()
        except Exception as error:
            failed = failed or error
    if failed is not None:
        raise failed
