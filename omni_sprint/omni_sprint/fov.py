"""Own the FOV override and persist the native value before changing BaseFOV.

The game's menu uses this field too. A title-screen transition can save our
value into the game's profile, so a memory-only backup cannot restore it after
reload. The mod keeps the user's own value in its hidden settings instead.
"""

from typing import Any

from mods_base import get_pc
from unrealsdk.unreal import WeakPointer

from . import report, settings

MS = 1_000_000
CHECK_NS = 500 * MS

_next_ns = 0
_owner: Any = None
_owner_id = 0
_game_fov: float | None = None
_written: float | None = None


def reset() -> None:
    global _next_ns, _owner, _owner_id, _game_fov, _written
    _next_ns, _owner, _owner_id, _game_fov, _written = 0, None, 0, None, None


def _player() -> Any:
    pc = get_pc(possibly_loading=True)
    if pc is None or getattr(pc, "OakCharacter", None) is None:
        return None
    return pc.Player


def _release() -> None:
    """Restore only the live player and only if our last write still owns the value."""
    if _owner is None:
        return
    player = _owner()
    if player is not None and _game_fov is not None and float(player.BaseFOV) == _written:
        player.BaseFOV = _game_fov
        if float(player.BaseFOV) != _game_fov:
            raise ValueError("FOV restoration failed")
        report.note(f"FOV given back to the game's {_game_fov:g}")
    reset()


def _restore_saved(player: Any) -> None:
    """Recover a persisted override when the option was turned off on reload."""
    native, applied = settings.saved_fov_pair()
    if (native is None or applied <= settings.GAME_MENU_MAX_FOV
            or native == applied or float(player.BaseFOV) != applied):
        return
    player.BaseFOV = native
    if float(player.BaseFOV) != native:
        raise ValueError("saved FOV restoration failed")
    report.note(f"FOV given back to the game's {native:g} after reload")


def _hold(player: Any) -> None:
    global _owner, _owner_id, _game_fov, _written
    player_id = int(player._get_address())
    if _owner is not None and (_owner_id != player_id or _owner() is None):
        _release()
    current = float(player.BaseFOV)
    wanted = settings.fov_value()
    saved_native, saved_applied = settings.saved_fov_pair()
    if current == wanted:
        if (_owner is None and saved_applied == wanted and wanted > settings.GAME_MENU_MAX_FOV
                and saved_native != wanted):
            _owner, _owner_id = WeakPointer(player), player_id
            _game_fov, _written = saved_native, wanted
            report.note(f"FOV restore value recovered: {saved_native:g}")
        return
    same_value = _owner is not None and current == _written
    if same_value:
        native = _game_fov
    elif (saved_applied is not None and saved_applied > settings.GAME_MENU_MAX_FOV
          and current == saved_applied and saved_native is not None):
        native = saved_native
    else:
        native = current
    if native is None:
        raise ValueError("native FOV missing")
    message = (f"FOV set to {wanted:g}" if same_value else
               f"FOV set to {wanted:g}, game's {native:g}" if _owner is None else
               f"FOV found at the game's {native:g}, set to {wanted:g} again")
    # If saving fails, leave BaseFOV untouched: otherwise its original could be lost.
    settings.remember_fov_pair(native, wanted)
    _game_fov = native
    _owner, _owner_id, _written = WeakPointer(player), player_id, wanted
    player.BaseFOV = wanted
    if float(player.BaseFOV) != wanted:
        raise ValueError("FOV assignment failed")
    report.note(message)


def on_frame(now_ns: int) -> None:
    global _next_ns
    if now_ns < _next_ns:
        return
    _next_ns = now_ns + CHECK_NS
    if not settings.custom_fov_enabled():
        _release()
        player = _player()
        if player is not None:
            _restore_saved(player)
        return
    player = _player()
    if player is None:
        _release()
        return
    _hold(player)


def stop() -> None:
    """Gives the game its FOV back if the option replaced it."""
    _release()
