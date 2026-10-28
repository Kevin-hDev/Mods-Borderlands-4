"""A duel's rounds between its players, for duel.py, which starts, beats and ends it (Kevin, 17 October 2026,
docs/duel/spec-equipes.md).

A round: a player the game shows down falls (fighters.py), protected, his duel team kept so that a teammate can stand
him up; stood up by the game, he is back. Once a single team has players standing it wins the round, once none has the
round is a draw (rounds.py). Then the pause: each player given his own team back, so that nobody hurts anybody (trial
5, verified in game), and KO_S later each player down stood up where he fell, every duel team handed again, the next
round on. A player an enemy around knocks down during the pause is protected too and stood up with the others, no
point given: unwatched, he would start the next round down, or die once the duel is stopped. In one against one the
first fall ends the round: the duel of 1.0.0.

The players are read at each step: one who leaves the game leaves the duel, which goes on while two teams have players;
one who comes ends it, as he would be the host team's ally without having chosen it (Kevin's choice)."""

from typing import Any, Callable

from unrealsdk.unreal import WeakPointer

from . import knockout, players, report, rounds
from .fighters import Fighter
from .score import Score

# Kevin, 16 October 2026: 3 s KO on the ground before the next round.
KO_S = 3.0
# A player just stood up is not asked again at once: the game may still show him down for a frame or two.
SETTLE_S = 1.0
# How often the players' teams are read back during a round, and how many times they may be handed again in a duel
# before the duel gives up: a team the game keeps taking back would otherwise be handed forever.
TEAM_CHECK_S = 1.0
MAX_HANDS = 20
PLAYING, PAUSED = "playing", "paused"


class Fight:
    """A duel's rounds; show(fight, now) puts the round's outcome and the score on the host's screen."""

    def __init__(self, world: Any, fighters: list[Fighter], score: Score, language: str, now: float,
                 show: Callable[[Any, float], None]) -> None:
        self.world = WeakPointer(world)
        self.fighters, self.score, self.language, self.show = fighters, score, language, show
        self.damage = knockout.damage_library()
        self.phase, self.until = PLAYING, 0.0
        self.last = self.checked = now
        self.hands = self.failed = 0
        # The last round's outcome, a team's number or rounds.DRAW, for the message.
        self.outcome: int | str | None = None
        # Why the duel must end, set by a step that cannot be undone here (a player not stood up).
        self.broken: str | None = None

    def members(self) -> list[Any]:
        return [fighter.member for fighter in self.fighters if fighter.member is not None]

    def beat(self, now: float) -> str | None:
        """One step of the duel; why it must end, or None."""
        world = players.world()
        if world is None or self.world() is None or not world == self.world():
            return "world_changed"
        found = players.everyone(world)
        if found is None:
            return "not_host"
        joined = [player for player in found if not any(fighter.is_player(player.state) for fighter in self.fighters)]
        if joined:
            report.note("player joined", players=len(found), characters=[players.label(one.pawn) for one in joined])
            return "player_joined"
        for fighter in [fighter for fighter in self.fighters
                        if not any(fighter.is_player(player.state) for player in found)]:
            self.leave(fighter)
        if len({fighter.team for fighter in self.fighters}) < 2:
            return "teams_left"
        self.watch(found, now)
        if self.phase == PAUSED:
            self.resume(now)
            return self.broken
        decided = rounds.outcome(self.standing())
        if decided != rounds.GOING:
            self.end_round(decided, now)
        elif now - self.checked >= TEAM_CHECK_S:
            self.checked = now
            return self.keep_teams()
        return None

    def standing(self) -> dict[int, int]:
        """Each team still in the duel and how many of its players stand."""
        counts: dict[int, int] = {}
        for fighter in self.fighters:
            counts[fighter.team] = counts.get(fighter.team, 0) + (not fighter.down)
        return counts

    def watch(self, found: list[players.Player], now: float) -> None:
        """Each player on foot asked whether the game shows him down: a fall, or a player stood up by the game."""
        changed = False
        for fighter in self.fighters:
            player = next((one for one in found if fighter.is_player(one.state)), None)
            pawn = fighter.pawn()
            # A vehicle has no down state; a player just stood up by the duel is not asked yet.
            if player is None or not player.on_foot or pawn is None or now < fighter.settled:
                continue
            down = pawn.InDownState() is True
            if down and not fighter.down:
                fighter.fall()
                changed = True
            elif fighter.down and not down:
                fighter.let_go()
                changed = True
        if changed:
            report.note("standing", teams=self.standing())

    def end_round(self, decided: int | str, now: float) -> None:
        if decided == rounds.DRAW:
            self.score.draw()
        else:
            self.score.won(decided)
        self.outcome = decided
        report.note("round", round=self.score.rounds, winner=decided, points=self.score.points)
        for member in self.members():
            member.give_back()
        self.phase, self.until = PAUSED, now + KO_S
        report.note("duel paused")
        self.show(self, now)

    def resume(self, now: float) -> None:
        """Once the pause is over: each player down stood up, every duel team handed again, the next round on."""
        if now < self.until:
            return
        for fighter in self.fighters:
            # Not stood up, he would lie down again with the duel resumed: the duel ends, a player down being the
            # game's own business once nobody holds his countdown.
            if fighter.down and not fighter.stand_up(self.damage, now, SETTLE_S):
                self.broken = "stand_up_failed"
        if self.broken is not None:
            return
        for member in self.members():
            member.hand()
        self.phase, self.checked = PLAYING, now
        report.note("duel resumed")

    def leave(self, fighter: Fighter) -> None:
        self.fighters.remove(fighter)
        self.score.left(fighter.team, fighter.number)
        report.note("player left", player=fighter.name, team=fighter.team)
        # His character may live a few frames more: his own team given back while it does.
        if fighter.member is not None and fighter.member.pawn() is not None:
            fighter.member.give_back()

    def keep_teams(self) -> str | None:
        """Each player's team read back; handed again when the game took it from him, as a death may."""
        for member in self.members():
            if member.holds_duel_team():
                continue
            self.hands += 1
            report.note("team lost, handed again", player=member.name, times=self.hands)
            if self.hands > MAX_HANDS or not member.hand():
                return "team_lost"
        return None

    def end(self, now: float) -> list[Any]:
        """Every player back to normal: each one still down stood up, each one's own team given back; those whose
        give-back the game refused."""
        for fighter in self.fighters:
            if fighter.down:
                fighter.stand_up(self.damage, now, SETTLE_S)
        return [member for member in self.members() if not member.give_back()]
