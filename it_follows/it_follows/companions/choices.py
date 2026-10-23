"""What the player chose on the window's COMPANIONS page (decision 50, spec-compagnons.md): the team, MOST names at
most, the same one as often as wanted (Kevin, 20 October 2026: « s'il veut 8 loveless ou 4 loveless + 2 vex et 2
pangolin ca passe »), and for each companion its shield on or off and its speed bonus off, +20 % or +30 % (« Les
deux , tous les compagnons »); for a hunter, his own outfit or the player's colours (spec-compagnons.md, « Deux
boutons de tenue », only on the card of the hunter the player plays: player_paint.py). Kept from one launch to the
next, as the starting point is, so that the player does not make the team again at each game
(plan-mod-compagnons.md, step 2): two hidden options, written through the window's settings transaction
(panel_model.Model.save).

Read tolerantly, so that a settings file edited by hand never keeps the team from starting: a name unknown is left
out, those past MOST too; a choice that is none reads as its default. What changes a value gives a new one, never the
option's own changed in place: the transaction compares the value before with the value after.
"""

from typing import Any, NamedTuple

from mods_base import HiddenOption

from . import kinds, pace

# Decision 21, Kevin, 20 October 2026: « le joueur doit pouvoir creer une equipe de 8 compagnons maximum ».
MOST = 8
# Off writes nothing (pace.py); +20 % is the trials' own since trial 138.
SPEEDS = {"Off": 1.0, "+20%": pace.FACTOR, "+30%": 1.3}
DEFAULT_SPEED = "+20%"
# The hunter's own outfit (trial 159) at first; the player's colours (trial 160) when chosen.
OUTFITS = ("own", "player")


class Choice(NamedTuple):
    shielded: bool = True
    speed: str = DEFAULT_SPEED
    outfit: str = OUTFITS[0]

    @property
    def factor(self) -> float:
        return SPEEDS[self.speed]


team = HiddenOption("companions_team", [])
chosen = HiddenOption("companions_choices", {})
ALL = [team, chosen]


def names(value: Any = None) -> list[str]:
    """The team's names, those the mod knows, MOST at most, in the order they were added."""
    held = team.value if value is None else value
    if not isinstance(held, list):
        return []
    return [name for name in held if isinstance(name, str) and name in kinds.BY_NAME][:MOST]


def count(name: str) -> int:
    return names().count(name)


def added(name: str) -> list[str] | None:
    """The team with one more of that name; None when it is full or the name unknown."""
    now = names()
    if name not in kinds.BY_NAME or len(now) >= MOST:
        return None
    return [*now, name]


def removed(name: str) -> list[str]:
    """The team with one fewer of that name, the last one added; as it is when there is none."""
    now = names()
    if name not in now:
        return now
    last = len(now) - 1 - now[::-1].index(name)
    return now[:last] + now[last + 1:]


def choice(name: str, value: Any = None) -> Choice:
    """The choice kept for that companion, its default for any part that is none."""
    held = chosen.value if value is None else value
    own = held.get(name) if isinstance(held, dict) else None
    if not isinstance(own, dict):
        return Choice()
    shielded, speed, outfit = own.get("shield"), own.get("speed"), own.get("outfit")
    # Strings only: a list or a dict edited in by hand cannot be looked up in SPEEDS, and would raise.
    return Choice(shielded if type(shielded) is bool else True,
                  speed if isinstance(speed, str) and speed in SPEEDS else DEFAULT_SPEED,
                  outfit if isinstance(outfit, str) and outfit in OUTFITS else OUTFITS[0])


def _written(one: Choice) -> dict:
    return {"shield": one.shielded, "speed": one.speed, "outfit": one.outfit}


def changed(name: str, shielded: bool | None = None, speed: str | None = None, outfit: str | None = None) -> dict:
    """Every choice kept, that companion's with its shield, its speed or its outfit changed; the others as they
    read."""
    held = chosen.value if isinstance(chosen.value, dict) else {}
    kept = {known: _written(choice(known, held)) for known in held if known in kinds.BY_NAME}
    old = choice(name, held)
    kept[name] = _written(Choice(old.shielded if shielded is None else shielded,
                                 old.speed if speed not in SPEEDS else speed,
                                 old.outfit if outfit not in OUTFITS else outfit))
    return kept


def team_choices() -> dict[str, Choice]:
    """The choice of each companion of the team, as a team starts with them (team.py)."""
    return {name: choice(name) for name in names()}
