"""The type marker of an animation event written by the SDK: the first field's place read from the structure and the
one it builds on; the game's marker read from one of its events, or none when the fields leave no room, or refused
when unreadable or no address; copied onto an event that lacks it, left when already there, refused when the write
fails or does not hold.
python test_event_marker.py"""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from apex_camera_runtime.event_marker import ensure, first_field, marker_of  # noqa: E402

GAME = (0x7FF7_5E14_6DD8).to_bytes(8, "little")
fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def kind(*offsets: int) -> object:
    fields = [types.SimpleNamespace(Offset_Internal=offset) for offset in offsets]
    return types.SimpleNamespace(_properties=lambda: fields)


def event(where: int, *kinds: object) -> object:
    layout = types.SimpleNamespace(_superfields=lambda: list(kinds))
    return types.SimpleNamespace(_type=layout, _get_address=lambda: where)


class Memory:
    def __init__(self) -> None:
        self.words: dict[int, bytes] = {}
        self.writes: list[int] = []
        self.refuse = self.drop = False

    def read(self, where: int, size: int) -> bytes | None:
        return self.words.get(where, bytes(size)) if where else None

    def write(self, where: int, data: bytes) -> bool:
        self.writes.append(where)
        if self.refuse:
            return False
        if not self.drop:
            self.words[where] = data
        return True


notify_event, linkable = kind(0x48, 0x4C, 0x50), kind(0x08, 0x10, 0x30)
model, added = event(100, notify_event, linkable), event(200, notify_event, linkable)
check("the first field read over the structure and the one it builds on", first_field(model) == 8)

memory = Memory()
memory.words[100] = GAME
marker = marker_of(model, memory.read)
check("the game's marker read from one of its events", marker == GAME)
check("an event the SDK wrote, zeroed: the marker copied, and read back",
      ensure(added, marker, memory.read, memory.write) and memory.words[200] == GAME and memory.writes == [200])
check("already the game's: nothing written", ensure(added, marker, memory.read, memory.write) and memory.writes == [200])

memory.refuse = True
check("a write refused: not safe", not ensure(event(300, notify_event), marker, memory.read, memory.write))
memory.refuse, memory.drop = False, True
check("a write that does not hold: not safe", not ensure(event(400, notify_event), marker, memory.read, memory.write))
memory.drop = False

check("fields from the first byte on: no marker, nothing to hold",
      marker_of(event(100, notify_event, kind(0x00, 0x08)), memory.read) == b""
      and ensure(event(500, notify_event), b"", memory.read, memory.write) and 500 not in memory.writes)
memory.words[600] = (0x40).to_bytes(8, "little")
check("a marker that is no address: refused", marker_of(event(600, notify_event, linkable), memory.read) is None)
check("a marker that cannot be read: refused", marker_of(event(0, notify_event, linkable), memory.read) is None)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
