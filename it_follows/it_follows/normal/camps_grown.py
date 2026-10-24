"""The game's camps around the player made to hold the level's times their enemies before any is born, so that the
enemies in more are the game's own, born by their camp in their zone and their team (decisions 80 and 81).

How, trials 22 to 25 (docs/RUN/enquetes/, vérifié en jeu): a camp's numbers of enemies are GbxParams of its style
(SpawnerComponent.SpawnerStyleData.InlineDef), written in memory (gbx_param.py); a camp loaded keeps the total it drew
(trial 22), and ResetSpawner(False) makes it draw again from the numbers written: a camp of 4 at ×10 bore 40 in 38 s
(trial 25). The same call makes a camp the player emptied bear its enemies again at once: only the camps none of whose
enemies is born yet are taken, so that nothing comes back (spec, section 1); one already born keeps the game's
numbers. That a camp not born stays waiting for the player after the call, as the two of trial 25 did (a chest's camp
and a boss's reinforcements), is not verified for a camp of enemies.

Only the enemies' camps: a mix of enemies (Mix_…), or one enemy the catalogue knows as no boss (kinds.py), never a
boss's reinforcements (…BossAdd, whose total has no end) nor a chest (Lootable_…), both met in trial 25. The level's
×1.5 is counted without chance from one camp to the next (decision 38): two camps of one enemy get one more between
them. The game still lets only some 29 ordinary enemies live at once (game_camps.py): past it, a camp's enemies come
as others die.

A pass runs every EVERY_S over the camps of the world in play (reads.search, decision 105: 0.03 to 0.06 ms where
find_all took 9 to 13 ms, the Horde's way since trial 39), part by part: a part stops after PART_S, and the mode
gives the next image the rest (play.py), PARTS_MOST parts at most, the rest at the next pass. Reaching a zone grew 84
to 114 camps in one image, 36 to 46 ms (trials 171 and 110; audit of 24 October 2026, N2 and N4); only the first
DETAILED camps grown in a game are written to the log, three lines each. A camp is held by its name, with a weak
pointer: the game unloads the camps of a place the player left and loads them again under the same name, as new camps
with the game's own numbers (game_camps.py), taken again then. At the stop each camp still there gets its numbers back;
one still not born is reset again, to draw the game's own; one born keeps what it drew until the game loads the place
again, since a reset would bring its dead back.
"""

import math
import time
from itertools import islice
from typing import Any, Callable

import unrealsdk

from .. import gbx_param, kinds
from ..characters import camps, reads

EVERY_S = 5.0
SPAWNER_CLASS = "Spawner"
# Farther than the 80 to 300 m at which the game wakes a camp (trial 6u): a camp is grown before the player comes near.
RANGE_M = 1000.0
# A part of a pass holds the game this long at most; a pass makes this many parts at most.
PART_S = 0.01
PARTS_MOST = 30
MAX_CAMPS = 3000
# The camps grown written to the log, the first of each game, as the enemies' writes (speed.DETAILED).
DETAILED = 20
# game_camps.MAX_HELD's bound: trial 6u found 220 camps held at once, trial 31 224. The camps the game freed are
# forgotten before this refuses: a long game meets many more (audit of 15 October 2026).
MAX_HELD = 2000
# A camp's number beyond this is no camp of enemies: a boss's reinforcements read 2147483647 in trial 25.
MOST_ENEMIES = 1000
# The numbers of enemies a camp's style may hold (trial 19 read their names in game); MAIN's, its total, is the one the
# fraction is counted on.
FIELDS =("NumTotalActors", "NumActors", "NumWaveActors", "NumWaveActorsPassive", "NumWaveActorsDistant",
          "NumActorsPassive", "NumActorsDistant")
MAIN = ("NumTotalActors", "NumActors")


def enemy_camp(definition: str) -> bool:
    """Whether a camp's definition is enemies': a mix, or one enemy of the catalogue that is no boss nor a boss's
    reinforcement."""
    if definition.startswith("Mix_"):
        return True
    sort = kinds.kind(definition)
    return sort is not None and sort[0] == kinds.ENEMY and "bossadd" not in definition.lower()


def _has(style: Any, name: str) -> bool:
    try:
        style._type._find_prop(name)
    except Exception:
        return False
    return True


class CampsGrown:
    """note(event, **fields) writes a line; announce(call, log, **fields) a call or a write before it is made."""

    def __init__(self, note: Callable[..., None], announce: Callable[..., None], factor: float) -> None:
        self.note, self.announce, self.factor = note, announce, factor
        # By name: its weak pointer, and the bytes owed by field, None for a camp left to the game.
        self.held: dict[str, tuple[Any, dict[str, tuple[str, str]] | None]] = {}
        self.carry = 0.0
        self.read_at = -math.inf
        self.detailed = 0

    def due(self, now: float) -> bool:
        return now - self.read_at >= EVERY_S

    def _sized(self, value: int) -> int:
        """A camp's total times the factor, the fraction carried to the next camp."""
        wanted = value * self.factor + self.carry
        made = max(value, math.floor(wanted + 1e-9))
        self.carry = wanted - made
        return made

    def grow(self, places: list[tuple], now: float, world: Any = None) -> dict:
        """One part of a pass: the camps within RANGE_M of any of the places (each player's, coop_guests.py) not
        held yet read, the enemies' camps not born grown and reset; what it did, and how the camps were searched.
        world: an actor of the world in play, whose camps are searched (reads.search); every object without it."""
        self.read_at = now
        counts = dict.fromkeys(("grown", "same", "born", "not_enemies", "too_many", "empty", "refused", "far"), 0)
        stopped, began = "complete", time.perf_counter()
        if not places:
            return {**counts, "stopped": "no_place", "search": None}
        spawners, search = reads.search(SPAWNER_CLASS, world)
        for spawner in islice(spawners, MAX_CAMPS):
            if time.perf_counter() - began > PART_S:
                stopped = "time_limit"
                break
            name = reads.clean(getattr(spawner, "Name", ""))
            if name.startswith("Default__") or (name in self.held and self.held[name][0]() is not None):
                continue
            at = reads.point(spawner)
            metres = min((reads.metres(at, here) for here in places if at is not None), default=None)
            if metres is None or metres > RANGE_M:
                counts["far"] += 1
                continue
            if len(self.held) >= MAX_HELD and not self._forget_gone():
                stopped = "held_limit"
                break
            counts[self._take(name, spawner)] += 1
        return {**counts, "held": len(self.held), "stopped": stopped, "search": search,
                "took_ms": round((time.perf_counter() - began) * 1000.0, 1)}

    def _forget_gone(self) -> bool:
        """The camps the game freed forgotten: one loaded again comes with the game's own numbers, nothing is owed to
        it. Whether there is room now."""
        for name in [name for name, (pointer, _) in self.held.items() if pointer() is None]:
            del self.held[name]
        return len(self.held) < MAX_HELD

    def _take(self, name: str, spawner: Any) -> str:
        """One camp read and, an enemies' camp not born, grown: what was done."""
        pointer = unrealsdk.unreal.WeakPointer(spawner)
        self.held[name] = (pointer, None)
        try:
            component = spawner.SpawnerComponent
            definition = reads.clean(getattr(component.GbxActorDef, "_name", ""))
            style = component.SpawnerStyleData.InlineDef
            if not enemy_camp(definition):
                return "not_enemies"
            if component.GetNumSpawnedActors(camps.ALL_SPAWNED) != 0:
                return "born"
            read = {field: gbx_param.read(style, field) for field in FIELDS if _has(style, field)}
        except Exception:
            return "refused"
        numbers = {field: found[1] for field, found in read.items()
                   if not isinstance(found, str) and found[1] is not None}
        if any(_largest(number) > MOST_ENEMIES for number in numbers.values()):
            return "too_many"
        main = next((field for field in MAIN if field in numbers), None)
        if main is None:
            return "refused"
        if _largest(numbers[main]) <= 0:
            return "empty"
        try:
            return self._write(name, pointer, component, style, list(numbers), main, definition)
        except Exception as error:
            self.note("normal_camp_failed", camp=name, error=type(error).__name__)
            return "refused"

    def _write(self, name: str, pointer: Any, component: Any, style: Any, fields: list[str], main: str,
               definition: str) -> str:
        """The numbers written, the main one first, each owed as soon as it is; then the camp reset."""
        kind, total = gbx_param.read(style, main)
        ratio = self._sized(total) / total if kind == gbx_param.WHOLE else self.factor
        if ratio == 1.0:
            # Its share of the fraction went to the next camp: nothing written, no reset.
            return "same"
        owed: dict[str, tuple[str, str]] = {}
        self.held[name] = (pointer, owed)
        detailed = self.detailed < DETAILED
        self.detailed += 1
        self.announce("SpawnerStyle", log=detailed, camp=name, enemy=definition, factor=round(ratio, 3))
        for field in (main, *(field for field in fields if field != main)):
            result = gbx_param.change(style, field, lambda kind, value: _times(kind, value, ratio))
            if "new" in result and result["new"] != result["old"]:
                owed[field] = (result["old"], result["new"])
        self.announce("ResetSpawner", log=detailed, camp=name)
        component.ResetSpawner(False)
        if detailed:
            self.note("normal_camp_grown", camp=name, enemy=definition,
                      total=[total, component.GetNumTotalActors()], written=len(owed))
        return "grown"

    def put_back(self) -> dict:
        """Each camp still there given its numbers back; one not born reset again; what was done."""
        tally = dict.fromkeys(("given", "reset", "gone", "failed"), 0)
        for name, (pointer, owed) in self.held.items():
            if not owed:
                continue
            spawner = pointer()
            if spawner is None:
                tally["gone"] += 1
                continue
            try:
                component = spawner.SpawnerComponent
                style = component.SpawnerStyleData.InlineDef
                for field, (old, new) in owed.items():
                    gbx_param.replace(style, field, new, old)
                tally["given"] += 1
                if component.GetNumSpawnedActors(camps.ALL_SPAWNED) == 0:
                    self.announce("ResetSpawner", camp=name, back=True)
                    component.ResetSpawner(False)
                    tally["reset"] += 1
            except Exception:
                tally["failed"] += 1
        self.held = {}
        return tally


def _largest(number: Any) -> float:
    """A whole or decimal number itself, a range its centre plus its half width."""
    return number[0] + number[1] if isinstance(number, list) else number


def _times(kind: int, value: Any, ratio: float) -> Any:
    """A camp's number times ratio: a whole number rounded, at least itself, so that 0 stays 0 where the trials' rule
    made it 1; a range, its centre and half width; a decimal one as it is."""
    if kind == gbx_param.RANGE:
        return [value[0] * ratio, value[1] * ratio]
    if kind == gbx_param.WHOLE:
        return max(value, round(value * ratio))
    return value * ratio
