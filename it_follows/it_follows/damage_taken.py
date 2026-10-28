"""BUFF and BUFF+ on the hunter (decision 79): he takes 10 % or 20 % more damage while a run goes on.

The lever is his character's DamageState.DamageTakenMultiplier, a value and its base: the game's attribute
damage_taken_multiplier reads that field on any character (source unique: the game's decoded attributes), and Vehicle
Driving writes it on the vehicle, where it acts (verified in game; the game applied 4.2 of the 5 asked,
docs/investigations/vehicle_driving/degats/). Not verified on the hunter.

Written as the game's own times the factor, never as the value in the game times it, so nothing is multiplied twice.
Read back once a sample: a base the game wrote anew is taken as its own and raised again; a value it computed again
from the raised base is left to it. The game's own is written back at the stop. Normal touches nothing.

The normal mode's Hardcore changes the factor during a game (decision 89): change writes the new one from the game's
own base, or from a base the game wrote anew, and the value without the old raise.
"""

from typing import Any, Callable

# A float read back equals the one written within this; a factor this near 1 is Normal.
SAME = 1e-3


def _multiplier(player: Any) -> Any:
    return player.DamageState.DamageTakenMultiplier


class DamageTaken:
    """announce(call, log, **fields) notes a write before it happens."""

    def __init__(self, announce: Callable[..., None], factor: float) -> None:
        self.announce, self.factor = announce, factor
        # The game's own base and the base written, while the mod holds the multiplier.
        self.game_base: float | None = None
        self.written_base = self.written_value = 0.0

    def start(self, player: Any) -> dict:
        """Raises the hunter's multiplier; what it was and what it is, or why not. Normal says nothing."""
        if abs(self.factor - 1.0) <= SAME:
            return {}
        try:
            pair = _multiplier(player)
            base, value = float(pair.BaseValue), float(pair.Value)
            self._raise(pair, base, value, log=True)
        except Exception as error:
            self.game_base = None
            return {"failed": type(error).__name__}
        return {"base": [round(base, 3), round(self.written_base, 3)],
                "value": [round(value, 3), round(self.written_value, 3)]}

    def _raise(self, pair: Any, base: float, value: float, log: bool) -> None:
        self.announce("DamageTakenMultiplier", log=log, value=round(value * self.factor, 3))
        pair.BaseValue = base * self.factor
        pair.Value = value * self.factor
        self.game_base, self.written_base, self.written_value = base, base * self.factor, value * self.factor

    def change(self, player: Any, factor: float) -> dict:
        """The multiplier raised by factor instead: what it was and what it is, or why not."""
        old, self.factor = self.factor, factor
        if self.game_base is None:
            return self.start(player)
        try:
            pair = _multiplier(player)
            base, value = float(pair.BaseValue), float(pair.Value)
            if abs(base - self.written_base) <= SAME:
                base, value = self.game_base, value / old
            self._raise(pair, base, value, log=True)
        except Exception as error:
            return {"failed": type(error).__name__}
        return {"base": [round(base, 3), round(self.written_base, 3)],
                "value": [round(value, 3), round(self.written_value, 3)]}

    def keep(self, player: Any) -> dict | None:
        """Once a sample: None while the multiplier holds; else what the game did, and the raise written again
        when it wrote a base of its own."""
        if self.game_base is None:
            return None
        try:
            pair = _multiplier(player)
            base, value = float(pair.BaseValue), float(pair.Value)
            if abs(base - self.written_base) > SAME:
                self._raise(pair, base, value, log=False)
                return {"taken": "again", "game_base": round(base, 3)}
            if abs(value - self.written_value) > SAME:
                self.written_value = value
                return {"taken": "computed", "value": round(value, 3)}
        except Exception as error:
            return {"taken": f"failed:{type(error).__name__}"}
        return None

    def put_back(self, player: Any) -> str:
        """The game's own base written back, and the value without the raise; the multiplier is let go either way."""
        game_base, self.game_base = self.game_base, None
        if game_base is None:
            return "not_raised"
        if player is None:
            return "unavailable"
        self.announce("DamageTakenMultiplier", back=True)
        try:
            pair = _multiplier(player)
            if abs(float(pair.BaseValue) - self.written_base) > SAME:
                return "left_to_game"
            pair.BaseValue = game_base
            pair.Value = float(pair.Value) / self.factor
        except Exception as error:
            return f"failed:{type(error).__name__}"
        return "restored"
