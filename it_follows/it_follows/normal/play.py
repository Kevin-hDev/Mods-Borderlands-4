"""One game played at the normal mode's level, from the moment the mode finds a game until the game is left or the
mode stops (spec-mode-normal.md, section 4): the camps grown before their enemies are born (camps_grown.py), the
enemies met given the level (enemies.py) and the shields it gives them (shields.py), their dodges sped up at each
image unless the player switched it off (options.fast_dodges) and their gestures sped up (enemy_time.py), and the damage
the player takes raised (damage_taken.py, the Horde's, the normal mode's own BUFF), and the player's rewards raised
(rewards.py: experience of the kills, ammo and money picked up), and the armed bandits' rest between two blows
shortened at each census (melee_rest.py), and the enemies' staggers made rarer, written again at each census
(staggers.py). In co-op the host's game does the same for each guest (coop_guests.py,
decision 131): the damage taken and the gains raised on the guest's character, the camps grown and the gestures watched
around each player, the dodges near a guest left to the game (decision 132), each guest told its kills and its
Hardcore's percent heard (coop_messages.py, decision 133). At its end everything it holds is given
back, as far as the game still holds it, and the Hardcore's kills are written. They are written with each status line
too: a game quit to the desktop never ends its play (trial 31), and its kills were lost.

The Hardcore (decision 89, normal/hardcore.py): the enemies the player killed are counted, and its factor is read
again each second; when it changes (switched on or off, a step reached), it is given at once to every enemy held and
to the damage taken, on top of the level's.

Each second (the mode's beat) does what is due: the camps every camps_grown.EVERY_S, the census every enemies.EVERY_S
but never in the camps' second, Predator's and God's broken shields refilled when their time comes, the damage taken
kept. A pass of the camps that stops at its time gives the rest to the next image (the beat's defer), part by part;
the census's image holds its search, the kills counted and the lost, and the enemies met and kept follow part by
part the same way (arrivals.py, trial 221).
Both every 5 s, the camps and the census fell in the same second, which held the game 35 to 43 ms in trials 28 to 32,
against some 25 ms for the camps alone (audit of 15 October 2026); the census
waits a second then, and they fall a second apart from then on. The camps go first: they are grown before their
enemies are born. A second that holds the game longer than run_gauge.SLOW_S is written down, and a status line every
run_gauge.STATUS_EVERY_S says what the mode holds (spec, section 4, « Les traces ») and what it costs, as a run's
does: the images a second, its beat's calls, each task's longest, the census's search and the looks at the dodges
(audit of 24 October 2026).
"""

from typing import Any, Callable

import unrealsdk

from .. import damage_taken, frame, report, run_gauge
from ..characters import reads
from . import camps_grown, coop_guests, coop_messages, enemies, enemy_time, hardcore, melee_rest, pursuit, rewards
from . import staggers

SLOW_EVENTS = ("normal_slow_second", "normal_slow_task")


class Play:
    """settings: normal.options.Settings; dodges: dodge_rate.Dodges, the mode's; fail(reason) ends the mode; beat:
    the mode's frame.Beat, which puts tasks off to later images and counts its calls."""

    def __init__(self, settings: Any, player: Any, dodges: Any, fail: Callable[[str], None], beat: Any) -> None:
        self.level = level = settings.level
        self.hard = hardcore.factor()
        self.player = unrealsdk.unreal.WeakPointer(player)
        self.chase = pursuit.Pursuit(report.announce, level.chase_m)
        self.enemies = enemies.Enemies(level, settings.allies, dodges, self.chase, report.note, report.announce,
                                       self.hard, settings.shields)
        self.camps = camps_grown.CampsGrown(report.note, report.announce, level.camps)
        self.taken = damage_taken.DamageTaken(report.announce, level.taken * self.hard)
        self.rewards = rewards.Rewards(level, report.announce)
        self.melee = melee_rest.MeleeRest(level.melee_rest, report.note, report.announce)
        self.staggers = staggers.Staggers(level.staggers, report.announce)
        self.guests = coop_guests.CoopGuests(level, report.announce)
        self.link = coop_messages.Link(host=True)
        self.watch = enemy_time.EnemyTime(report.note, level.dodge_speed if settings.fast_dodges else None,
                                          level.gestures, fail)
        self.dodges, self.beat = dodges, beat
        self.camps_stopped = "none"
        self.gauge = run_gauge.Gauge(report.note, 0.0, SLOW_EVENTS)
        self.said: set[str] = set()
        self.over = False
        # What the census's image found, until its parts are done and its line said; the parts it took.
        self.found: dict | None = None
        self.parts = 0

    def begin(self, now: float) -> None:
        raised = self.taken.start(self.player())
        if raised:
            report.note("normal_taken_raised", **raised)
        report.note("normal_rewards_raised", **self.rewards.start(self.player()))
        rarer = self.staggers.keep()
        if rarer:
            report.note("normal_staggers", **rarer)
        self.watch.start()
        self.link.start()
        self.gauge = run_gauge.Gauge(report.note, now, SLOW_EVENTS)
        self.gauge.frames(reads.frame_count(), now)
        self.tick(now)

    def tick(self, now: float) -> None:
        """One second of the game: what is due done, the time it took watched."""
        player = self.player()
        if player is None:
            return
        began = frame.now()
        heard = self.guests.heard(self.link.take())
        if heard:
            report.note("normal_guest_hardcore", **heard)
        if self.guests.due(now):
            joined = self.guests.look(player, now)
            if joined:
                report.note("normal_guests", **joined)
        if self.camps.due(now):
            self._camps(now)
        elif self.enemies.due(now):
            self._census(player, now)
        self._harden(player)
        shields = self.enemies.keep_shields(now)
        if shields:
            report.note("normal_shields", **shields)
        kept = self.taken.keep(player)
        if kept is not None and f"taken:{kept['taken']}" not in self.said:
            self.said.add(f"taken:{kept['taken']}")
            report.note("normal_taken_kept", **kept)
        for name, done in self.guests.keep().items():
            if f"guest:{name}:{done['taken']}" not in self.said:
                self.said.add(f"guest:{name}:{done['taken']}")
                report.note("normal_guest_taken_kept", guest=name, **done)
        self.gauge.second((frame.now() - began) * 1000.0, enemies=len(self.enemies.met))
        self.gauge.frames(reads.frame_count(), now)
        if self.gauge.status_due(now):
            self._status()

    def _places(self, player: Any) -> list[tuple]:
        """Each player's place: the host's, then each guest's (coop_guests.py)."""
        here = reads.point(player)
        return ([here] if here is not None else []) + self.guests.places()

    def _camps(self, now: float, part: int = 0) -> None:
        """One part of the camps' pass, searched in the player's world; one that stopped at its time leaves the rest
        to the next image, camps_grown.PARTS_MOST parts at most. A part left waiting once the game played is over
        does nothing: its camps were given back, none must be grown again with no one to give them back."""
        player = self.player()
        if player is None or self.over:
            return
        began = frame.now()
        grown = self.camps.grow(self._places(player), now, player)
        self.camps_stopped = grown["stopped"]
        if grown["grown"] or grown["refused"] or grown["too_many"] or grown["search"] not in ("actors", None):
            report.note("normal_camps", part=part, **grown)
        self._timed("camps", began)
        if grown["stopped"] == "time_limit" and part + 1 < camps_grown.PARTS_MOST:
            self.beat.defer("camps", lambda later: self._camps(later, part + 1))

    def _census(self, player: Any, now: float) -> None:
        """The census's image: the enemies lost, the kills counted, the dodges and gestures looked at from now on, the
        bandits' rest and the staggers kept; each timed. The new met and the held kept follow, part by part."""
        began = frame.now()
        self._tell(cut="census")
        found = self.enemies.look(player, now)
        self.gauge.task("census_search", self.enemies.scan_ms, enemies=len(self.enemies.met))
        self._count(found.get("kills", 0))
        told = self.guests.kills(found.get("by_others", {}))
        if told:
            report.note("normal_guest_kills", told=told)
        self.found, self.parts = found, 0
        self._watch(player)
        began = self._timed("census", began)
        rested = self.melee.keep()
        if rested:
            report.note("normal_melee_rest", **rested)
        began = self._timed("melee_rest", began)
        rarer = self.staggers.keep()
        if rarer:
            report.note("normal_staggers", **rarer)
        self._timed("staggers", began)
        self.beat.defer("census", self._arrive)

    def _arrive(self, now: float) -> None:
        """One part of what the census left (arrivals.py), timed; after the last, the census's line and the watch told
        of the enemies met. A part left waiting once the game played is over does nothing."""
        player = self.player()
        if player is None or self.over or self.found is None:
            return
        began = frame.now()
        self.enemies.arrivals.part()
        self.parts += 1
        self._timed("census_part", began)
        if self.enemies.arrivals.pending():
            self.beat.defer("census", self._arrive)
            return
        self._tell()
        self._watch(player)

    def _tell(self, cut: str | None = None) -> None:
        """The census's line, once: cut says what came before its parts were done, the next census or the end."""
        found, self.found = self.found, None
        if found is None:
            return
        line = self.enemies.arrived(found)
        if line:
            report.note("normal_enemies", parts=self.parts, **line, **({"cut": cut} if cut else {}))

    def _watch(self, player: Any) -> None:
        """The dodges and gestures of the nearest enemies met looked at from now on, those near a guest left to the
        game."""
        plain = self.enemies.nearest(self.guests.places(), coop_guests.PLAIN_M, enemies.MOST)
        self.watch.follow(self.enemies.nearest(self._places(player)), frozenset(plain))

    def _timed(self, task: str, began: float) -> float:
        """The task's time since began given to the gauge; the moment it ended."""
        ended = frame.now()
        self.gauge.task(task, (ended - began) * 1000.0, enemies=len(self.enemies.met))
        return ended

    def _status(self) -> None:
        hardcore.save("status")
        report.note("normal_status", enemies=len(self.enemies.met), guests=len(self.guests.held),
                    watched=len(self.watch.watched), dodges_sped=self.watch.counts[enemy_time.DODGE],
                    gestures_sped=self.watch.counts[enemy_time.GESTURE], camps_held=len(self.camps.held),
                    camps_grown=sum(1 for _, owed in self.camps.held.values() if owed),
                    camps_stopped=self.camps_stopped, families=len(self.dodges.files),
                    zones=self.chase.widened(), hardcore=hardcore.state(), percent=hardcore.percent(),
                    shields=len(self.enemies.shields.given) if self.enemies.shields is not None else None,
                    aimed=len(self.enemies.aim.held), watch=self.watch.gauge(),
                    kills_seen=self.enemies.reserve.said(), **self.beat.gauge(), **self.gauge.spent())

    def _count(self, dead: int) -> None:
        step = hardcore.count(dead)
        if step is not None:
            report.note("normal_hardcore_step", percent=step, kills=hardcore.kills())

    def _harden(self, player: Any) -> None:
        """The Hardcore's factor given to the enemies and the damage taken when it changed."""
        hard = hardcore.factor()
        if hard == self.hard:
            return
        self.hard = hard
        report.note("normal_hardcore", state=hardcore.state(), percent=hardcore.percent(), factor=round(hard, 3),
                    enemies=self.enemies.harden(hard), taken=self.taken.change(player, self.level.taken * hard))

    def end(self, reason: str) -> None:
        """Everything the game still holds given back, written down in one line; the Hardcore's kills written."""
        self.over = True
        self._tell(cut="end")
        sped = self.watch.stop()
        given = {"enemies": self.enemies.end(), "zones": self.chase.narrow(),
                 "camps": self.camps.put_back(), "taken": self.taken.put_back(self.player()),
                 "rewards": self.rewards.put_back(self.player()), "melee_rest": self.melee.put_back(),
                 "staggers": self.staggers.put_back(),
                 "guests": self.guests.end(), "link": self.link.stop(),
                 "hardcore_saved": hardcore.save("end")}
        report.note("normal_given_back", reason=reason, **sped, **given)
