"""Puts the player's weapon away: the game is asked to equip nothing, and lowers the weapon with its own animation.

How, verified in game on 2026-09-25 (cosmetics/heirloom, probe apex_weapon_calls.py, log
releves/2026-09-24-animations-sans-arme/unrealsdk_essai_rangement.log): the character's ServerSetCurrentWeapon with no
weapon and slot -1, as Holster Your Weapon (Pale66) sends it, makes the game lower the weapon for 0.46 to 0.6 s, then
switch to "no weapon". The call is the game's own. The weapon in hand is read at ActiveWeapons.Slots[0].Weapon, also
verified in game by the heirloom (apex_holster_follow.py).

Drawing the weapon back stays the game's: its weapon keys, the wheel and Triangle already do it (Kevin, 2026-09-25:
"la seule chose dont on a besoin c'est une touche pour ranger l'arme").
"""

from typing import Any, Callable

PUT_AWAY = "weapon put away"
NO_WEAPON = "no weapon in hand"
NOT_ON_FOOT = "not on foot"
GOING_DOWN = "weapon already going down"
# The weapon goes down for up to 0.6 s before the hand is empty: asked again meanwhile, the game is not asked twice.
# No longer: the same weapon drawn back right after is a new request to honour (audit, 2026-09-25).
GOING_DOWN_S = 0.6
NO_SLOT = -1


class Holster:
    def __init__(self, clock: Callable[[], float]) -> None:
        self._clock = clock
        # The weapon last asked away, by name, and when: no game object is held.
        self._asked: tuple[str, float] | None = None

    def put_away(self, pc: Any) -> str:
        """Asks the game to put away the weapon in hand; returns what was done, for the log."""
        character = getattr(pc, "OakCharacter", None) if pc is not None else None
        pawn = getattr(pc, "Pawn", None) if pc is not None else None
        # In a vehicle the controller drives the vehicle, not the character: there is no weapon in hand to put away.
        if character is None or pawn is None or pawn != character:
            return NOT_ON_FOOT
        weapon = character.ActiveWeapons.Slots[0].Weapon
        if weapon is None:
            return NO_WEAPON
        if self.going_down(weapon):
            return GOING_DOWN
        character.ServerSetCurrentWeapon(None, 0, 0, 0, NO_SLOT)
        self._asked = (str(weapon.Name), self._clock())
        return PUT_AWAY

    def going_down(self, weapon: Any) -> bool:
        """The weapon still in hand was asked away a moment ago, and the game is lowering it."""
        return (self._asked is not None and self._asked[0] == str(weapon.Name)
                and self._clock() - self._asked[1] < GOING_DOWN_S)
