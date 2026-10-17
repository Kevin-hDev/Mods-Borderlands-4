"""A duel's rounds, for duel.py, which starts, beats and ends it: each fall scored, the one who fell KO 3 s out of the
fight then stood up where he fell (knockout.py), the duel paused meanwhile, the guest's team kept, and why the duel must
end on its own.

Kevin's rules (docs/duel/README.md, décisions): a fall ends the round; the one who fell stays KO 3 s, neither hurting
nor hurt, then stands up in place. While a player is KO the guest gets his own team back, so that nobody hurts anybody
(trial 5, verified in game); once nobody is KO, the duel's team again.
"""

from typing import Any, Callable, NamedTuple

from unrealsdk.unreal import WeakPointer

from . import knockout, players, report, teams
from .score import GUEST, HOST, Score

# Kevin, 16 October 2026: 3 s KO on the ground, well within the ten seconds before the game kills him.
KO_S = 3.0
# A player just stood up is not asked again at once: the game may still show him down for a frame or two.
SETTLE_S = 1.0
# How often the guest's team is read back while nobody is KO, and how many times it may be handed again in a duel
# before the duel gives up: a team the game keeps taking back would otherwise be handed forever.
TEAM_CHECK_S = 1.0
MAX_HANDS = 20


class Knocked(NamedTuple):
    pointer: Any
    until: float
    damageable: bool


class Fight:
    """A duel's rounds between its two players; show(fight, now) puts the round's score on the host's screen."""

    def __init__(self, world: Any, host: Any, guest: teams.Guest, score: Score, language: str, now: float,
                 show: Callable[[Any, float], None]) -> None:
        self.world, self.host = WeakPointer(world), WeakPointer(host)
        self.host_label = players.label(host)
        self.guest, self.score, self.language = guest, score, language
        self.damage = knockout.damage_library()
        self.knocked: dict[str, Knocked] = {}
        self.settled: dict[str, float] = {}
        self.last = self.checked = now
        self.hands = self.failed = 0
        self.show = show
        # Why the duel must end, set by a step that cannot be undone here (a player not stood up).
        self.broken: str | None = None

    def beat(self, now: float) -> str | None:
        """One step of the duel; why it must end, or None."""
        world = players.world()
        if world is None or self.world() is None or not world == self.world():
            return "world_changed"
        found = players.find(world)
        if found is None:
            return "not_host"
        guest = self.guest.pawn()
        # Gone from the player list, his character may still live a few frames; in a vehicle he is in it as a rider.
        if guest is None or (not any(pawn == guest for pawn in found.guests) and not found.riding):
            return "guest_left"
        if len(found.guests) + found.riding > 1:
            return "third_player"
        self.wake(now)
        if self.broken is not None:
            return self.broken
        # A host in a vehicle is not asked: the vehicle has no down state.
        host = found.host if found.host_on_foot else None
        for pawn, side, label in ((host, HOST, self.host_label), (guest, GUEST, self.guest.label)):
            if pawn is None or label in self.knocked or now < self.settled.get(label, 0.0):
                continue
            if pawn.InDownState() is True:
                self.fell(pawn, side, label, now)
        if not self.knocked and now - self.checked >= TEAM_CHECK_S:
            self.checked = now
            return self.keep_team()
        return None

    def fell(self, pawn: Any, side: str, label: str, now: float) -> None:
        self.score.fell(side)
        report.note("round", loser=side, character=label, host=self.score.host, guest=self.score.guest)
        if not self.knocked:
            self.guest.give_back()
            report.note("duel paused")
        self.knocked[label] = Knocked(WeakPointer(pawn), now + KO_S, knockout.protect(label, pawn))
        self.show(self, now)

    def wake(self, now: float, every: bool = False) -> None:
        """Stands up each player whose KO is over, or every one still KO; the duel resumes once none is."""
        woken = False
        for label, knocked in list(self.knocked.items()):
            if not every and now < knocked.until:
                continue
            del self.knocked[label]
            self.settled[label] = now + SETTLE_S
            woken = True
            pawn = knocked.pointer()
            if pawn is None:
                report.note("character gone, nothing to stand up", character=label)
                continue
            # Not stood up, he would lie down again with the duel resumed: the duel ends, as a player down is
            # the game's own business once nobody holds his countdown.
            if not knockout.stand_up(self.damage, label, pawn, knocked.damageable) and not every:
                self.broken = "stand_up_failed"
        if woken and not self.knocked and not every and self.broken is None:
            self.guest.hand()
            report.note("duel resumed")
            self.checked = now

    def keep_team(self) -> str | None:
        """The guest's team read back; handed again when the game took it from him, as a death may."""
        if teams.holds_duel_team(self.guest.team()):
            return None
        self.hands += 1
        report.note("team lost, handed again", character=self.guest.label, times=self.hands)
        if self.hands > MAX_HANDS or not self.guest.hand():
            return "team_lost"
        return None

    def end(self, now: float) -> bool:
        """Every player back to normal: the one still KO stood up, the guest's own team given back; whether it was."""
        self.wake(now, every=True)
        return self.guest.give_back()
