"""One companion following the hunter and fighting at his side: the follow of docs/renforts' trials 135 to 188
(sondes/run_renforts_follow.py), its parts each in their module.

Its own combat zone set on the hunter and widened (zone.py); walked to him when it stands far, pushed to its own place
beside him for the last stretch (walk.py, push.py), its run locked while it walks and its speed bonus raised (pace.py);
teleported behind him when left too far, once he stands on ground, or when a walk is blocked (catch.py, stuck.py); the
nearest enemy imposed as its target, its walks stopped while it fights unless it stands beyond LEASH_M (fight.py); its
health a multiple of the hunter's by the level played, with a shield (tough.py, difficulty.py); its staggers locked
(calm.py). A sample each EVERY_S on the team's beat (team.py), the walk checked between samples. It ends at its death
(respawn.Fall: read dead, or downed then hidden or taken away), when it is gone, when its zone is gone or refused TRIES
moves in a row, on an error, or when the team stops; the walk is then aborted, the target cleared, its walk given back,
its speed bonus and its zone's radius written back and the zone put back. Its health and shield are left: it is the
team's own. Unless it died, the companion is then taken out of the world (leave.py, decision 59). Its start and its
end are written by report.py; the calls made at every sample are not, as It Follows writes none of those (report.py).

Its shield and its speed bonus are the ones chosen for it on the window's card (choices.Choice). Trial 190: 21 births
of 41 read no health pool at the start (tough.py, cause unknown), and went on with the game's health, no shield; the
health is tried again at the next HARDEN_TRIES samples, and the outcome written; a write that failed, too.
"""

from typing import Any, Callable

import unrealsdk
from mods_base import get_pc

from .. import brain_walk, health_pools, report, shield_pool, target, zone_radius
from . import calm, catch, choices, difficulty, fight, hunter_health, leave, pace, push, respawn, stuck, tough, walk
from . import world
from . import zone as zone_module

# Beyond this from the hunter it is walked back to him even while it fights: the fight must not leave the hunter alone.
LEASH_M = 40.0
EVERY_S = 1.0
TRIES = 3
HARDEN_TRIES = 5
MAX_TEXT = 120


def quiet(_text: str) -> None:
    """The calls made at every sample, never written (report.py)."""


def tried(make: Callable[[], Any]) -> Any:
    """What a step of the start gives, or why it failed: a step that fails is said, the follow goes on without it."""
    try:
        return make()
    except Exception as error:
        return f"failed:{type(error).__name__}:{str(error)[:MAX_TEXT]}"


def no_pool(toughened: Any) -> bool:
    """Whether the health was not written, for want of a health pool read (tough.py) or for a write that failed."""
    return (isinstance(toughened, dict) and toughened.get("health") == "no_pool") \
        or (isinstance(toughened, str) and toughened.startswith("failed:"))


class Follow:
    """One character following the hunter, sampled by beat(); finish(why) ends it once. offset: its samples' shift
    from rank 0's (team.offset), so that a team's samples do not all fall on one frame; picked: its card's choice."""

    def __init__(self, actor: Any, zone: Any, clock: Callable[[], float], rank: int, definition: str,
                 times: float | None, offset: float = 0.0, picked: choices.Choice | None = None) -> None:
        self.actor = unrealsdk.unreal.WeakPointer(actor)
        self.name, self.clock, self.rank = str(actor.Name), clock, rank
        # Told the death, with the definition and health to give the one coming back (respawn.py).
        self.definition, self.times, self.on_death = definition, times, None
        # Told any other end, with its why: the team calls it back unless it stopped (team.py).
        self.on_end: Callable[[str], None] | None = None
        # Its name in kinds.py, the team's own (team.join): the bars name it so.
        self.companion = definition
        self.picked = picked if picked is not None else choices.Choice()
        self.harden_left = 0
        self.zone = zone_module.ZoneOnHunter(zone, quiet)
        self.walker = walk.Walker(self.actor, self.name, quiet, brain_walk,
                                  push.Push(self.actor, self.name, quiet), catch.fan(rank))
        self.stuck = stuck.Stuck()
        self.fall = respawn.Fall()
        self.pace = pace.Pace(self.actor, self.name, quiet, self.picked.factor)
        self.catch = catch.CatchUp(self.actor, self.name, quiet, rank)
        pools = health_pools.HealthPools()
        self.tough = tough.Tough(self.actor, self.name, quiet, pools, shield_pool.ShieldPool(pools),
                                 health_pools.types, shield_pool.SHIELD)
        self.fight = fight.Fight(self.actor, self.name, quiet, world, target, unrealsdk.unreal.WeakPointer)
        self.started = clock()
        self.next = self.started + EVERY_S + offset
        self.between_at = self.started
        self.samples = 0
        self.done = False

    def begin(self, pc: Any) -> dict:
        """Its zone widened, its speed raised, its health and shield set by the level played, its staggers locked:
        what each did, or why it failed."""
        actor = self.actor()
        toughened = self._harden(pc)
        self.harden_left = HARDEN_TRIES if no_pool(toughened) else 0
        return {"radius": self.zone.widen(zone_radius), "boost": self.pace.boost(), "tough": toughened,
                "calm": tried(lambda: calm.calm(actor, quiet))}

    def _harden(self, pc: Any) -> Any:
        return tried(lambda: self.tough.harden(hunter_health.most(pc), difficulty.played(), self.times,
                                               self.picked.shielded))

    def harden_again(self, pc: Any) -> None:
        """Its health tried again, the start having read no health pool; the outcome written once it is no longer
        that, or at the last try."""
        self.harden_left -= 1
        toughened = self._harden(pc)
        if no_pool(toughened) and self.harden_left > 0:
            return
        report.note("companion_tough", character=self.name, tries=HARDEN_TRIES - self.harden_left, tough=toughened)
        self.harden_left = 0

    def beat(self) -> None:
        if self.done:
            return
        moment = self.clock()
        if moment < self.next:
            if self.walker.walking and moment >= self.between_at:
                pushed = self.walker.push.active
                self.between_at = moment + (push.PUSH_S if pushed else walk.ARRIVAL_EVERY_S)
                self.guarded(self.between)
            return
        self.next = moment + EVERY_S
        self.guarded(lambda: self.sample(moment))

    def guarded(self, step: Callable[[], None]) -> None:
        """A step of the follow; one that fails is said and ends the follow."""
        try:
            step()
        except Exception as error:
            report.note("companion_error", character=self.name, error=f"{type(error).__name__}:{str(error)[:MAX_TEXT]}")
            self.finish("error")

    def between(self) -> None:
        """Between samples, while it walks: pushed toward its place every PUSH_S, or its walk checked every
        ARRIVAL_EVERY_S, aborted as soon as it is within ARRIVAL_M of the hunter (walk.py). Gone, it reads no place:
        the next sample ends the follow."""
        here, at = world.place(world.hunter(get_pc())), world.place(self.actor())
        to_hunter = world.metres(at, here)
        if self.walker.push.active:
            self.walker.step(here, at, to_hunter)
        else:
            self.walker.arrive(to_hunter)

    def sample(self, now: float) -> None:
        self.samples += 1
        actor = self.actor()
        if self.zone.zone() is None:
            return self.finish("zone_gone")
        # Each read says None of a character gone (world.py, tough.py).
        end = self.fall.end(actor, world.dead(actor), self.tough.health(), world.place(actor))
        if end is not None:
            return self.finish(end)
        pc = get_pc()
        if self.harden_left > 0:
            self.harden_again(pc)
        goal = world.hunter(pc)
        here = world.place(goal)
        self.zone.follow(here, now)
        at = world.place(actor)
        actor_m = world.metres(at, here)
        # His character's mode even while he drives: it says MOVE_None in the saddle, the vehicle has none to read.
        character = getattr(pc, "OakCharacter", None) or goal
        mode, yaw = world.mode(character), catch.facing(goal)
        self.fight.keep(fight.characters(pc), character, here, at)
        caught = self.catch.keep(here, yaw, mode, actor_m, now, self.fight.fighting)
        if caught == "near":
            caught = self.stuck.unstick(self.walker.live(), self.fight.fighting, at, now,
                                        lambda: self.catch.unstick(here, yaw, mode, now))
        if caught.endswith("teleported"):
            actor_m = world.metres(world.place(actor), here)
        if self.fight.fighting and actor_m is not None and actor_m <= LEASH_M:
            self.walker.stop()
        else:
            self.walker.keep(actor_m, goal, pc, now, here, at)
        self.pace.keep(self.walker.walking, actor_m, self.fight.fighting)
        self.tough.keep(now)
        if self.zone.in_row >= TRIES:
            return self.finish("zone_refused")

    def finish(self, why: str) -> None:
        """Everything given back, each part on its own so that one failing leaves the others; the companion taken
        out of the world unless it died (leave.py); then the team told its death (on_death) or its other end
        (on_end)."""
        if self.done:
            return
        self.done = True
        given = {"walk_stop": tried(self.walker.stop), "target_back": tried(self.fight.release),
                 "pace_back": tried(self.pace.put_back), "radius_back": tried(self.zone.narrow),
                 "zone_back": tried(self.zone.put_back)}
        removed = None if why == "character_dead" else leave.leave(self.actor(), self.name, report.announce)
        report.note("companion_end", why=why, character=self.name, seconds=round(self.clock() - self.started),
                    walks=self.walker.walks, teleports=self.catch.teleports, targets=self.fight.imposed,
                    refills=self.tough.refills, **given, removed=removed)
        if why == "character_dead":
            if self.on_death is not None:
                self.on_death(self.definition, self.times)
        elif self.on_end is not None:
            self.on_end(why)
