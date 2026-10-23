"""The team a player makes: MOST names at most, the same one as often as wanted (decision 21, Kevin, 20 October 2026:
« s'il veut 8 loveless ou 4 loveless + 2 vex et 2 pangolin ca passe »), those the team knows (kinds.py), in the order
they were added. The rules only: each mod keeps its own team in its own settings (decision 69) and hands the value
here.

Read tolerantly, so that a settings file edited by hand never keeps a team from starting: a value that is no list is
no team, a name unknown is left out, those past MOST too. Each change gives a new list, never the one held changed in
place: the window's settings transaction compares the value before with the value after.
"""

from itertools import islice
from typing import Any

from . import kinds

MOST = kinds.MOST
# A list edited by hand is read this far at most, whatever it holds.
READ_MOST = 8 * MOST


def names(held: Any) -> list[str]:
    """The team's names, those known, MOST at most, in the order they were added; a list edited by hand is read
    only up to its MOST-th known name, and READ_MOST entries at most, however long it is (the window reads it at
    each paint)."""
    if not isinstance(held, list):
        return []
    return list(islice((name for name in islice(held, READ_MOST) if isinstance(name, str) and name in kinds.BY_NAME),
                       MOST))


def added(held: Any, name: str) -> list[str] | None:
    """The team with one more of that name; None when it is full or the name unknown."""
    now = names(held)
    if name not in kinds.BY_NAME or len(now) >= MOST:
        return None
    return [*now, name]


def removed(held: Any, name: str) -> list[str]:
    """The team with one fewer of that name, the last one added; as it is when there is none."""
    now = names(held)
    if name not in now:
        return now
    last = len(now) - 1 - now[::-1].index(name)
    return now[:last] + now[last + 1:]
