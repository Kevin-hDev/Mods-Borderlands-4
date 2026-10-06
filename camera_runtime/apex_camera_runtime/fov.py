"""Own BaseFOV and restore only a value this runtime still owns.

The speed gain (speed_fov.py) rides on the player's FOV and is written every frame while it moves. The saved pair
only changes with the player's FOV or the gain's setting, never with a frame's gain, so sprinting writes no file.
"""

import struct
from math import isfinite
from typing import Any, Callable

from .constants import FOV_CEILING, FOV_MAX, FOV_MIN, GAME_MENU_MAX_FOV


def single(value: float) -> float:
    """BaseFOV is a 32-bit float: a written value is compared with what the game reads back."""
    return struct.unpack("f", struct.pack("f", value))[0]


class FovEngine:
    def __init__(self, weak_ref: Callable, address_of: Callable) -> None:
        self._weak_ref = weak_ref
        self._address_of = address_of
        self._clear()

    def _clear(self) -> None:
        self._owner_name: str | None = None
        self._owner_ref: Any = None
        self._owner_id = 0
        self._native: float | None = None
        self._written: float | None = None
        self._base: float | None = None
        self._settings: Any = None

    def _release(self) -> None:
        if self._owner_ref is None:
            return
        player = self._owner_ref()
        if player is not None and self._native is not None and float(player.BaseFOV) == self._written:
            player.BaseFOV = self._native
            if float(player.BaseFOV) != self._native:
                raise ValueError("FOV restoration failed")
            self._settings.note(f"FOV given back to the game's {self._native:g}")
        self._clear()

    @staticmethod
    def _wanted(settings: Any) -> float:
        try:
            value = float(settings.fov_value())
        except (TypeError, ValueError):
            value = 110.0
        return min(FOV_MAX, max(FOV_MIN, value)) if isfinite(value) else 110.0

    @staticmethod
    def _recovered(current: float, settings: Any) -> float | None:
        """The game's value saved before a write that the game kept: the menu never goes above its maximum, so a
        value between it and the saved top is ours."""
        native, top = settings.saved_fov_pair()
        if native is None or top is None or native > GAME_MENU_MAX_FOV or not GAME_MENU_MAX_FOV < current <= top:
            return None
        return native

    def _restore_saved(self, player: Any, settings: Any) -> None:
        native = self._recovered(float(player.BaseFOV), settings)
        if native is None:
            return
        player.BaseFOV = native
        if float(player.BaseFOV) != native:
            raise ValueError("saved FOV restoration failed")
        settings.note(f"FOV given back to the game's {native:g} after reload")

    def apply(self, owner: str, player: Any, settings: Any, gain: float = 0.0, ceiling: float = 0.0) -> None:
        if self._owner_name is not None and self._owner_name != owner:
            self._release()
        custom = settings.fov_enabled()
        if not custom and gain <= 0:
            self._release()
            if player is not None:
                self._restore_saved(player, settings)
            return
        if player is None:
            self._release()
            return
        player_id = int(self._address_of(player))
        if self._owner_ref is not None and (self._owner_id != player_id or self._owner_ref() is None):
            self._release()
        current = float(player.BaseFOV)
        owned = self._owner_ref is not None and current == self._written
        recovered = None if owned else self._recovered(current, settings)
        native = self._native if owned else current if recovered is None else recovered
        if native is None:
            raise ValueError("native FOV missing")
        base = self._wanted(settings) if custom else native
        wanted = single(min(FOV_CEILING, base + gain))
        if not owned and recovered is None and current == wanted:
            # Already the value wanted: nothing to own until a write is needed.
            return
        top = min(FOV_CEILING, base + max(gain, ceiling))
        if settings.saved_fov_pair() != (native, top):
            settings.remember_fov_pair(native, top)
        if not owned:
            message = (f"FOV restore value recovered: {native:g}" if recovered is not None else
                       f"FOV set to {wanted:g}, game's {native:g}" if self._owner_ref is None else
                       f"FOV found at the game's {native:g}, set to {wanted:g} again")
            self._claim(owner, player, settings, native)
            settings.note(message)
        elif base != self._base:
            settings.note(f"FOV set to {base:g}")
        self._written, self._base = wanted, base
        if current != wanted:
            player.BaseFOV = wanted
            if float(player.BaseFOV) != wanted:
                raise ValueError("FOV assignment failed")

    def _claim(self, owner: str, player: Any, settings: Any, native: float) -> None:
        self._owner_name = owner
        self._owner_ref = self._weak_ref(player)
        self._owner_id = int(self._address_of(player))
        self._native = native
        self._settings = settings

    def stop(self) -> None:
        self._release()
