"""Where the game's saves are, and which save is a game: the one module that knows their paths.

Documents is asked from Windows first, since OneDrive may have moved it (it did on Kevin's PC), then the usual places
(essai 36, 2026-09-28). The saves are My Games/Borderlands 4/Saved/SaveGames/<account>/Profiles/client/<slot>.sav, one
folder per Steam account, each opening only with its own number: a game's save is the one whose text carries the
game's id. With several accounts, only the connected Steam account's saves are read (steam_account.py), since the game
loads no other: an older account's copy of a game no longer blocks it (Kevin's Vex, 2026-09-29). When that account
cannot be told, or has no folder, every account is read, as before.

The caller writes the save it is given, so the search answers only when it proves the game is in one save alone
(Kevin, 2026-09-29): a game found in two saves, a save file copied by hand, is refused, since the mod could not tell
which one the player picked and could write the other. Nothing is kept between searches, so a copy made at any time is
seen. Each search reads only the start of every save to learn its game, read longer while it cannot tell, where a
whole save takes 76 to 88 ms; it then opens whole and checks the one save that carries the game. It is refused, None
and a log line, whenever it cannot prove the game is in one save alone: over its bounds, a folder it cannot list, a
save still held after held_file's pauses, a save whose game is not told within START_CEILING, the time bound reached,
the game in two saves or more. A save that opens but is another account's, damaged or not a game's text is not the
game's: said with its slot, and the search goes on. Never logs a path nor an account number. Bounded: MAX_ACCOUNTS
accounts, MAX_SAVES saves each, MAX_SECONDS in all, since the game waits meanwhile.

A search that finds no save says why (Missing), for the page to tell the player the truth rather than one sentence for
all (Kevin, 2026-09-29: a save said « introuvable ou illisible » when it was found twice worries a player about his
game): NO_SAVE, no save carries the game; TWO_SAVES, two saves or more carry it; SAVES_UNSURE, not every save could be
read; SAVE_DAMAGED, the one save carrying it does not open whole or its header does not carry the game.
"""

import functools
import os
import pathlib
import re
import time
from dataclasses import dataclass

from . import game_id, held_file, report, save_codec, save_text, steam_account

SAVE_FOLDER = pathlib.Path("My Games") / "Borderlands 4" / "Saved" / "SaveGames"
ACCOUNT = re.compile(r"\d{17}")
SLOT = re.compile(r"(\d{1,3})\.sav")
MAX_ACCOUNTS = 10
MAX_SAVES = 200
MAX_SECONDS = 5.0
# The id's line starts 7 to 26 bytes into the text and is 45 bytes long in all 82 real games decrypted for Kevin's
# decision of 2026-09-29: FIRST_START holds it and comes from the first chunk, about 2 ms a save (2.2 to 2.6 ms over
# 32 invented saves of real size, 1.6 to 2.1 ms in the review, 2026-09-29). A start that ends before its answer, a
# field added before the id by a game patch, is read again twice as long, up to START_CEILING.
FIRST_START = 128
START_CEILING = 4096
DOCUMENTS_ID = "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}"  # FOLDERID_Documents
NO_SAVE, TWO_SAVES, SAVES_UNSURE, SAVE_DAMAGED = "no_save", "two_saves", "saves_unsure", "save_damaged"


@dataclass(frozen=True)
class Save:
    path: pathlib.Path
    account: int
    slot: int
    data: bytes
    text: bytes


@dataclass(frozen=True)
class Missing:
    """Why a search gives no save: NO_SAVE, TWO_SAVES, SAVES_UNSURE or SAVE_DAMAGED."""
    why: str


class _Refused(Exception):
    """The search cannot prove the game is in one save alone: `why` for the player, the message for the log."""

    def __init__(self, message: str, why: str = SAVES_UNSURE) -> None:
        super().__init__(message)
        self.why = why


def _known_documents() -> pathlib.Path | None:
    """Windows' own answer for Documents, wherever OneDrive moved it; None when the game's Python cannot ask."""
    try:
        import ctypes
        import uuid
        from ctypes import wintypes
        shell32, ole32 = ctypes.windll.shell32, ctypes.windll.ole32
    except (ImportError, AttributeError, OSError):
        return None

    class Guid(ctypes.Structure):
        _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD),
                    ("Data4", ctypes.c_ubyte * 8)]

    known = uuid.UUID(DOCUMENTS_ID)
    guid = Guid(known.time_low, known.time_mid, known.time_hi_version, (ctypes.c_ubyte * 8)(*known.bytes[8:]))
    found = ctypes.c_wchar_p()
    if shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(found)) != 0:
        return None
    try:
        return pathlib.Path(found.value) if found.value else None
    finally:
        ole32.CoTaskMemFree(found)


def documents_candidates() -> list[pathlib.Path]:
    places = [_known_documents()]
    places += [pathlib.Path(os.environ[name]) / "Documents" for name in ("OneDrive", "USERPROFILE")
               if os.environ.get(name)]
    return [place for place in places if place is not None]


def _read(path: pathlib.Path) -> bytes:
    with open(path, "rb") as source:
        return source.read(save_codec.MAX_SAVE_BYTES + 1)


def _all_saves(places: list[pathlib.Path]) -> list[tuple[pathlib.Path, int, int]]:
    """Every save of the accounts found, as (path, account, slot); _Refused over the bounds or when a folder cannot
    be listed, since a save left unseen could be a copy of the game."""
    root = next((place / SAVE_FOLDER for place in places if (place / SAVE_FOLDER).is_dir()), None)
    if root is None:
        return []
    try:
        accounts = sorted(path for path in root.iterdir() if path.is_dir() and ACCOUNT.fullmatch(path.name))
    except OSError as error:
        raise _Refused(f"the saves folder is not readable ({type(error).__name__})") from error
    if len(accounts) > MAX_ACCOUNTS:
        raise _Refused(f"{len(accounts)} accounts, more than {MAX_ACCOUNTS}")
    if len(accounts) > 1:
        accounts = _connected_only(accounts)
    found: list[tuple[pathlib.Path, int, int]] = []
    for account in accounts:
        client = account / "Profiles" / "client"
        try:
            slots = sorted((int(match.group(1)), path) for path in client.iterdir()
                           if (match := SLOT.fullmatch(path.name))) if client.is_dir() else []
        except OSError as error:
            raise _Refused(f"an account's saves are not readable ({type(error).__name__})") from error
        if len(slots) > MAX_SAVES:
            raise _Refused(f"{len(slots)} saves in an account, more than {MAX_SAVES}")
        found += [(path, int(account.name), slot) for slot, path in slots]
    return found


def _connected_only(accounts: list[pathlib.Path]) -> list[pathlib.Path]:
    """The connected Steam account's folder alone when it is among `accounts`, else all of them; said either way."""
    connected = steam_account.connected()
    mine = [account for account in accounts if int(account.name) == connected]
    if mine:
        report.note(f"save search: {len(accounts)} accounts, the connected Steam account's read alone")
        return mine
    unknown = "unknown" if connected is None else "has no saves folder"
    report.note(f"save search: {len(accounts)} accounts, the connected Steam account {unknown}, all read")
    return accounts


def _in_time(started: float) -> None:
    """_Refused once the search has run MAX_SECONDS. Checked before each save and before each longer read of a start:
    a forged save of empty deflate blocks can make one start read take seconds (final review, 2026-09-29)."""
    if time.monotonic() - started > MAX_SECONDS:
        raise _Refused(f"stopped after {MAX_SECONDS:.0f} s")


def _game_in(data: bytes, account: int, slot: int, started: float) -> str | save_text.NoId:
    """The game a save's start names, read twice as long while it cannot tell; ValueError when the save does not
    open, _Refused when START_CEILING is not enough, since that save could be a copy of the game, or when the search
    runs out of time."""
    size = FIRST_START
    while True:
        start = save_codec.decode_start(data, account, size)
        answer = save_text.game_of(start, whole=len(start) < size)
        if answer is not save_text.NoId.UNDECIDED:
            return answer
        if size >= START_CEILING:
            raise _Refused(f"slot {slot} does not name its game within {START_CEILING} bytes")
        _in_time(started)
        size = min(size * 2, START_CEILING)


def _carrying(game: str, places: list[pathlib.Path], sleep) -> list[tuple[pathlib.Path, int, int, bytes]]:
    """Every save whose start carries the game's id, with the bytes read."""
    started = time.monotonic()
    carrying = []
    for path, account, slot in _all_saves(places):
        _in_time(started)
        try:
            data = held_file.patiently(functools.partial(_read, path), sleep)
        except OSError as error:
            raise _Refused(f"slot {slot} stays unreadable ({type(error).__name__})") from error
        try:
            there = _game_in(data, account, slot, started)
        except ValueError as error:
            report.note(f"save search: slot {slot} does not open ({type(error).__name__})")
            continue
        if there is save_text.NoId.NOT_A_GAME:
            report.note(f"save search: slot {slot} is not a game's")
        elif there == game:
            carrying.append((path, account, slot, data))
    return carrying


def _whole(game: str, path: pathlib.Path, account: int, slot: int, data: bytes) -> Save | Missing:
    """The one save that carries the game, opened whole: its start alone does not prove the rest is sound."""
    try:
        text = save_codec.decode(data, account)
        head = save_text.header(text)
    except ValueError as error:
        report.note(f"save search: slot {slot} does not open whole ({type(error).__name__})")
        return Missing(SAVE_DAMAGED)
    if (head or {}).get("game") != game:
        report.note(f"save search: slot {slot} does not carry the game in its header")
        return Missing(SAVE_DAMAGED)
    return Save(path, account, slot, data, text)


def find(game: str, places: list[pathlib.Path] | None = None, sleep=time.sleep) -> Save | Missing:
    """The save of this game, opened whole and checked; Missing, with why, when no save carries its id, or when the
    search cannot prove that one save alone does."""
    if not isinstance(game, str) or game_id.PATTERN.fullmatch(game) is None:
        return Missing(NO_SAVE)
    try:
        matches = _carrying(game, documents_candidates() if places is None else places, sleep)
        if len(matches) > 1:
            raise _Refused(f"the game is in {len(matches)} saves, none is used", TWO_SAVES)
    except _Refused as refusal:
        report.note(f"save search refused: {refusal}")
        return Missing(refusal.why)
    return _whole(game, *matches[0]) if matches else Missing(NO_SAVE)


def stamp(save: Save) -> tuple[int, int] | None:
    """When the save was last written and its size, to tell that the game has stopped writing it; None when it cannot
    be read, which the caller takes as a change."""
    try:
        status = save.path.stat()
    except OSError:
        return None
    return status.st_mtime_ns, status.st_size
