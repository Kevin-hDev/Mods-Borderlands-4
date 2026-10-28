"""Copies of a save as the game wrote it, taken before the mod writes it: the one writer of the backups folder.

The folder is in the mods' settings folder, never in the game's save folder, so the game sees nothing more
(conception-idee-2.md, 28 September 2026). A copy is named by the game's id and the UTC time, which never goes back
when the clocks change, never by the account nor the path. Bounded: the last MAX_PER_GAME copies of each game,
MAX_GAMES games, the game backed up longest ago forgotten first; the copy just written is never the one removed, and a
temporary file a crash left is removed by the next copy.
"""

import re
import time
from pathlib import Path

from mods_base import SETTINGS_DIR

from . import file_replace, game_id, report

FOLDER = "hunter_change_backups"
MAX_PER_GAME = 5
MAX_GAMES = 50
COPY = re.compile(rf"({game_id.PATTERN.pattern})_(\d{{8}}-\d{{6}}-\d{{3}})\.sav")


def folder() -> Path:
    return Path(SETTINGS_DIR) / FOLDER


def _stamp(now: float) -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.gmtime(now)) + f"-{int(now * 1000) % 1000:03d}"


def save(game: str, data: bytes, now: float | None = None) -> Path | None:
    """The copy written, or None when it could not be: the caller then changes nothing."""
    if not isinstance(game, str) or game_id.PATTERN.fullmatch(game) is None:
        raise ValueError("unknown game id")
    target = folder() / f"{game}_{_stamp(time.time() if now is None else now)}.sav"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        file_replace.replace(target, data)
    except OSError as error:
        report.error_once("backups:write", f"backup not written ({type(error).__name__}): the save is not changed")
        return None
    _prune(keep=target)
    return target


def _prune(keep: Path) -> None:
    """A file that cannot be removed (read-only, held open by another program, a folder named like a copy) is passed
    over, never the end of the pruning: one stuck file stopping it would let every game grow past its bound."""
    try:
        gone = _past_bounds()
    except OSError as error:
        _not_all_removed(error)
        return
    for path in gone:
        if path == keep:
            continue
        try:
            path.unlink()
        except OSError as error:
            _not_all_removed(error)


def _past_bounds() -> list[Path]:
    """The temporary files a crash left, the games forgotten, then each game's surplus; raises OSError when the folder
    cannot be listed."""
    copies: dict[str, list[tuple[str, Path]]] = {}
    gone_early: list[Path] = []
    for path in folder().iterdir():
        match = COPY.fullmatch(path.name.removesuffix(file_replace.TEMPORARY_SUFFIX))
        if match is not None and path.name.endswith(file_replace.TEMPORARY_SUFFIX):
            gone_early.append(path)
        elif match is not None:
            copies.setdefault(match.group(1), []).append((match.group(2), path))
    by_age = sorted(copies.values(), key=lambda kept: max(kept)[0])
    gone = gone_early + [path for kept in by_age[:-MAX_GAMES] for _, path in kept]
    gone += [path for kept in by_age[-MAX_GAMES:] for _, path in sorted(kept)[:-MAX_PER_GAME]]
    return gone


def _not_all_removed(error: OSError) -> None:
    report.error_once("backups:prune", f"old backups not all removed ({type(error).__name__})")
