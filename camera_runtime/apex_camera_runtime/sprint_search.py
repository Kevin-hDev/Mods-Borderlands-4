"""Twice a second: finds the movement definition of the character played and keeps its sprint limit open, or puts it
back when nobody asks for the open sprint any more.

Moved from Omni Sprint's frame.py on 2026-10-09 (docs/omni_direction/spec-omni-direction.md). Loading a game makes a
new character, while a fast travel keeps it (2026-09-19, verified in game), and each character has its own definition,
so a new movement component means a new search. A definition not found yet is searched again later; one never found,
or found but not opened, is said once and left alone until the character changes.
"""

from typing import Any, Callable

from . import movement_definition as definition
from .sprint_limit import Limits, Lost, NotOpened

MS = 1_000_000
# Twice a second: a sprint started just after a zone change is opened within half a second.
CHECK_NS = 500 * MS
# While a game loads, the character exists before its definition can be found: on 2026-09-19 (13:39:40) the first
# search missed, and the same character's search found it two minutes later. So a miss is searched again, waiting
# twice as long each time up to RETRY_MAX_NS, and given up after MAX_TRIES, about two minutes in all.
RETRY_FIRST_NS = 500 * MS
RETRY_MAX_NS = 16_000 * MS
MAX_TRIES = 12
# Lines said once: bounded, a handful of characters per session.
MAX_SAID = 64


def component_address(pc: Any) -> int:
    """The address of the played character's movement component, 0 without a character (title screen, wheel)."""
    character = getattr(pc, "OakCharacter", None) if pc is not None else None
    movement = getattr(character, "CharacterMovement", None) if character is not None else None
    return int(movement._get_address()) if movement is not None else 0


class SprintKeeper:
    def __init__(self, log: Callable[[str], None]) -> None:
        self.log = log
        self.limits = Limits()
        self.said: set[str] = set()
        self.reset()

    def reset(self) -> None:
        self.shape: definition.Layout | None = None
        self.shape_read = False
        self.next_ns = 0
        # Until when the game's limit is back for a ground dash (crouch_dash.py); 0 while the limit is open.
        self.lowered_until = 0
        self._follow(0, 0)

    def _follow(self, component: int, now_ns: int) -> None:
        self.component, self.definition, self.tries = component, 0, 0
        self.next_search_ns, self.given_up = now_ns, False

    def _once(self, key: str, line: str) -> None:
        if key not in self.said and len(self.said) < MAX_SAID:
            self.said.add(key)
            self.log(line)

    def _layout(self) -> definition.Layout | None:
        # Read once per start: the type is the game's own and does not change while it runs.
        if not self.shape_read:
            self.shape_read = True
            self.shape = definition.layout()
            if self.shape is None:
                self._once("layout", f"the game's {definition.TYPE_NAME} type has changed: sprint limit not written")
        return self.shape

    def _look(self, shape: definition.Layout, now_ns: int) -> None:
        found = definition.find(self.component, shape)
        self.tries += 1
        if found is not None:
            self.definition = found.address
            after = f", after {self.tries} searches" if self.tries > 1 else ""
            self.log(f"movement definition found at {found.address:#x}, movement component +{found.slot:#x}{after}")
            return
        if self.tries >= MAX_TRIES:
            self.given_up = True
            self._once(f"none:{self.component:#x}", f"no movement definition found for this character after "
                                                    f"{self.tries} searches: sprint limit not written")
            return
        self.next_search_ns = now_ns + min(RETRY_FIRST_NS * 2 ** (self.tries - 1), RETRY_MAX_NS)

    def update(self, pc: Any, wanted: bool, now_ns: int) -> None:
        if now_ns < self.next_ns:
            return
        self.next_ns = now_ns + CHECK_NS
        shape = self._layout()
        if not wanted:
            self._give_back(shape)
            return
        component = component_address(pc) if shape is not None else 0
        if component == 0:
            return
        if component != self.component:
            self._follow(component, now_ns)
        if self.given_up:
            return
        if self.definition == 0:
            if now_ns >= self.next_search_ns:
                self._look(shape, now_ns)
            if self.definition == 0:
                return
        if self.lowered_until:
            return
        try:
            line = self.limits.hold(self.definition, shape)
        except Lost as exc:
            self.log(f"{exc}: looking for it again")
            self.component = 0
            return
        except NotOpened as exc:
            self._once(str(exc), str(exc))
            self.given_up = True
            return
        if line is not None:
            self.log(line)

    def lower(self, now_ns: int, duration_ns: int) -> bool:
        """The game's limit back for duration_ns: the ground dash the game only gives beyond it."""
        if not self.definition or self.shape is None:
            return False
        if not self.limits.lower(self.definition, self.shape):
            return False
        self.lowered_until = now_ns + duration_ns
        return True

    def reopen_if_due(self, now_ns: int) -> None:
        """Called every frame: 180 again as soon as the dash's time is over, not at the next check."""
        if self.lowered_until and now_ns >= self.lowered_until:
            self.lowered_until = 0
            if self.definition and self.shape is not None:
                self.limits.reopen(self.definition, self.shape)

    def _give_back(self, shape: definition.Layout | None) -> None:
        self.lowered_until = 0
        restored, left = self.limits.put_back(shape)
        if restored or left:
            line = f"open sprint no longer asked, game sprint limit put back in {restored} movement definition(s)"
            self.log(line + (f", {left} left alone: no longer recognised in memory" if left else ""))

    def stop(self) -> tuple[int, int]:
        """Puts back every limit opened: (put back, left alone)."""
        # A limit is only ever opened with the layout read: without one, there is nothing to put back.
        shape = self.shape
        self.reset()
        return self.limits.put_back(shape)
