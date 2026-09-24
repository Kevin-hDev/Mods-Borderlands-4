"""Own BaseFOV and restore only a value this runtime still owns."""

from math import isfinite
from typing import Any, Callable

from .constants import FOV_MAX, FOV_MIN, GAME_MENU_MAX_FOV


class FovEngine:
    def __init__(self, weak_ref: Callable, address_of: Callable) -> None:
        self._weak_ref = weak_ref
        self._address_of = address_of
        self._owner_name: str | None = None
        self._owner_ref: Any = None
        self._owner_id = 0
        self._native: float | None = None
        self._written: float | None = None
        self._settings: Any = None

    def _clear(self) -> None:
        self._owner_name = None
        self._owner_ref = None
        self._owner_id = 0
        self._native = None
        self._written = None
        self._settings = None

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
    def _restore_saved(player: Any, settings: Any) -> None:
        native, applied = settings.saved_fov_pair()
        if (native is None or applied is None or applied <= GAME_MENU_MAX_FOV
                or native == applied or float(player.BaseFOV) != applied):
            return
        player.BaseFOV = native
        if float(player.BaseFOV) != native:
            raise ValueError("saved FOV restoration failed")
        settings.note(f"FOV given back to the game's {native:g} after reload")

    def apply(self, owner: str, player: Any, settings: Any) -> None:
        if self._owner_name is not None and self._owner_name != owner:
            self._release()
        if not settings.fov_enabled():
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
        wanted = self._wanted(settings)
        saved_native, saved_applied = settings.saved_fov_pair()
        if current == wanted:
            if (self._owner_ref is None and saved_applied == wanted and wanted > GAME_MENU_MAX_FOV
                    and saved_native != wanted):
                self._claim(owner, player, settings, saved_native, wanted)
                settings.note(f"FOV restore value recovered: {saved_native:g}")
            return
        same_value = self._owner_ref is not None and current == self._written
        if same_value:
            native = self._native
        elif (saved_applied is not None and saved_applied > GAME_MENU_MAX_FOV
              and current == saved_applied and saved_native is not None):
            native = saved_native
        else:
            native = current
        if native is None:
            raise ValueError("native FOV missing")
        message = (f"FOV set to {wanted:g}" if same_value else
                   f"FOV set to {wanted:g}, game's {native:g}" if self._owner_ref is None else
                   f"FOV found at the game's {native:g}, set to {wanted:g} again")
        settings.remember_fov_pair(native, wanted)
        self._claim(owner, player, settings, native, wanted)
        player.BaseFOV = wanted
        if float(player.BaseFOV) != wanted:
            raise ValueError("FOV assignment failed")
        settings.note(message)

    def _claim(self, owner: str, player: Any, settings: Any, native: float, written: float) -> None:
        self._owner_name = owner
        self._owner_ref = self._weak_ref(player)
        self._owner_id = int(self._address_of(player))
        self._native = native
        self._written = written
        self._settings = settings

    def stop(self) -> None:
        self._release()
