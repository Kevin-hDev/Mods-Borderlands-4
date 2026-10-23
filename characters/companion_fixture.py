"""Fakes of the game for the tests of the companions' follow and team (characters/companions/follow.py, team.py):
the hunter, the companions and their enemies, each companion's zone owned by its spawner, the stance, attitude, hit
reaction and attribute libraries, and the package's parts the follow uses, each call recorded in calls. Taken from the
trials' test (docs/renforts/sondes/test_run_renforts_follow.py). Imported once sdk_stubs.install() has run;
install(state) sets the fakes in the SDK and in the follow module."""

import sys
import types
from typing import Any

import characters_fixture
from sdk_stubs import FakeObject, FakeStruct

follow = characters_fixture.part("companions.follow")
Tuning = characters_fixture.part("companions.tuning").Tuning

# What It Follows gives a companion at God, and with no level played, a card's shield on and +20 %
# (companion_levels.given, whose values test_companion_levels.py checks): God at first, as the trials since 187.
LEVELS = {"God": Tuning(12.0, 0.3, 45.0, 1.2, 45.0, "own", ("God", "normal")),
          None: Tuning(4.0, 0.3, None, 1.2, 45.0, "own", ("Bandit", "off"))}
_level = {"now": LEVELS["God"]}

# Every call the fakes took, in order: a test clears it and reads it back.
calls: list[str] = []
pushes: list[tuple] = []


def vec(x: float, y: float = 0.0, z: float = 0.0) -> Any:
    return types.SimpleNamespace(X=x, Y=y, Z=z)


class Clock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


class Zone:
    """A combat zone owned by a spawner: where it stands, its radius; stuck it does not move, broken its move raises."""

    def __init__(self, at: tuple, owner: str = "OakSpawner_1") -> None:
        self.Name, self.Class, self.owner = "Territory", types.SimpleNamespace(Name="GbxTerritoryComponent"), owner
        self.at, self.destroyed, self.stuck, self.broken = at, False, False, False
        self.settings = types.SimpleNamespace(CombatTerritory=types.SimpleNamespace(Radius=1500.0))
        self.moves: list[tuple] = []

    def GetOwner(self) -> Any:
        return types.SimpleNamespace(Name=self.owner, Class=types.SimpleNamespace(Name="OakSpawner"))

    def K2_GetComponentLocation(self) -> Any:
        return vec(*self.at)

    def K2_SetWorldLocation(self, NewLocation: Any, bSweep: bool, SweepHitResult: Any, bTeleport: bool) -> None:
        if self.broken:
            raise RuntimeError("refused")
        self.moves.append(((NewLocation.X, NewLocation.Y, NewLocation.Z), bSweep, bTeleport))
        if not self.stuck:
            self.at = (NewLocation.X, NewLocation.Y, NewLocation.Z)


class Brain:
    """It Follows' brain_walk: each walk and abort recorded."""

    def __init__(self) -> None:
        self.walks: list[tuple] = []
        self.aborts: list[Any] = []

    def walk(self, actor: Any, goal: Any, pc: Any) -> Any:
        self.walks.append((actor, goal, pc))
        return types.SimpleNamespace(Exec=0)

    def ended(self, block: Any) -> bool:
        return block.Exec != 0

    def outcome(self, block: Any) -> str:
        return f"Exec {block.Exec}"

    def abort(self, actor: Any) -> None:
        self.aborts.append(actor)


class Character(FakeObject):
    """A character of the game: its definition, its zone, alive or dead; destroyed, the game no longer holds it."""

    def GetTerritory(self) -> Any:
        return self.zone

    def K2_GetActorLocation(self) -> Any:
        return vec(*self.where)

    def K2_TeleportTo(self, DestLocation: Any, DestRotation: Any) -> bool:
        calls.append(f"teleport {self.Name} {DestLocation.X} {DestLocation.Y}")
        self.where = (DestLocation.X, DestLocation.Y, DestLocation.Z)
        return True

    def GbxDestroyActor(self, bNetForce: bool) -> None:
        """Taken out of the world, as the game does; one made to refuse raises, as a refused call would."""
        if getattr(self, "refuse_removal", False):
            raise RuntimeError("refused")
        calls.append(f"remove {self.Name} {bNetForce}")
        object.__setattr__(self, "destroyed", True)

    def AddMovementInput(self, WorldDirection: Any, ScaleValue: float, bForce: bool) -> None:
        pushes.append((self.Name, round(WorldDirection.X, 3), round(WorldDirection.Y, 3), WorldDirection.Z,
                       ScaleValue, bForce))


def character(name: str, definition: str, at: tuple, zone: Any = None, dead: bool = False,
              hostile: bool = False) -> Character:
    found = Character("OakCharacter", {
        "GbxActorData": FakeStruct({"GbxActorDef": types.SimpleNamespace(_name=definition)}),
        "HealthState": types.SimpleNamespace(bCurrentlyDead=dead)})
    for key, value in {"Name": name, "zone": zone, "where": at, "hostile": hostile, "destroyed": False,
                       "CharacterMovement": types.SimpleNamespace(
                           MaxGroundSpeedScale=types.SimpleNamespace(Value=1.0)),
                       "ReplicatedStance": types.SimpleNamespace(stance=types.SimpleNamespace(
                           _name="Stance_Passive_Walk"))}.items():
        object.__setattr__(found, key, value)
    return found


class Handle:
    """The game's FGameDataHandle, as trial 138 read it written."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"FGameDataHandle(12, '{self.name}', None)"


def lock(actor: Any, reason: str, block: bool, stance: Handle) -> None:
    calls.append(f"lock {reason} {block} {stance.name}")
    actor.ReplicatedStance.stance._name = stance.name


def unlock(reason: str, actor: Any) -> None:
    calls.append(f"unlock {reason}")
    actor.ReplicatedStance.stance._name = "Stance_Passive_Walk"


def stance_for(tag: Any, actor: Any) -> tuple:
    return Handle("Stance_" + tag.TagName.rsplit(".", 1)[-1]), tag


class Pools:
    """It Follows' HealthPools: one health pool of 100 unless written, four fifths full unless the character says."""

    def most(self, actor: Any, pool: int) -> float:
        return getattr(actor, "pools", {0: 100.0}).get(pool, 0.0)

    def set_base(self, actor: Any, pool: int, base: float) -> float:
        object.__setattr__(actor, "pools", {**getattr(actor, "pools", {0: 100.0}), pool: base})
        return base

    def set_share(self, actor: Any, pool: int, wanted: float) -> None:
        calls.append(f"share {pool} {wanted}")

    def share(self, actor: Any, pool: int) -> float:
        return getattr(actor, "left", {}).get(pool, 0.8)


class Shields:
    """It Follows' ShieldPool: a shield added on pool 1, full."""

    def __init__(self, pools: Any) -> None:
        self.pools = pools

    def add(self, actor: Any, share: float) -> tuple:
        object.__setattr__(actor, "shield", 1.0)
        object.__setattr__(actor, "pools", {**getattr(actor, "pools", {0: 100.0}), 1: 125.0})
        return 1, 125.0

    def fill(self, actor: Any, pool: int) -> float:
        return actor.shield

    def refill(self, actor: Any, seconds: float) -> None:
        calls.append(f"refill {round(seconds, 2)}")


class Patch:
    """It Follows' TargetPatch, its foe imposed."""

    def __init__(self, actor: Any, foe: Any) -> None:
        self.actor, self.foe, self.applied = actor, foe, False

    def read(self) -> str:
        return "player" if self.applied else "none"

    def apply(self) -> None:
        self.applied = True
        calls.append(f"target {self.foe().Name}")

    def restore(self) -> str:
        self.applied = False
        calls.append("clear")
        return "restored"


class Radius:
    """It Follows' TerritoryRadiusPatch."""

    def __init__(self, cm: float) -> None:
        self.cm = cm

    def apply(self, zone: Any) -> float:
        self.before, zone.settings.CombatTerritory.Radius = zone.settings.CombatTerritory.Radius, self.cm
        return self.before

    def restore(self, zone: Any) -> str:
        zone.settings.CombatTerritory.Radius = self.before
        return "restored"


class Weak:
    """unrealsdk.unreal.WeakPointer: the object, or None once the game has destroyed it."""

    def __init__(self, target: Any) -> None:
        self.target = target

    def __call__(self) -> Any:
        return None if getattr(self.target, "destroyed", False) else self.target


def at_level(name: str | None) -> None:
    """What It Follows gives at that level, God, or none played, from now on (tuned)."""
    _level["now"] = LEVELS[name]


def tuned(_name: str) -> Tuning:
    """What a team of these tests gives any companion (team.Team.tuned): the level at_level set."""
    return _level["now"]


class Game:
    """The world: the hunter, the characters GetAllActorsOfClass gives, his most health (1000 / 12, so that God's
    twelve times are the 1000 a companion is given), the libraries the follow calls."""

    def __init__(self, state: dict) -> None:
        self.state = state
        self.brain = Brain()
        self.hunter = character("OakCharacter_Hunter", "Char_Hunter", (0.0, 0.0, 0.0))
        self.hunter.yaw = 0.0
        self.hunter.K2_GetActorRotation = lambda: types.SimpleNamespace(Pitch=0.0, Yaw=self.hunter.yaw, Roll=0.0)
        object.__setattr__(self.hunter, "CharacterMovement", types.SimpleNamespace(MovementMode="MOVE_Walking"))
        self.actors: list = []
        self.locks: list[tuple] = []
        state["classes"].update({
            "GameplayStatics": types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
                GetAllActorsOfClass=lambda WorldContextObject, ActorClass, OutActors: (None, list(self.actors)))),
            "OakCharacter": "OakCharacterClass",
            "GbxStanceBlueprintLibrary": types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
                GetStanceForTag=stance_for, UnlockStance=unlock)),
            "GbxNavBlueprintLibrary": types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(LockStance=lock)),
            "GbxTeamFunctionLibrary": types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
                GetAttitudeTowards=lambda player, actor: types.SimpleNamespace(
                    name="hostile" if getattr(actor, "hostile", False) else "friendly"))),
            "OakHitReactionBlueprintLibrary": types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
                LockHitReactions=lambda AIActor, type, reason, Block: self.locks.append(
                    (str(AIActor.Name), type, Block)))),
            "GbxAttributeBlueprintLibrary": types.SimpleNamespace(ClassDefaultObject=types.SimpleNamespace(
                GetValueOfAttribute=lambda name, actor, default: 1000.0 / 12
                if name == "health_resource_max_value" and actor is self.hunter else default))})
        state["pc"] = types.SimpleNamespace(Pawn=None, OakCharacter=self.hunter,
                                            GetControlRotation=lambda: types.SimpleNamespace(Yaw=0.0))
        sys.modules["unrealsdk.unreal"].WeakPointer = Weak
        follow.brain_walk = self.brain
        follow.health_pools = types.SimpleNamespace(HealthPools=Pools, types=lambda actor: getattr(
            actor, "kinds", ["HealthType_AI_Flesh"]))
        follow.shield_pool = types.SimpleNamespace(ShieldPool=Shields, SHIELD="HealthType_AI_Energy")
        follow.target = types.SimpleNamespace(imposed=Patch)
        follow.zone_radius = types.SimpleNamespace(TerritoryRadiusPatch=Radius)
        at_level("God")
        calls.clear()
        pushes.clear()

    def companion(self, number: int, at: tuple = (1000.0, 0.0, 0.0), definition: str = "Char_NPC_Abomination",
                  dead: bool = False) -> Character:
        """A companion born of spawner OakSpawner_<number>, its zone its own."""
        one = character(f"{definition}_{number}", definition, at, Zone((50000.0, 0.0, 0.0), f"OakSpawner_{number}"),
                        dead)
        self.actors.append(one)
        return one

    def enemy(self, name: str, at: tuple) -> Character:
        one = character(name, "Char_Bandit", at, hostile=True)
        self.actors.append(one)
        return one


class Births:
    """birth.Births as the team asks it: each ask makes a companion born of a new spawner, in front of the hunter."""

    def __init__(self, game: Game) -> None:
        self.game, self.asked, self.number = game, [], 100

    def ask(self, definition: str, pc: Any) -> dict:
        self.number += 1
        self.asked.append(definition)
        self.game.companion(self.number, (300.0, 0.0, 0.0), definition)
        return {"done": "asked", "spawner": f"OakSpawner_{self.number}"}
