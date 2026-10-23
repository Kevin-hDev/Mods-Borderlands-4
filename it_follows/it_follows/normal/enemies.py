"""The game's enemies the normal mode meets in one game, each given the level: its dodges (dodge_rate.py), its speed
(speed.py), its health (toughness.py), its zone's long chase (pursuit.py), a shield when it has none and the level
gives it (shields.py), its weapons' aim (aim.py), and, when the player chose it, the one team (teams.py). Each is let
go when it dies or leaves, and everything is given back when the game is left or the mode stops. A boss gets the
level's health, speed, shield and aim only, never the chase, the dodges or the one team (decision 90: Kevin wants them
stronger; decision 4 kept them home because the chase takes one from its arena; decision 113 gives them the shield).
Each census gives the aim again to the enemies held alive: a weapon taken since gets it, one that kept it is left. The
shield is given before the health is raised, so that the level and the Hardcore raise it with the rest and
toughness.py gives it back: it stays SHIELD_SHARE of the health shown.

The Hardcore (decision 89) multiplies the level's health: harden gives a new factor to every enemy held, at once. Its
kills are counted from each census (kills.py).

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

from .. import census, speed, teams, toughness
from ..characters import reads
from . import aim as aim_module
from . import kills as kills_module
from . import shields as shields_module

EVERY_S = 5.0
# The census holds the game while it reads: a quarter of a second at most, as the Horde's recruiter (recruit.READ_S).
READ_S = 0.25
# Below the 240 enemies whose health toughness.py tends at once.
MOST = 200
# The enemies whose dodges and gestures are looked at each image (enemy_time.py): the nearest, within reach of a fight.
WATCH_M = 60.0
WATCH_MOST = 48


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
                 announce: Callable[..., None], hard: float = 1.0, shields: bool = False) -> None:
        self.dodges, self.chase, self.note, self.level_health = dodges, chase, note, level.health
        self.speed = speed.SpeedBoost(announce, level.speed)
        self.toughness = toughness.Toughness(announce, note, level.health * hard)
        self.teams = teams.Teams(announce) if allies else None
        self.shields = shields_module.Shields(announce, level.shield_refill, note=note) if shields else None
        self.shielded: dict[str, int] = {}
        self.aim = aim_module.Aim(announce, level.spread, level.bullet_speed)
        self.aimed: dict[str, int] = {}
        self.met: dict[str, Met] = {}
        self.read_at = -math.inf
        self.said: set[str] = set()
        self.kills = kills_module.Kills()

    def due(self, now: float) -> bool:
        return now - self.read_at >= EVERY_S

    def look(self, player: Any, now: float) -> dict:
        """One census: the lost let go, the new met; what changed, empty when nothing did."""
        self.read_at = now
        found, read, sighting = census.seen_around(player, READ_S, bosses=True, kills=True, pc=mods_base.get_pc())
        kills, said, fights, by_others = self.kills.count(sighting, self.met)
        lost = self._lose(sighting, read["stopped"] == "complete")
        here = reads.point(player)
        new = [seen for seen in census.everyone(found, here, len(found)) if seen.name not in self.met]
        room = max(0, MOST - len(self.met))
        self.shielded, self.aimed = {}, {}
        joined = [self._meet(seen) for seen in new[:room]]
        again = 0
        for met in self.met.values():
            mover = met.actor()
            if mover is not None:
                self.speed.keep(met.name, mover)
                if reads.dead(mover) is False and self.aim.give(met.name, mover) == "given":
                    again += 1
        if not joined and not lost and not said and not again:
            return {}
        result = {"met": len(joined), "lost": lost, "held": len(self.met), "left_out": len(new) - len(joined),
                  "read": read["read"], "stopped": read["stopped"]}
        if said:
            result["kills"], result["killers"] = kills, said
        if fights:
            result["fights"] = fights
        if by_others:
            result["by_others"] = by_others
        if again:
            result["aim_again"] = again
        if joined:
            result["aim"] = self.aimed
            if self.shielded:
                result["shields"] = self.shielded
            result["health"] = self.toughness.start(joined)
            result["boosted"] = len(self.speed.start(joined))
            fighters = [met for met in joined if not met.boss]
            if len(fighters) < len(joined):
                result["bosses"] = len(joined) - len(fighters)
            if self.teams is not None and fighters:
                joined_team = self.teams.join(fighters)
                result["team"] = joined_team.get("team")
                refused = [row["set"] for row in joined_team.get("enemies", [])
                           if row.get("set") not in ("handed", "kept", "taken_back")]
                if refused:
                    result["team_refused"] = refused
        return result

    def _meet(self, seen: Any) -> Met:
        """An enemy held before anything is written on it, so that a write that fails half way is still given back."""
        met = Met(seen.name, unrealsdk.unreal.WeakPointer(seen.actor), boss=seen.boss)
        self.met[seen.name] = met
        if self.shields is not None:
            outcome = self.shields.give(seen.name, seen.actor)
            self.shielded[outcome] = self.shielded.get(outcome, 0) + 1
            if outcome.startswith("failed:"):
                self._say_once("shield", outcome)
        outcome = self.aim.give(seen.name, seen.actor)
        self.aimed[outcome] = self.aimed.get(outcome, 0) + 1
        if outcome.startswith("failed:"):
            self._say_once("aim", outcome)
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
                 "health": self.toughness.put_back(met.name, mover, not alive), "aim": self.aim.take_off(met.name)}
        if self.shields is not None:
            given["shield"] = self.shields.take_off(met.name, mover, alive)
        if self.teams is not None:
            given["team"] = self.teams.give_back(met.name, mover, not alive, away=away)
        if alive and met.family is not None:
            try:
                given["dodges"] = self.dodges.give_back(mover)
            except Exception as error:
                given["dodges"] = f"failed:{type(error).__name__}"
        return given

    def keep_shields(self, now: float) -> dict[str, int]:
        """Predator's and God's broken shields refilled when due, on the enemies the game says alive; what happened,
        counted."""
        tally: dict[str, int] = {}
        if self.shields is None:
            return tally
        for name in list(self.shields.given):
            met = self.met.get(name)
            mover = met.actor() if met is not None else None
            if mover is None or reads.dead(mover) is not False:
                continue
            outcome = self.shields.keep(name, mover, now)
            if outcome is not None:
                tally[outcome] = tally.get(outcome, 0) + 1
        return tally

    def nearest(self, places: list[tuple], within_m: float = WATCH_M, most: int = WATCH_MOST) -> dict[str, Any]:
        """The enemies met within within_m of any of the places (each player's), nearest first, at most most, bosses
        left out: name to weak pointer."""
        near = []
        for met in self.met.values():
            mover = met.actor() if not met.boss else None
            at = reads.point(mover) if mover is not None else None
            metres = min((reads.metres(at, here) for here in places), default=None) if at is not None else None
            if metres is not None and metres <= within_m:
                near.append((metres, met))
        near.sort(key=lambda pair: pair[0])
        return {met.name: met.pointer for _, met in near[:most]}

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
        shielded: dict[str, int] = {}
        aimed: dict[str, int] = {}
        for met in self.met.values():
            mover = met.actor()
            alive = mover is not None and reads.dead(mover) is False
            given = self._let_go(met, mover, alive)
            tally[given["health"]] = tally.get(given["health"], 0) + 1
            aimed[given["aim"]] = aimed.get(given["aim"], 0) + 1
            if "shield" in given:
                shielded[given["shield"]] = shielded.get(given["shield"], 0) + 1
        result = {"enemies": len(self.met), "health": tally, "aim": aimed}
        if shielded:
            result["shields"] = shielded
        self.met = {}
        return result
