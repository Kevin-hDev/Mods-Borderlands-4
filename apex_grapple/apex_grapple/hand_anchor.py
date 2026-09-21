"""The measured grapple socket is the single authority for the rope's hand position."""

import math

from unrealsdk.unreal import WeakPointer

from . import arms, report

# Confirmed on the current arms mesh by the 0.11.3 game session, 2026-09-21.
SOCKET = "FX_L_Hand_Grapple"
MAX_COORDINATE = 1e9
_character = None
_mesh = None
_failed = False


def reset():
    global _character, _mesh, _failed
    _character = _mesh = None
    _failed = False


def mesh_for(character):
    instance = arms.find(character)
    mesh = instance.Outer if instance is not None else None
    if mesh is None or not mesh.DoesSocketExist(SOCKET):
        raise ValueError("named grapple hand socket unavailable")
    return mesh


def read(mesh):
    if mesh is None:
        raise ValueError("named grapple hand socket mesh unavailable")
    point = mesh.GetSocketLocation(SOCKET)
    xyz = tuple(float(getattr(point, axis)) for axis in ("X", "Y", "Z"))
    if not all(math.isfinite(value) and abs(value) <= MAX_COORDINATE for value in xyz):
        raise ValueError("invalid socket coordinates")
    return xyz


def position(character):
    """One weak mesh per shot; failure uses the caller's fallback until the next shot."""
    global _character, _mesh, _failed
    try:
        if _character is None or _character() != character:
            reset()
            _character = WeakPointer(character)
            # The arms module caches its instance; a new pawn must never inherit the old mesh.
            arms.forget()
        if _failed:
            return None
        if _mesh is None:
            _mesh = WeakPointer(mesh_for(character))
            report.note(f"rope hand origin | following {SOCKET}")
        return read(_mesh())
    except Exception as exc:
        _failed = True
        report.error_once("hand:anchor", f"rope hand socket unavailable; using estimated origin: {exc!r}")
        return None
