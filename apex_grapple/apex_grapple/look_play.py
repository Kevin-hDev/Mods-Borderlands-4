"""The grapple gun's look for the hunter, shot by shot: the one owner of what a shot of ours shows, from the press
to the last gesture. Each frame it asks look_moves where the gestures are, plays them (look_gestures), shows the pistol
and the holster in the view of the moment (look_gun), finds the muzzle (look_muzzle) and lays the ropes from it
(look_shots).

The ends are the conception's (docs/apex_grapple/pistolet-grappin/spec-pistolet-grappin.md, section 3.3; conception-
pistolet-et-gestes.md): from behind, the hook comes back into the muzzle, then the pistol goes back into its holster.
Through the eyes, the arm folds and leaves the screen with the pistol, the rope still hooked, unless some of the rope
would show once the arm is out: then the hook comes back into the muzzle while the arm leaves (look_sight). Once the
arm is out, a rope still hooked is checked again: still on screen, its hook comes back; off it, rope and hook go.
Through the eyes the arms' pistol shows once the arm's gesture has faded in, the hand off the weapon (drawings of 14
October). The pieces live on the character: a new one gets new pieces, the old ones are forgotten, never called.
rope_visuals.py is the only caller, and owns what a failure here costs.
"""

import math
from dataclasses import dataclass
from typing import Any

from unrealsdk import unreal

from . import (arms, game, look_assets, look_eye, look_gestures, look_gun, look_hunter, look_load, look_moves,
               look_muzzle, look_outfit, look_settings, look_shots, look_sight, look_timing, look_view, look_weapon,
               report, settings)

_ARMS = next(one for one in look_assets.GESTURES if one["view"] == "arms")
ENTRY_S = _ARMS["parts"]["entry"][1] - _ARMS["parts"]["entry"][0]
EXIT_S = _ARMS["parts"]["exit"][1] - _ARMS["parts"]["exit"][0]
NS = look_timing.NS_PER_S
# The screen's height over its width, for whether the rope shows: Kevin's window, 16:9 like most players'.
SCREEN = 9.0 / 16.0


@dataclass
class _Shot:
    moves: look_moves.Moves
    rope: look_timing.Shot | None
    kind: str | None
    fired_ns: int
    leaving: bool = False
    pull: look_moves.Pull | None = None
    pose: look_moves.Pose | None = None


_shot: _Shot | None = None
_gun: look_gun.Gun | None = None
_owner: Any = None


def _mine(character: Any) -> bool:
    return _owner is not None and _owner() is character


def prepare(character: Any) -> None:
    """The pistol, the holster and the ropes built on `character` unless they are already. Raises look_load.Missing
    for what the game does not have; the arms not found yet, nothing is built and the next frame tries again."""
    global _gun, _owner
    if _owner is not None and not _mine(character):
        reset()
    if _gun is None:
        found = arms.find(character)
        if found is None:
            return
        hunter = look_hunter.of(character)
        if hunter is None:
            return
        _gun = look_gun.Gun(character, found.Outer, look_load.fetch(look_gun.wanted(hunter)), hunter)
        _owner = unreal.WeakPointer(character)
    look_shots.prepare(character)


def ready() -> bool:
    return _gun is not None


def built() -> bool:
    """Whether any of our pieces is on the character."""
    return _gun is not None or look_shots.built()


def busy() -> bool:
    return _shot is not None or look_shots.busy()


def start(character: Any, anchor: tuple, now_ns: int, flight_s: float) -> None:
    global _shot
    if _shot is not None and _shot.leaving and _shot.rope is not None:
        look_shots.let_go(_shot.rope, now_ns)
    moves = look_moves.Moves(ENTRY_S, EXIT_S, now_ns, float(settings.longest_pull.value))
    kind = look_weapon.kind(character)
    _shot = _Shot(moves, None, kind, now_ns)
    pc = game.controller()
    view = look_view.of(pc, character)
    held = "no weapon" if kind is None else f"weapon {kind}"
    report.note(f"grapple gun shot: {view} person, {held} in the right hand")
    pose = _shot.pose = moves.frame(now_ns)
    _shot.rope = look_shots.start(character, _muzzle(pc, view, pose, 0.0), anchor, now_ns, flight_s)


def catch(character: Any, now_ns: int, start_gap: float, near: float, pull_cap: float) -> None:
    """The hook bites `start_gap` cm away; the pull lets go `near` cm from the anchor and adds up to `pull_cap`."""
    if _shot is None:
        return
    _shot.moves.catch(now_ns, start_gap, near, pull_cap)
    look_shots.hold(look_shots.hand(), now_ns)


def pulled(to_anchor: tuple, velocity: tuple) -> None:
    """This frame of the pull, as the grapple sees it: numbers only."""
    if _shot is not None:
        _shot.pull = look_moves.Pull(tuple(to_anchor), tuple(velocity))


def end(character: Any, now_ns: int) -> None:
    """The pull or the flight ends, however."""
    if _shot is None:
        return
    _shot.moves.end(now_ns)
    if _shot.rope is None:
        return
    pc = game.controller()
    if look_view.of(pc, character) == look_view.FIRST and not _rope_shows(pc, _shot.rope, now_ns):
        _shot.leaving = True
        report.note("grapple gun: the rope leaves the screen with the arm")
    else:
        look_shots.let_go(_shot.rope, now_ns)


def tick(character: Any, now_ns: int) -> None:
    """Every frame while the look is ours: the shot's gestures, the pieces in the view of the moment, the ropes."""
    global _shot
    prepare(character)
    if _gun is None:
        return
    pc = game.controller()
    # Every frame, shot or not: the next frame's camera, filled at the end of this one, is moved from here.
    seen, spot = look_eye.note(pc)
    view = look_view.of(pc, character, spot if seen == character else None)
    # Read only where the holster shows: the outfit is read again at each frame, never kept.
    holster = (look_settings.holster.value == look_settings.WITH and view == look_view.THIRD
               and not look_outfit.covers_hip(character))
    if _shot is None:
        _gun.show(look_gun.shown(view, False, False, holster))
        return
    shot = _shot
    pose = shot.pose = shot.moves.frame(now_ns, shot.pull)
    shot.pull = None
    look_gestures.frame(character, pose, shot.kind, look_shots.holds(shot.rope))
    since_s = (now_ns - shot.fired_ns) / NS
    gone = pose.left[0] == look_moves.GONE
    if shot.leaving and gone:
        shot.leaving = False
        if _rope_shows(pc, shot.rope, now_ns, noted=True):
            look_shots.let_go(shot.rope, now_ns)
        else:
            look_shots.drop(shot.rope)
    # The pistol hangs on the hand shown or not: its muzzle is found before the ropes move, the pieces shown after,
    # so that a hook back in the muzzle puts the pistol back in its holster on the same frame.
    look_shots.tick(character, _muzzle(pc, view, pose, since_s), now_ns)
    holding = look_shots.holds(shot.rope)
    _gun.show(look_gun.shown(view, _arms_pistol(pose, since_s), holding, holster))
    if gone and not holding and not look_gestures.busy():
        _shot = None


def _arms_pistol(pose: look_moves.Pose, since_s: float) -> bool:
    """The arms' pistol shows once their gesture has faded in, the hand off the weapon, until the arm is out."""
    return since_s >= look_gestures.FADE_S and pose.left[0] != look_moves.GONE


def _muzzle(pc: Any, view: str, pose: look_moves.Pose, since_s: float) -> tuple:
    """Called by tick, which has noted the eye in this frame."""
    if view == look_view.THIRD:
        return look_muzzle.on_piece(_gun.pieces[look_gun.BODY_PISTOL],
                                    look_assets.PIECES[look_gun.BODY_PISTOL]["muzzle_cm"])
    seen = look_eye.camera(pc, noted=True)
    if _arms_pistol(pose, since_s):
        return look_muzzle.from_arms(pc, look_muzzle.on_piece(_gun.pieces[look_gun.ARMS_PISTOL],
                                                              look_assets.PIECES[look_gun.ARMS_PISTOL]["muzzle_cm"]),
                                     seen)
    out = pose.left[0] == look_moves.GONE
    return look_muzzle.waiting(pc, look_assets.MUZZLE_OUT_CM if out else look_assets.MUZZLE_IN_CM, seen)


def _rope_shows(pc: Any, rope: look_timing.Shot, now_ns: int, noted: bool = False) -> bool:
    """Whether the rope from the muzzle's place once the arm is out to its hook would cross the screen. `noted`: called
    by tick, which has noted the eye in this frame."""
    seen = look_eye.camera(pc, noted)
    out = look_muzzle.waiting(pc, look_assets.MUZZLE_OUT_CM, seen)
    found = look_timing.where(rope, out, now_ns)
    if found is None:
        return False
    eye, axes = seen
    world, _arms = look_muzzle.fields(pc)
    across = math.tan(math.radians(world) / 2)
    return look_sight.shows(eye, axes, across, across * SCREEN, [out, found[0]])


def reset() -> None:
    """Every gesture stopped and every piece removed at once; each tried even when another fails, the first failure
    raised after."""
    global _shot, _gun, _owner
    gun, alive = _gun, _owner is not None and _owner() is not None
    _shot, _gun, _owner = None, None, None
    look_eye.forget()
    look_outfit.forget()
    failed = None
    for step in (look_gestures.stop, look_shots.reset, (gun.destroy if gun is not None and alive else None)):
        if step is None:
            continue
        try:
            step()
        except Exception as error:
            failed = failed or error
    if failed is not None:
        raise failed
