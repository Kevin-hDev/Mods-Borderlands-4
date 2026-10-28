"""The Hardcore's kills (decision 89): the enemies the census reads dead that the player killed (killers.py), met by the
normal mode or not: an enemy killed before a census read it alive counts too (trial 31, BL4 Arena's enemies killed
within 5 s of their birth). Each body counts once; one read alive again is the game's next enemy, its body reused,
whose death counts; the dead the first census reads were there before and count not.

The bodies another character killed are counted by that character's name too: in co-op the host's game sees a guest's
kills so, at the guest's character (trials 75 and 77: « by »: OakCharacter_…), and tells the guest its own
(coop_messages.py, decision 133).
"""

from typing import Any

from .. import killers

# The bodies counted, remembered so that each counts once, the oldest forgotten first: some minutes of fights.
COUNTED_MOST = 2000
# The enemies another character killed, written by census: trial 52 saw 10 within 30 s.
FIGHTS_MOST = 12


class Kills:
    def __init__(self) -> None:
        self.counted: dict[str, None] = {}
        self.first = True
        # The player's kills the last count added, by name: where their bodies lay is measured (reserve_kills.py).
        self.fresh: list[str] = []

    def count(self, sighting: Any, met: dict | set) -> tuple[int, dict[str, int], list[dict], dict[str, int]]:
        """The bodies read dead not counted yet: how many the player killed, what KillerActor/LastHitBy said of them,
        counted by what they said, for those another character killed, who, and whether each was met (met: the
        names the mode holds; one not met is no one it gave the one team, born since the last census or no enemy),
        and how many each other character killed, by its name."""
        self.fresh = []
        for name in sighting.alive:
            self.counted.pop(name, None)
        others = dict(sighting.killed_by_other)
        kills, said, fights, by_others = 0, {}, [], {}
        for name, by in sighting.killed:
            if name in self.counted:
                continue
            self.counted[name] = None
            while len(self.counted) > COUNTED_MOST:
                del self.counted[next(iter(self.counted))]
            if self.first:
                continue
            key = "/".join(by)
            said[key] = said.get(key, 0) + 1
            mine = killers.by_player(by)
            kills += mine
            if mine:
                self.fresh.append(name)
            if name in others:
                by_others[others[name]] = by_others.get(others[name], 0) + 1
            if name in others and len(fights) < FIGHTS_MOST:
                fights.append({"dead": name, "dead_met": name in met, "by": others[name],
                               "by_met": others[name] in met})
        self.first = False
        return kills, said, fights, by_others
