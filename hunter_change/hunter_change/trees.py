"""Each game's skill trees, as its hunters left them: the one reader and writer of the trees file.

A hunter leaving a game leaves its tree here, or its lack of one. A tree put back into its game stays here too, until
that hunter leaves again and the save's own tree replaces it (Kevin, 28 September 2026): "Continue" clicked right
after a change makes the game write back the save it holds in memory (essai 8), and the tree put back would otherwise
be nowhere. Each tree is the save's progression.graphs block byte for byte, which the game keeps as given when it is
the hunter's (essai 2). Entries are read tolerantly, one by one; but a file that is there and cannot be read, or was
written by a newer version of the mod, blocks every change, since writing it would erase the trees it keeps. Bounded:
MAX_GAMES games and MAX_BYTES, the game changed longest ago forgotten first; a file larger than MAX_BYTES, which the
next start would refuse, is never written.
"""

import json
from pathlib import Path

from mods_base import SETTINGS_DIR

from . import file_replace, game_id, hunters, report, save_text

VERSION = 1
FILE_NAME = "hunter_change_trees.json"
MAX_GAMES = 50
# Vex's whole tree is 1.6 kB (2026-09-28): the bounds leave room without reading a wrong file whole.
MAX_TREE_BYTES = 64_000
MAX_BYTES = 1_000_000

_games: dict[str, dict[str, bytes]] | None = None
_loaded = False


class _Newer(Exception):
    """The file was written by a newer version of the mod, which reads it: removing it would erase its trees."""


def path() -> Path:
    return Path(SETTINGS_DIR) / FILE_NAME


def forget() -> None:
    """The next question reads the file again."""
    global _games, _loaded
    _games, _loaded = None, False


def keepable(game: object, code: object, tree: object) -> bool:
    """Whether this file would keep the tree for this game's hunter: of its group, and not too large as the file holds
    it, so that one game's six trees always fit in MAX_BYTES."""
    hunter = hunters.by_code(code) if isinstance(code, str) else None
    return (isinstance(game, str) and game_id.PATTERN.fullmatch(game) is not None and hunter is not None
            and isinstance(tree, bytes) and save_text.valid_tree(tree) and _held_size(tree) <= MAX_TREE_BYTES
            and save_text.belongs(tree, hunter))


def _held_size(tree: bytes) -> int:
    """The tree's size in the file. json.dumps escapes every character outside printable ASCII, up to six bytes for one
    ("é", a control character), so the raw size says too little."""
    return len(json.dumps(tree.decode("utf-8")))


def _bounded(games: dict[str, dict[str, bytes]]) -> dict[str, dict[str, bytes]]:
    while len(games) > MAX_GAMES:
        _forget_oldest(games)
    return games


def _forget_oldest(games: dict[str, dict[str, bytes]]) -> None:
    del games[next(iter(games))]
    report.note("trees: the trees of the game changed longest ago forgotten")


def _read() -> dict[str, dict[str, bytes]] | None:
    """The file's games, oldest first; None when the file is there and cannot be read."""
    try:
        with open(path(), "rb") as source:
            data = source.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("oversized")
        content = json.loads(data)
        if not isinstance(content, dict) or not isinstance(content.get("games"), list):
            raise ValueError("not a trees file")
        if content.get("version", VERSION) > VERSION:
            raise _Newer()
        entries = content["games"]
    except FileNotFoundError:
        return {}
    except _Newer:
        report.error_once("trees:newer", "trees file written by a newer version of the mod: no hunter is changed until "
                                         "that version is reinstalled; do not remove the file, it holds the trees")
        return None
    except (OSError, ValueError, TypeError, RecursionError) as error:
        report.error_once("trees:read", f"trees file unreadable ({type(error).__name__}): "
                                        "no hunter is changed until it is repaired or removed")
        return None
    games: dict[str, dict[str, bytes]] = {}
    trees_skipped = entries_skipped = 0
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("trees"), dict):
            entries_skipped += 1
            continue
        game = entry.get("game")
        found = {code: _encoded(tree) for code, tree in entry["trees"].items()}
        kept = {code: tree for code, tree in found.items() if keepable(game, code, tree)}
        trees_skipped += len(found) - len(kept)
        if kept:
            games.pop(game, None)
            games[game] = kept
    # Said, since the next write leaves them out: the log answers "where did my tree go?", without naming a game.
    if trees_skipped or entries_skipped:
        report.note(f"trees: {trees_skipped} tree(s) and {entries_skipped} entry(ies) of the file unreadable, "
                    "left out at the next write")
    return _bounded(games)


def _encoded(tree: object) -> bytes | None:
    """A tree from the file as bytes; None for anything else, such as half a character a hand edit left."""
    try:
        return tree.encode("utf-8") if isinstance(tree, str) else None
    except UnicodeEncodeError:
        return None


def _memory() -> dict[str, dict[str, bytes]] | None:
    global _games, _loaded
    if not _loaded:
        _games, _loaded = _read(), True
    return _games


def readable() -> bool:
    return _memory() is not None


def kept(game: str, code: str) -> bytes | None:
    games = _memory()
    return None if games is None else games.get(game, {}).get(code)


def _encode(games: dict[str, dict[str, bytes]]) -> bytes | None:
    """The file's bytes; the games changed longest ago forgotten first until it holds in MAX_BYTES, since a larger file
    would not be read back. None when one game alone does not hold, which keepable's bound should make impossible:
    six trees of MAX_TREE_BYTES as the file holds them are far below it."""
    while True:
        content = {"version": VERSION, "games": [
            {"game": game, "trees": {code: tree.decode("utf-8") for code, tree in kept.items()}}
            for game, kept in games.items()]}
        encoded = json.dumps(content, indent=1).encode("utf-8")
        if len(encoded) <= MAX_BYTES:
            return encoded
        if len(games) <= 1:
            return None
        _forget_oldest(games)


def _write(games: dict[str, dict[str, bytes]]) -> bool:
    """Whether the file took the games; when not, the memory is forgotten, to follow the disk again."""
    encoded = _encode(games)
    if encoded is None:
        report.error_once("trees:size", "trees file not written: one game's trees exceed the file's bound")
        forget()
        return False
    target = path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        file_replace.replace(target, encoded)
    except OSError as error:
        report.error_once("trees:write", f"trees file not written ({type(error).__name__})")
        forget()
        return False
    return True


def keep(game: str, code: str, tree: bytes) -> bool:
    """Keeps the tree a game's hunter leaves; whether the file took it. Nothing is written while it is unreadable."""
    if not keepable(game, code, tree):
        raise ValueError("not a tree of this hunter")
    games = _memory()
    if games is None:
        return False
    kept_here = games.pop(game, {})
    kept_here[code] = tree
    games[game] = kept_here
    _bounded(games)
    return _write(games)


def drop(game: str, code: str) -> bool:
    """Forgets the tree of a hunter that leaves its game without one; whether the file took it."""
    games = _memory()
    if games is None:
        return False
    kept_here = games.get(game, {})
    if kept_here.pop(code, None) is None:
        return True
    if not kept_here:
        del games[game]
    return _write(games)
