"""A fake memory holding decision trees as the game lays them out (brain_trees.py), for the tests of brain_trees and
normal/melee_rest: the tree's type, its storage at +0x30 and that storage's type, the table of its nodes at +0x28 with
their count and capacity, each node a type within the image and its name's token at +0x10, and a Timer node's rest at
the offset given."""

import struct
import types

BASE = 0x140000000


class Memory:
    def __init__(self) -> None:
        self.base = BASE
        self.cells: dict[int, bytearray] = {}
        self.next = 0x10000000
        self.writes: list[tuple[int, bytes]] = []
        self.refuse_writes = False

    def block(self, size: int) -> int:
        address = self.next
        self.cells[address] = bytearray(size)
        self.next += max(size, 0x1000)
        return address

    def put(self, address: int, data: bytes) -> None:
        start = max(cell for cell in self.cells if cell <= address)
        self.cells[start][address - start:address - start + len(data)] = data

    def read(self, address: int, size: int) -> bytes | None:
        starts = [cell for cell in self.cells if cell <= address]
        if not starts:
            return None
        start = max(starts)
        cell = self.cells[start]
        if address - start + size > len(cell):
            return None
        return bytes(cell[address - start:address - start + size])

    def write(self, address: int, data: bytes) -> bool:
        if self.refuse_writes or self.read(address, len(data)) is None:
            return False
        self.put(address, data)
        self.writes.append((address, data))
        return True


def token(name: str) -> int:
    return 1000 + sum(ord(letter) * (index + 1) for index, letter in enumerate(name))


def rest(centre: float, half: float) -> bytes:
    raw = bytearray(56)
    struct.pack_into("<ff", raw, 8, centre, half)
    struct.pack_into("<H", raw, 32, 8)
    raw[40] = 11
    return bytes(raw)


def tree(memory: Memory, names: tuple[str, ...], timer: int | None = None, value: bytes | None = None,
         at: int = 448) -> types.SimpleNamespace:
    """A tree object as the SDK hands it, its nodes laid out in memory; the Timer node at timer holds value at at."""
    from it_follows import brain_trees
    asset = memory.block(0x80)
    storage = memory.block(0x80)
    table = memory.block(8 * len(names))
    memory.put(asset, struct.pack("<Q", BASE + brain_trees.TREE_TYPE_AT))
    memory.put(asset + brain_trees.STORAGE_AT, struct.pack("<Q", storage))
    memory.put(storage, struct.pack("<Q", BASE + brain_trees.STORAGE_TYPE_AT))
    memory.put(storage + brain_trees.TABLE_AT, struct.pack("<Qii", table, len(names), len(names) + 4))
    nodes = []
    for index, name in enumerate(names):
        node = memory.block(0x400)
        memory.put(node, struct.pack("<Q", BASE + 0x1000))
        memory.put(node + brain_trees.NAME_AT, struct.pack("<Q", token(name)))
        memory.put(table + index * 8, struct.pack("<Q", node))
        nodes.append(node)
    if timer is not None and value is not None:
        memory.put(nodes[timer] + at, value)
    return types.SimpleNamespace(_get_address=lambda: asset, nodes=nodes, storage=storage, table=table)
