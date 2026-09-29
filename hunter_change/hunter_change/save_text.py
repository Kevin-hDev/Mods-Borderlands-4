"""A game's text, read and changed as bytes: its header (the state block), its skill tree (progression.graphs), the
hunter and the name it shows.

No YAML parser: the game's Python has none, and the game's own layout, tags and trailing spaces are kept byte for
byte; the game loads a save changed this way (essais 1 to 3). The layout, read in Kevin's saves on 2026-09-28: the text
opens on "state: " whose fields sit two spaces in; the progression block's first field is "  graphs: " when the
character has a tree, whose list items start "  - " at the same indent; a game whose tree was never started has no
graphs field at all (Loveless, level 14). Anything not where the game writes it raises ValueError or names nothing
(None, NoId), never a guess.
"""

import enum
import re

from . import game_id, hunters
from .hunters import Hunter

# The header's fields besides the game's id (game_of) and the character level.
FIELDS = {"class": "hunter", "char_name": "name"}
PROGRESSION = b"\nprogression: \n"
GRAPHS = b"  graphs: \n"
GROUP = re.compile(rb"^    group_def_name: (\S+)$", re.M)
# The lines that may follow a block's body, and a tree: the next top-level block, and another field of progression.
TOP_LINE = re.compile(rb"[^ \t\r\n-]")
FIELD_LINE = re.compile(rb"  [^ \t\r\n-]")
NUMBERED = re.compile(r"(.+) (\d{1,3})")
# Names the mod writes: a hunter's name, maybe with a number; plain words the game's YAML reads back as they are.
SAFE_NAME = re.compile(r"[A-Za-z0-9]+(?: [0-9]{1,3})?")


def _next_line(text: bytes, at: int) -> int:
    return (text.find(b"\n", at) + 1) or len(text)


def _block_end(text: bytes, start: int) -> int:
    """Where a top-level block's body ends: the first line from `start` that does not start with a space."""
    end = start
    while end < len(text) and text.startswith(b" ", end):
        end = _next_line(text, end)
    return end


class NoId(enum.Enum):
    """Why game_of names no game."""
    NOT_A_GAME = "not a game's text"
    UNDECIDED = "the beginning ends before the answer"


def game_of(start: bytes, whole: bool = False) -> str | NoId:
    """The game's id: the first char_guid line two spaces into the state block that opens the text, its value an id
    as game_id.PATTERN writes it. `start` is the text's beginning, or all of it when `whole`. NoId.NOT_A_GAME when the
    text does not open on "state:", when that block ends before such a line, or when its value is not an id;
    NoId.UNDECIDED when a beginning ends before either answer, a longer one then decides. Read no further than the
    first char_guid line, so the save search reads only each save's start; header() takes its id from here, so both
    always name the same game."""
    lines = start.split(b"\n")
    if not whole:
        lines.pop()  # no line end yet: it may be cut
    if not lines:
        return NoId.UNDECIDED
    if lines[0].rstrip() != b"state:":
        return NoId.NOT_A_GAME
    for line in lines[1:]:
        if line and not line.startswith(b" "):
            return NoId.NOT_A_GAME
        field, _, value = line.strip().partition(b":")
        if line.startswith(b"  ") and not line.startswith(b"   ") and field == b"char_guid":
            game = value.strip().decode("ascii", "replace")
            return game if game_id.PATTERN.fullmatch(game) else NoId.NOT_A_GAME
    return NoId.NOT_A_GAME if whole else NoId.UNDECIDED


def header(text: bytes) -> dict | None:
    """The game's identifier (game_of's), hunter, name and character level from the state block, or None."""
    game = game_of(text, whole=True)
    if isinstance(game, NoId):
        return None
    try:
        lines = text.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return None
    found: dict = {"game": game}
    in_character = False
    for line in lines[1:]:
        if line and not line.startswith(" "):
            break
        field, _, value = line.strip().partition(":")
        value = value.strip()
        if line.startswith("  ") and not line.startswith("   ") and field in FIELDS and value:
            found[FIELDS[field]] = value
        elif line.strip().startswith("- type:"):
            in_character = line.strip() == "- type: Character"
        elif in_character and field == "level" and value.isascii() and value.isdigit():
            found["level"] = int(value)
            in_character = False
    return found if len(found) == len(FIELDS) + 2 else None


def _tree_span(text: bytes) -> tuple[int, int]:
    """Where the tree is, or would go: its start and end, equal when the game has no tree."""
    if text.count(PROGRESSION) != 1:
        raise ValueError("not one progression block")
    start = text.find(PROGRESSION) + len(PROGRESSION)
    body_end = _block_end(text, start)
    # A blank line, or one opening on a tab, would end the body early and hide what follows it from the checks below.
    # The game writes no blank line (none in 85 copies of Kevin's saves, 2026-09-29) and indents with spaces, so
    # refusing them costs nothing.
    if body_end < len(text) and TOP_LINE.match(text, body_end) is None:
        raise ValueError("a line in progression the game does not write")
    if text.find(b"\n  graphs:", start, body_end) != -1:
        raise ValueError("a tree not where the game writes it")
    if not text.startswith(GRAPHS, start):
        if text.startswith(b"  graphs:", start):
            raise ValueError("a tree field written another way")
        return start, start
    end = start + len(GRAPHS)
    while end < body_end and (text.startswith(b"   ", end) or text.startswith(b"  - ", end)):
        end = _next_line(text, end)
    # Stopped on any line but a field, one of spaces only for one, the tree would be cut there and its rest left in the
    # save, orphaned.
    if end < body_end and FIELD_LINE.match(text, end) is None:
        raise ValueError("a tree not followed by a field")
    return start, end


def tree(text: bytes) -> bytes | None:
    """The game's tree block as written, or None when the game never started one."""
    start, end = _tree_span(text)
    return text[start:end] or None


def groups(block: bytes) -> set[str]:
    return {group.decode("utf-8", "replace") for group in GROUP.findall(block)}


def belongs(block: bytes, hunter: Hunter) -> bool:
    """Whether every graph of the tree has its group, the hunter's."""
    graphs = sum(1 for line in block.split(b"\n") if line.startswith(b"  - "))
    return groups(block) == {hunter.tree_group} and len(GROUP.findall(block)) == graphs


def valid_tree(block: bytes) -> bool:
    """Whether the bytes are one tree block as the game writes it, and nothing more."""
    if not block.startswith(GRAPHS) or not block.endswith(b"\n") or b"\n  - " not in block:
        return False
    try:
        block.decode("utf-8")
        return tree(PROGRESSION + block + b"  point_pools: \n") == block
    except (UnicodeDecodeError, ValueError):
        return False


def with_tree(text: bytes, block: bytes | None) -> bytes:
    """The text with this tree where the game writes it, or with none."""
    if block is not None and not valid_tree(block):
        raise ValueError("not a tree block")
    start, end = _tree_span(text)
    return text[:start] + (block or b"") + text[end:]


def _once(block: bytes, old: bytes, new: bytes) -> bytes:
    if block.count(old) != 1:
        raise ValueError("a field not found once where the game writes it")
    return block.replace(old, new)


def with_hunter(text: bytes, hunter: Hunter, name: str) -> bytes:
    """The text showing this hunter under this name, on the state block's own lines."""
    found = header(text)
    if found is None:
        raise ValueError("no header")
    state_end = _block_end(text, text.find(b"\n") + 1)
    state = _once(text[:state_end], f"\n  class: {found['hunter']}\n".encode(),
                  f"\n  class: {hunters.CHARACTER_PREFIX}{hunter.code}\n".encode())
    if name != found["name"]:
        if SAFE_NAME.fullmatch(name) is None:
            raise ValueError("a name the game may not read back")
        state = _once(state, f"\n  char_name: {found['name']}\n".encode("utf-8"), f"\n  char_name: {name}\n".encode())
    return state + text[state_end:]


def followed_name(name: str, old: Hunter, new: Hunter) -> str:
    """The name follows the hunter, a number kept; any other name stays (Kevin, 2026-09-28, 19:55)."""
    if name == old.name:
        return new.name
    numbered = NUMBERED.fullmatch(name)
    if numbered is not None and numbered.group(1) == old.name:
        return f"{new.name} {numbered.group(2)}"
    return name
