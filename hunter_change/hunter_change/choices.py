"""Which hunter each saved game wears: the one reader and writer of the choices file.

The mods' own settings hold one value for every game, while a look is chosen per game (Claude's choice, noted in
docs/reverse-and-change-hunters/plan-du-mod.md), keyed by the game's id (game_id.py). The file keeps the hunter's code
and nothing of the outfit: the outfit worn stays the game's business (Kevin, 2026-09-28). A game chosen again moves to
the end, so the one chosen longest ago goes first when the file is full.
"""

import json
from pathlib import Path

from mods_base import SETTINGS_DIR

from . import file_replace, game_id, hunters, report

VERSION = 1
FILE_NAME = "hunter_change_choices.json"
MAX_GAMES = 200
# 200 games take about 16 kB: anything much larger is not ours and is not read.
MAX_BYTES = 64_000

_games: dict[str, str] | None = None


def path() -> Path:
    return Path(SETTINGS_DIR) / FILE_NAME


def forget() -> None:
    """The next question reads the file again."""
    global _games
    _games = None


def _known(game: object, hunter: object) -> bool:
    return (isinstance(game, str) and game_id.PATTERN.fullmatch(game) is not None
            and isinstance(hunter, str) and hunters.by_code(hunter) is not None)


def _read() -> dict[str, str]:
    """The file's games, oldest first; entries the mod does not know skipped, an unreadable file taken as empty."""
    try:
        with open(path(), "rb") as source:
            data = source.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("oversized")
        entries = json.loads(data)["games"]
        if not isinstance(entries, list):
            raise ValueError("games is not a list")
    except FileNotFoundError:
        return {}
    # RecursionError: json raises it on a file nested too deep; escaping here, it would reach a switch already written.
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        report.error_once("choices:read", f"choices file unreadable ({type(error).__name__}), no look chosen")
        return {}
    games: dict[str, str] = {}
    for entry in entries:
        if isinstance(entry, dict) and _known(entry.get("game"), entry.get("hunter")):
            games.pop(entry["game"], None)
            games[entry["game"]] = entry["hunter"]
    return _bounded(games)


def _bounded(games: dict[str, str]) -> dict[str, str]:
    while len(games) > MAX_GAMES:
        del games[next(iter(games))]
    return games


def _write(games: dict[str, str]) -> bool:
    content = {"version": VERSION, "games": [{"game": game, "hunter": hunter} for game, hunter in games.items()]}
    target = path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(content, indent=1).encode("utf-8")
        file_replace.replace(target, data)
    except OSError as error:
        report.error_once("choices:write", f"choices file not written ({type(error).__name__}), "
                                           "the look stays for this session only")
        return False
    return True


def _memory() -> dict[str, str]:
    global _games
    if _games is None:
        _games = _read()
    return _games


def chosen(game: str) -> str | None:
    return _memory().get(game)


def choose(game: str, hunter: str | None) -> bool:
    """Remembers the hunter worn in a game, None for its own; whether the file took it. The session keeps it anyway."""
    if not isinstance(game, str) or game_id.PATTERN.fullmatch(game) is None or (
            hunter is not None and not _known(game, hunter)):
        raise ValueError("unknown game id or hunter")
    games = _memory()
    games.pop(game, None)
    if hunter is not None:
        games[game] = hunter
        _bounded(games)
    return _write(games)
