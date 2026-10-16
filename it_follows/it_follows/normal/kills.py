"""The Hardcore's kills (decision 89): the enemies the census reads dead that the player killed (killers.py), met by the
normal mode or not: an enemy killed before a census read it alive counts too (trial 31, BL4 Arena's enemies killed
within 5 s of their birth). Each body counts once; one read alive again is the game's next enemy, its body reused,
whose death counts; the dead the first census reads were there before and count not.
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

    def count(self, sighting: Any, met: dict | set) -> tuple[int, dict[str, int], list[dict]]:
        """The bodies read dead not counted yet: how many the player killed, what KillerActor/LastHitBy said of them,
        counted by what they said, and, for those another character killed, who, and whether each was met (met: the
        names the mode holds; one not met is no one it gave the one team, born since the last census or no enemy)."""
        for name in sighting.alive:
            self.counted.pop(name, None)
        others = dict(sighting.killed_by_other)
        kills, said, fights = 0, {}, []
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
            kills += killers.by_player(by)
            if name in others and len(fights) < FIGHTS_MOST:
                fights.append({"dead": name, "dead_met": name in met, "by": others[name],
                               "by_met": others[name] in met})
        self.first = False
        return kills, said, fights
