"""Kevin's rule against a run where nobody comes (14 October 2026, after trial 18, where a run started with a single
enemy around and its horde ran dry at 3 minutes): « des le lancement du run, le mod compte jusqu'a 3, si a 3 seconde on
a pas au moins 2 ennemi qui on ciblé et qui suivent le joueur, on fait spawn des ennemies nous memes ». Kept all along
the run, not only at its start (« faut detecter les moment ou on ne voit aucun ennemies apparaitre et ciblé le
joueur »): once fewer than FEW enemies have followed the hunter for WAIT_S, GROUP enemies of the place are asked, born
as the killed come back (wave.py), and no other group before SETTLE_S.

The enemies of the place: the kinds met within zone_kinds.PLACE_M of the hunter during the run, else those met last
anywhere in it. With none met, nobody can be asked: whether a place's kinds can be read from the game's camps before
any of their enemies is born is trial 19's question (docs/RUN/sondes/run_camp_kinds.py).
"""

import math
from typing import Any, Callable

FEW = 2
WAIT_S = 3.0
# Kevin, 15 October 2026: « 20 ca commence a faire beaucoup pour seulement trois secondes de run ».
GROUP = 15
# A group is born within some 6 s of being asked (trial 8b) and joins at the next census, 5 s later.
SETTLE_S = 15.0


class Guard:
    """note(event, **fields) writes a line to the SDK log (report.note)."""

    def __init__(self, note: Callable[..., None]) -> None:
        self.note = note
        self.short_since: float | None = None
        self.asked_at = -math.inf
        self.groups = 0

    def _due(self, following: int, now: float) -> bool:
        if following >= FEW:
            self.short_since = None
            return False
        if self.short_since is None:
            self.short_since = now
        return now - self.short_since >= WAIT_S and now - self.asked_at >= SETTLE_S

    def group(self, following: int, now: float, kinds: Any, here: tuple | None,
              knows: Callable[[str], bool]) -> list[tuple[str, str]]:
        """The group to ask, as (name, kind), once fewer than FEW have followed the hunter for WAIT_S; empty
        otherwise. kinds is the run's zone_kinds.ZoneKinds; knows says which kinds It Follows' camps can make."""
        if not self._due(following, now):
            return []
        self.asked_at, self.short_since = now, None
        self.groups += 1
        place = kinds.around(here, knows)
        chosen = place or kinds.latest(knows)
        if not chosen:
            self.note("guard", group=self.groups, following=following, asked=0, why="no_kind")
            return []
        self.note("guard", group=self.groups, following=following, asked=GROUP, of="place" if place else "run",
                  kinds=sorted(set(chosen)))
        return [(f"guard_{self.groups}", chosen[index % len(chosen)]) for index in range(GROUP)]
