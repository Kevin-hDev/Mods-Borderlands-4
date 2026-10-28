"""Gives back the reload sounds the game left out of Loveless's pistol reloads (reload_sound_catalog.py).

While a camera mod is elected, every CHECK_NS, each pistol reload of the catalog found in memory and not seen yet gets
its sounds, made as the game makes its own (reload_sound_objects.py), at the catalog's instants, each then given the
game's type marker (event_marker.py), read once a run on the first event the game built in the catalog's model
reload. A reload already holding a sound, or of another length than in the files, is left alone: the game changed it.
A reload seen stays seen while it lives; loaded again, a new object, it is seen again. Stopping takes away what was
added.

The list belongs to the game's animation, which the engine may read on another thread if Loveless reloads a pistol at
that very instant: each addition takes microseconds, once per animation loaded (déduction; trials 10 and 14,
2026-10-25, saw nothing go wrong). Any unexpected failure stops this for the session, what was added taken away first.
"""

from typing import Any, Callable, NamedTuple

from . import reload_sound_catalog as catalog
from . import reload_sound_objects as objects
from .event_marker import ensure, marker_of

CHECK_NS = 2_000_000_000
# The game's reloads carry at most 6 events (Vex's Tediore throws): more, and the animation is not the one read.
MOST_EVENTS = 16
SAME_TIME = 0.0001
SAME_LENGTH = 0.001


class Game(NamedTuple):
    find: Callable[[str], Any]
    weak: Callable[[Any], Callable[[], Any]]
    read: Callable[[int, int], bytes | None]
    write: Callable[[int, bytes], bool]
    log: Callable[[str], None]
    construct: Callable[[str, Any, int], Any]
    make_struct: Callable[..., Any]
    def_ptr: Callable[[str, Any], Any]
    find_class: Callable[[str], Any]
    find_enum: Callable[[str], Any]


class Seen:
    """A pistol reload in memory, and our events in it, by sound object address and instant."""

    def __init__(self, weak: Callable[[], Any]) -> None:
        self.weak, self.ours = weak, []


def address(item: Any) -> int:
    return int(item._get_address()) if item is not None else 0


def events(anim: Any) -> list:
    count = len(anim.Notifies)
    if count > MOST_EVENTS:
        raise ValueError("more events than any reload in the files")
    return [anim.Notifies[index] for index in range(count)]


def sounds(anim: Any) -> list:
    return [event for event in events(anim)
            if event.Notify is not None and str(event.Notify.Class.Name) == catalog.SOUND_CLASS]


def log_line(message: str) -> None:
    """The log, apart from the game's other access (game_modules), so that a failure to reach that access is said."""
    from unrealsdk import logging
    logging.info(f"[Camera Runtime] {message}")


class ReloadSounds:
    def __init__(self, load: Callable[[], Game], say: Callable[[str], None] = log_line) -> None:
        """load() gives the game's access at the first check: the runtime exists before the game's modules load."""
        self.load, self.say = load, say
        self.game: Game | None = None
        self.seen: dict[str, Seen] = {}
        # The game's marker for an animation event and the Wwise field's type, the same for all in one run of the game.
        self.marker: bytes | None = None
        self.kind: Any = None
        self.waiting_told = False
        self.next_ns = 0
        self.failed = False

    def sync(self, now_ns: int) -> None:
        if self.failed or now_ns < self.next_ns:
            return
        self.next_ns = now_ns + CHECK_NS
        try:
            if self.game is None:
                self.game = self.load()
            for pistol, rows in catalog.pistols().items():
                self._visit(pistol, rows)
        except Exception as error:
            self.failed = True
            self._say(f"reload sounds stopped for the session: {type(error).__name__}: {error}")
            try:
                self._take_away()
            except Exception as cleanup:
                self._say(f"reload sounds not taken away: {type(cleanup).__name__}")

    def stop(self) -> None:
        self.next_ns = 0
        self._take_away()

    def _say(self, message: str) -> None:
        (self.game.log if self.game is not None else self.say)(message)

    def _visit(self, pistol: str, rows: tuple) -> None:
        seen = self.seen.get(pistol)
        if seen is not None and seen.weak() is not None:
            return
        self.seen.pop(pistol, None)
        anim = self.game.find(catalog.path(pistol))
        if anim is None or not self._ready():
            return
        seen = self.seen[pistol] = Seen(self.game.weak(anim))
        if self._fits(anim, pistol):
            self._give(anim, pistol, rows, seen)

    def _ready(self) -> bool:
        """The Wwise field's type and the game's marker, each looked up once a run; False while the model is away."""
        if self.kind is None:
            self.kind = objects.wwise_type(self.game)
            if self.kind is None:
                raise RuntimeError("the sound's Wwise event field is not the typed reference the game's files show")
        if self.marker is None:
            model = self.game.find(catalog.path(catalog.MODEL))
            built = None if model is None else next((e for e in events(model) if e.Notify is not None), None)
            if built is None:
                if not self.waiting_told:
                    self.waiting_told = True
                    self._say(f"reload sounds: waiting for {catalog.MODEL}, where the game's event marker is read")
                return False
            # Read before any addition: adding to the model's own list moves its events (trial 13).
            self.marker = marker_of(built, self.game.read)
            if self.marker is None:
                raise RuntimeError("the game's event marker could not be read")
        return True

    def _fits(self, anim: Any, pistol: str) -> bool:
        length, expected = float(anim.SequenceLength), catalog.LENGTHS[pistol]
        if abs(length - expected) > SAME_LENGTH:
            self._say(f"reload sounds: {pistol} lasts {length:.3f} s, not {expected:.3f} s; left alone")
            return False
        if sounds(anim):
            self._say(f"reload sounds: {pistol} already has a sound; left alone")
            return False
        return True

    def _give(self, anim: Any, pistol: str, rows: tuple, seen: Seen) -> None:
        for row in rows:
            notify = objects.make_sound(self.game, anim, row, self.kind)
            event = objects.make_event(self.game, anim, notify, row.at)
            # Kept before the write: an addition half done is still taken away.
            seen.ours.append((address(notify), row.at))
            anim.Notifies.append(event)
            if not ensure(anim.Notifies[len(anim.Notifies) - 1], self.marker, self.game.read, self.game.write):
                raise RuntimeError("event marker not written")
        self._check_markers(anim)
        self._say(f"reload sounds: Loveless {pistol} given {len(rows)} sound(s)")

    def _check_markers(self, anim: Any) -> None:
        """A list that grows or shrinks can move its events: each marker read again (none lost in trials 10 and 14)."""
        if self.marker and not all(ensure(event, self.marker, self.game.read, self.game.write)
                                   for event in events(anim)):
            raise RuntimeError("event marker lost")

    def _take_away(self) -> None:
        removed = 0
        for pistol in tuple(self.seen):
            seen = self.seen[pistol]
            anim = seen.weak()
            if anim is not None and seen.ours:
                for notify, at in reversed(seen.ours):
                    found = events(anim)
                    index = next((i for i in reversed(range(len(found))) if address(found[i].Notify) == notify
                                  and abs(float(found[i].LinkValue) - at) < SAME_TIME), None)
                    if index is not None:
                        del anim.Notifies[index]
                        removed += 1
                self._check_markers(anim)
            del self.seen[pistol]
        if removed:
            self._say(f"reload sounds: {removed} taken away, Loveless's pistols as the game made them")


def game_modules() -> Game:
    import unrealsdk
    from unrealsdk.unreal import FGbxDefPtr, WeakPointer

    from . import process_memory

    def find(path: str) -> Any:
        try:
            return unrealsdk.find_object("AnimSequence", path)
        except ValueError:
            # Not in memory: the hunter is not in the game, an expected answer.
            return None

    return Game(find, WeakPointer, process_memory.read, process_memory.write, log_line,
                lambda cls, outer, flags: unrealsdk.construct_object(cls, outer, flags=flags), unrealsdk.make_struct,
                FGbxDefPtr, unrealsdk.find_class, unrealsdk.find_enum)
