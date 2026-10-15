"""The level's quicker dodges (decision 80): while an enemy dodges, its own time runs the level's times faster, then is
given back. Kevin, 15 October 2026: « ca doit plus vif qu'un dash de chasseur »; ×2, ×3 and ×4 seen and kept by him at
trial 21 (« j'ai bien vue les differences de vitesse d'esquive,, c'est bon comme ca »).

The lever is the enemy research's (apex_probe/enemy_boost.py, vérifié en jeu at ×4, ×5 and ×6, séance 7), which trial
21 used (docs/RUN/sondes/run_dodge_watch.py): the character's CustomTimeDilation {Value, BaseValue}, sped up while
AIDodgeState.ActiveDodge holds an Action. A dodge lasts 68 to 401 ms: only a look at each image sees it, through the
game's animation update (frame.HOOK) under a name of its own, one call let through every FRAME_GAP_S. The enemies looked
at are the nearest the last census found (enemies.nearest). One held is looked at until its dodge ends, even once out
of that list: an enemy left sped up would stay fast. Its time is written back even dead, a value and not a call.
"""

from typing import Any, Callable

from mods_base import hook
from unrealsdk.hooks import Type

from .. import frame

IDENTIFIER = "it_follows:normal_dodges"
FIELD = "CustomTimeDilation"
FRAME_GAP_S = 0.008
MAX_HELD = 32
# Longer than any dodge measured: past it the time is given back whatever the state says.
LONGEST_S = 3.0


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


class DodgeSpeed:
    """note(event, **fields) writes a line; fail(reason) ends the mode when a look raises."""

    def __init__(self, note: Callable[..., None], factor: float, fail: Callable[[str], None]) -> None:
        self.note, self.factor, self.fail = note, factor, fail
        self.watched: dict[str, Any] = {}
        # By name: its weak pointer, when the dodge began, and its own time to give back.
        self.held: dict[str, dict] = {}
        # Given back at LONGEST_S while their state still said dodging: not taken again until it says otherwise.
        self.stuck: set[str] = set()
        self.count = 0
        self.failed: set[str] = set()
        self.hook: Any = None
        self.last = 0.0

    def start(self) -> None:
        self.hook = hook(frame.HOOK, Type.POST, hook_identifier=IDENTIFIER)(self._frame)
        self.hook.enable()

    def follow(self, watched: dict[str, Any]) -> None:
        """The enemies to look at from now on, by name, each a weak pointer."""
        self.watched = watched

    def _frame(self, *_args: Any) -> None:
        if self.hook is None:
            return
        moment = frame.now()
        if moment - self.last < FRAME_GAP_S:
            return
        self.last = moment
        try:
            self.look(moment)
        except Exception as error:
            self.fail(f"dodge_error:{type(error).__name__}")

    def look(self, now: float) -> None:
        """One image: each dodge that begins sped up, each that ends given back."""
        for name in set(self.watched) | set(self.held):
            held = self.held.get(name)
            pawn = (held["pointer"] if held is not None else self.watched[name])()
            if pawn is None:
                self.held.pop(name, None)
                continue
            try:
                action = dodging(pawn)
            except Exception:
                action = None
            if action is None:
                self.stuck.discard(name)
            if held is not None:
                if action is None or now - held["at"] > LONGEST_S:
                    self._give_back(name, pawn)
                    if action is not None:
                        self.stuck.add(name)
            elif action is not None and name not in self.stuck and len(self.held) < MAX_HELD:
                self._take(name, pawn, now)

    def _say_once(self, what: str, error: Exception) -> None:
        key = f"{what}:{type(error).__name__}"
        if key not in self.failed:
            self.failed.add(key)
            self.note("normal_dodge_speed_failed", what=what, error=type(error).__name__)

    def _take(self, name: str, pawn: Any, now: float) -> None:
        try:
            original = _time(pawn)
        except Exception as error:
            # Not tried again before this dodge ends.
            self.stuck.add(name)
            self._say_once("read", error)
            return
        self.count += 1
        # Held before the write: a write that fails half way may have sped the enemy up all the same.
        self.held[name] = {"pointer": self.watched[name], "at": now, "original": original}
        try:
            _set_time(pawn, (original[0] * self.factor, original[1] * self.factor))
        except Exception as error:
            self._say_once("write", error)

    def _give_back(self, name: str, pawn: Any) -> None:
        held = self.held.pop(name)
        try:
            _set_time(pawn, held["original"])
        except Exception as error:
            self._say_once("give_back", error)

    def stop(self) -> dict:
        """Unhooked, and each enemy still dodging given its own time back: how many dodges were sped up."""
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
        self.watched, self.stuck = {}, set()
        return {"dodges": self.count, "hook": unhooked}
