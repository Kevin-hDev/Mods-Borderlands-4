"""A run's counts: the enemies killed and the hunter's deaths (decision 49).

A kill is an enemy of the horde found dead (horde.py, every second), or a character the census saw alive and reads
dead at a later census (census.Sighting, every 5 s): an enemy killed before it joined the horde counts too. A name
counts once a life: the game gives a dead enemy's body to the next one (docs/spawn-boss/enquetes/
2026-10-05-plusieurs-ennemis.md), so a name seen alive again begins a new life. Not counted (non vérifié: how often):
an enemy born and killed between two censuses without ever joining the horde, or whose body is given to another
enemy before a census reads it dead.

A death of the hunter is each time he is read dead after a read that did not say dead, once a second (reads.dead on
his character; trial 9 read the value, false, and has not yet seen it true). A read that says nothing changes
nothing: an unreadable second between two dead ones never counts a second death.
"""

# Names remembered, alive or counted dead: the oldest are forgotten past this, as many as a run of an hour could see.
MAX_NAMES = 4000


class Stats:
    def __init__(self, hunter_dead: bool | None = None) -> None:
        self.kills = 0
        self.deaths = 0
        # Each name seen alive, and each counted dead in its present life, the oldest first.
        self._alive: dict[str, None] = {}
        self._counted: dict[str, None] = {}
        self._hunter_dead = hunter_dead

    @staticmethod
    def _keep(table: dict[str, None], name: str) -> None:
        table.pop(name, None)
        table[name] = None
        while len(table) > MAX_NAMES:
            del table[next(iter(table))]

    def seen_alive(self, names: frozenset[str] | set[str]) -> None:
        """Characters a census kept alive: a name counted dead before begins a new life."""
        for name in names:
            self._counted.pop(name, None)
            self._keep(self._alive, name)

    def seen_dead(self, names: frozenset[str] | set[str]) -> int:
        """Characters a census read dead: each seen alive before, and not counted in this life, is a kill. How many."""
        found = 0
        for name in names:
            if name in self._alive and name not in self._counted:
                self._alive.pop(name)
                self._keep(self._counted, name)
                found += 1
        self.kills += found
        return found

    def killed(self, name: str) -> bool:
        """An enemy of the horde found dead: a kill, unless its present life was counted already."""
        if name in self._counted:
            return False
        self._alive.pop(name, None)
        self._keep(self._counted, name)
        self.kills += 1
        return True

    def hunter(self, dead: bool | None) -> bool:
        """The hunter read this second: whether this is a new death."""
        if dead is None:
            return False
        died = dead and self._hunter_dead is not True
        self._hunter_dead = dead
        if died:
            self.deaths += 1
        return died
