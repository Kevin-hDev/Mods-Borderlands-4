"""Where the left hand is: the spot the beam leaves from.

The first-person arms are the mesh named FirstPersonArms that belongs to the character (Apex Movement, session F,
2026-09-17). Its left hand carries the socket FX_L_Hand_Weave in the middle of the palm (read in the game's
skeleton and used in game since 2026-10-01) and FX_L_Hand_Grapple on the back of the wrist (Apex Grapple,
2026-09-21, verified in game): the beam leaves the palm, or the wrist on arms without the palm's socket. Its own
copy of the arms' lookup rather than those mods': a mod must not need another one installed. The arms being drawn
at a field of view of their own, the spot handed back is the one the world shows there (arms_view.py).

In third person the arms are not shown: the beam leaves the left hand of the body seen from outside, the character's
own mesh, at its socket FX_L_Hand (read on 2026-10-01 in the skeletons of three player characters, seen in game
that day on the Siren), or at the hand's bone on a body without that socket.
"""

import math
from itertools import islice
from typing import Any

import unrealsdk
from unrealsdk import unreal

from . import aim, arms_view, report, view

ANIM_INSTANCE = "/Script/Engine.AnimInstance"
ARMS_MESH = "FirstPersonArms"
SOCKETS = ("FX_L_Hand_Weave", "FX_L_Hand_Grapple")
BODY_SOCKETS = ("FX_L_Hand", "L_Hand")
# Bounded: a level held 202 to 322 animation instances when Apex Movement measured it.
MAX_ANIM_INSTANCES = 20_000
MAX_COORDINATE = 1e9
# When the arms cannot be found: below and to the left of the camera, a forearm ahead of it.
FALLBACK_AHEAD, FALLBACK_LEFT, FALLBACK_DOWN = 40.0, 25.0, 20.0

_mesh: Any = None
# Looking for the arms walks the game's animation list: after a failure it waits for the next shot.
_failed = False


def forget() -> None:
    """Called at each new shot: the arms are looked for again, and so is a hand that could not be read."""
    global _mesh, _failed
    _mesh = None
    _failed = False


def arms(character: Any) -> Any:
    """The arms' mesh, looked for once per shot (attack.py forgets it at each new one) and kept weakly."""
    global _mesh
    held = _mesh() if _mesh is not None else None
    if held is not None and held.Outer == character:
        return held
    _mesh = None
    for instance in islice(unrealsdk.find_all(ANIM_INSTANCE, exact=False), MAX_ANIM_INSTANCES):
        mesh = instance.Outer
        if (mesh is not None and str(mesh.Name) == ARMS_MESH and mesh.Outer == character
                and mesh.GetAnimInstance() == instance):
            _mesh = unreal.WeakPointer(mesh)
            return mesh
    return None


def body(character: Any) -> Any:
    """The body seen from outside: the character's own mesh (Apex Movement reads its animation there)."""
    return character.Mesh


def beside_camera(pc: Any) -> tuple[float, float, float]:
    """A spot low and left of the camera, for when the hand itself cannot be read."""
    spot, turn = aim.eye(pc)
    yaw = math.radians(float(turn.Yaw))
    ahead, left = (math.cos(yaw), math.sin(yaw)), (math.sin(yaw), -math.cos(yaw))
    return (spot[0] + ahead[0] * FALLBACK_AHEAD + left[0] * FALLBACK_LEFT,
            spot[1] + ahead[1] * FALLBACK_AHEAD + left[1] * FALLBACK_LEFT,
            spot[2] - FALLBACK_DOWN)


def spot(pc: Any, character: Any) -> tuple[float, float, float]:
    """The left hand in the world; a spot beside the camera, said once, when the hand cannot be read."""
    global _failed
    if _failed:
        return beside_camera(pc)
    try:
        outside = view.third_person(pc, character)
        mesh, sockets = (body(character), BODY_SOCKETS) if outside else (arms(character), SOCKETS)
        socket = next((name for name in sockets if mesh is not None and mesh.DoesSocketExist(name)), None)
        if socket is None:
            raise ValueError(f"no left hand socket on the {'body' if outside else 'arms'}")
        point = mesh.GetSocketLocation(socket)
        found = (float(point.X), float(point.Y), float(point.Z))
        if not all(math.isfinite(value) and abs(value) <= MAX_COORDINATE for value in found):
            raise ValueError("invalid hand coordinates")
        # The body is drawn as the world is; the arms are not (arms_view.py).
        return found if outside else arms_view.shown(pc, found)
    except Exception as error:
        _failed = True
        report.error_once("hand", f"the left hand could not be read, the beam leaves from beside the camera: {error!r}")
        return beside_camera(pc)
