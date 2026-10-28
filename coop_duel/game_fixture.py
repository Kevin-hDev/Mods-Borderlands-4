"""A fake co-op game for Co-op Duel's tests, installed over sdk_stubs: the world and its player list (each player's
PlayerState, his character or the vehicle he drives, none while he is away), each player's character (its role, down
state, damage switch, countdown pauses), the team library with its attitudes, the health library, the screen subsystem
the message goes on, and the player's controller. Built from the duel trials' own fakes (docs/duel/sondes/
test_duel_up.py), each answer shaped as the game gave it in the trials' logs."""

import sys
from types import SimpleNamespace
from typing import Any

import unrealsdk

AUTHORITY, PROXY = "ROLE_Authority", "ROLE_AutonomousProxy"
TEAM_KIND = 15


class Handle:
    def __init__(self, kind: int, name: str) -> None:
        self.kind, self.name = kind, name

    def __str__(self) -> str:
        return f"FGameDataHandle({self.kind}, '{self.name}', None)"


KINDS = (Handle(12289, "HealthType_Player_Health_Flesh"), Handle(12289, "HealthType_Player_Shield_Energy"),
         Handle(12289, "HealthType_Player_Overshield"))
PLAYER = Handle(TEAM_KIND, "Team_Player")
REVIVED = SimpleNamespace(name="revived")


class State:
    """A player's PlayerState: who he is for the whole session; the game's list holds it, his character points to
    it, and it outlives his character's deaths."""

    def __init__(self, name: str, player: str) -> None:
        self.Name, self.player = name, player
        self.PawnPrivate = None

    def GetPlayerName(self) -> str:
        return self.player


class Character:
    def __init__(self, name: str, player: str, *, local: bool = False, role: str = AUTHORITY) -> None:
        self.Name, self.local, self.role = name, local, role
        self.Class = SimpleNamespace(Name="OakCharacter")
        self.CharacterMovement = SimpleNamespace(Name="CharMoveComp")
        self.HealthState = SimpleNamespace(HealthTypeStates=[SimpleNamespace(HealthType=kind) for kind in KINDS])
        self.PlayerState = State(f"PS_{name}", player)
        # A player in the game without a character yet (joining, coming back): seat() lists him without one.
        self.away = False
        self.down, self.asked, self.stops, self.pauses = False, 0, [], []
        self.bCanBeDamaged = True
        self.broken = self.stuck = False

    def GetLocalRole(self) -> str:
        return self.role

    def IsLocallyControlled(self) -> bool:
        return self.local

    def InDownState(self) -> bool:
        if self.broken:
            raise RuntimeError("unreadable")
        self.asked += 1
        return self.down

    def PauseDownStateTimer(self, paused: bool, reason: str) -> None:
        self.pauses.append((paused, reason))

    def StopDownState(self, reason: Any) -> None:
        self.stops.append(reason)
        self.down = self.down and self.stuck

    def renew_state(self) -> None:
        """A travel: the game gives the player a new PlayerState, under the same player name."""
        self.PlayerState = State(f"PS_{self.Name}_new", self.PlayerState.player)


class Vehicle:
    def __init__(self, name: str, *, local: bool = False, driver: Any = None) -> None:
        self.Name, self.local = name, local
        # Driven, the vehicle is its driver's pawn: his PlayerState stays his.
        self.PlayerState = driver.PlayerState if driver is not None else State(f"PS_{name}", "")

    def GetLocalRole(self) -> str:
        return AUTHORITY

    def IsLocallyControlled(self) -> bool:
        return self.local


class Teams:
    """GbxTeamFunctionLibrary: each actor's team, SetTeam recorded, attitudes by team; refuse names the actors whose SetTeam raises, keep_player those whose team never changes."""

    def __init__(self) -> None:
        self.ClassDefaultObject = self
        self.teams: dict[str, Handle] = {}
        self.set_calls: list[tuple[str, str]] = []
        self.refuse: set[str] = set()
        self.keep_player: set[str] = set()

    def _find(self, _name: str) -> Any:
        return SimpleNamespace(_find=lambda _parameter: SimpleNamespace(TypeHandle=TEAM_KIND))

    def GetTeam(self, actor: Any) -> Handle:
        return self.teams.get(actor.Name, PLAYER)

    def SetTeam(self, actor: Any, team: Handle) -> None:
        if actor.Name in self.refuse:
            raise RuntimeError("refused")
        self.set_calls.append((actor.Name, team.name))
        if actor.Name not in self.keep_player:
            self.teams[actor.Name] = team

    def GetAttitudeTowards(self, one: Any, other: Any) -> int:
        """As the game's table reads (docs/duel/spec-equipes.md): a team is friendly to its own members, Team_Hostile
        excepted, and hostile to any other team."""
        mine, theirs = self.GetTeam(one).name, self.GetTeam(other).name
        if mine == theirs:
            return 2 if mine == "Team_Hostile" else 0
        return 2


class Damage:
    def __init__(self) -> None:
        self.ClassDefaultObject = self
        self.refills: list[tuple] = []

    def RefillHealthPercent(self, actor: Any, kind: Handle, percent: float, max_percent: float) -> None:
        self.refills.append((actor.Name, kind.name, percent, max_percent))


class Screen:
    """GameViewportSubsystem: the message's widgets added and taken off."""

    def __init__(self) -> None:
        self.Name = "GameViewportSubsystem_0"
        self.added: list[Any] = []

    def AddWidget(self, holder: Any, _slot: Any) -> bool:
        self.added.append(holder)
        holder.on_screen = True
        return True


class World:
    """A world, held weakly by the duel as the game's is."""

    def __init__(self, players: list) -> None:
        self.GameState = SimpleNamespace(PlayerArray=players)


class Game:
    def __init__(self) -> None:
        self.teams, self.damage, self.screen = Teams(), Damage(), Screen()
        self.world = World([])
        self.pc = SimpleNamespace(Name="PC")

    def seat(self, *pawns: Any) -> None:
        """The game's player list made of these pawns' PlayerStates, each pointing to its pawn, none for one away."""
        states = []
        for pawn in pawns:
            state = pawn.PlayerState
            state.PawnPrivate = None if getattr(pawn, "away", False) else pawn
            states.append(state)
        self.world.GameState.PlayerArray = states

    def travel(self) -> None:
        self.world = World(self.world.GameState.PlayerArray)
        sys.modules["mods_base"].ENGINE.GameViewport.World = self.world


def install(state: dict) -> Game:
    game = Game()
    libraries = {"GbxTeamFunctionLibrary": game.teams, "DamageStatics": game.damage}
    enums = {"ENetRole": SimpleNamespace(ROLE_Authority=AUTHORITY),
             "EExitDownStateReason": SimpleNamespace(revived=REVIVED)}

    def find_class(name: str) -> Any:
        if name not in libraries:
            raise ValueError(f"no class {name}")
        return libraries[name]

    unrealsdk.find_class = find_class
    unrealsdk.find_enum = lambda name: enums[name] if name in enums else _Enum(name)
    unrealsdk.find_all = lambda name: [game.screen] if name == "GameViewportSubsystem" else []
    unrealsdk.unreal.FGameDataHandle = Handle
    mods_base = sys.modules["mods_base"]
    mods_base.ENGINE = SimpleNamespace(GameViewport=SimpleNamespace(World=game.world))
    mods_base.get_pc = lambda **_kwargs: game.pc
    state["game"] = game
    return game


class _Enum:
    """Any other engine enum: each member read as "Enum.member"."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __getattr__(self, member: str) -> str:
        if member.startswith("__"):
            raise AttributeError(member)
        return f"{self.name}.{member}"


def duel_lines(state: dict) -> list[dict]:
    """The mod's log lines, read back as their JSON."""
    import json
    prefix = "[Co-op Duel] "
    return [json.loads(line[len(prefix):]) for line in state["logs"]
            if line.startswith(prefix) and line[len(prefix):].startswith("{")]
