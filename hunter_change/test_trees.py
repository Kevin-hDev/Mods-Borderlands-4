"""The trees file: nothing kept and nothing written without one; a tree kept in memory and on disk with the file's
version, read back byte for byte; a tree dropped leaves the file, and a game with it when it was its last; bounded,
the game changed longest ago forgotten first and said; never written larger than it can be read back, one game over
the bound not written at all; read tolerantly (unknown fields ignored, bad entries skipped and counted, half a
character skipped); an unreadable, oversized, too deep or newer version's file blocks every change, is left as it is
and said once, a newer version's asking for that version again rather than the file removed; written whole through
a temporary file, a failed write said and the memory following the disk; a tree that is not of the hunter, or too
large as the file holds it, refused, and told before by keepable."""

import json
import os
import sys

import sdk_stubs

state = sdk_stubs.install()

import save_fixture as fx  # noqa: E402
from hunter_change import file_replace, hunters, report, trees  # noqa: E402

fails: list[str] = []
G, V = fx.HARLOWE_GAME, fx.VEX_GAME
GRAV, PALADIN = fx.TREES["Gravitar"], fx.TREES["Paladin"]


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def stored() -> dict:
    return json.loads(trees.path().read_text(encoding="utf-8"))


def held(tree: bytes) -> int:
    """A tree's size as the file holds it: a JSON string, its line ends escaped."""
    return len(json.dumps(tree.decode("utf-8")))


def filled(hunter: hunters.Hunter, filler: bytes) -> bytes:
    """A tree of the hunter whose one node's name is half the bound long, in this one-byte filler."""
    return (b"  graphs: \n  - name: Progress_Filler\n    group_def_name: " + hunter.tree_group.encode("utf-8")
            + b"\n    nodes: \n    - name: " + filler * (trees.MAX_TREE_BYTES // 2) + b"\n")


def fresh(content: str | None = None) -> None:
    """The file as another run left it, and the mod starting again."""
    if content is None:
        trees.path().unlink(missing_ok=True)
    else:
        trees.path().write_text(content, encoding="utf-8")
    trees.forget()
    report.reset()
    state["errors"].clear()


check("the file in the mods' settings folder", trees.path().parent == state["settings_dir"])
check("nothing kept and nothing written without a file",
      trees.readable() and trees.kept(G, "Gravitar") is None and not trees.path().exists())

check("a tree kept in memory", trees.keep(G, "Gravitar", GRAV) and trees.kept(G, "Gravitar") == GRAV)
check("a tree kept on disk with the file's version",
      stored() == {"version": 1, "games": [{"game": G, "trees": {"Gravitar": GRAV.decode("utf-8")}}]})
trees.forget()
check("read back byte for byte", trees.kept(G, "Gravitar") == GRAV)
trees.keep(G, "Paladin", PALADIN)
check("a tree dropped leaves the file", trees.drop(G, "Gravitar") and trees.kept(G, "Gravitar") is None
      and stored()["games"] == [{"game": G, "trees": {"Paladin": PALADIN.decode("utf-8")}}])
check("a game leaves with its last tree", trees.drop(G, "Paladin") and stored()["games"] == [])
check("dropping a tree not kept is fine", trees.drop(G, "Paladin"))

fresh()
games = [f"{index:032X}" for index in range(1, trees.MAX_GAMES + 1)]
for game in games:
    trees.keep(game, "Gravitar", GRAV)
trees.keep(games[0], "Paladin", PALADIN)
trees.keep(G, "Gravitar", GRAV)
kept = [entry["game"] for entry in stored()["games"]]
check("bounded, the game changed longest ago forgotten first and said", len(kept) == trees.MAX_GAMES
      and games[1] not in kept and kept[-2:] == [games[0], G] and trees.kept(games[1], "Gravitar") is None
      and any("longest ago" in line for line in state["logs"]))

fresh()
node = b"    - name: Progress_Grav_Node\n      points_spent: 1\n"
large = GRAV + node * ((trees.MAX_TREE_BYTES - held(GRAV)) // (held(node) - 2))
for game in games[:30]:
    trees.keep(game, "Gravitar", large)
size = trees.path().stat().st_size
trees.forget()
check("never written larger than it can be read back", size <= trees.MAX_BYTES and trees.readable()
      and trees.kept(games[29], "Gravitar") == large and trees.kept(games[0], "Gravitar") is None)

fresh()
trees.keep(G, "Gravitar", GRAV)
before = trees.path().read_bytes()
taken = []
for hunter in hunters.HUNTERS:
    try:
        taken.append(trees.keep(G, hunter.code, filled(hunter, b"\x01")))
    except ValueError:
        taken.append(False)
trees.forget()
check("six trees of control characters in one game, each within the bound in raw bytes: none taken, the file "
      "unchanged and readable", not any(taken) and trees.path().read_bytes() == before and trees.readable()
      and trees.kept(G, "Gravitar") == GRAV
      and trees.keepable(G, "Gravitar", filled(hunters.by_code("Gravitar"), b"x")))

# keepable makes one game fit by construction: the bound lowered to the file as it is reaches the guard behind it.
bound, trees.MAX_BYTES = trees.MAX_BYTES, len(before)
written = trees.keep(G, "Paladin", PALADIN)
trees.MAX_BYTES = bound
check("one game alone over the file's bound: nothing written, said once without a path, the memory following the disk",
      not written and trees.path().read_bytes() == before and len(state["errors"]) == 1
      and "trees" in state["errors"][0] and str(trees.path().parent) not in state["errors"][0]
      and trees.kept(G, "Paladin") is None and trees.kept(G, "Gravitar") == GRAV)

fresh(json.dumps({"version": 1, "note": "unknown", "games": [
    {"game": G, "trees": {"Gravitar": GRAV.decode("utf-8"), "Paladin": GRAV.decode("utf-8"), "Echo4": "x"}, "since": 1},
    {"game": "not-an-id", "trees": {"Gravitar": GRAV.decode("utf-8")}},
    {"game": V, "trees": {"DarkSiren": "  graphs: \n", "Paladin": PALADIN.decode("utf-8") + "\ud800"}},
    {"game": V.lower(), "trees": {}}, "odd", {"trees": 3}]}))
check("read tolerantly: unknown fields ignored, bad entries skipped and counted, half a character skipped",
      trees.readable() and trees.kept(G, "Gravitar") == GRAV and trees.kept(G, "Paladin") is None
      and trees.kept(V, "DarkSiren") is None and trees.kept(V, "Paladin") is None and not state["errors"]
      and any("5 tree(s) and 2 entry(ies)" in line for line in state["logs"]))

fresh("{ not json")
check("an unreadable file blocks every change",
      not trees.readable() and trees.kept(G, "Gravitar") is None and not trees.keep(G, "Gravitar", GRAV)
      and not trees.drop(G, "Gravitar"))
check("the unreadable file is left as it is and said once, to be repaired or removed",
      trees.path().read_text(encoding="utf-8") == "{ not json" and len(state["errors"]) == 1
      and "trees" in state["errors"][0] and "repaired or removed" in state["errors"][0])
fresh(json.dumps({"version": 1, "games": "none"}))
check("a file of another shape blocks too", not trees.readable())
fresh(" " * (trees.MAX_BYTES + 1))
check("an oversized file blocks too", not trees.readable())
fresh("[" * 100_000 + "]" * 100_000)
check("a file too deep to read blocks too", not trees.readable())
fresh(json.dumps({"version": 2, "games": [{"game": G, "trees": {"Gravitar": GRAV.decode("utf-8")}}]}))
check("a newer version's file blocks too, left as it is",
      not trees.readable() and not trees.keep(G, "Paladin", PALADIN) and not trees.drop(G, "Gravitar")
      and '"version": 2' in trees.path().read_text())
check("a newer version's file said once as such: that version reinstalled, the file never removed",
      len(state["errors"]) == 1 and "newer version" in state["errors"][0] and "reinstall" in state["errors"][0]
      and "repaired or removed" not in state["errors"][0])

fresh()
trees.keep(G, "Gravitar", GRAV)
check("written whole through a temporary file",
      not trees.path().with_name(trees.path().name + file_replace.TEMPORARY_SUFFIX).exists())
real_replace = os.replace
os.replace = lambda *_args: (_ for _ in ()).throw(OSError("disk full"))
written = trees.keep(G, "Paladin", PALADIN)
os.replace = real_replace
check("a failed write said, the memory following the disk", not written and len(state["errors"]) == 1
      and trees.kept(G, "Paladin") is None and trees.kept(G, "Gravitar") == GRAV)

too_large = large + node
refused = []
for game, code, tree in ((G.lower(), "Gravitar", GRAV), (G, "Echo4", GRAV), (G, "Paladin", GRAV),
                         (G, "Gravitar", b"  graphs: \n"), (G, "Gravitar", too_large)):
    try:
        trees.keep(game, code, tree)
    except ValueError:
        refused.append(code)
check("a tree that is not of the hunter, or not a tree, or too large, refused", len(refused) == 5)
check("told before by keepable", trees.keepable(G, "Gravitar", GRAV) and not trees.keepable(G, "Paladin", GRAV)
      and not trees.keepable(G, "Gravitar", too_large) and not trees.keepable(G.lower(), "Gravitar", GRAV))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
