"""A run of It Follows: its start, its sample each second, its stop (spec, sections 2 and 6; decisions 46 to 52).

Taken from the trials' move trial (docs/RUN/sondes/run_move_trial.py), without what only its records needed and
without its two phases: a run has no end of its own but its time limit. At the start, the enemies around the hunter
are read (census.py); the wave makes the camp whose zone is lent to the horde and a copy of each enemy near
(wave.py, copies.py); the camps of the enemies follow the hunter (camp_follow.py); the zone is put on him and widened
to 600 m (decision 33); each enemy is drawn (horde.py), made faster and tougher as chosen, and put in one team; the
hunter takes the damage chosen (decision 79). Each second the horde is kept, the wave held on the level's target,
the camps and the zone follow him; every few seconds the enemies around join; the time played, the kills and the
deaths are counted and shown in the bar.

A run stops on Stop, at the end of its time, when the player leaves the game (his character's weak pointer dies:
then the world is gone and the game has put everything back itself, trial 7), when the mod is disabled, when the
lent zone is gone or cannot be kept on him (hunter_zone.lost), or on an error in a sample. At the stop everything still
lent is given back, as the trials did. Unlike them, an empty horde stops nothing: the enemies come when the hunter
meets them, and a run may start with nobody around.

The second's heavy work is spread over the images after the sample (frame.Beat.defer): the pass over the horde in
parts (sweep.py, decision 107), the camps that follow the hunter, the census with its recruits, and the game's camps
each take an image of their own. In trial 16 they all fell
in one image with the sample, 77 to 89 ms with 120 enemies, the census 17 ms and the game's camps 13 ms of it, and
every 10 s both together (audit of 15 October 2026). Each re-reads the hunter, since the sample's may be gone by then.
The status line takes an image of its own too, its reads of the mod's camps measured with the rest (audit of 16
October 2026); the engine's image count is read each second for the images a second it writes (decision 102).
"""

import types
from typing import Any, Callable

import mods_base
import unrealsdk

from . import (bar, budget, camp_follow, camp_map, catch_up, census, chaser, clock, copies, damage_taken, float_watch,
               frame, game_camps, ground, horde, hunter_zone, levels, recruit, report, run_gauge, run_hardcore, speed,
               spread, stats, sweep, teams, texts, toughness, wave)
from .characters import brain_walk, reads

# Decision 33: the radius with which a Psycho followed the hunter much farther from its home (enemy research,
# session 11, verified in game).
WIDE_RADIUS_CM = 60000.0


class Run:
    """One run, from its start to its stop; end(reason) is the module's stop, which forgets it."""

    def __init__(self, settings: Any, pc: Any, player: Any, pool: Any, end: Callable[[str], None]) -> None:
        self.settings, self.pool, self.on_end = settings, pool, end
        self.level = levels.level(settings.level)
        weak = unrealsdk.unreal.WeakPointer
        self.player, self.pc = weak(player), weak(pc)
        self.horde = self.follow = self.zone = self.wave = self.beat = self.bar = self.camps = self.gauge = None
        self.hardcore = None
        self.taken = damage_taken.DamageTaken(report.announce, settings.taken)
        self.last_here: tuple | None = None
        self.said: set[str] = set()
        # The bodies the last census read, for the status line.
        self.bodies = 0

    def begin(self, now: float) -> str:
        """Everything put in place: "started", or why not, everything done so far given back."""
        player, pc = self.player(), self.pc()
        here = reads.point(player)
        report.note("starting", level=self.level.target, speed=self.settings.speed, health=self.settings.health,
                    taken=self.settings.taken,
                    duration_s=self.settings.duration_s, respawn=self.settings.respawn,
                    crowd_max=self.settings.crowd_max, manage_far=self.settings.manage_far, at=reads.spot(here))
        found, said, sighting = census.seen_around(player, in_world=True)
        # Decision 97: with the far enemies not managed, one beyond the catch-up's distance would be let go at once.
        crowd = census.everyone(found, here, self.settings.crowd_max,
                                None if self.settings.manage_far else self.level.far_m)
        # The clock first: the wave's growth counts the time played.
        self.clock = clock.Clock(pc, now)
        # A trace each, as the trials had: a trace that failed stops its owner's traces for the run, not both.
        made = copies.Copies(report.announce, self.pool, ground.GroundTrace(report.announce),
                             budget.Budget(report.announce), spread.Spread(self.level.spread))
        self.wave = wave.Wave(made, report.note, lambda: self.clock.played, self.level, self.settings.respawn,
                              self.settings.crowd_max)
        host = self.wave.start(crowd, player, pc, here)
        if host is None:
            return self._refused("no_camp")
        self.wave.saw(sighting.kept)
        self.camps = game_camps.GameCamps(report.announce, self.wave.ours)
        report.note("game_camps", **self.camps.wake(here, now, player))
        self.zone = hunter_zone.HunterZone(host, report.announce)
        places = camp_map.CampMap()
        self.follow = camp_follow.CampFollow(places, report.announce)
        self.stats = stats.Stats(reads.dead(player))
        self.stats.seen_alive(sighting.alive)
        self.recruiter = recruit.Recruiter(now)
        trace = ground.GroundTrace(report.announce)
        parts = types.SimpleNamespace(
            zone=self.zone, camp_map=places, follow=self.follow, ground=trace, wave=self.wave, stats=self.stats,
            catch=catch_up.CatchUp(report.announce, trace, self.level.behind_m, self.level.far_m,
                                   spread.Spread(self.level.spread)),
            speed=speed.SpeedBoost(report.announce, self.settings.speed), teams=teams.Teams(report.announce),
            recruiter=self.recruiter, chaser=chaser, player_ref=self.player, near_m=wave.RADIUS_M,
            crowd_max=self.settings.crowd_max, manage_far=self.settings.manage_far,
            toughness=toughness.Toughness(report.announce, report.note, self.settings.health))
        self.parts = parts
        self.hardcore = run_hardcore.RunHardcore(parts.toughness, self.taken, self.settings.health,
                                                 self.settings.taken, report.note)
        self.floating = float_watch.FloatWatch(ground.GroundTrace(report.announce), parts.catch.last.get)
        self.horde = horde.Horde(parts, report.note, report.announce)
        made.held = self._held_camps
        free = self.horde.free_of(crowd)
        self.horde.note_camps([seen for seen, _ in free])
        report.note("camps_placed", camps=len(self.follow.place(here, now)))
        try:
            placed = self.zone.place(here, now)
        except Exception as error:
            placed = f"call_failed:{type(error).__name__}"
        if placed != "moved":
            return self._refused(f"zone_{placed}")
        try:
            widened = self.zone.widen(WIDE_RADIUS_CM)["widened"]
        except Exception as error:
            widened = f"call_failed:{type(error).__name__}"
        if widened != "done":
            return self._refused(f"zone_widen_{widened}")
        drawn = self.horde.draw_all(free, player, pc, here, now)
        parts.speed.start(drawn)
        parts.toughness.start(drawn)
        parts.teams.unite(drawn)
        raised = self.taken.start(player)
        if raised:
            report.note("taken_raised", **raised)
        self.bar = bar.Bar(report.announce, self.settings.bar_points) if self.settings.bar else None
        if self.bar is not None:
            self.bar.show(pc, self._words())
        self.beat = frame.Beat(self.tick, self.on_end)
        self.sweep = sweep.Sweep(self.horde, parts, self.floating, self.beat.defer, self.player,
                                 lambda: self.pc() or mods_base.get_pc(), self._timed, frame.now)
        self.beat.start()
        self.gauge = run_gauge.Gauge(report.note, now)
        report.announce("GetFrameCount")
        self.gauge.frames(reads.frame_count(), frame.now())
        report.note("started", crowd=len(crowd), drawn=len(drawn), read=said["read"], kept=said["kept"],
                    search=said["search"])
        return "started"

    def _refused(self, why: str) -> str:
        report.note("refused", why=why)
        self.end(why)
        return why

    def _words(self) -> str:
        played = self.clock.played if getattr(self, "clock", None) is not None else 0.0
        percent = self.hardcore.percent if self.hardcore is not None else 0
        return texts.bar(self.settings.language, self.stats.kills, self.stats.deaths, len(self.horde.drawn()), percent,
                         played)

    def _once(self, key: str, event: str, **fields: Any) -> None:
        if key not in self.said:
            self.said.add(key)
            report.note(event, **fields)

    def tick(self, now: float) -> None:
        """One second of the run: the hunter, the horde, the wave, the clock and the bar; the camps that follow him, the
        census and the game's camps put off to the images after it."""
        player = self.player()
        if player is None:
            self.on_end("left_game")
            return
        pc = self.pc() or mods_base.get_pc()
        began = frame.now()
        here = reads.point(player)
        jump = reads.metres(here, self.last_here)
        if jump is not None and jump > reads.JUMP_M:
            report.note("hunter_jumped", m=jump, at=reads.spot(here))
        self.last_here = here if here is not None else self.last_here
        lost = self.zone.lost(here, now, report.note)
        if lost is not None:
            self.on_end(lost)
            return
        self.parts.catch.walk(here, pc, now, reads.mode(player) == "MOVE_Swimming")
        self.sweep.start(player, pc, here, now)
        self.beat.defer("follow", self._follow)
        if self.recruiter.due(now):
            self.beat.defer("census", self._census)
        if self.camps.due(now):
            self.beat.defer("game_camps", self._game_camps)
        kept = self.taken.keep(player)
        if kept is not None:
            self._once(f"taken:{kept['taken']}", "taken_kept", **kept)
        self.hardcore.keep(self.stats.kills, player)
        if self.stats.hunter(reads.dead(player)):
            report.note("hunter_died", deaths=self.stats.deaths)
        gaps = self.clock.tick(pc, now)
        if gaps["real_gap_s"] > clock.GAP_S:
            report.note("gap", **gaps)
        limit = self.settings.duration_s
        if limit is not None and self.clock.played >= limit:
            self.on_end("time_up")
            return
        shown = self.bar.keep(pc, self._words()) if self.bar is not None else "written"
        if shown not in ("written", "shown"):
            self._once(f"bar:{shown}", "bar_failed", outcome=shown)
        self.gauge.second((frame.now() - began) * 1000.0, len(self.horde.drawn()))
        self.gauge.frames(reads.frame_count(), now)
        if self.gauge.status_due(now):
            self.beat.defer("status", self._status)

    def _status(self, now: float) -> None:
        began = frame.now()
        report.note("status", played_s=round(self.clock.played, 1), kills=self.stats.kills, deaths=self.stats.deaths,
                    hardcore=self.hardcore.percent,
                    horde=len(self.horde.drawn()), copies=self.horde.copies(self.wave.ours),
                    horde_at=self.sweep.horde_at, **self.wave.gauge(), floating=self.floating.gauge(),
                    copy_camps=self.wave.copies.status(), game_camps=len(self.camps.held),
                    catch_up=self.parts.catch.gauge(), walk_blocks=len(brain_walk.kept()), walks=brain_walk.gauge(),
                    bodies=self.bodies, sweep=self.sweep.gauge(), **self.beat.gauge(), **self.gauge.spent())
        self._timed("status", began)

    def _follow(self, now: float) -> None:
        """The camps that follow the hunter, then the zone lent to the horde."""
        began, here = frame.now(), reads.point(self.player())
        moved = self.follow.follow(here, now)
        self.zone.follow(here, now, bool(moved))
        self._timed("follow", began)

    def _census(self, now: float) -> None:
        """The enemies around join the horde; the census's kills and kinds of the place counted; the camps of the mod
        left empty let go."""
        player = self.player()
        if player is None:
            return
        began = frame.now()
        sighting = self.horde.recruit(player, self.pc() or mods_base.get_pc(), reads.point(player), now)
        self.wave.saw(sighting.kept)
        self.stats.seen_dead(sighting.dead)
        self.bodies = len(sighting.dead)
        self.stats.seen_alive(sighting.alive)
        self.follow.release_empty(self.horde.names(), self.wave.ours)
        self._timed("census", began)

    def _game_camps(self, now: float) -> None:
        player = self.player()
        if player is None:
            return
        began = frame.now()
        woken = self.camps.wake(reads.point(player), now, player)
        if woken["made"] or woken["stopped"] != "complete" or woken["search"] != "actors":
            report.note("game_camps", **woken)
        self._timed("game_camps", began)

    def _held_camps(self) -> frozenset[str | None]:
        """The camps of the enemies the horde holds, read alive at this second's sample: busy, not asked."""
        of = self.parts.camp_map.of
        return frozenset(of.get(name) for name in self.horde.names())

    def _timed(self, name: str, began: float) -> None:
        self.gauge.task(name, (frame.now() - began) * 1000.0, len(self.horde.drawn()))

    def end(self, reason: str) -> None:
        """Everything still lent given back, as the trials did; written down with the run's counts."""
        beat = self.beat.stop() if self.beat is not None else "inactive"
        released = self.horde.let_go_all(reason) if self.horde is not None else {"released": 0}
        camps_back = self.follow.put_back() if self.follow is not None else {}
        zone = self.zone.put_back() if self.zone is not None else "none"
        radius = self.zone.narrow() if self.zone is not None else "none"
        limit = self.wave.put_back() if self.wave is not None else "none"
        critical = self.camps.put_back() if self.camps is not None else {}
        shown = self.bar.remove() if self.bar is not None else "none"
        taken = self.taken.put_back(self.player())
        played = self.clock.played if getattr(self, "clock", None) is not None else 0.0
        counts = getattr(self, "stats", None)
        report.note("stopped", reason=reason, level=self.level.target, played_s=round(played, 1),
                    kills=counts.kills if counts else 0, deaths=counts.deaths if counts else 0,
                    hardcore=self.hardcore.percent if self.hardcore is not None else 0, **released,
                    camps=len(camps_back), zone=zone, radius=radius, budget=limit, game_camps=critical, bar=shown,
                    taken=taken, beat=beat)

