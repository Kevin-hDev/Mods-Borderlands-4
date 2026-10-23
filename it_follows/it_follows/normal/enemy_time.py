"""The enemies' own time, sped up by the level while they dodge (decision 80) or play a gesture (decisions 121 and 124,
gestures.py), then given back. One owner for that field: a dodge within a gesture changes the factor, never takes the
enemy's own time twice nor gives back a sped one.

The dodges: Kevin, 15 October 2026: « ca doit plus vif qu'un dash de chasseur »; ×2, ×3 and ×4 seen and kept by him at
trial 21 (« j'ai bien vue les differences de vitesse d'esquive,, c'est bon comme ca »). The gestures: ×1.1, ×1.2 and
×1.3 (decision 121), the grenades and the turrets set down left to the game.

The lever is the enemy research's (apex_probe/enemy_boost.py, vérifié en jeu at ×4, ×5 and ×6, séance 7), which trial
21 used (docs/RUN/sondes/run_dodge_watch.py): the character's CustomTimeDilation {Value, BaseValue}, sped up while
AIDodgeState.ActiveDodge holds an Action. A dodge lasts 68 to 401 ms: only a look at each image sees it, through the
game's animation update (frame.HOOK) under a name of its own, one call let through every FRAME_GAP_S. A gesture lasts
0.8 to 4.3 s (trial 63): its scripts are read every GESTURE_GAP_S only, on the GESTURE_MOST nearest, since reading six
enemies 30 times a second cost the game some 15 ms a second there. The enemies looked at are the nearest the last
census found (enemies.nearest). One held is looked at until its time is given back, even once out of that list: an
enemy left sped up would stay fast. Its time is written back even dead, a value and not a call.

A value the game wrote over the level's meanwhile is the game's own and stays: it is given back as the game left it,
and a new factor is laid on it (audit of 17 October 2026: a gesture lasts up to 8 s, and giving back the time read at
its start would undo what the game did meanwhile). Each of the two values on its own: the game may change one only.

In co-op the enemies near a guest dodge at the game's speed (decision 132): the guest's copy plays a dodge sped on the
host at the game's speed, stops short, then pops to where the host put it (trial 77, Kevin: « quand les esquives
accelerer son desactiver, le probleme n'est plus présent »). Their gestures are still sped.
"""

from itertools import islice
from typing import Any, Callable

from mods_base import hook
from unrealsdk.hooks import Type

from .. import frame, game_thread
from . import gestures

IDENTIFIER = "it_follows:normal_time"
FIELD = "CustomTimeDilation"
FRAME_GAP_S = 0.008
GESTURE_GAP_S = 0.05
GESTURE_MOST = 12
MAX_HELD = 32
MAX_STUCK = 64
DODGE, GESTURE = "dodge", "gesture"
# Two values read back as written, the field being 32-bit floats.
CLOSE = 1e-4
# Longer than any dodge (401 ms) or gesture (4.3 s) measured: past it the time is given back whatever the state says.
LONGEST_S = {DODGE: 3.0, GESTURE: 8.0}
# The gestures' scripts named in the log the first time each is sped up, at most this many.
MAX_SAID = 64


def dodging(pawn: Any) -> Any:
    """The dodge's action while one plays, else None."""
    return pawn.AIDodgeState.ActiveDodge.Action


def _time(pawn: Any) -> tuple[float, float]:
    pair = getattr(pawn, FIELD)
    return float(pair.BaseValue), float(pair.Value)


def _set_time(pawn: Any, values: tuple[float, float]) -> None:
    pair = getattr(pawn, FIELD)
    pair.BaseValue, pair.Value = values
    # Assigned back whole: the SDK may hand out a copy of the struct (enemy_boost.py).
    setattr(pawn, FIELD, pair)


def _close(one: float, other: float) -> bool:
    return abs(one - other) <= CLOSE * max(1.0, abs(other))


class EnemyTime:
    """note(event, **fields) writes a line; dodge and gesture are the factors, None when not sped; fail(reason) ends
    the mode when a look raises."""

    def __init__(self, note: Callable[..., None], dodge: float | None, gesture: float | None,
                 fail: Callable[[str], None]) -> None:
        self.note, self.fail = note, fail
        self.factors = {DODGE: dodge, GESTURE: gesture}
        self.watched: dict[str, Any] = {}
        self.plain: frozenset[str] = frozenset()
        # By name: its weak pointer, what speeds it and since when, and its own time to give back.
        self.held: dict[str, dict] = {}
        # Given back at LONGEST_S while it still did the same, DODGE or the gesture's script: not taken again while it
        # still does that. The oldest forgotten past MAX_STUCK.
        self.stuck: dict[str, str] = {}
        # By name, the gesture script the last read found, for the GESTURE_MOST nearest and those held.
        self.playing: dict[str, str] = {}
        self.counts = {DODGE: 0, GESTURE: 0}
        self.failed: set[str] = set()
        self.said: set[str] = set()
        self.hook: Any = None
        self.guard: game_thread.Guard | None = None
        self.last = 0.0
        self.last_gestures = 0.0

    def start(self) -> None:
        # On the game's thread, as the hook: a call that comes elsewhere does nothing (game_thread.py).
        self.guard = game_thread.Guard(IDENTIFIER)
        self.hook = hook(frame.HOOK, Type.POST, hook_identifier=IDENTIFIER)(self._frame)
        self.hook.enable()

    def follow(self, watched: dict[str, Any], plain: frozenset[str] = frozenset()) -> None:
        """The enemies to look at from now on, by name, nearest first, each a weak pointer; plain: those whose dodges
        are left to the game."""
        self.watched, self.plain = watched, plain

    def _frame(self, *_args: Any) -> None:
        if self.hook is None or (self.guard is not None and not self.guard.here()):
            return
        moment = frame.now()
        if moment - self.last < FRAME_GAP_S:
            return
        self.last = moment
        try:
            self.look(moment)
        except Exception as error:
            self.fail(f"time_error:{type(error).__name__}")

    def look(self, now: float) -> None:
        """One image: each enemy that begins a dodge or a gesture sped up, each that ends given back."""
        if self.factors[GESTURE] is not None and now - self.last_gestures >= GESTURE_GAP_S:
            self.last_gestures = now
            self._read_gestures()
        for name in set(self.watched) | set(self.held):
            held = self.held.get(name)
            pawn = (held["pointer"] if held is not None else self.watched[name])()
            if pawn is None:
                self.held.pop(name, None)
                continue
            doing = self._doing(name, pawn)
            if held is None:
                if doing is not None and len(self.held) < MAX_HELD:
                    self._take(name, pawn, doing, now)
            elif doing is None:
                self._give_back(name, pawn)
            elif doing != held["doing"]:
                self._speed(name, pawn, doing, now)
            elif now - held["at"] > LONGEST_S[doing]:
                self._give_back(name, pawn)
                self._stick(name, doing)

    def _doing(self, name: str, pawn: Any) -> str | None:
        """What speeds the enemy now: a dodge first, else a gesture, else None. With the dodges left to the game, for
        all or for this enemy (plain), a dodge within a gesture plays at the game's speed too (decision 121)."""
        dodge = self._dodging(pawn)
        script = self.playing.get(name)
        stuck = self.stuck.get(name)
        if stuck == DODGE and not dodge or stuck not in (None, DODGE) and stuck != script:
            self.stuck.pop(name)
            stuck = None
        if dodge:
            if self.factors[DODGE] is None or name in self.plain:
                return None
            if stuck != DODGE:
                return DODGE
        return GESTURE if script is not None and stuck != script else None

    def _dodging(self, pawn: Any) -> bool:
        try:
            return dodging(pawn) is not None
        except Exception as error:
            self._say_once("dodge_read", error)
            return False

    def _stick(self, name: str, doing: str) -> None:
        marker = DODGE if doing == DODGE else self.playing.get(name)
        if marker is None:
            return
        self.stuck.pop(name, None)
        if len(self.stuck) >= MAX_STUCK:
            self.stuck.pop(next(iter(self.stuck)))
        self.stuck[name] = marker

    def _read_gestures(self) -> None:
        looked = dict(islice(self.watched.items(), GESTURE_MOST))
        looked.update({name: held["pointer"] for name, held in self.held.items()})
        playing = {}
        for name, pointer in looked.items():
            pawn = pointer()
            if pawn is None:
                continue
            try:
                script = gestures.playing(pawn)
            except Exception as error:
                self._say_once("gesture_read", error)
                continue
            if script is not None:
                playing[name] = script
        self.playing = playing

    def _say_once(self, what: str, error: Exception) -> None:
        key = f"{what}:{type(error).__name__}"
        if key not in self.failed:
            self.failed.add(key)
            self.note("normal_time_failed", what=what, error=type(error).__name__)

    def _take(self, name: str, pawn: Any, doing: str, now: float) -> None:
        try:
            original = _time(pawn)
        except Exception as error:
            # Not tried again before it does something else.
            self._stick(name, doing)
            self._say_once("read", error)
            return
        # Held before the write: a write that fails half way may have sped the enemy up all the same.
        self.held[name] = {"pointer": self.watched[name], "original": original, "wrote": None}
        self._speed(name, pawn, doing, now)

    def _own(self, held: dict, pawn: Any) -> tuple[float, float]:
        """The enemy's own time: the one taken, each value the game wrote since the last write taken as its own."""
        if held["wrote"] is not None:
            try:
                now = _time(pawn)
            except Exception as error:
                self._say_once("read", error)
                return held["original"]
            held["original"] = tuple(own if _close(read, wrote) else read
                                     for own, read, wrote in zip(held["original"], now, held["wrote"]))
        return held["original"]

    def _speed(self, name: str, pawn: Any, doing: str, now: float) -> None:
        held = self.held[name]
        held["doing"], held["at"] = doing, now
        self.counts[doing] += 1
        factor = self.factors[doing]
        script = self.playing.get(name) if doing == GESTURE else None
        if script is not None and script not in self.said and len(self.said) < MAX_SAID:
            self.said.add(script)
            self.note("normal_gesture_sped", script=script, factor=factor)
        original = self._own(held, pawn)
        held["wrote"] = (original[0] * factor, original[1] * factor)
        try:
            _set_time(pawn, held["wrote"])
        except Exception as error:
            self._say_once("write", error)

    def _give_back(self, name: str, pawn: Any) -> None:
        held = self.held.pop(name)
        try:
            _set_time(pawn, self._own(held, pawn))
        except Exception as error:
            self._say_once("give_back", error)

    def stop(self) -> dict:
        """Unhooked, and each enemy still sped up given its own time back: how many dodges and gestures were."""
        active, self.hook = self.hook, None
        unhooked = "inactive"
        if active is not None:
            try:
                active.disable()
                unhooked = "removed"
            except Exception:
                unhooked = "remove_failed"
        for name in list(self.held):
            pawn = self.held[name]["pointer"]()
            if pawn is None:
                self.held.pop(name)
                continue
            self._give_back(name, pawn)
        self.watched, self.stuck, self.playing = {}, {}, {}
        return {"dodges": self.counts[DODGE], "gestures": self.counts[GESTURE], "hook": unhooked}
