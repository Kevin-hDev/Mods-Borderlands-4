"""Fake zones, camps' spawners and enemies for the tests of the zone lent to the horde and of the camps that follow the
hunter (it_follows/zone_shift.py, zone_loan.py, zone_radius.py, hunter_zone.py, camp_map.py, camp_follow.py): what
the game does with each call, written in one journal for the tests to read. Imported once sdk_stubs.install() has run:
Fixture(state) gives that fake SDK a make_struct that keeps the structure's name. Taken from the trials' tests
(docs/RUN/sondes/test_run_zone_shift.py, test_run_zone_loan.py, test_run_hunter_zone.py, test_run_camp_watch.py,
test_run_camp_follow.py)."""

import json
import sys
import types
from typing import Any

from sdk_stubs import vector

from it_follows import report
from it_follows.seen import Seen

PATH = "/Game/Maps/World_P.World_P:PersistentLevel.{name}.Territory"
# The game's EComponentMobility.Movable, kept apart from the mod's own so that a wrong value in the mod shows.
GAME_MOVABLE = 2


def announced(call: str, log: bool = True, **fields: Any) -> tuple:
    """The journal's line for a call announced."""
    return ("announce", call, log, fields)


class Zone:
    """A combat zone, read and moved by a component's functions only, part of its spawner (Outer). Stuck, it does not
    move; failing, its move raises; it lands offset_cm along X from the point asked."""

    def __init__(self, journal: list, name: str, at: tuple, radius_cm: float, outer: Any) -> None:
        self.journal, self.name, self.at, self.Outer = journal, name, at, outer
        self.path = PATH.format(name=name)
        self.settings = types.SimpleNamespace(CombatTerritory=types.SimpleNamespace(Radius=radius_cm))
        self.stuck = self.fail = self.freed = False
        self.offset_cm = 0.0
        self.calls: list[dict] = []

    def _path_name(self) -> str:
        return self.path

    def K2_GetComponentLocation(self) -> Any:
        return vector(*self.at)

    def K2_SetWorldLocation(self, *, NewLocation: Any, bSweep: bool, SweepHitResult: Any, bTeleport: bool) -> tuple:
        self.journal.append(("move", self.name, NewLocation.X))
        self.calls.append({"sweep": bSweep, "hit": SweepHitResult.struct_name, "teleport": bTeleport})
        if self.fail:
            raise RuntimeError("refused")
        if not self.stuck:
            self.at = (NewLocation.X + self.offset_cm, NewLocation.Y, NewLocation.Z)
        return (..., SweepHitResult)


class Root:
    """A spawner's root component; refusing, SetMobility changes nothing."""

    def __init__(self, journal: list, owner: str, mobility: int, refuses: bool) -> None:
        self.journal, self.owner, self.Mobility, self.refuses = journal, owner, mobility, refuses

    def SetMobility(self, value: int) -> None:
        self.journal.append(("mobility", self.owner, value))
        if not self.refuses:
            self.Mobility = value


class Spawner:
    """A camp's spawner: a whole actor, read and moved by an actor's functions only, and moved only while its root is
    movable, the game saying nothing otherwise (trial 6h). Failing, its move raises."""

    def __init__(self, journal: list, name: str, at: tuple, mobility: int, refuses: bool) -> None:
        self.journal, self.Name, self.at = journal, name, at
        self.RootComponent = Root(journal, name, mobility, refuses)
        self.SpawnerComponent = types.SimpleNamespace()
        self.fail = self.freed = False
        self.calls: list[dict] = []

    def K2_GetActorLocation(self) -> Any:
        return vector(*self.at)

    def K2_SetActorLocation(self, *, NewLocation: Any, bSweep: bool, SweepHitResult: Any, bTeleport: bool) -> tuple:
        self.journal.append(("move", self.Name, NewLocation.X))
        self.calls.append({"sweep": bSweep, "hit": SweepHitResult.struct_name, "teleport": bTeleport})
        if self.fail:
            raise RuntimeError("refused")
        if int(self.RootComponent.Mobility) == GAME_MOVABLE:
            self.at = (NewLocation.X, NewLocation.Y, NewLocation.Z)
        return (True, SweepHitResult)


class Enemy:
    """An enemy and the zone it holds. Refusing, it keeps the zone it has; failing, SetTerritory raises."""

    def __init__(self, journal: list, name: str, home: Zone | None) -> None:
        self.journal, self.name, self.home, self.zone = journal, name, home, home
        self.refuse = self.fail = self.freed = False

    def GetTerritory(self) -> Any:
        return self.zone

    def SetTerritory(self, zone: Any) -> None:
        self.journal.append(("set", self.name, None if zone is None else zone.name))
        if self.fail:
            raise RuntimeError("refused")
        if not self.refuse:
            self.zone = zone


class Fixture:
    """One journal for every fake, and announce: each call written in the journal, then passed to It Follows' own
    announce, which refuses a field named as one of its own. Trial 8c was lost to a fake announce that took any name
    (commit b86ba6da): the real one runs in every test."""

    def __init__(self, state: dict) -> None:
        self.state, self.journal = state, []
        sys.modules["unrealsdk"].make_struct = lambda name, **fields: types.SimpleNamespace(struct_name=name, **fields)

    def announce(self, call: str, log: bool = True, **fields: Any) -> None:
        self.journal.append(announced(call, log, **fields))
        report.announce(call, log, **fields)

    def logged(self) -> dict:
        """The last line It Follows wrote to the SDK log, read back."""
        return json.loads(self.state["info"][-1].removeprefix(report.PREFIX + " "))

    def zone(self, name: str, at: tuple, radius_cm: float = 4000.0, outer: Any = None) -> Zone:
        return Zone(self.journal, name, at, radius_cm, outer)

    def spawner(self, name: str, at: tuple, mobility: int = GAME_MOVABLE, refuses: bool = False) -> Spawner:
        return Spawner(self.journal, name, at, mobility, refuses)

    def zone_of(self, spawner: Spawner) -> Zone:
        """A zone part of that camp's spawner."""
        return self.zone(f"{spawner.Name}_Territory", spawner.at, outer=spawner)

    def enemy(self, name: str, home: Zone | None) -> Enemy:
        return Enemy(self.journal, name, home)

    def seen(self, name: str, zone: Zone | None, actor: Any = None) -> Seen:
        """What the census reads of a character holding that zone."""
        return Seen(actor=actor, name=name, definition="Char_Cat", zone=zone,
                    zone_path="" if zone is None else zone.path, centre=None if zone is None else zone.at,
                    radius_m=0.0 if zone is None else zone.settings.CombatTerritory.Radius / 100.0, at=None)
