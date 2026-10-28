"""One player in a duel, for fight.py: his number J and duel team, his character held weakly, his PlayerState to find
him in the game's list, the team the game gives him (teams.Member; None for the host, never changed), and his fall.

Down, he is protected as in 1.0.0 (knockout.protect: the game's countdown paused, no damage taken) and keeps his duel
team, so that a teammate can stand him up (Kevin, 17 October 2026, docs/duel/spec-equipes.md). Stood up by the game
during the round, by a teammate or a second wind, he is let go: countdown and damage as before. At the round's end the
duel stands him up itself (knockout.stand_up)."""

from typing import Any

from unrealsdk.unreal import WeakPointer

from . import knockout, report


class Fighter:
    def __init__(self, number: int, team: int, pawn: Any, state: Any, member: Any) -> None:
        self.number, self.team, self.member = number, team, member
        self.pointer, self.state = WeakPointer(pawn), WeakPointer(state)
        self.down = False
        self.damageable = True
        # Until when a player just stood up by the duel is not asked: the game may show him down a frame or two more.
        self.settled = 0.0

    @property
    def name(self) -> str:
        return report.player(self.number)

    def pawn(self) -> Any:
        return self.pointer()

    def is_player(self, state: Any) -> bool:
        mine = self.state()
        return mine is not None and mine == state

    def fall(self) -> None:
        self.down = True
        self.damageable = knockout.protect(self.name, self.pawn())
        report.note("fell", player=self.name, team=self.team)

    def let_go(self) -> None:
        """Stood up by the game during the round: back in it."""
        self.down = False
        pawn = self.pawn()
        if pawn is not None:
            knockout.release(self.name, pawn, self.damageable)
        report.note("stood up in the round", player=self.name, team=self.team)

    def stand_up(self, damage: Any, now: float, settle: float) -> bool:
        """Stood up by the duel at the round's end: whether the game no longer shows him down."""
        self.down = False
        self.settled = now + settle
        pawn = self.pawn()
        if pawn is None:
            report.note("character gone, nothing to stand up", player=self.name)
            return True
        return knockout.stand_up(damage, self.name, pawn, self.damageable)
