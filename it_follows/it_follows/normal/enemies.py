"""The game's enemies the normal mode meets in one game, each given the level: its dodges (dodge_rate.py), its speed
(speed.py), its health (toughness.py), its zone's long chase (pursuit.py) and, when the player chose it, the one team
(teams.py). Each is let go when it dies or leaves, and everything is given back when the game is left or the mode
stops. A boss gets the level's health and speed only, never the chase, the dodges or the one team (decision 90:
Kevin wants them stronger; decision 4 kept them home because the chase takes one from its arena).

The Hardcore (decision 89) multiplies the level's health: harden gives a new factor to every enemy held, at once. Its
kills are the enemies the census reads dead that the player killed (killers.py), met or not: an enemy killed before a
census read it alive counts too (trial 31, BL4 Arena's enemies killed within 5 s of their birth). Each body counts
once; one read alive again is the game's next enemy, its body reused, whose death counts; the dead the first census
reads were there before and count not.

Every EVERY_S the census reads the enemies the game holds (census.py, the Horde's, bosses kept: world events and the
game's reserve passed over, decision 4); those not met yet are met, nearest first, up to MOST at once. An enemy is let
go when the census reads it dead, when its weak pointer is gone, or when a complete census no longer reads it alive (in
the game's reserve, among others): nothing is called on it then, since the game gives a dead enemy's body to the next
one (spec, « Oublier les morts »), and its own speed is written back all the same, a value and not a call, as the Horde
does (horde.let_go). A census cut short by its time lets no one go: who it did not read is unknown. One no longer read
alive is the same enemy should it come again: its health is taken back as raised (toughness.py) and its own team was
set aside (teams.py), never laid twice nor kept for good in the one team (audit of 15 October 2026: 36 enemies of
trials 28 to 32 left that way).
"""

import math
from dataclasses import dataclass
from typing import Any, Callable

import mods_base
import unrealsdk

from .. import census, killers, reads, speed, teams, toughness

EVERY_S = 5.0
# The census holds the game while it reads: a quarter of a second at most, as the Horde's recruiter (recruit.READ_S).
READ_S = 0.25
# Below the 240 enemies whose health toughness.py tends at once.
MOST = 200
# The enemies whose dodges are looked at each image (dodge_speed.py): the nearest, within reach of a fight.
WATCH_M = 60.0
WATCH_MOST = 48
# The bodies counted, remembered so that each counts once, the oldest forgotten first: some minutes of fights.
COUNTED_MOST = 2000


@dataclass
class Met:
    """One enemy met: its name, its weak pointer, its family of dodges (None without), whether it is a boss."""
    name: str
    pointer: Any
    family: str | None = None
    boss: bool = False

    def actor(self) -> Any:
        return self.pointer()


class Enemies:
    """dodges: dodge_rate.Dodges, kept by the mode from one game to the next; chase: pursuit.Pursuit, the level's
    long chase; hard: the Hardcore's factor at the start, on top of the level's health. note(event, **fields) writes a
    line, announce(call, log, **fields) a call before it is made."""

    def __init__(self, level: Any, allies: bool, dodges: Any, chase: Any, note: Callable[..., None],
                 announce: Callable[..., None], hard: float = 1.0) -> None:
        self.dodges, self.chase, self.note, self.level_health = dodges, chase, note, level.health
        self.speed = speed.SpeedBoost(announce, level.speed)
        self.toughness = toughness.Toughness(announce, note, level.health * hard)
        self.teams = teams.Teams(announce) if allies else None
        self.met: dict[str, Met] = {}
        self.read_at = -math.inf
        self.said: set[str] = set()
        self.counted: dict[str, None] = {}
        self.first = True

    def due(self, now: float) -> bool:
        return now - self.read_at >= EVERY_S

    def look(self, player: Any, now: float) -> dict:
        """One census: the lost let go, the new met; what changed, empty when nothing did."""
        self.read_at = now
        found, read, sighting = census.seen_around(player, READ_S, bosses=True, kills=True, pc=mods_base.get_pc())
        kills, said = self._kills(sighting)
        lost = self._lose(sighting, read["stopped"] == "complete")
        here = reads.point(player)
        new = [seen for seen in census.everyone(found, here, len(found)) if seen.name not in self.met]
        room = max(0, MOST - len(self.met))
        joined = [self._meet(seen) for seen in new[:room]]
        for met in self.met.values():
            mover = met.actor()
            if mover is not None:
                self.speed.keep(met.name, mover)
        if not joined and not lost and not said:
            return {}
        result = {"met": len(joined), "lost": lost, "held": len(self.met), "left_out": len(new) - len(joined),
                  "read": read["read"], "stopped": read["stopped"]}
        if said:
            result["kills"], result["killers"] = kills, said
        if joined:
            result["health"] = self.toughness.start(joined)
            result["boosted"] = len(self.speed.start(joined))
            fighters = [met for met in joined if not met.boss]
            if len(fighters) < len(joined):
                result["bosses"] = len(joined) - len(fighters)
            if self.teams is not None and fighters:
                result["team"] = self.teams.join(fighters).get("team")
        return result

    def _kills(self, sighting: Any) -> tuple[int, dict[str, int]]:
        """The bodies read dead not counted yet: how many the player killed, and what KillerActor/LastHitBy said of
        them, counted by what they said."""
        for name in sighting.alive:
            self.counted.pop(name, None)
        kills, said = 0, {}
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
        self.first = False
        return kills, said

    def _meet(self, seen: Any) -> Met:
        """An enemy held before anything is written on it, so that a write that fails half way is still given back."""
        met = Met(seen.name, unrealsdk.unreal.WeakPointer(seen.actor), boss=seen.boss)
        self.met[seen.name] = met
        if met.boss:
            return met
        try:
            met.family = self.dodges.meet(seen.actor)
        except Exception as error:
            self._say_once("dodges", error)
        outcome = self.chase.widen(seen)
        if outcome.startswith("failed:"):
            self._say_once("chase", outcome)
        return met

    def _say_once(self, what: str, error: Any) -> None:
        text = error if isinstance(error, str) else type(error).__name__
        if f"{what}:{text}" not in self.said:
            self.said.add(f"{what}:{text}")
            self.note("normal_enemy_failed", what=what, error=text)

    def _lose(self, sighting: Any, complete: bool) -> dict[str, int]:
        """The enemies dead, gone, or no longer read alive by a complete census, let go without a call."""
        lost: dict[str, int] = {}
        for name, met in list(self.met.items()):
            mover = met.actor()
            if mover is None:
                why = "gone"
            elif name in sighting.dead or reads.dead(mover) is True:
                why = "dead"
            elif complete and name not in sighting.alive:
                why = "away"
            else:
                continue
            self._let_go(met, mover, alive=False, away=why == "away")
            del self.met[name]
            lost[why] = lost.get(why, 0) + 1
        return lost

    def _let_go(self, met: Met, mover: Any, alive: bool, away: bool = False) -> dict:
        """What the enemy holds given back: calls only on one alive and in the world, its speed even dead; one away has
        its own team set aside."""
        given = {"boost": self.speed.put_back(met.name, mover),
                 "health": self.toughness.put_back(met.name, mover, not alive)}
        if self.teams is not None:
            given["team"] = self.teams.give_back(met.name, mover, not alive, away=away)
        if alive and met.family is not None:
            try:
                given["dodges"] = self.dodges.give_back(mover)
            except Exception as error:
                given["dodges"] = f"failed:{type(error).__name__}"
        return given

    def nearest(self, here: tuple | None) -> dict[str, Any]:
        """The enemies met within WATCH_M, nearest first, at most WATCH_MOST: name to weak pointer."""
        near = []
        for met in self.met.values():
            mover = met.actor() if not met.boss else None
            metres = reads.metres(reads.point(mover), here) if mover is not None else None
            if metres is not None and metres <= WATCH_M:
                near.append((metres, met))
        near.sort(key=lambda pair: pair[0])
        return {met.name: met.pointer for _, met in near[:WATCH_MOST]}

    def harden(self, hard: float) -> dict[str, int]:
        """The Hardcore's factor hard on top of the level's health: given to the enemies met from now on and to every
        one held that the game says alive, at once; how each went. Nothing is called on one it does not."""
        self.toughness.harden(self.level_health * hard)
        tally: dict[str, int] = {}
        for met in self.met.values():
            mover = met.actor()
            outcome = (self.toughness.reach(met.name, mover) if mover is not None and reads.dead(mover) is False
                       else "not_alive")
            tally[outcome] = tally.get(outcome, 0) + 1
        return tally

    def end(self) -> dict:
        """Every enemy still met let go: given back what it holds when alive, as when lost otherwise; counted."""
        tally: dict[str, int] = {}
        for met in self.met.values():
            mover = met.actor()
            alive = mover is not None and reads.dead(mover) is False
            outcome = self._let_go(met, mover, alive)["health"]
            tally[outcome] = tally.get(outcome, 0) + 1
        result = {"enemies": len(self.met), "health": tally}
        self.met = {}
        return result
