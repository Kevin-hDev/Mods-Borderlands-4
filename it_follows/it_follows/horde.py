"""The horde: the enemies drawn to the hunter, each one's part of a sample, those lost let go, the recruits drawn.

Taken from the trials' move trial (docs/RUN/sondes/run_move_rows.py, run_move_enlist.py), without the lines its
records wrote. Each second, each enemy is checked (gone, dead, taken back by the game, or given another zone: lost),
kept on the hunter (chaser.py), brought back when left behind (catch_up.py) unless it rides, its speed kept
(speed.py), and what it targets read, for the wave's count (wave.near). An enemy lost is let go: what it still holds
given back (its zone, its target, its walk, its team, its speed, its health), nothing called on a body the game
reuses, and every table kept about it forgotten, so that none grows with the length of a run. A killed one is
counted (stats.py) and waits to come back (wave.py); the camp the mod made for it is let go with it
(camp_follow.release).

Every few seconds the census chooses the enemies around the hunter not yet drawn (recruit.py, decision 36), and they
join: their camps placed on the hunter, their speed, their health (toughness.py) and their team given; a copy
tells the catch-up how far behind him it joins, since the spread has it born up to 65 m behind (decision 66). A
name lost less than LOST_WATCH_S ago is not drawn again at once: the game may give its body to another enemy, or
take it back again.

The horde holds at most the run's crowd_max, the player's choice (decision 96). With the far enemies not managed
(decision 97, Kevin, 15 October 2026: « pour que les joueurs qui veulent de meilleur performance puisse le
desactiver »), an enemy the catch-up would bring back is let go instead, everything given back. It stays alive in the
world and is never born again (decision 98, wave.left_behind); the census then draws only the enemies within the
catch-up's distance and the births of the mod's camps not joined yet, so that one let go joins again once back within
reach, and not before.
"""

import time
from typing import Any, Callable

from .characters import reads, target

# run_chaser's reason for an enemy found dead: the one loss that comes back (wave.py).
KILLED = "mover_dead"
# An enemy the game took back alive, without a zone: one in its reserve (docs/RUN/enquetes/2026-10-10-recensement.md).
PARKED = "mover_parked"
# An enemy the catch-up would bring back, let go instead while the far enemies are not managed (decision 97).
LEFT_BEHIND = "left_behind"
# Losses after which nothing is called on the enemy: the game reuses a dead or removed enemy's body, and one in its
# reserve has no zone.
BODY_REUSED = (KILLED, "mover_gone", PARKED)
# Trial 6f (decision 20): the hunter imposed again once the game cleared the target; while it held, the cats came even
# when the game ended their walk.
IMPOSE_AGAIN = True
# Trial 6p: a bandit teleported while riding landed 370 m from the place asked, and its band was gone 2 s later: a
# rider is never brought back; its mount, brought back, carries it along.
SEATED = "MOVE_None"
# A name lost is not drawn again for this long (the trials kept a lost enemy's line this long).
LOST_WATCH_S = 10.0
# The most enemies drawn at once, the most the player may choose (options.CROWDS), and the most camps It Follows makes
# (session.py). Decision 69, Kevin, 14 October 2026, after trial 15, where the horde reached 200 with the mod's
# heaviest second at 155 ms and the big enemies taking all the room: « le plafond d'ennemies on va le placer a 120 ».
CROWD_MAX = 120


class Horde:
    """parts holds the run's pieces: zone (hunter_zone.HunterZone), camp_map, follow (camp_follow.CampFollow), catch
    (catch_up.CatchUp), ground (ground.GroundTrace), speed, toughness, teams, wave, stats, recruiter, chaser (the
    chaser module), player_ref (the hunter's weak pointer), near_m (wave.RADIUS_M, within which the wave counts whom
    an enemy targets), crowd_max (the most drawn at once) and manage_far (whether the far enemies are brought back).
    note(event, **fields) writes to the log, announce(call, log, **fields) before a call."""

    def __init__(self, parts: Any, note: Callable[..., None], announce: Callable[..., None]) -> None:
        self.parts, self.note, self.announce = parts, note, announce
        self.chasers: list[Any] = []
        self.lost_at: dict[str, float] = {}

    def drawn(self) -> list[Any]:
        return [chaser for chaser in self.chasers if chaser.ended is None]

    def names(self) -> set[str]:
        return {chaser.name for chaser in self.drawn()}

    def copies(self, ours: Callable[[str | None], bool]) -> int:
        """How many enemies drawn are copies, born of a camp It Follows made: the rest are the game's own."""
        return sum(1 for chaser in self.drawn() if ours(self.parts.camp_map.of.get(chaser.name)))

    def free_of(self, seens: list) -> list[tuple]:
        """Each enemy with its chaser, but those another script imposes a target on."""
        chasers = [self.parts.chaser.Chaser(seen, self.parts.player_ref, self.announce) for seen in seens]
        return [(seen, chaser) for seen, chaser in zip(seens, chasers) if chaser.patch.read() == "none"]

    def note_camps(self, seens: list) -> list[str | None]:
        """The camp of each enemy, noted before it ever follows the hunter."""
        return [self.parts.camp_map.add(seen.name, seen.zone) for seen in seens]

    def draw_all(self, free: list[tuple], player: Any, pc: Any, here: tuple | None, now: float) -> list[Any]:
        """Draws each enemy (chaser.draw); one refusing is let go alone. The enemies drawn."""
        taken = []
        for seen, chaser in free:
            self.chasers.append(chaser)
            far = (reads.metres(seen.at, here) or 0.0) > self.parts.chaser.ARRIVAL_M
            refused = chaser.draw(self.parts.zone, seen, player, pc, far, now)
            if refused is None:
                taken.append(chaser)
                camp = self.parts.camp_map.of.get(chaser.name)
                if self.parts.wave.ours(camp):
                    self.parts.wave.joined(camp)
                    self.parts.catch.arrived(chaser.name, reads.metres(seen.at, here))
            else:
                self.lose(chaser, refused, now)
        return taken

    def let_go(self, chaser: Any, reason: str) -> dict:
        """What the enemy still holds given back: its zone, target and walk (chaser.release), its own team, and its
        speed bonus even on a body the game reuses, since that is a value written, not a call (run_speed_boost), and
        its health unless the game reuses its body (toughness.put_back)."""
        parts, body_reused = self.parts, reason in BODY_REUSED
        released = chaser.release(parts.zone, reason, body_reused)
        if not released:
            return {}
        return {**released, "team": parts.teams.give_back(chaser.name, chaser.actor(), body_reused,
                                                          away=reason == PARKED),
                "boost": parts.speed.put_back(chaser.name, chaser.actor()),
                "health": parts.toughness.put_back(chaser.name, chaser.actor(), body_reused)}

    def lose(self, chaser: Any, reason: str, now: float) -> None:
        """Lets the enemy go and writes it down; a killed one is counted and waits to come back; its tables are
        forgotten. The camp the mod made for it is let go with it, so that the wave may hand it a new enemy."""
        parts = self.parts
        camp = parts.camp_map.of.get(chaser.name)
        respawn = None
        if reason == KILLED:
            parts.stats.killed(chaser.name)
            respawn = parts.wave.killed(chaser.name, chaser.kind)
        elif reason == LEFT_BEHIND:
            respawn = parts.wave.left_behind()
        given = self.let_go(chaser, reason)
        self.lost_at[chaser.name] = now
        parts.catch.forget(chaser.name)
        parts.ground.forget(chaser.name)
        parts.camp_map.forget_enemy(chaser.name)
        ours = parts.wave.ours(camp)
        if ours:
            parts.follow.release(camp)
        self.note("lost", on=chaser.name, reason=reason, copy=ours, respawn=respawn, **given)

    def sample(self, chasers: list, player: Any, pc: Any, here: tuple | None, now: float) -> list[dict]:
        """These enemies' part of this second, in their order (catch_up.queue: those brought back longest ago first),
        those let go since left out; how far each stands, and whom it targets within near_m, the one distance the wave
        counts it at (wave.near): beyond, None, unread. In trials 16 to 19, 86 % of the horde stood farther, a call
        each a second for nothing (audit of 15 October 2026)."""
        parts = self.parts
        lines = []
        for chaser in chasers:
            if chaser.ended is not None:
                continue
            mover, reason = chaser.check(parts.zone)
            if reason is not None:
                self.lose(chaser, reason, now)
                continue
            at = reads.point(mover)
            to_player = reads.metres(at, here)
            if not parts.manage_far and parts.catch.beyond(chaser.name, to_player):
                self.lose(chaser, LEFT_BEHIND, now)
                continue
            try:
                chaser.keep(to_player, player, pc, IMPOSE_AGAIN, now)
            except Exception as error:
                self.lose(chaser, f"walk_again_failed:{type(error).__name__}", now)
                continue
            if reads.mode(mover) != SEATED:
                parts.catch.consider(chaser.name, mover, at, here, to_player, now)
            parts.speed.keep(chaser.name, mover)
            near = to_player is not None and to_player <= parts.near_m
            lines.append({"target": target.aimed(mover, player) if near else None, "to_player_m": to_player})
        self.chasers = self.drawn()
        return lines

    def _forget_lost(self, now: float) -> None:
        for name in [name for name, at in self.lost_at.items() if now - at >= LOST_WATCH_S]:
            del self.lost_at[name]

    def recruit(self, player: Any, pc: Any, here: tuple | None, now: float) -> Any:
        """The enemies around the hunter not yet drawn join the horde, up to crowd_max drawn (decision 36): their camps
        placed, their speed, their health and their team given; with the far enemies not managed, only those it would
        keep (decision 97). The census runs even with the horde full, for the kills it reads. Gives the census's
        sighting (census.Sighting)."""
        parts = self.parts
        self._forget_lost(now)
        room = max(0, parts.crowd_max - len(self.drawn()))
        drawn = self.names()
        keep = None if parts.manage_far else lambda seen: self._kept(seen, here)
        chosen, said, sighting = parts.recruiter.choose(player, here, drawn | set(self.lost_at), room, known=drawn,
                                                        keep=keep)
        began = time.perf_counter()
        free = self.free_of(chosen)
        if free:
            self.note_camps([seen for seen, _ in free])
            camps = parts.follow.place_new(here)
            joined = self.draw_all(free, player, pc, here, now)
            boosted = parts.speed.start(joined)
            toughened = parts.toughness.start(joined)
            teams = parts.teams.join(joined)
            # How long they took to join, apart from the census's search (audit of 16 October 2026, A1).
            self.note("recruit", joined=len(joined), camps_placed=len(camps), boosted=len(boosted),
                      toughened=toughened, team=teams.get("team"),
                      join_ms=round((time.perf_counter() - began) * 1000.0, 1), **said)
        return sighting

    def _kept(self, seen: Any, here: tuple | None) -> bool:
        """Whether an enemy may join while the far enemies are not managed: within the catch-up's distance, or the
        birth of a camp of the mod not joined yet, wherever it was born."""
        return not self.parts.catch.beyond(seen.name, reads.metres(seen.at, here)) or self.parts.wave.owes(
            reads.camp_of(seen.zone))

    def let_go_all(self, reason: str) -> dict:
        """Every enemy still drawn let go, at the run's stop: one gone, or read dead since the last second, as a lost
        one, nothing called on its body, the dead counted killed (audit of 15 October 2026: the stop called on a body
        killed in its last second as on a living one, as the rule « nothing called on a killed one » forbids). How
        many, the killed, and each way each part was given back counted, since no line is written for each of them."""
        drawn = self.drawn()
        killed = 0
        tally: dict[str, dict[str, int]] = {}
        for chaser in drawn:
            mover = chaser.actor()
            why = reason
            if mover is None:
                why = "mover_gone"
            elif reads.dead(mover) is True:
                why = KILLED
                killed += 1 if self.parts.stats.killed(chaser.name) else 0
            for part, outcome in self.let_go(chaser, why).items():
                counts = tally.setdefault(part, {})
                counts[str(outcome)] = counts.get(str(outcome), 0) + 1
        self.chasers = []
        return {"released": len(drawn), "killed": killed, **tally}
