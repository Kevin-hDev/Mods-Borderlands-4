"""Fakes of the game for the tests of the camps (characters/camps.py, the companions' births) and of It Follows' wave
(budget, copies, wave): the spawners the camps make and the statics that make them, the zones they own, the game's
enemy list, the ground under a point and the world's settings. Every call they take is recorded in events, in order,
with report.py's lines among them once record_log() ran. Imported after sdk_stubs.install(), as the package is: its
modules are the copy the test reads (characters_fixture.part).
"""

import json
import sys
import types
from typing import Any

import characters_fixture
from sdk_stubs import vector

camp_kit, report = characters_fixture.part("camp_kit"), characters_fixture.part("report")

# The calls the fakes took and the log's lines, in order: a test clears it and reads it back.
events: list[tuple] = []


def record_log() -> None:
    """report.py's lines recorded in events too, as ("log", line), so that a test reads what was written before a
    call."""
    logging = sys.modules["unrealsdk.logging"]
    keep = logging.info

    def info(text: str) -> None:
        keep(text)
        events.append(("log", json.loads(text.removeprefix(report.PREFIX + " "))))

    logging.info = info


def lines() -> list[dict]:
    """The log's lines among events, in order."""
    return [entry[1] for entry in events if entry[0] == "log"]


def announced_first(entries: list[tuple]) -> bool:
    """Whether every call of the game among entries comes after the line that names it, with no other call between:
    the last line before a crash names the call that crashed."""
    named = None
    for entry in entries:
        if entry[0] == "log":
            named = entry[1].get("call")
        elif entry[0] != named:
            return False
    return True


def free(target: Any) -> None:
    """The game no longer holds target: sdk_stubs.FakeWeak gives None for it."""
    object.__setattr__(target, "freed", True)


class DefPtr:
    """Stands for unrealsdk.unreal.FGbxDefPtr built with a name and the game's definition type."""

    def __init__(self, name: str, kind: Any) -> None:
        self.name, self.kind = name, kind


class Root:
    """A spawner's root, static until made movable; one that stays static when told."""

    def __init__(self, owner: str, stays: bool = False) -> None:
        self.owner, self.Mobility, self.stays = owner, 0, stays

    def SetMobility(self, value: int) -> None:
        events.append(("SetMobility", self.owner, value))
        if not self.stays:
            self.Mobility = value


class Component:
    """A spawner's component: whether its enemy died, how many are alive, and the calls of a hand, those named in fails
    refused. An Exception held as died or alive is raised when read."""

    def __init__(self, owner: str) -> None:
        self.owner, self.died, self.alive, self.fails = owner, True, 0, set()
        self.SpawnDetails = types.SimpleNamespace(bCritical=False, bOverrideCritical=False)

    def _read(self, name: str, kind: int, value: Any) -> Any:
        events.append((name, self.owner, kind))
        if isinstance(value, Exception):
            raise value
        return value

    def _call(self, name: str, *args: Any) -> None:
        events.append((name, self.owner, *args))
        if name in self.fails:
            raise RuntimeError("refused")

    def HaveAllDied(self, kind: int) -> Any:
        return self._read("HaveAllDied", kind, self.died)

    def GetNumAliveActors(self, kind: int) -> Any:
        return self._read("GetNumAliveActors", kind, self.alive)

    def SetSpawnerEnabled(self, on: bool) -> None:
        self._call("SetSpawnerEnabled", on)

    def PushActorDef(self, reason: str, reference: DefPtr, destroy: bool) -> None:
        self._call("PushActorDef", reason, reference, destroy)

    def ResetSpawner(self, now: bool) -> None:
        self._call("ResetSpawner", now)


class Spawner:
    """A spawner as the game spawns it, where it was asked. sticks: it does not move when told; off_cm: it lands that
    far beside the place asked."""

    count = 0

    def __init__(self, where: Any = None, name: str | None = None) -> None:
        Spawner.count += 1
        self.Name = name or f"OakSpawner_21470000{Spawner.count:02d}"
        self.RootComponent, self.SpawnerComponent = Root(self.Name), Component(self.Name)
        self.at = (0.0, 0.0, 0.0) if where is None else (where.Translation.X, where.Translation.Y, where.Translation.Z)
        self.where, self.sticks, self.off_cm = where, False, 0.0

    def K2_SetActorLocation(self, target: Any, sweep: bool, hit: Any, teleport: bool) -> tuple:
        events.append(("K2_SetActorLocation", self.Name, sweep, getattr(hit, "struct_name", None), teleport))
        if self.RootComponent.Mobility == 2 and not self.sticks:
            self.at = (target.X + self.off_cm, target.Y, target.Z)
        return True, hit

    def K2_GetActorLocation(self) -> Any:
        return vector(*self.at)


class Zone:
    """A GbxTerritoryComponent owned by a spawner: its path, its centre and its combat radius."""

    def __init__(self, owner: Any, x: float = -4000.0) -> None:
        self.Outer, self.x = owner, x
        self.settings = types.SimpleNamespace(CombatTerritory=types.SimpleNamespace(Radius=1500.0))

    def _path_name(self) -> str:
        return f"/Game/Maps/WorldLevels/World_P.World_P:PersistentLevel.{self.Outer.Name}.Territory"

    def K2_GetComponentLocation(self) -> Any:
        return vector(self.x, 0.0, 0.0)


class Statics:
    """GameplayStatics as it spawns: begun where asked, then finished, either refused when told. With zones, each
    spawner made gets its own zone there, as the game's spawners own one."""

    def __init__(self, zones: list | None = None) -> None:
        self.zones, self.refuse_begin, self.refuse_finish = zones, False, False

    def BeginDeferredActorSpawnFromClass(self, context: Any, cls: Any, where: Any, collision: int, owner: Any,
                                         scale: int) -> Any:
        events.append(("BeginDeferredActorSpawnFromClass", context, cls, collision, owner, scale))
        if self.refuse_begin:
            return None
        spawner = Spawner(where)
        if self.zones is not None:
            self.zones.append(Zone(spawner, spawner.at[0]))
        return spawner, None

    def FinishSpawningActor(self, spawner: Any, where: Any, scale: int) -> Any:
        events.append(("FinishSpawningActor", spawner.Name, scale))
        if self.refuse_finish:
            raise RuntimeError("refused")
        return spawner


class Library:
    """The game's library of definitions: its enemy list is names; None gives nothing, an Exception is raised."""

    def __init__(self, names: Any) -> None:
        self.names = names

    def GetEnemiesActorDefStrings(self) -> Any:
        events.append(("GetEnemiesActorDefStrings",))
        if isinstance(self.names, Exception):
            raise self.names
        return self.names


def give_kit(state: dict, statics: Statics, names: Any) -> tuple:
    """The game's kit for making camps put in the fake SDK: its definition type, the spawner class, the statics and the
    library of definitions. Gives back the definition type, the spawner class and the library."""
    definition_type, spawner_class, library = object(), object(), Library(names)
    state["objects"][camp_kit.DEF_TYPE] = definition_type
    state["classes"][camp_kit.SPAWNER_CLASS] = spawner_class
    state["classes"][camp_kit.STATICS] = types.SimpleNamespace(ClassDefaultObject=statics)
    state["classes"][camp_kit.DEFS_LIBRARY] = types.SimpleNamespace(ClassDefaultObject=library)
    return definition_type, spawner_class, library


class Ground:
    """ground.py's trace: the ground 5 m under each point asked, but water, nothing or a character at the asks named by
    number."""

    def __init__(self, water: tuple = (), no_ground: tuple = (), not_world: tuple = ()) -> None:
        self.asked: list[tuple] = []
        self.water, self.no_ground, self.not_world = set(water), set(no_ground), set(not_world)

    def ground(self, name: str, mover: Any, point: tuple, up_cm: float, down_cm: float) -> tuple:
        self.asked.append((name, mover, point, up_cm, down_cm))
        index = len(self.asked) - 1
        if index in self.water:
            return "water", None, "WaterBodyOcean"
        if index in self.no_ground:
            return "no_ground", None, None
        if index in self.not_world:
            return "not_world", None, "PersistentLevel.Char_BatRanged_1.CollisionBubble"
        return "found", (point[0], point[1], point[2] - 500.0), "Landscape"


class Settings:
    """The world's settings: each write recorded as (field, value), all refused once refuses is set."""

    def __init__(self, off: bool = False, refuses: bool = False) -> None:
        for name, value in (("Name", "OakWorldSettings_0"), ("bDisableSpawnBudget", off), ("refuses", refuses)):
            object.__setattr__(self, name, value)

    def __setattr__(self, name: str, value: Any) -> None:
        events.append((name, value))
        if self.refuses:
            raise RuntimeError("read only")
        object.__setattr__(self, name, value)


def play(settings: Any) -> None:
    """The world in play holds settings, None for a world without any."""
    sys.modules["mods_base"].ENGINE = types.SimpleNamespace(GameViewport=types.SimpleNamespace(
        World=types.SimpleNamespace(PersistentLevel=types.SimpleNamespace(WorldSettings=settings))))
