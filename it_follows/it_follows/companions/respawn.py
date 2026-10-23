"""The companions on their way: called when the team starts (call), or dead and coming back AFTER_S later (died;
decision 23 of docs/renforts, Kevin, 20 October 2026: « Si un compagnon meurt on fait le respawn au bout de 45
secondes »; trial 183).

The follow tells died() when it reads its companion dead (HealthState.bCurrentlyDead). When one is due, the same
companion is asked of the companions' own camps in front of the hunter (birth.py), then found by its spawner
and followed as any other, with the same health. Born in front of him so that the player sees it come; a spawner is
never destroyed (destroying an actor we spawned crashed the game, 2026-10-05): a dead one's spawner is handed the next
companion, as It Follows' camps do for its enemies (camps.py), where the trials made a fresh one each time.

Nobody is asked while the hunter is dead, not on foot (in the air, a companion would be born in the air, decision 26;
driving, in front of his vehicle), nor for SETTLE_S after his place jumped JUMP_M (It Follows' wave.py: at his death
his place read 16.8 km away for 4 s). One is asked a beat at most, so that two dead together are not born in one
another. Once asked, it is looked for each beat until FIND_S: a spawner's character is not there the moment it is
asked; one not found by then is asked again, ASKS_MOST asks in all. A companion refused, lost or failing is dropped
and said; the others go on. Waiting ones are MOST at most, the team's size: there cannot be more dead than companions.

A companion the game took away (gone, never read dead), or whose follow ended otherwise, is called back by the team
(team.py, decision 59): after a map change, the team comes back by itself.

Since trial 186, a companion downed counts as dead once the game hides it or takes it away (Fall). The Decrepit Frame
can be downed (its definition's bcanbedowned): at 0 health it is downed, not dead, and the player can revive it, as a
teammate (trial 184); left so, the game hides it at the world's origin some 30 s later, then takes it away, never
reading it dead (trials 183 to 185, three times out of three). Kevin, 21 October 2026: « on garde sa reanimation comme
actuellement, comme ca il est re animable et sil n'est pas reanimer il meurt et respawn comme les autres ».
"""

import math
from typing import Any, Callable

AFTER_S = 45.0
EVERY_S = 1.0
# One asked is looked for this often between beats (trial 190: found a beat after its birth, a hunter showed as
# Lemmy for a second before he was hidden and dressed). Only while one is asked: the search reads every character.
FIND_EVERY_S = 0.05
FIND_S = 15.0
# Until FIND_S, only these answers give one up: any other (not there yet, the hunter unread, a call failing) may pass.
FINAL = ("unknown", "team_full", "followed_already")
# Asked and never found within FIND_S, it is asked again, this many asks in all; then lost (review of 22 October 2026:
# lost at once, the team kept one fewer for good).
ASKS_MOST = 2
SETTLE_S = 10.0
# It Follows' reads.JUMP_M: farther in one beat, his place jumped (a death, a fast travel).
JUMP_M = 200.0
# On foot only: birth.py asks the companion 3 m in front of him, at his height.
FOOT = ("MOVE_Walking", "MOVE_NavWalking")
MAX_TEXT = 120
# Within this of the world's origin, flat, a companion is hidden there (trials 183 to 185 read it at 0.0 m).
ORIGIN_CM = 100.0


class Fall:
    """How a companion's follow ends at its death: read dead, or seen downed (its health at 0) then hidden at the
    world's origin or taken away. A companion revived stays seen downed: if the game hides it later, it died."""

    def __init__(self) -> None:
        self.downed = False

    def end(self, actor: Any, dead: bool | None, health: float | None, place: tuple | None) -> str | None:
        """character_dead, character_gone (taken away, never seen downed), or None while it lives."""
        if actor is None:
            return "character_dead" if self.downed else "character_gone"
        if dead is True:
            return "character_dead"
        self.downed = self.downed or health == 0.0
        if self.downed and place is not None and math.hypot(place[0], place[1]) < ORIGIN_CM:
            return "character_dead"
        return None


def looked(pc: Any, read: Any, mode_of: Callable[[Any], Any]) -> tuple:
    """The hunter's character's (place, dead, mode), read as the follow reads him (world.py)."""
    character = getattr(pc, "OakCharacter", None)
    return read.place(character), read.dead(character), mode_of(character)


class Respawns:
    """The companions called or dead, waiting to come, each known by its name in kinds.py: the six hunters share
    Lemmy's definition, and a Rafa dead must come back Rafa. look() gives the hunter's (place, dead, mode);
    spawn(companion) asks one and gives birth.Births.ask's answer; start(companion, spawner, times) follows the one
    that spawner bore and gives team.Team.join's answer; note(event, **fields) says what happens (report.note);
    clock() the follows' time."""

    def __init__(self, look: Callable[[], tuple], spawn: Callable[[str], dict],
                 start: Callable[[str, str, float | None], dict], note: Callable[..., None], most: int,
                 clock: Callable[[], float], after_s: float = AFTER_S) -> None:
        self.look, self.spawn, self.start, self.note, self.clock = look, spawn, start, note, clock
        self.most, self.after_s = most, after_s
        self.waiting: list[dict] = []
        self.next = self.next_find = 0.0
        self.last: tuple | None = None
        self.last_at = self.jumped_at = -math.inf
        self.back = self.lost = 0

    def died(self, companion: str, times: float | None) -> None:
        if self._wait(companion, times, self.after_s):
            self.note("companion_dead", companion=companion, back_in_s=self.after_s)

    def call(self, companion: str, times: float | None) -> None:
        """One more for the team, asked as soon as the hunter may have one born."""
        if self._wait(companion, times, 0.0):
            self.note("companion_called", companion=companion)

    def _wait(self, companion: str, times: float | None, after_s: float) -> bool:
        if len(self.waiting) >= self.most:
            self.note("companion_refused", companion=companion, waiting=len(self.waiting))
            return False
        self.waiting.append({"companion": companion, "times": times, "due": self.clock() + after_s,
                             "after_s": after_s, "spawner": None, "asked": None, "why": None, "asks": 0})
        return True

    def pending(self) -> bool:
        return bool(self.waiting)

    def clear(self) -> int:
        """Forgets the waiting ones (the team stopped); says how many."""
        count, self.waiting = len(self.waiting), []
        return count

    def beat(self) -> None:
        """Each EVERY_S, one due asked and those asked looked for; in between, every FIND_EVERY_S, those asked
        looked for."""
        now = self.clock()
        if not self.waiting:
            return
        if now >= self.next:
            self.next = now + EVERY_S
            self._turn(now, True)
        elif now >= self.next_find and any(one["spawner"] is not None for one in self.waiting):
            self._turn(now, False)
        else:
            return
        self.next_find = now + FIND_EVERY_S

    def _turn(self, now: float, may_ask: bool) -> None:
        asked = False
        for one in list(self.waiting):
            try:
                if one["spawner"] is not None:
                    self._find(one, now)
                elif may_ask and now >= one["due"] and not asked:
                    asked = self._may(one, now)
                    if asked:
                        self._ask(one, now)
            except Exception as error:
                why = f"failed:{type(error).__name__}:{str(error)[:MAX_TEXT]}"
                if one["spawner"] is None or now - one["asked"] >= FIND_S:
                    self._drop(one, why)

    def why_not(self, now: float) -> str | None:
        """Why no companion may be born now, None when one may."""
        place, dead, mode = self.look()
        if place is None:
            return "no_hunter"
        if self.last is not None and now - self.last_at <= 2 * EVERY_S \
                and math.dist(place, self.last) / 100.0 > JUMP_M:
            self.jumped_at = now
        self.last, self.last_at = place, now
        if dead is True:
            return "hunter_dead"
        if now - self.jumped_at < SETTLE_S:
            return "hunter_moved"
        return None if mode in FOOT else "not_on_foot"

    def _may(self, one: dict, now: float) -> bool:
        """Whether it may be asked now; why not said when it changes."""
        why = self.why_not(now)
        if why is not None and why != one["why"]:
            one["why"] = why
            self.note("companion_waits", companion=one["companion"], why=why)
        return why is None

    def _ask(self, one: dict, now: float) -> None:
        self.note("companion_asked", companion=one["companion"], late_s=round(now - one["due"], 1))
        spawner = self.spawn(one["companion"]).get("spawner")
        if not isinstance(spawner, str):
            self._drop(one, "not_asked")
        else:
            one["spawner"], one["asked"] = spawner, now
            one["asks"] += 1

    def _find(self, one: dict, now: float) -> None:
        done = self.start(one["companion"], one["spawner"], one["times"]).get("done")
        if done == "started":
            self.waiting.remove(one)
            self.back += 1
            self.note("companion_back", companion=one["companion"], spawner=one["spawner"],
                      after_s=round(now - one["due"] + one["after_s"], 1))
        elif done in FINAL or now - one["asked"] >= FIND_S:
            self._drop(one, str(done))

    def _drop(self, one: dict, why: str) -> None:
        """One given up; asked and never found, it is asked again, ASKS_MOST times in all."""
        if one in self.waiting and one["spawner"] is not None and one["asks"] < ASKS_MOST and why not in FINAL:
            one.update(spawner=None, asked=None, why=None, due=self.clock())
            self.note("companion_asked_again", companion=one["companion"], why=why, asks=one["asks"])
            return
        if one in self.waiting:
            self.waiting.remove(one)
        self.lost += 1
        self.note("companion_lost", companion=one["companion"], why=why)
