"""Reinforcements, trial 140: a reinforcement fights before it follows. Once a living enemy of the hunter stands within
COMBAT_M of the hunter or of it, the nearest one to it is imposed as its target; the next once that one is dead, gone
or out of reach; the target cleared once none is left.

Kevin, 20 October 2026, after trial 139: « il pense avant tout a me suivre quand on est en plein combat plutot que de
se battres, il court a coter des ennemies, passe devant eu sans rien faire pour me suivre et meme sur place il met
beaucoup de temps a reagir ». The imposed target is It Follows' (it_follows/target.py, TargetPatch, handed in):
AISetScriptedTarget without the game's restrictions, read back, cleared only if still its own;
the research held such a target 80 to 280 s (séance 31). It Follows imposes the hunter on enemies; here an enemy is
imposed on an ally. An enemy is the hunter's, by the game's attitude (hostile, docs/spawn-boss/enquetes/
2026-10-11-equipes-des-ennemis.md). The follow reads `fighting` to stop its walks while the fight lasts. A target the
game refuses is said and tried again at the next sample, as It Follows does: the enemy stays the one fought.
"""

import math
from itertools import islice
from typing import Any, Callable

import unrealsdk

COMBAT_M = 35.0
CHARACTER = "OakCharacter"
MOST_SCAN = 1000
MAX_TEXT = 60


def characters(pc: Any) -> list:
    """The world's characters, MOST_SCAN at most, read without a line: once a second, and every
    respawn.FIND_EVERY_S while a companion asked is not found yet."""
    statics = unrealsdk.find_class("GameplayStatics").ClassDefaultObject
    _void, actors = statics.GetAllActorsOfClass(WorldContextObject=pc, ActorClass=unrealsdk.find_class(CHARACTER),
                                                OutActors=[])
    return list(islice(actors, MOST_SCAN))


class Fight:
    """One character's fights: actor its weak pointer; read the reads of world.py; targets It Follows' target
    module; weak(actor) a weak pointer; note(text) says a call before it is made."""

    def __init__(self, actor: Any, name: str, note: Callable[[str], None], read: Any, targets: Any,
                 weak: Callable[[Any], Callable[[], Any]]) -> None:
        self.actor, self.name, self.note = actor, name, note
        self.read, self.targets, self.weak = read, targets, weak
        self.foe: Callable[[], Any] | None = None
        self.foe_name: str | None = None
        self.patch: Any = None
        self.imposed = 0

    @property
    def fighting(self) -> bool:
        return self.foe is not None

    def _near(self, foe: Any, places: tuple) -> float | None:
        """Its distance to the character when within COMBAT_M of the hunter or of the character, alive; else None."""
        if foe is None or self.read.dead(foe) is True:
            return None
        at = self.read.place(foe)
        gaps = [gap for place in places if (gap := self.read.metres(at, place)) is not None]
        if not gaps or min(gaps) > COMBAT_M:
            return None
        return gaps[-1]

    def nearest(self, characters: list, player: Any, here: tuple, mine: tuple) -> Any:
        """The hunter's living enemy nearest the character, within COMBAT_M of either; None if there is none."""
        best, best_m = None, math.inf
        for foe in characters:
            gap = self._near(foe, (here, mine))
            if gap is not None and gap < best_m and self.read.attitude(player, foe) == "hostile":
                best, best_m = foe, gap
        return best

    def keep(self, characters: list, player: Any, here: tuple | None, mine: tuple | None) -> str:
        """Once a sample: the target kept while it stands near and alive, imposed again if the game cleared or refused
        it; else released and the nearest enemy imposed; calm when none. Says what it did. A failing read raises."""
        if here is None or mine is None:
            return "unknown"
        foe = self.foe() if self.foe is not None else None
        if foe is not None and self._near(foe, (here, mine)) is not None:
            if self.patch is not None and self.patch.read() == "player":
                return f"fighting:{self.foe_name}"
            self._clear()
            return self._impose(foe)
        done = self.release()
        foe = self.nearest(characters, player, here, mine)
        if foe is None:
            return "calm" if done == "inactive" else f"calm:{done}"
        return self._impose(foe)

    def _impose(self, foe: Any) -> str:
        self.foe, self.foe_name = self.weak(foe), str(foe.Name)[:MAX_TEXT]
        self.patch = self.targets.imposed(self.actor, self.foe)
        self.note(f"about to call AISetScriptedTarget {self.foe_name} on {self.name}")
        try:
            self.patch.apply()
        except Exception as error:
            self._clear()
            return f"refused:{self.foe_name}:{type(error).__name__}"
        self.imposed += 1
        return f"target:{self.foe_name}"

    def _clear(self) -> str:
        """Clears the target it imposed, if the game still holds it, the enemy kept; says how it ended."""
        patch, self.patch = self.patch, None
        if patch is None:
            return "inactive"
        self.note(f"about to call AIClearScriptedTarget on {self.name}")
        try:
            return str(patch.restore())
        except Exception as error:
            return f"restore_error:{type(error).__name__}"

    def release(self) -> str:
        """The target cleared and the enemy forgotten; says how it ended."""
        done = self._clear()
        self.foe, self.foe_name = None, None
        return done
