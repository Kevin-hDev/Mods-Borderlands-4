"""It Follows' own camps (decisions 41 and 45): the spawners it makes during a game, found free again, moved and
handed one enemy each, for the copies at the start and the killed coming back; and, made apart, the camp whose zone is
lent to the horde. What the game gives for making them is looked up by camp_kit.py.

The recipe is the domed arena's, its calls and their order verified in game (docs/spawn-boss: closed dome trials 5 and
6, boss bar trials 19 to 21, lots trials 1 to 3), then in RUN's trials 8c to 8e. An enemy is born of a spawner, never
placed straight: placed straight, bandits crashed the game after their deaths. A spawner is never destroyed, for
destroying an actor the mod spawned crashed the game: it is held weakly and handed a new enemy once
HaveAllDied(InternalAndExternal) says its enemy died, or once STUCK_S passed with none of its enemies alive. Its
requests are made critical: without it, of 50 asked, 29 lived at once at most. The definition is pushed typed with the
game's own definition type: untyped, such a reference crashed the game. A spawner whose root is static is made movable
before it is moved, or the game refuses the move without an error. Each call is announced before it is made: the SDK
log outlives a crash.
"""

import math
import time
from typing import Any, Callable, NamedTuple

import unrealsdk
from unrealsdk.unreal import FGbxDefPtr, WeakPointer

from .camp_kit import Kit, enemy_list, look_up

# PushActorDef's reason, a name the game keeps with the definition pushed.
REASON = "RUN"
# ESpawnedActorType.InternalAndExternal, read in game (boss bar trial 21): External said "all died" with a boss alive.
ALL_SPAWNED = 2
# ESpawnActorCollisionHandlingMethod.AlwaysSpawn and ESpawnActorScaleMethod.MultiplyWithRoot, as the domed arena's.
ALWAYS_SPAWN = 1
MULTIPLY_WITH_ROOT = 1
# A camp handed an enemy this recently is busy whatever HaveAllDied says, its enemy maybe not born yet: in trial 8b, 192
# of the 194 enemies born of a camp taken again joined the horde within 6 s.
PENDING_S = 10.0
# A camp handed an enemy this long ago with none of its enemies alive is taken back, as free: in trial 14, 141 of the
# 200 camps were handed an enemy that was never born, or was gone, while HaveAllDied never said it died; they were held
# from the moment many enemies were asked at one place, never freed once the hunter drove away, and the killed could no
# longer come back. Three times PENDING_S: an enemy is born within 6 s of its camp's hand (trial 8b).
STUCK_S = 30.0
# EComponentMobility.Movable; a camp farther than MOVED_M from where it was sent has not moved.
MOVABLE = 2
MOVED_M = 1.0
# hand's steps up to PushActorDef: refused there, no enemy can come of the camp, which is free again.
PUSHED_STEP = 1


class Survey(NamedTuple):
    # (Camp, spawner) of each free camp, oldest first.
    free: list
    # Those whose enemy is alive, or that could not be asked.
    busy: int
    # Those handed an enemy less than PENDING_S ago.
    pending: int
    # Of the free camps, those taken back for holding no enemy alive STUCK_S after their hand.
    stuck: int = 0


class Camp:
    """A camp It Follows made, held weakly; when it was last handed an enemy, and of which kind."""

    __slots__ = ("pointer", "handed_at", "kind")

    def __init__(self, spawner: Any) -> None:
        self.pointer, self.handed_at, self.kind = WeakPointer(spawner), None, ""


def _transform(point: tuple, yaw: float) -> Any:
    """The engine's Transform at point, turned to yaw degrees."""
    half, make = math.radians(yaw) / 2.0, unrealsdk.make_struct
    return make("Transform", Translation=make("Vector", X=point[0], Y=point[1], Z=point[2]),
                Rotation=make("Quat", X=0.0, Y=0.0, Z=math.sin(half), W=math.cos(half)),
                Scale3D=make("Vector", X=1.0, Y=1.0, Z=1.0))


def _pending(camp: Camp, now: float) -> bool:
    """Whether the camp was handed an enemy less than PENDING_S ago."""
    return camp.handed_at is not None and now - camp.handed_at < PENDING_S


def _died(spawner: Any) -> bool:
    """Whether HaveAllDied(InternalAndExternal) says the camp's enemy died, which only True says; it may raise."""
    return spawner.SpawnerComponent.HaveAllDied(ALL_SPAWNED) is True


def _stuck(camp: Camp, spawner: Any, now: float) -> bool:
    """Whether the camp was handed an enemy STUCK_S ago or more and none of its enemies is alive, read as the status has
    read it every 30 s since trial 8e; it may raise."""
    return (camp.handed_at is not None and now - camp.handed_at >= STUCK_S
            and spawner.SpawnerComponent.GetNumAliveActors(ALL_SPAWNED) == 0)


class Camps:
    """It Follows' camps, at most most of them, one enemy each at a time; the lent zone's camp is made apart and never
    handed an enemy. One Camps serves every run of a game session (the run keeps it): a Camps for each run would leave
    up to most more camps in the world at each run, never destroyed. announce(call, log, **fields) notes a call before
    it is made; no field is named event, run, call or log, the names a line of report.py holds itself: in trial 8c a
    field named like the line's own kind raised before every hand, and no enemy was ever asked."""

    def __init__(self, announce: Callable[..., None], most: int) -> None:
        self.announce, self.most = announce, most
        self.pool: list[Camp] = []
        # The names of the camps put to work, the lent zones' and those handed an enemy (copies.py), kept from one
        # run to the next as the pool is: a camp of an earlier run whose enemy still lives is still the mod's.
        self.mine: set[str] = set()
        # The definitions of the game's enemy list, read once; None until then.
        self.known: set[str] | None = None

    def _called(self, call: str, make: Callable[[], Any], **fields: Any) -> tuple[bool, Any]:
        """make's answer, announced first; (False, why) when it raised."""
        self.announce(call, **fields)
        try:
            return True, make()
        except Exception as error:
            return False, f"{call}:{type(error).__name__}"

    def kit(self) -> Kit | str:
        """The kit, and the game's enemy list read the first time; or why not."""
        kit = look_up(self._called)
        if isinstance(kit, str) or self.known is not None:
            return kit
        known = enemy_list(self._called)
        if isinstance(known, str):
            return known
        self.known = known
        return kit

    def knows(self, kind: str) -> bool:
        return self.known is not None and kind in self.known

    def made(self, kit: Kit, point: tuple, yaw: float, character: Any) -> Any:
        """A new spawner at point, facing yaw, kept out of the pool; None at the game's refusal."""
        where = _transform(point, yaw)
        done, begun = self._called("BeginDeferredActorSpawnFromClass", lambda: kit.statics.
                                   BeginDeferredActorSpawnFromClass(character, kit.spawner_class, where, ALWAYS_SPAWN,
                                                                    None, MULTIPLY_WITH_ROOT))
        spawner = begun[0] if isinstance(begun, tuple) else begun
        if not done or spawner is None:
            return None
        done, finished = self._called("FinishSpawningActor", lambda: kit.statics.FinishSpawningActor(
            spawner, where, MULTIPLY_WITH_ROOT), on=spawner.Name)
        spawner = finished[0] if isinstance(finished, tuple) else finished
        return spawner if done else None

    def survey(self, log: bool = True) -> Survey:
        """The camps free, those stuck taken back among them, busy and pending; the camps the game took are
        forgotten. log: whether the calls are written down, as at each asking."""
        self.pool[:] = [camp for camp in self.pool if camp.pointer() is not None]
        free, busy, pending, stuck, now = [], 0, 0, 0, time.monotonic()
        self.announce("HaveAllDied", log=log, camps=len(self.pool))
        for camp in self.pool:
            spawner = camp.pointer()
            if spawner is None:
                continue
            if _pending(camp, now):
                pending += 1
                continue
            try:
                died = _died(spawner)
                taken = not died and _stuck(camp, spawner, now)
            except Exception:
                died = taken = False
            if died or taken:
                free.append((camp, spawner))
                stuck += taken
            else:
                busy += 1
        return Survey(free, busy, pending, stuck)

    def room(self, survey: Survey) -> int:
        """How many enemies can be handed a camp now: the free camps, and those still to be made under most."""
        return len(survey.free) + max(0, self.most - len(self.pool))

    def place(self, kit: Kit, free: list, point: tuple, yaw: float, character: Any) -> tuple[Camp, Any] | None:
        """A free camp taken from free and moved to point, one that does not move left aside, else a new one made
        there under most; None if neither."""
        while free:
            camp, spawner = free.pop(0)
            if self._moved(spawner, point):
                return camp, spawner
        if len(self.pool) >= self.most:
            return None
        spawner = self.made(kit, point, yaw, character)
        if spawner is None:
            return None
        camp = Camp(spawner)
        self.pool.append(camp)
        return camp, spawner

    def _moved(self, spawner: Any, point: tuple) -> bool:
        """True once the spawner stands at point, its root made movable first, teleported there without sweep."""
        root = spawner.RootComponent
        if root is None:
            return False
        if int(root.Mobility) != MOVABLE:
            self._called("SetMobility", lambda: root.SetMobility(MOVABLE), on=spawner.Name)
            if int(root.Mobility) != MOVABLE:
                return False
        target = unrealsdk.make_struct("Vector", X=point[0], Y=point[1], Z=point[2])
        if not self._called("K2_SetActorLocation", lambda: spawner.K2_SetActorLocation(
                target, False, unrealsdk.make_struct("HitResult"), True), on=spawner.Name)[0]:
            return False
        there = spawner.K2_GetActorLocation()
        return math.dist((float(there.X), float(there.Y), float(there.Z)), point) / 100.0 <= MOVED_M

    def hand(self, kit: Kit, camp: Camp, spawner: Any, kind: str) -> str | None:
        """kind's definition handed to the camp, its requests critical, started again; None once all was taken, else
        the step refused. Refused up to the push, the camp is free again; after it, it counts as busy."""
        camp.handed_at, camp.kind = time.monotonic(), kind
        component = spawner.SpawnerComponent

        def critical() -> None:
            details = component.SpawnDetails
            details.bCritical = details.bOverrideCritical = True
            component.SpawnDetails = details

        # Refused, the enemy is asked all the same, as the domed arena's were.
        self._called("SpawnDetails critical", critical, on=spawner.Name)
        reference = FGbxDefPtr(kind, kit.kind)
        steps = (("SetSpawnerEnabled", lambda: component.SetSpawnerEnabled(True)),
                 ("PushActorDef", lambda: component.PushActorDef(REASON, reference, True)),
                 ("ResetSpawner", lambda: component.ResetSpawner(True)))
        for index, (call, make) in enumerate(steps):
            done, why = self._called(call, make, on=spawner.Name, definition=kind)
            if not done:
                if index <= PUSHED_STEP:
                    camp.handed_at = None
                return why
        return None

    def status(self) -> dict:
        """How many camps hold their enemy alive, how many the game no longer holds, and of those without an enemy
        alive: pending, free, or stuck, neither free nor holding an enemy though handed one long ago (trial 8d: 80
        enemies handed to the camps never joined the horde, nor were their camps free again)."""
        counts = dict.fromkeys(("alive", "pending", "free", "stuck", "gone", "failed"), 0)
        now = time.monotonic()
        self.announce("GetNumAliveActors", log=False, camps=len(self.pool))
        self.announce("HaveAllDied", log=False, camps=len(self.pool))
        for camp in self.pool:
            spawner = camp.pointer()
            if spawner is None:
                counts["gone"] += 1
                continue
            try:
                if spawner.SpawnerComponent.GetNumAliveActors(ALL_SPAWNED) > 0:
                    counts["alive"] += 1
                elif _pending(camp, now):
                    counts["pending"] += 1
                else:
                    counts["free" if _died(spawner) else "stuck"] += 1
            except Exception:
                counts["failed"] += 1
        return {"camps": len(self.pool), **counts}
