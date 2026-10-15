"""The normal mode while it is on (decision 80, spec-mode-normal.md, section 4): it waits for a game, plays in it at its
level, and waits again when the game is left (a load, the main menu), until STOP or the mod switched off. session.py,
the one owner of what runs, starts and ends it.

Once a second (frame.py's beat, under its own name) it looks for a game to play in (presence.py): without one, from a
vehicle or in a game of several players it waits, each reason written once; with one, it plays (play.Play), and goes on
playing if the player gets in a vehicle. The families' dodge files outlive a change of map (dodge_rate.py): the mode
keeps them opened from one game to the next, and gives them back when it stops.
"""

from typing import Any, Callable

from .. import frame, presence, report
from . import dodge_rate, play

IDENTIFIER = "it_follows:normal"


class Mode:
    """settings: normal.options.Settings; fail(reason): a second that raised, the mode to be ended."""

    def __init__(self, settings: Any, fail: Callable[[str], None]) -> None:
        self.settings, self.fail = settings, fail
        self.play: play.Play | None = None
        self.waiting_for: str | None = None
        self.dodges = dodge_rate.Dodges(settings.level, report.note, report.announce)
        self.beat = frame.Beat(self.tick, fail, IDENTIFIER)

    def begin(self, now: float) -> str:
        """The mode on: "playing" in a game in play, else "waiting" for one."""
        report.note("normal_on", level=self.settings.level.name, allies=self.settings.allies)
        self.beat.start()
        self.tick(now)
        return "playing" if self.playing() else "waiting"

    def playing(self) -> bool:
        return self.play is not None

    def tick(self, now: float) -> None:
        """One second: the game played, left, or found."""
        if self.play is not None:
            if self.play.player() is None:
                self._leave("left_game")
            else:
                self.play.tick(now)
            return
        seat = presence.look()
        if seat.why is not None:
            if seat.why != self.waiting_for:
                self.waiting_for = seat.why
                report.note("normal_waiting", why=seat.why)
            return
        self.waiting_for = None
        report.note("normal_playing", level=self.settings.level.name)
        self.play = play.Play(self.settings, seat.player, self.dodges, self.fail)
        self.play.begin(now)

    def _leave(self, why: str) -> None:
        current, self.play = self.play, None
        report.note("normal_left", why=why)
        if current is not None:
            current.end(why)

    def end(self, reason: str) -> None:
        """The mode off: its beat unhooked, the game it played in given back, then the families' dodge files."""
        beat = self.beat.stop()
        if self.play is not None:
            self._leave(reason)
        report.note("normal_off", reason=reason, beat=beat, dodge_files=self.dodges.stop())
