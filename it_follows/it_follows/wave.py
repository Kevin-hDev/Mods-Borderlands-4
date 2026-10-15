"""It Follows' wave (decisions 38 and 39): at the start the horde is doubled, each enemy near given a copy, and the zone
lent is that of a camp It Follows makes (copies.py, decision 41); then each enemy of the horde killed comes back,
unless the player turned the coming back off (decision 44: a menu option, on by default).

A killed one comes back once until GROW_FROM_S, then GROWTH times as often, compounded at each minute begun, the share
beyond a whole one carried to the next killed (decision 38's fractions: over time exactly GROWTH times as many come
back, with no chance). The enemies that target the hunter within RADIUS_M are counted at each sample: under the level's
band the wave grows until the count reaches the level's target; within the band a killed one comes back once; above it
none comes back until the count is down to the target, and no enemy alive is ever taken away (Kevin, 13 October 2026: a
living enemy taken away would vanish under the player's eyes).

The killed wait here, oldest first, with their kind; once a second at most they are asked again through copies.py, born
as the copies were, behind the hunter out of his sight (decision 23), and the census draws them like any other enemy.
Each comes back as an enemy of the place, the kinds met during the run around where the hunter stands taken in turn, as
itself when none was met there (decisions 56 and 68, zone_kinds.py). Nobody is asked beyond the room the horde has,
the run's most (decision 96) less those drawn and the births not joined yet: one born beyond would stay out of it. An
enemy let go for being left behind, the far enemies not managed, is only counted, never asked again (decision 98): it
stays alive in the world, and joins again once back within reach. Nothing
bounds the enemies beyond RADIUS_M (decision 65, Kevin after trial 13: the quantity is read and kept within a
perimeter, without stopping more enemies from being around it): only the camps It Follows can hold (horde.CROWD_MAX)
bound the copies alive. In trial 13 a cap on the
whole horde, copies far away included, held the coming back while fewer than the target stood near. An enemy the game
took back, or that vanished, was not killed and does not come back. Asking stops at the first one the game refuses: that
one is dropped, counted, or it would hold back all the others for good. Nobody is asked while the hunter is dead, nor
for SETTLE_S after his place jumped: at his death in trial 6z bis his place read 16.8 km away and 1.8 km up for 4 s,
then where he came back; an enemy asked there would have been born in the air.
"""

import math
from typing import Any, Callable

from . import guard, horde, reads, zone_kinds

# The run's pace, a sample a second: the killed of one second are asked together.
EVERY_S = 1.0
# Farther than reads.JUMP_M in one sample, the hunter's place jumped (a death, a fast travel).
JUMP_M = reads.JUMP_M
# Long enough for a death's 4 s at the far place (trial 6z bis) to pass, with room to spare.
SETTLE_S = 10.0
# Decision 38: once until 5 minutes, then more each minute from the sixth, compounded (decision 39). The trials
# started it after 1 minute, only to see it within their 3 minutes. 14 % more each minute rather than decision 38's
# 20 % (decision 71, Kevin, 14 October 2026, after trial 15: « le timing de la monter exponentiel on devrait le reduire
# un petit peu [...] je pense reduire de peux etre 30% »): 30 % less growth a minute, so that a factor takes about 40 %
# longer to reach.
GROW_FROM_S = 300.0
GROWTH = 1.14
# Decision 39: the enemies that target the hunter within this radius are counted (Kevin: « oui 50 m c'est bon »).
RADIUS_M = 50.0
# Beyond RADIUS_M, an enemy within this many metres is on its way to the hunter, for the status line only.
ON_WAY_M = 100.0
# The share a sum of factors may fall short of a whole one in floating point.
EPSILON = 1e-9
# The births lost before they joined are looked for as often as the census draws the born (recruit.EVERY_S).
UNSEEN_EVERY_S = 5.0


def near(lines: list[dict]) -> int:
    """How many enemies of a sample's lines target the hunter within RADIUS_M (decision 39)."""
    return sum(1 for line in lines if line.get("target") == "player" and line.get("to_player_m") is not None
               and line["to_player_m"] <= RADIUS_M)


def where(lines: list[dict]) -> dict:
    """Where the enemies of a sample's lines stand, whatever they target: within RADIUS_M, within ON_WAY_M, farther,
    or unplaced. Why (trial 15): with 200 enemies in the horde, as few as 28 were counted near, and where the others
    stood was not written."""
    counts = dict.fromkeys(("close", "on_way", "far", "unplaced"), 0)
    for line in lines:
        metres = line.get("to_player_m")
        if metres is None:
            counts["unplaced"] += 1
        else:
            counts["close" if metres <= RADIUS_M else "on_way" if metres <= ON_WAY_M else "far"] += 1
    return counts


class Wave:
    """copies is a copies.Copies; note(event, **fields) writes a line to the SDK log (report.note); played(): the time
    played since the run began (clock.py), on which the growth counts, so that a pause of the game delays it as it
    stops the bar's time; level: the level chosen (levels.py), its target and its band, low to high; respawn: whether
    the killed come back (decision 44); most: the most enemies the horde holds (decision 96), as many as wait to come
    back, the killed beyond counted, not kept."""

    def __init__(self, copies: Any, note: Callable[..., None], played: Callable[[], float], level: Any,
                 respawn: bool, most: int = horde.CROWD_MAX) -> None:
        self.copies, self.note, self.played, self.level, self.respawn = copies, note, played, level, respawn
        self.most = most
        # The killed waiting to come back, as (name, kind), oldest first; one killed twice when it comes back twice.
        self.waiting: list[tuple[str, str]] = []
        self.asked_at = -math.inf
        self.place: tuple | None = None
        self.jumped_at = -math.inf
        self.broken: str | None = None
        # grow, hold or reduce (decision 39); the last count near; the share of a comeback carried to the next killed.
        self.mode, self.near, self.credit = "grow", None, 0.0
        # How many enemies followed the hunter at the last sample (regulate), for Kevin's rule; None before any.
        self.following: int | None = None
        self.unseen_at = -math.inf
        self.guard = guard.Guard(note)
        self.kinds = zone_kinds.ZoneKinds()
        self.counts = {"killed": 0, "born_again": 0, "extra": 0, "held_back": 0, "unknown_kind": 0, "waiting_full": 0,
                       "refused": 0, "respawn_off": 0, "unseen": 0, "left_behind": 0}

    def start(self, crowd: list, character: Any, pc: Any, here: tuple | None) -> Any:
        """The camp whose zone is lent, and the copies, made and written down: the zone as a Seen; None when none was
        made, and the run then writes why it does not start."""
        try:
            host, said = self.copies.ask(crowd, character, pc, here, self.most - len(crowd))
        except Exception as error:
            host, said = None, {"made": f"error:{type(error).__name__}"}
        self.note("copies", **said)
        return host

    def ours(self, camp: str | None) -> bool:
        return self.copies.ours(camp)

    def owes(self, camp: str | None) -> bool:
        return self.copies.owes(camp)

    def joined(self, camp: str | None) -> None:
        self.copies.joined(camp)

    def factor(self) -> float:
        """How many times a killed one comes back while the wave grows: once until GROW_FROM_S, then GROWTH times more
        for each minute begun."""
        since = self.played() - GROW_FROM_S
        return 1.0 if since < 0.0 else GROWTH ** (int(since // 60.0) + 1)

    def saw(self, kept: Any) -> int:
        """A census's kept enemies (census.Sighting.kept): the game's enemies among them are remembered where they
        stand, the kinds of their place (decisions 56 and 68). How many were met."""
        return self.kinds.saw(kept, self.copies.ours)

    def regulate(self, count: int, following: int | None = None) -> None:
        """The mode the count of enemies near puts the wave in, written down when it changes (decision 39); following,
        how many enemies the horde sampled, for Kevin's rule."""
        level, mode = self.level, self.mode
        self.following = following
        if count > level.high:
            mode = "reduce"
        elif count < level.low:
            mode = "grow"
        elif (self.mode == "reduce" and count <= level.target) or (self.mode == "grow" and count >= level.target):
            mode = "hold"
        self.near = count
        if mode != self.mode:
            self.note("regulated", mode=mode, was=self.mode, near=count, target=level.target)
            self.mode = mode

    def killed(self, name: str, kind: str) -> str:
        """An enemy of the horde seen killed: how many times it waits to come back, as the mode says, or why none. With
        the coming back off, it is counted and never waits."""
        self.counts["killed"] += 1
        return self._back(name, kind)

    def left_behind(self) -> str:
        """An enemy of the horde let go for being left behind, counted and never asked again (decision 98, after trial
        33: the one let go stayed alive and kept chasing the hunter, so that a second one born for it doubled it, held
        a camp, and the bar showed 13 enemies for the 120 copies alive); it joins again once back within reach."""
        self.counts["left_behind"] += 1
        return "rejoins_near"

    def _back(self, name: str, kind: str) -> str:
        if not self.respawn:
            self.counts["respawn_off"] += 1
            return "respawn_off"
        if not self.copies.knows(kind):
            self.counts["unknown_kind"] += 1
            return "unknown_kind"
        if self.mode == "reduce":
            self.counts["held_back"] += 1
            return "held_back"
        back = 1
        if self.mode == "grow":
            self.credit += self.factor()
            back = int(self.credit + EPSILON)
            self.credit -= back
        back = min(back, self.most - len(self.waiting))
        if back < 1:
            self.counts["waiting_full"] += 1
            return "waiting_full"
        self.waiting += [(name, kind)] * back
        self.counts["extra"] += back - 1
        return "waiting" if back == 1 else f"waiting_x{back}"

    def tick(self, character: Any, pc: Any, here: tuple | None, now: float) -> None:
        """Once a sample, the hunter's place kept; once EVERY_S at most, the killed waiting asked again, each as a
        kind of the place: those handed leave the list, and the first one
        the game refused with them, written down with the kinds born when someone was asked or the asking failed. An
        error ends the coming back for the rest of the run, said once: asked again each second, it would only fail
        again. Before, while the killed come back: the births lost before they joined, and Kevin's rule's group."""
        held = self._held(character, here, now)
        if self.respawn and now - self.unseen_at >= UNSEEN_EVERY_S:
            self.unseen_at = now
            lost = self.copies.unseen()[:self.most - len(self.waiting)]
            self.counts["unseen"] += len(lost)
            self.waiting += [("unseen", kind) for kind in lost]
        if self.respawn and not held and not self.waiting and self.following is not None:
            self.waiting += self.guard.group(self.following, now, self.kinds, here, self.copies.knows)
        if not self.waiting or self.broken is not None or now - self.asked_at < EVERY_S or held:
            return
        room = self.most - (self.following or 0) - self.copies.owing()
        if room < 1:
            return
        self.asked_at = now
        around = self.kinds.around(here, self.copies.knows)
        wanted = [(name, self.kinds.pick(kind, around)) for name, kind in self.waiting[:room]]
        try:
            said = self.copies.again(wanted, character, pc, here)
        except Exception as error:
            self.broken = f"error:{type(error).__name__}"
            self.note("born_again", again=self.broken, waiting=len(self.waiting))
            return
        handed = said["handed"]
        born = [name for name, _kind in wanted[:handed]]
        refused = [name for name, _kind in wanted[handed:handed + 1]] if handed < said.get("asked", 0) else []
        del self.waiting[:handed + len(refused)]
        self.counts["born_again"] += len(born)
        self.counts["refused"] += len(refused)
        if said["again"] != "done" or said["asked"] > 0:
            self.note("born_again", **said, of=born, kinds=[kind for _name, kind in wanted[:handed]], refused=refused,
                      waiting=len(self.waiting))

    def _held(self, character: Any, here: tuple | None, now: float) -> bool:
        """Whether nobody may be asked now: the hunter's place unread, the hunter dead, or his place jumped less than
        SETTLE_S ago. His place is kept at every sample, so that a jump is seen even while nobody waits."""
        if here is None:
            return True
        if self.place is not None and math.dist(here, self.place) > JUMP_M * 100.0:
            self.jumped_at = now
        self.place = here
        return reads.dead(character) is True or now - self.jumped_at < SETTLE_S

    def gauge(self) -> dict:
        """What a sample writes of the wave: the count near, the mode, the factor while it grows, those waiting, and
        the kinds of the place where the hunter stood at the last sample."""
        return {"near": self.near, "mode": self.mode, "factor": round(self.factor(), 3),
                "waiting": len(self.waiting), **self.kinds.gauge(self.place)}

    def status(self) -> dict:
        """It Follows' camps (copies.py), and the coming back: the killed, those born again and the extra among them,
        those held back or waiting, and why the others will not come back."""
        return {**self.copies.status(), **self.counts, "waiting": len(self.waiting), "broken": self.broken,
                "mode": self.mode}

    def put_back(self) -> str:
        """What the copies lifted, given back at the run's stop (copies.py)."""
        return self.copies.put_back()
