"""The normal mode in a co-op guest's game (decision 129: « on veut que le mod fonctionne pleinement des deux cotés »):
the host's mod makes the enemies, their health, shields, dodges and chase; the guest's game only shows them, and keeps
the game's speeds on its own copies (trial 71). So here the level's run only is written, on those copies (speed.py,
the host's own writer), at the guest's own level until the host tells its own (coop_messages.RUN, every 5 s), then at
the host's: one run for every player, whatever level or REDUCED each chose. Nothing else is written, nothing is called
to change.

Their own time is never sped up here (enemy_time.py): trial 72 sped their gestures on the guest's copies, which then
jumped from one place to another, seen by Kevin as teleports (« La je vois des teleportation »); the run alone, by the
probe, ran faster without a jump (« le probleme est plus la »). The guest's game never reads a dodge (none at trial 72).

Every EVERY_S the enemies near the hunter are read (guest_enemies.py): one new gets the level's run, one held whose
bonus the game wrote again gets it again, one no longer found gets its own back. At the end each held gets its own run
back.

The Hardcore is the guest's own (decision 133): the host's game tells it each enemy it killed, counted here and kept in
this game's settings (hardcore.py), and is told this game's percent, which it gives the guest's damage taken. The
percent goes first when the host asks, then each time it changes: a step reached, the Hardcore switched off or on. It
is written with each status line and at the end, as play.py does.
"""

from types import SimpleNamespace
from typing import Any, Callable

import unrealsdk

import mods_base

from .. import report, speed
from ..characters import reads
from . import coop_messages, enemies, guest_enemies, hardcore

STATUS_EVERY_S = 30.0
# More than trial 71 found near the guest (21 within 80 m).
MAX_HELD = 96


class GuestPlay:
    """settings: normal.options.Settings; fail(reason), the mode's, kept for the same shape as play.Play."""

    def __init__(self, settings: Any, player: Any, fail: Callable[[str], None]) -> None:
        self.player = unrealsdk.unreal.WeakPointer(player)
        self.speed = speed.SpeedBoost(report.announce, settings.level.speed)
        # By name: the weak pointer of each enemy whose run was written.
        self.held: dict[str, Any] = {}
        self.read_at = -1e9
        self.next_status = 0.0
        self.link = coop_messages.Link(host=False)
        # The percent the host was told last; None until it asks.
        self.told: int | None = None

    def begin(self, now: float) -> None:
        self.link.start()
        self.next_status = now + STATUS_EVERY_S
        self.tick(now)

    def tick(self, now: float) -> None:
        player = self.player()
        if player is None:
            return
        if now - self.read_at >= enemies.EVERY_S:
            self.read_at = now
            self._look(player)
        self._hear(player)
        if now >= self.next_status:
            self.next_status = now + STATUS_EVERY_S
            hardcore.save("status")
            report.note("normal_guest_status", held=len(self.held), hardcore=hardcore.state(), percent=_percent(),
                        told=self.told, dropped=self.link.dropped)

    def _hear(self, player: Any) -> None:
        """The host's words of the last second: its run followed, each enemy killed counted, the percent told when
        asked or changed."""
        asked = False
        for _, (word, number) in self.link.take():
            if word == coop_messages.ASK:
                asked = True
                continue
            if word == coop_messages.RUN:
                self._follow(player, number / 1000.0)
                continue
            step = hardcore.count(number)
            report.note("normal_guest_killed", kills=number, total=hardcore.kills())
            if step is not None:
                report.note("normal_hardcore_step", percent=step, kills=hardcore.kills())
        percent = _percent()
        if not asked and (self.told is None or percent == self.told):
            return
        pc = mods_base.get_pc()
        if pc is None:
            return
        report.announce("ServerSetSpectatorLocation", percent=percent)
        try:
            coop_messages.tell_host(pc, percent)
        except Exception as error:
            report.note("normal_guest_hardcore", failed=type(error).__name__)
            return
        self.told = percent
        report.note("normal_guest_hardcore", told=percent)

    def _follow(self, player: Any, run: float) -> None:
        """The host's run on the enemies held and met from now on, written at once; the same as ours, nothing."""
        if abs(run - self.speed.factor) <= speed.SAME:
            return
        given = self._let_go(list(self.held))
        report.note("normal_guest_run", host_run=run, was=round(self.speed.factor, 3), given_back=given)
        self.speed = speed.SpeedBoost(report.announce, run)
        self._look(player)

    def _look(self, player: Any) -> None:
        here = reads.point(player)
        found, left = guest_enemies.scan(player, here)
        seen, sped, again, refused = set(), 0, 0, 0
        for _, name, actor in found:
            seen.add(name)
            if name in self.held:
                again += self.speed.keep(name, actor) is not None
                continue
            if len(self.held) >= MAX_HELD:
                left["too_many"] = left.get("too_many", 0) + 1
                continue
            raised = self.speed.start([SimpleNamespace(name=name, actor=lambda target=actor: target)])
            if raised and "failed" in raised[0]:
                refused += 1
                continue
            self.held[name] = unrealsdk.unreal.WeakPointer(actor)
            sped += 1
        given = self._let_go([name for name in self.held if name not in seen])
        if sped or again or refused or given:
            report.note("normal_guest_enemies", sped=sped, again=again, refused=refused, given_back=given,
                        held=len(self.held), left=left)

    def _let_go(self, names: list[str]) -> dict[str, int]:
        tally: dict[str, int] = {}
        for name in names:
            outcome = self.speed.put_back(name, self.held.pop(name)())
            tally[outcome] = tally.get(outcome, 0) + 1
        return tally

    def end(self, reason: str) -> None:
        """Every enemy held given its own run back, written down in one line."""
        given = self._let_go(list(self.held))
        report.note("normal_given_back", reason=reason, guest=True, speed=given, link=self.link.stop(),
                    hardcore_saved=hardcore.save("end"))


def _percent() -> int:
    """The percent this game's Hardcore applies: none while it is off."""
    return hardcore.percent() if hardcore.state() != "off" else 0
