"""The level's dodges (decisions 83 to 85): every condition open, the rests divided, the chance set, in each family's
dodge file and in each enemy's own copy of it, given back when the mode stops.

What and why, trials 21 to 27 (docs/RUN/enquetes/, vérifié en jeu):
- an enemy takes its family's file at birth and keeps its own copy (AIDodgeState, trial 22): the file alone left the
  enemies already born with the game's dodges, and Kevin saw no change until both were written (trial 25);
- the conditions opened as the enemy research opened them (apex_probe/enemy_reach.py): the shooter's distance, the
  angle, the wait before a dodge; the tickets a dodge may wait for switched off (trial 25); the two greatest distances
  set far past any fight, in case the game reads them whatever its switches say (decision 83, non vérifié);
- the rest after each dodge and the warmup before the first of a fight divided by levels.DODGE_REST_DIVIDE, the chance
  of the three dodges set to the level's, IsMovingSpeed times the level's (Predator; by its name the speed under which
  an enemy counts as standing, non vérifié). Trials 26 and 27 counted about 19 dodges a minute of fight at Bandit,
  against about 2 for the game.

A file is shared by a whole family and outlives a change of map: it is opened once while the mode is on, held by a weak
pointer, and given back at the stop. Its conditions are fields the SDK writes; its hidden values are GbxParams
(gbx_param.py), written after the conditions, since a struct assigned back whole carries the bytes read with it. A copy
is brought to its file's values only where it still holds the file's own: one born after the file was opened holds the
opened ones already. A copy is given back the same way, its file's own values written where the opened ones lie.
"""

from typing import Any, Callable

import unrealsdk

from .. import gbx_param, reads
from . import levels

ENTRIES = ("DodgeBullet", "DodgeGrenade", "DodgeZone")
ALL_ENTRIES = ENTRIES + ("DodgeRandom",)
TICKETS = "bUseTicketSettings"
# 10 km, in the game's centimetres.
FAR_CM = 1.0e6
OPENINGS: tuple[tuple[str, Any], ...] = (
    ("MinShooterDistance", 0.0),
    ("MaxShooterDistance", FAR_CM),
    ("MaxDistance", FAR_CM),
    ("bLimitMinShooterDistance", False),
    ("bLimitMaxShooterDistance", False),
    ("bLimitAngle", False),
    ("bLimitDistance", False),
    ("bRemoveAllDelay", True),
)
# Trial 25 met 5 families, trial 27 8 in the first zone. The game describes some 60 AIDodges_ families
# (docs/enemies/catalogues/ressources.csv, source unique): room for all of them, a game long (audit of 15 October 2026).
MAX_FAMILIES = 128


def _changes(entry: str) -> list[tuple[str, Any]]:
    """The conditions opened on the three dodges, the tickets on all four."""
    return [*(OPENINGS if entry in ENTRIES else ()), (TICKETS, False)]


def _set_to(level_value: float) -> Callable[[int, Any], Any]:
    """A chance set to the level's, whatever it was; a range gets it and no width."""
    def rule(kind: int, value: Any) -> Any:
        if kind == gbx_param.RANGE:
            return [level_value, 0.0]
        return level_value if kind == gbx_param.DECIMAL else value
    return rule


def _times(factor: float) -> Callable[[int, Any], Any]:
    def rule(kind: int, value: Any) -> Any:
        if kind == gbx_param.RANGE:
            return [value[0] * factor, value[1] * factor]
        return round(value * factor) if kind == gbx_param.WHOLE else value * factor
    return rule


def targets(level: levels.Level) -> tuple[tuple[str, Callable[[int, Any], Any]], ...]:
    """The hidden values the level writes, each by its name in a file or a copy, with its rule."""
    rest = _times(1.0 / levels.DODGE_REST_DIVIDE)
    found = [(f"{entry}.Chance", _set_to(level.dodge_chance)) for entry in ENTRIES]
    found += [(f"{entry}.cooldown", rest) for entry in ALL_ENTRIES]
    found.append(("CombatStartedWarmup", rest))
    if level.dodge_moving != 1.0:
        found.append(("IsMovingSpeed", _times(level.dodge_moving)))
    return tuple(found)


def _part(holder: Any, key: str) -> tuple[Any, str]:
    """What holds key's field in a file or a copy, and the field."""
    entry, _, field = key.rpartition(".")
    return (getattr(holder, entry) if entry else holder), field


class Family:
    """One family's file as opened: its conditions, each (entry, field, the game's value, the value opened), entry
    None for the file's own tickets; and its hidden values, each name with the game's bytes and those written."""

    def __init__(self, data: Any) -> None:
        self.pointer = unrealsdk.unreal.WeakPointer(data)
        self.opened: list[tuple[str | None, str, Any, Any]] = []
        self.params: dict[str, tuple[str, str]] = {}


def _bring(family: Family, holder: Any, back: bool) -> dict[str, int]:
    """Brings a copy (or, given back, a file too) from the game's values to the opened ones, or back; a field is
    written only where it holds the values it is brought from. What each write did, counted."""
    tally: dict[str, int] = {}
    for entry in ALL_ENTRIES:
        fields = [opened for opened in family.opened if opened[0] == entry]
        if not fields:
            continue
        part = getattr(holder, entry)
        for _, field, game, opened in fields:
            source, target = (opened, game) if back else (game, opened)
            if getattr(part, field) == source:
                setattr(part, field, target)
        # Assigned back whole: the SDK may hand out a copy of the struct (enemy_reach.py).
        setattr(holder, entry, part)
    for key, (old, new) in family.params.items():
        status = gbx_param.replace(*_part(holder, key), *((new, old) if back else (old, new)))
        tally[status] = tally.get(status, 0) + 1
    return tally


class Dodges:
    """The families opened while the mode is on. note(event, **fields) writes a line; announce(call, log, **fields) a
    write before it is made."""

    def __init__(self, level: levels.Level, note: Callable[..., None], announce: Callable[..., None]) -> None:
        self.targets = targets(level)
        self.note, self.announce = note, announce
        self.files: dict[str, Family] = {}

    def meet(self, actor: Any) -> str | None:
        """Opens the family of this enemy once, and brings its copy to the opened values; the family, or None for an
        enemy without dodges or past MAX_FAMILIES."""
        state = actor.AIDodgeState
        data = state.CurrentDodgeData
        if data is None:
            return None
        family = reads.clean(data.Name)
        held = self.files.get(family)
        if held is None or held.pointer() is None:
            if held is None and len(self.files) >= MAX_FAMILIES:
                return None
            held = self._open(family, data)
        _bring(held, state, back=False)
        return family

    def _open(self, family: str, data: Any) -> Family:
        """The file's conditions opened, then its hidden values written, each owed before it is written."""
        self.announce("AIDodgeData", family=family)
        held = Family(data)
        self.files[family] = held
        for entry in ALL_ENTRIES:
            part = getattr(data, entry)
            for field, value in _changes(entry):
                before = getattr(part, field)
                if before != value:
                    held.opened.append((entry, field, before, value))
                    setattr(part, field, value)
            setattr(data, entry, part)
        if getattr(data, TICKETS) is not False:
            held.opened.append((None, TICKETS, getattr(data, TICKETS), False))
            setattr(data, TICKETS, False)
        refused: dict[str, str] = {}
        for key, rule in self.targets:
            result = gbx_param.change(*_part(data, key), rule)
            if "new" in result:
                held.params[key] = (result["old"], result["new"])
            else:
                refused[key] = result["refused"]
        self.note("normal_dodges_opened", family=family, opened=len(held.opened), written=len(held.params),
                  refused=refused)
        return held

    def give_back(self, actor: Any) -> dict[str, int]:
        """The enemy's copy brought back to its file's own values; nothing for a family never opened."""
        state = actor.AIDodgeState
        data = state.CurrentDodgeData
        held = None if data is None else self.files.get(reads.clean(data.Name))
        return {} if held is None else _bring(held, state, back=True)

    def stop(self) -> dict:
        """Every file the game still holds given back, its own tickets last; those it dropped owe nothing."""
        tally: dict[str, int] = {"gone": 0}
        for held in self.files.values():
            data = held.pointer()
            if data is None:
                tally["gone"] += 1
                continue
            try:
                for status, count in _bring(held, data, back=True).items():
                    tally[status] = tally.get(status, 0) + count
                for entry, field, game, opened in held.opened:
                    if entry is None and getattr(data, field) == opened:
                        setattr(data, field, game)
            except Exception as error:
                key = f"failed:{type(error).__name__}"
                tally[key] = tally.get(key, 0) + 1
        result = {"families": len(self.files), **tally}
        self.files = {}
        return result
