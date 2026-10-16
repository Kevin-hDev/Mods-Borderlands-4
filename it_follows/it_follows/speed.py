"""It Follows' speed: every enemy of the horde runs faster by the bonus the player chose in the menu (decision 48:
Normal, +10 % to +50 %), and has the game's own bonus written back once let go.

Why (docs/RUN/enquetes/2026-10-10-horde-serree.md): trial 6h's cats ran 7 m/s, the hunter 9 to 15 with Apex Movement,
and they fell 35 to 65 m behind him on a straight run. The lever is the character's own speed bonus,
CharacterMovement.MaxGroundSpeedScale.Value: the game's maximum speed is its stance's speed times it
(borderlands_4/fonctions_borderlands_4.md, GetMaxSpeed). Trial 6i wrote 1.2 times the game's bonus on one cat in two:
those ran 20 % faster (8.4 m/s against 7.0), and the game kept the value all the trial (vérifié en jeu, three cats,
once). Only +20 % has been tried: each other choice is to be verified in game. The bonus is still read back once a
sample and written again should the game change it. Normal writes nothing: each enemy keeps the game's own bonus.
The bonus is written back as soon as the enemy is let go, even dead or taken back: the game may give its body to
another enemy, which must not keep it. A value written, not a call: the rule of nothing called on such a body is about
calls.
"""

from typing import Any, Callable

# A float read back equals the one written within this; a factor this near 1 is Normal.
SAME = 1e-3
# The bonuses written to the log on joining, for a trial to read, the first of each run; the rest are only written,
# 1 150 lines of trial 33's run (audit of 16 October 2026). Given back, each is written: the enemy may be dead.
DETAILED = 20


class SpeedBoost:
    """The enemies made faster by factor (1.0 for Normal to 1.5 for +50 %), each with the bonus the game had given it;
    announce(call, log, **fields) notes a write or a call before it happens."""

    def __init__(self, announce: Callable[..., None], factor: float) -> None:
        self.announce, self.factor = announce, factor
        self.base: dict[str, float] = {}
        self.detailed = 0

    def start(self, chasers: list) -> list[dict]:
        """Makes every enemy drawn faster; says for each its bonus before and after. Normal writes nothing and says
        nothing. The trials also read the game's maximum speed before and after, for their records only."""
        if abs(self.factor - 1.0) <= SAME:
            return []
        return [self._raise(chaser.name, chaser.actor()) for chaser in chasers]

    def _raise(self, name: str, mover: Any) -> dict:
        line: dict = {"on": name}
        try:
            scale = mover.CharacterMovement.MaxGroundSpeedScale
            base = float(scale.Value)
            self.announce("MaxGroundSpeedScale", log=self.detailed < DETAILED, on=name,
                          value=round(base * self.factor, 3))
            self.detailed += 1
            scale.Value = base * self.factor
            self.base[name] = base
            line["scale"] = [round(base, 3), round(float(scale.Value), 3)]
        except Exception as error:
            line["failed"] = type(error).__name__
        return line

    def keep(self, name: str, mover: Any) -> dict | None:
        """Once a sample: None when the bonus held or the enemy was never made faster; else it is written again, and
        the value the game had put is said."""
        base = self.base.get(name)
        if base is None:
            return None
        try:
            scale = mover.CharacterMovement.MaxGroundSpeedScale
            value = float(scale.Value)
            if abs(value - base * self.factor) <= SAME:
                return None
            self.announce("MaxGroundSpeedScale", log=False, on=name, again=True)
            scale.Value = base * self.factor
        except Exception as error:
            return {"boost": f"failed:{type(error).__name__}"}
        return {"boost": "again", "game_value": round(value, 3)}

    def put_back(self, name: str, mover: Any) -> str:
        """Writes back the bonus the game had given it, once; the enemy is forgotten either way."""
        base = self.base.pop(name, None)
        if base is None:
            return "not_boosted"
        if mover is None:
            return "unavailable"
        self.announce("MaxGroundSpeedScale", on=name, back=True)
        try:
            mover.CharacterMovement.MaxGroundSpeedScale.Value = base
        except Exception as error:
            return f"failed:{type(error).__name__}"
        return "restored"
