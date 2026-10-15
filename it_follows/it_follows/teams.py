"""It Follows' one team: every enemy of the horde, of every kind, is put in one team so that they do not fight each
other on the way to the hunter, and each is given its own team back when let go (decision 32).

Why: Kevin, 2026-10-12: « les espèces qui se battent entre elles, ce problème-là on sait déjà comment le régler ! ».
BL4 Arena hands each enemy of an arena the team of its first enemy (mods/perso/bl4_arena/source/bl4_arena/allies.py):
GbxTeamFunctionLibrary.SetTeam with the handle the game returned by GetTeam, never one built in Python, which the game
would not resolve. The AI follows at once: the families stop fighting each other and all aim at the player
(docs/spawn-boss/enquetes/2026-10-11-equipes-des-ennemis.md, vérifié en jeu, five arenas without a refusal). On the
world's own enemies, their own team given back at the end, it was verified once only (trial 6p,
docs/RUN/enquetes/2026-10-12-arret-au-loin.md): each call is announced first.
The team shared is the one most enemies of the horde already have, the nearest the hunter first among equals: the
fewest changes. A refusal is said and that enemy keeps its team, as in BL4 Arena; the others are still handed theirs.

An enemy the game took away alive (the horde's parked, the normal mode's lost from sight) is called on no more, but
its own team is set aside with the team it was handed: should it come again still holding that one, its own is the one
set aside, given back when let go, whichever team is shared then. Without it, read in the shared team, it was kept as
one of the team's own and stayed in it after the stop (audit of 15 October 2026). The teams set aside outlive a run and
a game, as toughness.py's bodies: one may come again after STOP and START, or the hunter's death (review of 15 October
2026). A killed one's is not set aside: its body may come again as another enemy.
"""

import re
from typing import Any, Callable

import unrealsdk

LIBRARY = "GbxTeamFunctionLibrary"
# The own teams set aside, the oldest forgotten first: as many as toughness.LEFT_MOST bodies.
ASIDE_MOST = 1000
# By name: (its own team, the team it was handed).
_aside: dict[str, tuple[Any, Any]] = {}


def label(team: Any) -> str:
    """The team's name, Team_Bandit for FGameDataHandle(15, 'Team_Bandit', None) as the SDK shows it."""
    text = str(team)
    found = re.search(r"'(\w+)'", text)
    return found.group(1) if found else text[:60]


class Teams:
    """announce(call, **fields) notes a call before it happens. Keeps, for each enemy handed another team, the handle
    of its own, to give it back."""

    def __init__(self, announce: Callable[..., None]) -> None:
        self.announce = announce
        self.own: dict[str, Any] = {}
        # The library's default object, through a weak pointer as every game object It Follows keeps.
        self.library: Any = None
        self.shared: Any = None

    def unite(self, chasers: list) -> dict:
        """Reads the team of each enemy drawn (chaser.Chaser, nearest the hunter first), then hands the shared team to
        those of another; the team shared and, for each enemy, its own team and what was done."""
        library, broken = self._library()
        if library is None:
            return {"team": None, "error": broken}
        read = self._read(library, chasers)
        known = [str(team) for _, team, _ in read if team is not None]
        if not known:
            return {"team": None, "enemies": [{"on": chaser.name, "set": said} for chaser, _, said in read]}
        shared_text = max(known, key=known.count)
        self.shared = next(team for _, team, _ in read if team is not None and str(team) == shared_text)
        return {"team": label(self.shared), "enemies": [self._hand(library, chaser, team, said, self.shared)
                                                        for chaser, team, said in read]}

    def join(self, chasers: list) -> dict:
        """Hands the team shared at unite to enemies drawn later (trial 6s); unite itself while none is shared yet."""
        if self.shared is None:
            return self.unite(chasers)
        library, broken = self._library()
        if library is None:
            return {"team": None, "error": broken}
        return {"team": label(self.shared), "enemies": [self._hand(library, chaser, team, said, self.shared)
                                                        for chaser, team, said in self._read(library, chasers)]}

    def _read(self, library: Any, chasers: list) -> list[tuple[Any, Any, str | None]]:
        """Each enemy's own team, read, the call announced first; or why it could not be."""
        read: list[tuple[Any, Any, str | None]] = []
        for chaser in chasers:
            mover = chaser.actor()
            if mover is None:
                read.append((chaser, None, "gone"))
                continue
            self.announce("GetTeam", on=chaser.name)
            try:
                read.append((chaser, library.GetTeam(mover), None))
            except Exception as error:
                read.append((chaser, None, f"call_failed:{type(error).__name__}"))
        return read

    def give_back(self, name: str, mover: Any, body_reused: bool, away: bool = False) -> str:
        """Its own team back to an enemy let go, but nothing called on a body the game may reuse; one taken away alive
        has its own team set aside; what was done. The enemy is forgotten either way."""
        team = self.own.pop(name, None)
        if team is None:
            return "not_needed"
        if away:
            _aside.pop(name, None)
            _aside[name] = (team, self.shared)
            while len(_aside) > ASIDE_MOST:
                del _aside[next(iter(_aside))]
            return "set_aside"
        if body_reused or mover is None:
            return "not_called"
        library, broken = self._library()
        if library is None:
            return broken
        self.announce("SetTeam", on=name, back=True)
        try:
            library.SetTeam(mover, team)
        except Exception as error:
            return f"call_failed:{type(error).__name__}"
        return "restored"

    def _hand(self, library: Any, chaser: Any, held: Any, said: str | None, shared: Any) -> dict:
        """held: the team the enemy holds, its own unless it was set aside still holding the team it was handed. Its
        own kept to give back whenever the team it holds after this is another."""
        if held is None:
            return {"on": chaser.name, "own": None, "set": said}
        aside = _aside.pop(chaser.name, None)
        own = aside[0] if aside is not None and str(held) == str(aside[1]) else held
        if str(held) == str(shared):
            outcome = "kept" if str(own) == str(held) else "taken_back"
        else:
            outcome = self._set(library, chaser, shared)
            held = shared if outcome == "handed" else held
        if str(own) != str(held):
            self.own[chaser.name] = own
        return {"on": chaser.name, "own": label(own), "set": outcome}

    def _set(self, library: Any, chaser: Any, shared: Any) -> str:
        mover = chaser.actor()
        if mover is None:
            return "gone"
        self.announce("SetTeam", on=chaser.name)
        try:
            library.SetTeam(mover, shared)
        except Exception as error:
            return f"call_failed:{type(error).__name__}"
        return "handed"

    def _library(self) -> tuple[Any, str | None]:
        library = self.library() if self.library is not None else None
        if library is None:
            try:
                library = unrealsdk.find_class(LIBRARY).ClassDefaultObject
                self.library = unrealsdk.unreal.WeakPointer(library)
            except Exception as error:
                return None, f"no_library:{type(error).__name__}"
        return library, None
