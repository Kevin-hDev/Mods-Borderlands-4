"""The rope on screen: the game's own grapple beam, put in the world between the hand and the anchor.

The effect is `NS_Grapple_Beam`, named by the game's own grapple settings (`grapplebeameffect` in
Nexus-Data-Grapple4.ncs, decoded on 2026-09-18).

Native components were observed unattached under OakWorldSettings on 2026-09-21.
Free spawning alone did not fix visibility. Trial 0.11.0 tests local endpoints through rope_pose;
active/visible component flags do not prove that any particles were rendered.

Under what name and through which function the two ends are written is `rope_ends.py`.

Everything is guarded: the rope is what the player sees, not what carries him, and a beam that
cannot be drawn must never cost a pull.
"""

from typing import Any

import unrealsdk

from . import beam_cleanup, game, report, rope_ends, rope_lifetime, rope_light, rope_pose

LIBRARY = "NiagaraFunctionLibrary"
# Where the beam is put, likeliest first. The game puts its own free in the world, so that is
# tried first and the old way is kept only as a fallback.
SPAWNS = ("loose", "attached")
# Fields the game's own rope carries and a bare spawn does not. Read on 2026-09-21 by writing down
# all 173 fields of both ropes and comparing them: seven differed, five of them only identity.
COPIED = (("bVisibleInRayTracing", True),)

_component: Any = None
_spawned_as: str | None = None
# Why each way of putting the beam anywhere was refused, kept for the log rather than swallowed.
_spawn_refusals: dict[str, str] = {}
_end_name: str | None = None
_source_name: str | None = None
_broken = False


def reset() -> None:
    global _end_name, _source_name, _spawned_as, _broken
    stop()
    _end_name = _source_name = _spawned_as = None
    _spawn_refusals.clear()
    _broken = False
    rope_ends.reset()


def _library() -> Any:
    return unrealsdk.find_class(LIBRARY).ClassDefaultObject


def start(character: Any, anchor: tuple[float, float, float]) -> None:
    """Puts the rope in the world. Silent and harmless when the game will not have it."""
    global _component
    if _broken or _component is not None:
        return
    if not beam_cleanup.retry():
        return
    try:
        system = game.beam_effect()
        if system is None:
            report.error_once("beam:missing", "the grapple beam NS_Grapple_Beam was not found")
            return
        rope_ends.read_names(system)
        hand = game.hand_spot(character)
        _component = _spawn(system, character, hand, rope_pose.facing(hand, anchor))
        if _component is None:
            refused = "; ".join(f"{how}: {why}" for how, why in _spawn_refusals.items())
            report.error_once("beam:spawn", f"the grapple beam could not be put anywhere. Refusals: {refused}")
            return
        _copy_game(_component)
        rope_lifetime.configure(_component, system)
        follow(hand, anchor)
        if _component is not None:
            rope_light.switch_on(_component)
    except Exception as exc:
        _fail(exc)


def _spawn(system: Any, character: Any, hand: tuple[float, float, float],
           facing: tuple[float, float]) -> Any:
    """Puts the beam in the game the way the game itself does, and keeps the way that answered."""
    global _spawned_as
    for how in (_spawned_as,) if _spawned_as is not None else SPAWNS:
        try:
            component = (_loose(system, character, hand, facing) if how == "loose"
                         else _attached(system, character))
        except Exception as exc:
            _spawn_refusals.setdefault(how, repr(exc))
            continue
        if component is None:
            _spawn_refusals.setdefault(how, "the game handed back nothing")
            continue
        _spawned_as = how
        report.note(f"grapple beam spawned {how}")
        return component
    return None


def _copy_game(component: Any) -> None:
    """The handful of fields the game's rope carries that a bare spawn leaves behind."""
    for name, value in COPIED:
        try:
            setattr(component, name, value)
        except Exception as exc:
            report.note(f"the grapple beam would not take {name}: {exc!r}")


def _loose(system: Any, character: Any, hand: tuple[float, float, float],
           facing: tuple[float, float]) -> Any:
    """Free in the world, as the game does it.

    It starts facing the anchor. Rotation alone failed in 0.9.0; the local endpoint trial also
    follows the moving hand and feeds the length rather than the anchor's world coordinates.

    The shot owns the component until stop(). Niagara must not auto-destroy it when the emitters
    complete while a long hook is still flying or pulling; beam_cleanup is the single authority
    that deactivates and removes it.
    """
    return _library().SpawnSystemAtLocation(
        character, system, rope_ends.vector(hand),
        unrealsdk.make_struct("Rotator", Pitch=facing[0], Yaw=facing[1], Roll=0.0),
        unrealsdk.make_struct("Vector", X=1.0, Y=1.0, Z=1.0),
        False, False, 0, True,
    )


def _attached(system: Any, character: Any) -> Any:
    """On the player, as the mod did until 0.7.0. Kept as the fallback, never as the first choice."""
    return _library().SpawnSystemAttached(
        SystemTemplate=system, AttachToComponent=character.Mesh, AttachPointName="None",
        Location=unrealsdk.make_struct("Vector", X=0.0, Y=0.0, Z=0.0),
        Rotation=unrealsdk.make_struct("Rotator", Pitch=0.0, Yaw=0.0, Roll=0.0),
        LocationType=0, bAutoDestroy=False, bAutoActivate=False, PoolingMethod=0,
        bPreCullCheck=True,
    )


def follow(hand: tuple[float, float, float], anchor: tuple[float, float, float]) -> None:
    """Updates the component's world pose and supplies its two ends in local coordinates."""
    global _end_name, _source_name
    if _broken or _component is None:
        return
    try:
        target = rope_pose.follow(_component, hand, anchor)
        if _end_name is not None:
            rope_ends.write(_component, _library(), _end_name, target)
            if _source_name is not None:
                rope_ends.write(_component, _library(), _source_name, rope_pose.ORIGIN)
            return
        _end_name = rope_ends.find(_component, _library(), rope_ends.TARGET_WORDS, target, "far end")
        if _end_name is None:
            report.error_once("beam:end",
                              f"nothing sets the grapple beam far end. Refusals: {rope_ends.refusals()}")
            rope_ends.tell_writers(_component, _library())
            return
        _source_name = rope_ends.find(_component, _library(), rope_ends.SOURCE_WORDS,
                                     rope_pose.ORIGIN, "near end")
    except Exception as exc:
        _fail(exc)


def stop() -> None:
    global _component
    if _component is None:
        beam_cleanup.retry()
        return
    held, _component = _component, None
    beam_cleanup.release(held)


def _fail(exc: Exception) -> None:
    global _broken
    _broken = True
    report.error_once("beam", f"the grapple beam was switched off after an error: {exc!r}")
    stop()
