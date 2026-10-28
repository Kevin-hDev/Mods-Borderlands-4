"""The game's camps of the horde's enemies follow the hunter: each camp's spawner, the game's object that makes its
enemies and owns their zone, is moved onto him and follows him as the lent zone does, then is put back.

Why (decision 25, docs/RUN/enquetes/2026-10-10-camps-qui-suivent.md): in trials 6d to 6f the game took whole camps back
once the hunter had stayed far from them for about 25 s, even an enemy that was coming to him; the game's spawn settings
name a distance to the player for taking a spawner's enemies back (not verified). A spawner standing on the hunter is
never far from him. A camp's spawner is placed in the level, maybe with a static root: the game refuses to move such an
actor without an error, and SetMobility(2) let the arena move its dome (docs/spawn-boss/sondes/spawn_move.py). The
spawners are moved before the lent zone and put back before it: a zone part of a spawner would otherwise be carried away
from where it was put. A camp It Follows made is let go of once its enemy is lost (release, trial 8b), and a camp of the
game no enemy of the horde comes from any more is put back and forgotten (release_empty): over a run of an hour, the
camps followed would otherwise pile up, every one moved every FOLLOW_S. Taken from the trials'
docs/RUN/sondes/run_camp_follow.py.
"""

from typing import Any, Callable, Iterable

from .characters import reads
from .camp_map import CampMap
from .hunter_zone import FOLLOW_M, FOLLOW_S
from .zone_shift import Shift

# EComponentMobility: 0 static, 1 stationary, 2 movable.
MOVABLE = 2


class CampFollow:
    """The spawners of the camps noted in camp_map, by camp name; announce(call, log=True, **fields) notes a call before
    it happens."""

    def __init__(self, camp_map: CampMap, announce: Callable[..., None]) -> None:
        self.camp_map, self.announce = camp_map, announce
        self.shifts: dict[str, Shift] = {}
        self.followed_at: float | None = None
        # Every camp tried once, moved or not: a static root is not asked again at each recruit.
        self.tried: set[str] = set()
        # The camps whose last move took: their root, movable then, is not read again at each follow, two reads
        # for each of about 100 camps every FOLLOW_S with a full horde (audit of 16 October 2026).
        self.movable: set[str] = set()

    def place(self, here: tuple | None, now: float) -> dict:
        """Moves every camp's spawner onto the hunter; says, by camp: moved, not_moved, static, gone, unavailable or
        call_failed:<error>. A camp that cannot move is only said: its enemies still have the lent zone."""
        self.followed_at = now
        return self.place_new(here)

    def place_new(self, here: tuple | None) -> dict:
        """Moves onto the hunter each camp never tried yet (trial 6s: the camps of enemies drawn later)."""
        fresh = [name for name in self.camp_map.spawners if name not in self.tried]
        self.tried.update(fresh)
        return {name: self._place(name, here) for name in fresh}

    def follow(self, here: tuple | None, now: float) -> dict | None:
        """Moves back onto the hunter, at most every FOLLOW_S, each spawner he has walked away from; None when it is not
        time, else what was done by camp."""
        if self.followed_at is None or now - self.followed_at < FOLLOW_S:
            return None
        self.followed_at = now
        away = {name: reads.metres(shift.where(), here) for name, shift in self.shifts.items()}
        return {name: self._place(name, here) for name, metres in away.items()
                if metres is not None and metres > FOLLOW_M}

    def release(self, name: str) -> None:
        """Lets go of a camp: no longer followed, put back nor noted; it follows again once an enemy of it is drawn
        anew. The run lets go of a camp It Follows made once its enemy is lost, so that the wave may hand it a new
        enemy where it asks: in trial 8a, such camps moved back onto the hunter right after being taken again made
        fewer and fewer new enemies, none in the last 20 s (docs/RUN/enquetes/2026-10-13-reapparition.md)."""
        self.shifts.pop(name, None)
        self.tried.discard(name)
        self.movable.discard(name)
        self.camp_map.forget(name)

    def release_empty(self, drawn: Iterable[str], ours: Callable[[str], bool]) -> dict:
        """Puts back where it stood, then lets go of (release), each followed camp of the game that no enemy of the
        horde comes from any more, whatever the put back says; drawn holds the names of the enemies still in the horde,
        ours(name) whether It Follows made the camp. Says what was done by camp."""
        held = {self.camp_map.of.get(enemy) for enemy in drawn}
        empty = [name for name in self.shifts if name not in held and not ours(name)]
        done = {}
        for name in empty:
            done[name] = self._put_back(name)
            self.release(name)
        return done

    def put_back(self) -> dict:
        """Stops following and puts each moved spawner back where it stood."""
        self.followed_at = None
        return {name: self._put_back(name) for name in self.shifts}

    def _put_back(self, name: str) -> str:
        return self.shifts[name].put_back(lambda: self.announce("K2_SetActorLocation", camp=name, back=True))

    def _place(self, name: str, here: tuple | None) -> str:
        pointer = self.camp_map.spawners.get(name)
        spawner = pointer() if pointer is not None else None
        if spawner is None:
            return "gone"
        try:
            if name not in self.movable and not self._movable(spawner, name):
                return "static"
            shift = self.shifts.get(name)
            if shift is None:
                shift = self.shifts[name] = Shift(spawner, actor=True)
            said = shift.place(here, lambda: self.announce("K2_SetActorLocation", log=False, camp=name))
        except Exception as error:
            self.movable.discard(name)
            return f"call_failed:{type(error).__name__}"
        if said == "moved":
            self.movable.add(name)
        else:
            self.movable.discard(name)
        return said

    def _movable(self, spawner: Any, name: str) -> bool:
        """Its root made movable, the call announced first; whether it is."""
        root = spawner.RootComponent
        if root is None:
            return False
        if int(root.Mobility) == MOVABLE:
            return True
        self.announce("SetMobility", camp=name)
        root.SetMobility(MOVABLE)
        return int(root.Mobility) == MOVABLE
