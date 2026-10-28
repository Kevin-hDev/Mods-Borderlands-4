"""Reinforcements, trials 138 to 141: a character's pace while it comes to the hunter: its own combat run locked while
it walks to him (sprint when far); its combat walk locked while it fights (trial 141); once it arrives and fights no
more, its passive walk locked then freed; and its speed bonus raised by FACTOR the whole follow.

Kevin, 20 October 2026: he must run, 20 % faster. Trial 137 read in game Lemmy walking in Stance_GunToter_Passive_Walk
(150 cm/s) and the stance functions' parameters: GbxStanceBlueprintLibrary.GetStanceForTag(Tag, OwnerContext) gives a
character's stance for a tag; GbxNavBlueprintLibrary.LockStance(Actor, reason, Block, stance) locks one;
GbxStanceBlueprintLibrary.UnlockStance(reason, OwnerContext) frees it. The game's data give his Passive_Run 400 and
Passive_Sprint 600 cm/s (docs/enemies/catalogues). Trial 138: the passive run and sprint locked, his stance and speed
followed, 4.8 and 7.2 m/s, but he kept his walk's animation: his three passive paces share one set of animations
(NavAnim_GunToter_Passive), his combat paces have their own (NavAnim_GunToter_Rifle_Combat); and UnlockStance left him
in the run. Hence trial 139: the combat tags, which char_ai, his root, maps to its combat stances; and the passive walk
locked before freeing (REST). A tag the game gives no stance for is said and nothing is locked. The bonus is It
Follows' (it_follows/speed.py): CharacterMovement.MaxGroundSpeedScale.Value times FACTOR, written again should the game
change it, the game's own written back at the end.

Trial 140: in a fight, unlocked, he went from his passive walk to his combat walk and back, again and again, with no
call of ours (Kevin saw it; the trace too, and trial 139's). His default stance is a picker (char_ai's stance.Default:
PickerStance_Aggro, game data Nexus-Data-Stance0): combat while the attribute ai_has_aggro holds, passive otherwise; his
aggro comes and goes. Hence FIGHT, locked while he fights and walks nowhere.

The bonus is each companion's own, the one its mod gives (tuning.py: in It Follows a card's off, +20 % or +30 %,
decision 50; in Companions a setting, decision 67); FACTOR, the trials' +20 %, is the one a follow gets when nothing
is given. Off, nothing is written.
"""

import math
import re
from typing import Any, Callable

import unrealsdk

STANCES = "GbxStanceBlueprintLibrary"
NAV = "GbxNavBlueprintLibrary"
RUN = "stance.Combat.Run"
SPRINT = "stance.Combat.Sprint"
REST = "stance.Passive.Walk"
FIGHT = "stance.Combat.Walk"
# Trial 138 read FGameDataHandle(12, 'Stance_GunToter_Passive_Run', None): the stance's name is the second field.
HANDLE_NAME = re.compile(r"FGameDataHandle\(\s*-?\d+\s*,\s*'([^']*)'")
# Sprint beyond SPRINT_M, back to the run within RUN_M: the gap keeps it from switching at every sample.
SPRINT_M = 30.0
RUN_M = 20.0
REASON = "Renforts"
BLOCK = True
FACTOR = 1.2
SAME = 1e-3
MAX_TEXT = 60


def _library(name: str) -> Any:
    return unrealsdk.find_class(name).ClassDefaultObject


def first(answer: Any) -> Any:
    """The return value of a call that may give its out parameters after it."""
    return answer[0] if isinstance(answer, tuple) else answer


def named(stance: Any) -> str | None:
    """The stance a handle names, None when it names none."""
    found = HANDLE_NAME.match(str(stance))
    name = found.group(1) if found else None
    return name if name and name != "None" else None


def stance_of(actor: Any) -> str | None:
    try:
        return str(actor.ReplicatedStance.stance._name)[:MAX_TEXT]
    except Exception:
        return None


class Pace:
    """One character's locked stance (locked: the tag, or None) and its speed bonus (base: the game's, once raised,
    times factor); actor is its weak pointer; note(text) says a call or a write before it is made."""

    def __init__(self, actor: Any, name: str, note: Callable[[str], None], factor: float = FACTOR) -> None:
        self.actor, self.name, self.note, self.factor = actor, name, note, factor
        self.locked: str | None = None
        self.base: float | None = None
        self.locks = 0

    def boost(self) -> str:
        """Raises the bonus by its factor, once; says the game's and the new value, or off for a factor of 1."""
        if abs(self.factor - 1.0) <= SAME:
            return "off"
        try:
            scale = self.actor().CharacterMovement.MaxGroundSpeedScale
            base = float(scale.Value)
            self.note(f"about to write MaxGroundSpeedScale {round(base * self.factor, 3)} on {self.name}")
            scale.Value = base * self.factor
            self.base = base
            return f"{round(base, 3)}->{round(float(scale.Value), 3)}"
        except Exception as error:
            return f"failed:{type(error).__name__}"

    def _hold_boost(self) -> str | None:
        if self.base is None:
            return None
        scale = self.actor().CharacterMovement.MaxGroundSpeedScale
        if abs(float(scale.Value) - self.base * self.factor) <= SAME:
            return None
        self.note(f"about to write MaxGroundSpeedScale again on {self.name}")
        scale.Value = self.base * self.factor
        return "boost_again"

    def _lock(self, tag: str) -> str:
        actor = self.actor()
        self.note(f"about to call GetStanceForTag {tag} on {self.name}")
        stance = first(_library(STANCES).GetStanceForTag(unrealsdk.make_struct("GameplayTag", TagName=tag), actor))
        if named(stance) is None:
            return f"no_stance:{tag.rsplit('.', 1)[-1]}:{str(stance)[:MAX_TEXT]}"
        if self.locked is not None:
            self._unlock(actor)
        self.note(f"about to call LockStance {str(stance)[:MAX_TEXT]} on {self.name}")
        _library(NAV).LockStance(actor, REASON, BLOCK, stance)
        self.locked = tag
        self.locks += 1
        return f"locked:{tag.rsplit('.', 1)[-1]}"

    def _unlock(self, actor: Any) -> None:
        self.note(f"about to call UnlockStance on {self.name}")
        self.locked = None
        _library(STANCES).UnlockStance(REASON, actor)

    def _rest(self) -> str:
        """Its passive walk locked, then freed: freeing alone leaves it in the stance last locked (trial 138)."""
        rested = self._lock(REST)
        self._unlock(self.actor())
        return "rested" if rested.startswith("locked") else f"unlocked:{rested}"

    def keep(self, walking: bool, to_hunter: float | None, fighting: bool) -> str:
        """Once a sample: the run locked while it walks to the hunter, the sprint beyond SPRINT_M until it is back
        within RUN_M; its combat walk locked while it fights without walking; its walk locked then freed once it
        neither walks nor fights (_rest); the bonus written again if the game changed it. Says what it did. A failing
        call raises."""
        again = self._hold_boost()
        done = "held"
        if not walking:
            if fighting:
                if self.locked != FIGHT:
                    done = self._lock(FIGHT)
            elif self.locked is not None:
                done = self._rest()
        elif to_hunter is not None and math.isfinite(to_hunter):
            wanted = self.locked if self.locked in (RUN, SPRINT) else RUN
            if to_hunter > SPRINT_M:
                wanted = SPRINT
            elif to_hunter < RUN_M:
                wanted = RUN
            if wanted != self.locked:
                done = self._lock(wanted)
        return f"{done},{again}" if again else done

    def put_back(self) -> dict:
        """Rests the stance (_rest) and writes the game's bonus back, each once; says how each went."""
        actor = self.actor()
        back: dict = {"stance": "not_locked", "boost": "not_boosted"}
        if self.locked is not None and actor is None:
            # Gone: the game dropped its lock with it, and no stance call is made on no character.
            self.locked, back["stance"] = None, "gone"
        elif self.locked is not None:
            try:
                back["stance"] = self._rest()
            except Exception as error:
                back["stance"] = f"failed:{type(error).__name__}"
        if self.base is not None:
            base, self.base = self.base, None
            try:
                self.note(f"about to write MaxGroundSpeedScale {round(base, 3)} back on {self.name}")
                actor.CharacterMovement.MaxGroundSpeedScale.Value = base
                back["boost"] = "restored"
            except Exception as error:
                back["boost"] = f"failed:{type(error).__name__}"
        return back
