"""What the player chose on the window's COMPANIONS page (decision 50, spec-compagnons.md): the team, MOST names at
most, the same one as often as wanted (Kevin, 20 October 2026: « s'il veut 8 loveless ou 4 loveless + 2 vex et 2
pangolin ca passe »), and for each companion its shield on or off and its speed bonus off, +20 % or +30 % (« Les
deux , tous les compagnons »); for a hunter, his own outfit or the player's colours (spec-compagnons.md, « Deux
boutons de tenue », only on the card of the hunter the player plays: companions/player_paint.py). Kept from one
launch to the next, as the starting point is, so that the player does not make the team again at each game
(plan-mod-compagnons.md, step 2): two hidden options, written through the window's settings transaction
(panel_model.Model.save). And the bars on the left of the screen shown or not (companions/bars.py), an option of the
same page. It Follows' own, never the companions' (decision 69: the companions' code serves two mods, and Companions
keeps its own choices); companion_levels.given turns a card into what a companion is given. The team's rules (MOST,
the names known, the last one taken away) are the companions' code's (companions/roster.py), for both mods.

Read tolerantly, so that a settings file edited by hand never keeps the team from starting: a name unknown is left
out, those past MOST too; a choice that is none reads as its default. What changes a value gives a new one, never the
option's own changed in place: the transaction compares the value before with the value after.
"""

from typing import Any, NamedTuple

from mods_base import BoolOption, HiddenOption

from .characters.companions import kinds, pace, roster

MOST = roster.MOST
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
bars = BoolOption("companion_bars", False, display_name="Health bars on screen",
                  description="Each companion's health at the bottom left of the screen, as a teammate's in co-op.")


def names(value: Any = None) -> list[str]:
    """The team's names, those the mod knows, MOST at most, in the order they were added."""
    return roster.names(team.value if value is None else value)


def count(name: str) -> int:
    return names().count(name)


def added(name: str) -> list[str] | None:
    """The team with one more of that name; None when it is full or the name unknown."""
    return roster.added(team.value, name)


def removed(name: str) -> list[str]:
    """The team with one fewer of that name, the last one added; as it is when there is none."""
    return roster.removed(team.value, name)


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
    """The choice of each companion of the team, as a team starts with them (session.start_team)."""
    return {name: choice(name) for name in names()}
