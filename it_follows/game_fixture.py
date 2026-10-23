"""A fake game for It Follows' whole run (test_run.py): the hunter and his controller, enemies with their zones and
camps, the libraries of the game the run calls (targeting, brain, teams, traces, statics, the enemy list), the world's
settings, players and clock, and the screen the bar is put on (bar_fixture.py).

Taken from the move trial's test (docs/RUN/sondes/test_run_move_trial.py), which ran the trials' probes in the same
fake game. The camps the mod makes are made for real here: a spawner handed a definition gives birth to an enemy of
that kind beside it, as the game does, which the census then finds like any other.
"""

import math
import sys
import types
from typing import Any

import bar_fixture
from sdk_stubs import FakeCharacter, FakeGbxDefPtr, FakePawn, FakeStruct, spawn_details, vector

# EComponentMobility.Movable, ESpawnedActorType.InternalAndExternal.
MOVABLE, ALL_SPAWNED = 2, 2
DEF_TYPE = "/Script/GbxSpawn.GbxActorDef"


class Game:
    """Everything the fake game holds, and what was called on it: calls lists (call, name) in order."""

    def __init__(self, state: dict) -> None:
        self.state = state
        self.calls: list[tuple] = []
        self.world_clock = [0.0]
        self.imposed: dict[int, Any] = {}
        self.aims: dict[int, Any] = {}
        self.addresses = iter(range(100, 1_000_000))
        self.enemies: list[Any] = []
        self.zones: list[Any] = []
        self.spawners_made: list[Any] = []
        self.blocks: dict[int, Any] = {}
        # Every zone refuses to move while this is set; the game refuses to make a spawner while refuse_spawn is.
        self.zones_stuck = self.refuse_spawn = False
        self.screen = bar_fixture.Fixture(state)
        self.world_settings = types.SimpleNamespace(Name="OakWorldSettings_0", bDisableSpawnBudget=False)
        self.players = [object()]
        self.world = types.SimpleNamespace(
            Name="World_P", freed=False, PersistentLevel=types.SimpleNamespace(WorldSettings=self.world_settings),
            GameState=types.SimpleNamespace(PlayerArray=self.players))
        sys.modules["mods_base"].ENGINE.GameViewport.World = self.world
        self.hunter = self._hunter()
        self.pc = types.SimpleNamespace(Name="OakPlayerController_0", OakCharacter=self.hunter, freed=False,
                                        GetControlRotation=lambda: types.SimpleNamespace(Yaw=self.view_yaw))
        self.view_yaw = 0.0
        state["pc"] = self.pc
        state["all"]["OakCharacter"] = [self.hunter]
        state["all"]["GbxTerritoryComponent"] = self.zones
        self._libraries()
        sys.modules["unrealsdk"].unreal.WrappedStruct = self.make_block

    def make_block(self, function: Any, **fields: Any) -> Any:
        """A walk's parameter block, which the fake process_event finds by its address, as the SDK's WrappedStruct."""
        block = Block(function, **fields)
        self.blocks[id(block)] = block
        return block

    def process_event(self, obj: int, func: int, params: int) -> None:
        """AIScriptedMove run on the block at params, as the game runs it: the walk starts, Start in its Exec."""
        block = self.blocks[params]
        self.calls.append(("walk", block.AIActor.Name))
        block.Exec = 0

    def end_walks(self) -> None:
        """The game ends every walk given: Failed (2) in each block's Exec, as trial 6d read it."""
        for block in self.blocks.values():
            block.Exec = 2

    def _hunter(self) -> Any:
        hunter = FakeCharacter()
        hunter.Name, hunter.freed, hunter.RootComponent = "OakCharacter_2147480393", False, object()
        hunter._get_address = lambda: 1
        hunter.HealthState = types.SimpleNamespace(bCurrentlyDead=False)
        return hunter

    def zone(self, x: float, name: str, spawner: Any = None) -> Any:
        """A zone at x, part of a camp's spawner 1 m beside it (made here unless given)."""
        zone = Zone(self, x, name, spawner if spawner is not None else Spawner(self, name, x + 100.0))
        self.zones.append(zone)
        return zone

    def enemy(self, name: str, x: float, definition: str, zone: Any, y: float = 0.0) -> Any:
        """An enemy standing at (x, y), holding zone, alive and walking, in the bandits' team."""
        pawn = FakePawn(name, vector(x, y, 0.0), speed=650.0, fields={
            "HealthState": types.SimpleNamespace(bCurrentlyDead=False),
            "GbxActorData": FakeStruct({"GbxActorDef": FakeGbxDefPtr(definition)})})
        address = next(self.addresses)
        pawn.freed, pawn.zone, pawn.home, pawn.RootComponent = False, zone, zone, object()
        pawn.team = BANDITS
        pawn._get_address = lambda: address
        pawn.GetTerritory = lambda: pawn.zone
        movement = pawn.CharacterMovement
        movement.MaxGroundSpeedScale = types.SimpleNamespace(Value=1.0)
        movement.GetMaxSpeed = lambda: 583.0 * movement.MaxGroundSpeedScale.Value
        movement.fields["MovementMode"] = "<EMovementMode.MOVE_NavWalking: 2>"
        pawn.CapsuleComponent = types.SimpleNamespace(GetScaledCapsuleHalfHeight=lambda: 80.0)

        def teleport_to(*, DestLocation: Any, DestRotation: Any) -> bool:
            self.calls.append(("teleport", name))
            pawn.location = vector(DestLocation.X, DestLocation.Y, DestLocation.Z)
            return True

        def set_territory(new: Any) -> None:
            self.calls.append(("give_back" if new is pawn.home else "lend", name))
            pawn.zone = new

        pawn.K2_TeleportTo, pawn.SetTerritory = teleport_to, set_territory
        self.enemies.append(pawn)
        self.state["all"]["OakCharacter"].append(pawn)
        return pawn

    def kill(self, pawn: Any) -> None:
        pawn.HealthState.bCurrentlyDead = True

    def _libraries(self) -> None:
        classes, game = self.state["classes"], self

        def set_scripted(AIActor: Any, TargetActor: Any, bApplyRestrictions: bool) -> None:
            game.calls.append(("set_target", AIActor.Name))
            game.imposed[AIActor._get_address()] = TargetActor

        def clear_scripted(AIActor: Any) -> None:
            game.calls.append(("clear_target", AIActor.Name))
            game.imposed.pop(AIActor._get_address(), None)

        classes["GbxTargetingFunctionLibrary"] = types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
            GetPrimaryTarget=lambda AIActor: game.aims.get(AIActor._get_address(), game.hunter),
            AIGetScriptedTarget=lambda AIActor: game.imposed.get(AIActor._get_address()),
            AISetScriptedTarget=set_scripted, AIClearScriptedTarget=clear_scripted))

        def abort(*, AIActor: Any, bStopImmediately: bool) -> None:
            game.calls.append(("abort", AIActor.Name))

        classes["GbxBrainFunctionLibrary"] = types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
            _get_address=lambda: 0x1000, AbortScriptedBrainTask=abort,
            AIScriptedMove=types.SimpleNamespace(func=types.SimpleNamespace(_get_address=lambda: 0x2000))))

        def line_trace(context: Any, start: Any, end: Any, *rest: Any) -> tuple:
            met = types.SimpleNamespace(ImpactPoint=vector(start.X, start.Y, 0.0),
                                        Component=types.SimpleNamespace(_path_name=lambda: "Landscape"),
                                        PhysMaterial=None)
            return end.Z <= 0.0 <= start.Z, rest[2], met

        classes["KismetSystemLibrary"] = types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
            LineTraceSingle=line_trace))

        def set_team(actor: Any, team: Any) -> None:
            game.calls.append(("set_team", actor.Name, team.name))
            actor.team = team

        classes["GbxTeamFunctionLibrary"] = types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
            GetTeam=lambda actor: actor.team, SetTeam=set_team))
        classes["GameplayStatics"] = types.SimpleNamespace(ClassDefaultObject=Statics(self))
        classes["OakSpawner"] = types.SimpleNamespace(Name="OakSpawner")
        for name in ("OakCharacter", "Spawner"):
            classes[name] = types.SimpleNamespace(Name=name)
        classes["GbxActorDefBlueprintFunctionLibrary"] = types.SimpleNamespace(
            ClassDefaultObject=types.SimpleNamespace(GetEnemiesActorDefStrings=lambda: list(KNOWN_KINDS)))
        self.state["objects"][DEF_TYPE] = types.SimpleNamespace(Name="GbxActorDef")


class Block:
    """Stands for the SDK's WrappedStruct of a function's parameters, each field an attribute that can be written."""

    def __init__(self, function: Any, **fields: Any) -> None:
        self.function = function
        for name, value in fields.items():
            setattr(self, name, value)

    def _get_address(self) -> int:
        return id(self)


class DefPtr:
    """Stands for unrealsdk.unreal.FGbxDefPtr built with a name and the game's definition type, as camps.py builds
    it."""

    def __init__(self, name: str, kind: Any) -> None:
        self.name, self.kind = name, kind


class TeamHandle:
    """Stands for the game's FGameDataHandle, shown as the SDK shows it."""

    def __init__(self, number: int, name: str) -> None:
        self.number, self.name = number, name

    def __str__(self) -> str:
        return f"FGameDataHandle({self.number}, '{self.name}', None)"


BANDITS, ORDER = TeamHandle(15, "Team_Bandit"), TeamHandle(16, "Team_Order")
KNOWN_KINDS = ("Char_PsychoBasic_Male", "Char_GunToterPistol_Male", "Char_CatAdult", "Char_BatBasic")


class Root:
    """A spawner's root, static as placed in the level until made movable."""

    def __init__(self, mobility: int = 0) -> None:
        self.Mobility = mobility

    def SetMobility(self, value: int) -> None:
        self.Mobility = value


class Spawner:
    """A camp: the spawner a zone is part of; it moves only once its root is movable. Handed a definition and started
    again, it gives birth to one enemy of that kind beside it, as the game does."""

    def __init__(self, game: Game, name: str, x: float, y: float = 100.0, mobility: int = 0) -> None:
        self.game, self.Name, self.home = game, name, (x, y, 0.0)
        self.x, self.y, self.z, self.freed = x, y, 0.0, False
        self.RootComponent = Root(mobility)
        self.SpawnerComponent = SpawnerComponent(self)

    def K2_GetActorLocation(self) -> Any:
        return vector(self.x, self.y, self.z)

    def K2_SetActorLocation(self, *args: Any, **fields: Any) -> tuple:
        where = fields.get("NewLocation", args[0] if args else None)
        if self.RootComponent.Mobility == MOVABLE:
            self.x, self.y, self.z = where.X, where.Y, where.Z
        return (True, None)


class SpawnerComponent:
    def __init__(self, spawner: Spawner) -> None:
        self.spawner = spawner
        self.SpawnDetails = spawn_details()
        self.pushed: str | None = None
        self.child: Any = None
        self.births = 0

    def SetSpawnerEnabled(self, on: bool) -> None:
        self.spawner.game.calls.append(("enable", self.spawner.Name, on))

    def PushActorDef(self, reason: str, reference: Any, destroy: bool) -> None:
        self.pushed = getattr(reference, "name", None) or getattr(reference, "_name", None)

    def ResetSpawner(self, now: bool) -> None:
        if self.pushed is None:
            return
        game, spawner = self.spawner.game, self.spawner
        self.births += 1
        zone = next((zone for zone in game.zones if zone.Outer is spawner), None)
        self.child = game.enemy(f"{self.pushed}_{spawner.Name}_{self.births}", spawner.x + 50.0, self.pushed,
                                zone, spawner.y)

    def HaveAllDied(self, kind: int) -> bool:
        child = self.child
        return child is None or child.freed or child.HealthState.bCurrentlyDead is True

    def GetNumAliveActors(self, kind: int) -> int:
        return 0 if self.HaveAllDied(kind) else 1


class Zone:
    """A combat zone at x, part of its camp's spawner; a combat radius of 30 m."""

    def __init__(self, game: Game, x: float, name: str, spawner: Spawner) -> None:
        self.game, self.x, self.y, self.z, self.freed = game, x, 0.0, 0.0, False
        self.path = f"/Game/Maps/WorldLevels/World_P.World_P:PersistentLevel.{name}.Territory"
        self.settings = types.SimpleNamespace(CombatTerritory=types.SimpleNamespace(Radius=3000.0))
        self.Mobility = "EComponentMobility.Movable"
        self.Outer = spawner

    def _path_name(self) -> str:
        return self.path

    def K2_GetComponentLocation(self) -> Any:
        return vector(self.x, self.y, self.z)

    def K2_SetWorldLocation(self, *, NewLocation: Any, bSweep: bool, SweepHitResult: Any, bTeleport: bool) -> tuple:
        if not self.game.zones_stuck:
            self.x, self.y, self.z = NewLocation.X, NewLocation.Y, NewLocation.Z
        return (True, SweepHitResult)


class Statics:
    """GameplayStatics: the world's time, the actors of a class as find_all reads them, and the spawners the mod
    makes, a zone made with each."""

    def __init__(self, game: Game) -> None:
        self.game = game

    def GetTimeSeconds(self, context: Any) -> float:
        return self.game.world_clock[0]

    def GetAllActorsOfClass(self, *, WorldContextObject: Any, ActorClass: Any, OutActors: list) -> tuple:
        return ..., list(self.game.state["all"].get(ActorClass.Name, []))

    def BeginDeferredActorSpawnFromClass(self, context: Any, cls: Any, where: Any, collision: int, owner: Any,
                                         scale: int) -> tuple:
        game = self.game
        if game.refuse_spawn:
            return None, None
        name = f"OakSpawner_ItFollows_{len(game.spawners_made)}"
        point = where.Translation
        spawner = Spawner(game, name, point.X, point.Y, MOVABLE)
        spawner.z = point.Z
        game.zone(point.X, name, spawner)
        game.spawners_made.append(spawner)
        return spawner, None

    def FinishSpawningActor(self, spawner: Any, where: Any, scale: int) -> Any:
        return spawner


def metres(a: Any, b: Any) -> float:
    return math.dist((a.X, a.Y, a.Z), (b.X, b.Y, b.Z)) / 100.0
