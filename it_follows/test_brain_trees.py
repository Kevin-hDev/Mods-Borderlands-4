"""Tests the decision trees' nodes found in memory (it_follows/brain_trees.py): a tree laid out as the game does gives
its nodes in order; a wrong tree type, a wrong storage type, a node count that differs, a node of another name, a node
whose type lies outside the image, an address not readable each give their reason and no node; the names' tokens read
from the structs the SDK makes, a name it cannot make left out."""

import pathlib
import struct
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import brain_fixture as fx  # noqa: E402
from it_follows import brain_trees  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


NAMES = ("Root", "CloseMelee", "Timer", "Condition")
NAMED = {name: fx.token(name) for name in NAMES}

try:
    memory = fx.Memory()
    tree = fx.tree(memory, NAMES)
    check("a tree laid out as the game does gives its nodes in order",
          brain_trees.nodes(memory, tree, list(NAMES), NAMED) == tree.nodes)

    other = fx.tree(memory, NAMES)
    memory.put(other._get_address(), struct.pack("<Q", fx.BASE + 8))
    check("a wrong tree type", brain_trees.nodes(memory, other, list(NAMES), NAMED) == "tree_type")
    other = fx.tree(memory, NAMES)
    memory.put(other.storage, struct.pack("<Q", fx.BASE + 8))
    check("a wrong storage type", brain_trees.nodes(memory, other, list(NAMES), NAMED) == "storage_type")
    check("a node count that differs", brain_trees.nodes(memory, tree, list(NAMES) + ["Timer"], NAMED) == "table")
    renamed = fx.tree(memory, ("Root", "CloseMelee", "Ticket", "Condition"))
    check("a node of another name: its index", brain_trees.nodes(memory, renamed, list(NAMES),
                                                                 {**NAMED, "Ticket": fx.token("Ticket")}) == "node:2")
    outside = fx.tree(memory, NAMES)
    memory.put(outside.nodes[3], struct.pack("<Q", fx.BASE + brain_trees.IMAGE_BYTES + 8))
    check("a node whose type lies outside the image", brain_trees.nodes(memory, outside, list(NAMES), NAMED)
          == "node:3")
    roomy = fx.tree(memory, NAMES)
    memory.put(roomy.storage + brain_trees.TABLE_AT + 12, struct.pack("<i", brain_trees.MAX_CAPACITY + 1))
    check("a capacity past its bound", brain_trees.nodes(memory, roomy, list(NAMES), NAMED) == "table")
    small = fx.tree(memory, NAMES)
    memory.put(small.storage + brain_trees.TABLE_AT + 12, struct.pack("<i", len(NAMES) - 1))
    check("a capacity below the count", brain_trees.nodes(memory, small, list(NAMES), NAMED) == "table")
    crowd = tuple(f"Node{index}" for index in range(brain_trees.MAX_NODES + 1))
    many = fx.tree(memory, crowd)
    check("more nodes than MAX_NODES", brain_trees.nodes(memory, many, list(crowd),
                                                         {name: fx.token(name) for name in crowd}) == "table")
    lost = types.SimpleNamespace(_get_address=lambda: 0x7FFF0000)
    check("an address not readable", brain_trees.nodes(memory, lost, list(NAMES), NAMED) == "tree_type")
    broken = fx.tree(memory, NAMES)
    memory.put(broken.table + 8, struct.pack("<Q", 0x7FFF0000))
    check("a node address not readable", brain_trees.nodes(memory, broken, list(NAMES), NAMED) == "node_unread")

    keys = {}

    def make_struct(name: str, **fields: object) -> object:
        if fields["Name"] == "Unmade":
            raise ValueError("no such name")
        address = memory.block(16)
        memory.put(address, struct.pack("<Q", fx.token(str(fields["Name"]))))
        keys[fields["Name"]] = name
        return types.SimpleNamespace(_get_address=lambda: address)

    sys.modules["unrealsdk"].make_struct = make_struct
    found = brain_trees.tokens(memory, ["Timer", "Root", "Timer", "Unmade"])
    check("the names' tokens read from the structs the SDK makes, once each, a name not made left out",
          found == {"Root": fx.token("Root"), "Timer": fx.token("Timer")}
          and set(keys.values()) == {brain_trees.NAME_STRUCT})
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
