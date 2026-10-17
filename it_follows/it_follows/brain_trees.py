"""The nodes of an enemy's decision tree, found in the game's memory: the SDK sees the tree (GbxBrainTaskData_AITree)
but not its nodes, which are native.

The way is the enemy research's (apex_probe/apex_brain_storage.py, locate, and its contract; séance 28 on the common
trees, séance 35 on 11 species trees, vérifié en jeu; It Follows' trials 66 and 67 read and wrote through it): the
tree's own type at its first 8 bytes, its storage at +0x30 and that storage's type, the table of its nodes at +0x28
with their count and capacity, then each node's name at +0x10, all of them in the order the tree was decoded in. The
types are counted from the game's image: another version of the game changes them, and nothing is then found. Every
check is made again at each call, from the live tree: an address is never kept from one call to the next.
"""

import struct
from typing import Any

import unrealsdk

# Game 1.10.2-4845623 (Steam), apex_brain_storage_contract.json.
TREE_TYPE_AT = 180623264
STORAGE_TYPE_AT = 180643120
IMAGE_BYTES = 834191360
STORAGE_AT, TABLE_AT, NAME_AT = 0x30, 0x28, 0x10
MAX_NODES, MAX_CAPACITY = 64, 256
# A struct whose first 8 bytes are a name as the game holds it (apex_territory_survey_data.candidates).
NAME_STRUCT = "GbxBlackboardEntryRef"


def tokens(memory: Any, names: list[str]) -> dict[str, int]:
    """Each name as the game holds it, 8 bytes read as a number; a name that cannot be made is left out, and its
    caller says which (normal/melee_rest.py)."""
    found = {}
    for name in sorted(set(names)):
        try:
            key = unrealsdk.make_struct(NAME_STRUCT, Name=name)
            raw = memory.read(key._get_address(), 8)
        except Exception:
            continue
        if raw is not None and struct.unpack("<Q", raw)[0]:
            found[name] = struct.unpack("<Q", raw)[0]
    return found


def _u64(memory: Any, address: int) -> int | None:
    raw = memory.read(address, 8)
    return None if raw is None else struct.unpack("<Q", raw)[0]


def nodes(memory: Any, tree: Any, names: list[str], named: dict[str, int]) -> list[int] | str:
    """The addresses of the tree's nodes, or why they were not found: names are the nodes in order, named their
    tokens."""
    base = memory.base
    address = tree._get_address()
    if _u64(memory, address) != base + TREE_TYPE_AT:
        return "tree_type"
    storage = _u64(memory, address + STORAGE_AT)
    if not storage or _u64(memory, storage) != base + STORAGE_TYPE_AT:
        return "storage_type"
    raw = memory.read(storage + TABLE_AT, 16)
    if raw is None:
        return "table_unread"
    table, count, capacity = struct.unpack("<Qii", raw)
    if not table or count != len(names) or not 1 <= count <= MAX_NODES or not count <= capacity <= MAX_CAPACITY:
        return "table"
    found = []
    for index, name in enumerate(names):
        node = _u64(memory, table + index * 8)
        header = memory.read(node, NAME_AT + 8) if node else None
        if header is None:
            return "node_unread"
        kind, token = struct.unpack_from("<Q", header)[0], struct.unpack_from("<Q", header, NAME_AT)[0]
        if not base <= kind < base + IMAGE_BYTES or named.get(name) != token:
            return f"node:{index}"
        found.append(node)
    return found
