"""Where the saves are: a game's save found and opened whole, with its account and slot; no save (why NO_SAVE) for a
game no save carries, for an id that is not a game's, and without a save folder; a save of another account never taken
for a game; with several accounts, the connected Steam account's saves read alone, its copy of the game found though
another account holds one too, and said; all accounts read when the connected one is unknown or has no folder, a game
in two of them refused as TWO_SAVES; two saves of the game in the connected account refused as TWO_SAVES; why said for
each refusal: TWO_SAVES for a copy, SAVE_DAMAGED for the one save that does not open whole or whose header does not
carry the game, SAVES_UNSURE whenever the search could not read every save;
the profile not read as a game; nothing written to the folder; nothing kept between searches: a copy made after a
search refused at the next, and said, then the game found again once alone; a save whose start names the game refused
when its header does not, when its header raises, or when the whole save is damaged; a copy whose id line is past the
first start read but within the ceiling still counted, so refused, and one past the ceiling refusing the search; a save
that is not a game's text said with its slot, the search going on; more than MAX_SAVES saves in an account, or more
than MAX_ACCOUNTS accounts, refuse the search and say their count, the bounds themselves accepted; a save that does not
open said with its slot, the search going on; every save's start read once at the first size, one chunk each, a real
size save included, and only the game's save opened whole; a save held an instant tried again and found; a save held
for good, an unreadable account and the time bound each refuse the search and say it, the bound passed inside one
save's longer start reads too; the start never read past the ceiling, whatever the first size; a found save's stamp,
its last write and size, changed when it is written again with another size, None once it is gone; an unreadable saves
folder said, never raised; no Steam ID and no path in the whole log; the places Windows gives for Documents listed
without failing."""

import pathlib
import re
import shutil
import sys
import time
import zlib

import sdk_stubs

state = sdk_stubs.install()

import save_fixture as fx  # noqa: E402
from hunter_change import held_file, save_codec, save_places, save_text, steam_account  # noqa: E402

# No test reads the real registry: the connected account is set where it matters.
steam_account.connected = lambda: None

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def snapshot(root: pathlib.Path) -> dict:
    return {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in root.rglob("*") if path.is_file()}


def said(since: int, words: str) -> bool:
    """Whether a log line written after the first `since` ones holds these words."""
    return any(words in line for line in state["logs"][since:])


def why(answer) -> str | None:
    """Why the search found no save, None when it found one."""
    return answer.why if isinstance(answer, save_places.Missing) else None


def harlowe_found() -> bool:
    found = save_places.find(fx.HARLOWE_GAME, [documents])
    return isinstance(found, save_places.Save) and found.slot == 4


documents, client = fx.saves_folder()
save_games = client.parents[2]
theirs = save_games / str(fx.OTHER) / "Profiles" / "client"
theirs.mkdir(parents=True)
VEX = fx.full_size(fx.game_text(fx.VEX_GAME, "DarkSiren", "Vex", None))
HARLOWE = fx.game_text(fx.HARLOWE_GAME, "Gravitar", "Harlowe", fx.TREES["Gravitar"])
AMON_GAME = "C" * 32
AMON = fx.game_text(AMON_GAME, "Paladin", "Amon", None)
fx.put(client, 1, VEX)
fx.put(client, 4, HARLOWE)
(client / "profile.sav").write_bytes(save_codec.encode(b"domains: \n", fx.ACCOUNT))
# Closed with ACCOUNT in OTHER's folder: it opens only with ACCOUNT, as a save of another account would.
fx.put(theirs, 1, fx.game_text("F" * 32, "Paladin", "Amon", None))
before = snapshot(documents)

found = save_places.find(fx.HARLOWE_GAME, [documents])
check("a game's save found and opened, with its account and slot",
      isinstance(found, save_places.Save) and (found.slot, found.account, found.text) == (4, fx.ACCOUNT, HARLOWE)
      and found.data == (client / "4.sav").read_bytes() and found.path == client / "4.sav")
check("no save for a game no save carries", why(save_places.find("E" * 32, [documents])) == save_places.NO_SAVE)
check("a save of another account never taken for a game",
      why(save_places.find("F" * 32, [documents])) == save_places.NO_SAVE)
check("no save for an id that is not a game's",
      why(save_places.find("../x", [documents])) == save_places.NO_SAVE
      and why(save_places.find(fx.HARLOWE_GAME.lower(), [documents])) == save_places.NO_SAVE)
check("nothing written to the folder", snapshot(documents) == before)

fx.put(client, 7, HARLOWE)
since = len(state["logs"])
check("a copy made after a search refused at the next, and said",
      why(save_places.find(fx.HARLOWE_GAME, [documents])) == save_places.TWO_SAVES and said(since, "2 saves"))
(client / "7.sav").unlink()
check("the game found again once alone", harlowe_found())

# The game in two accounts, as an older account's folder keeps a copy of it (Kevin's Vex, 2026-09-29).
fx.put(theirs, 4, HARLOWE, fx.OTHER)
since = len(state["logs"])
check("with several accounts and the connected one unknown, all read: the game in two refused as TWO_SAVES",
      why(save_places.find(fx.HARLOWE_GAME, [documents])) == save_places.TWO_SAVES
      and said(since, "2 accounts, the connected Steam account unknown, all read") and said(since, "2 saves"))
steam_account.connected = lambda: fx.ACCOUNT
since = len(state["logs"])
found = save_places.find(fx.HARLOWE_GAME, [documents])
check("the connected account's saves read alone: its copy found, though another account holds one, and said",
      isinstance(found, save_places.Save) and (found.path, found.account) == (client / "4.sav", fx.ACCOUNT)
      and said(since, "2 accounts, the connected Steam account's read alone"))
steam_account.connected = lambda: fx.OTHER
found = save_places.find(fx.HARLOWE_GAME, [documents])
check("the other account connected: its own copy found",
      isinstance(found, save_places.Save) and (found.path, found.account) == (theirs / "4.sav", fx.OTHER))
steam_account.connected = lambda: fx.OTHER + 7
since = len(state["logs"])
check("a connected account without a folder: all read, the game in two refused as TWO_SAVES",
      why(save_places.find(fx.HARLOWE_GAME, [documents])) == save_places.TWO_SAVES
      and said(since, "2 accounts, the connected Steam account has no saves folder, all read"))
(theirs / "4.sav").unlink()
steam_account.connected = lambda: fx.ACCOUNT
fx.put(client, 7, HARLOWE)
check("two saves of the game in the connected account refused as TWO_SAVES",
      why(save_places.find(fx.HARLOWE_GAME, [documents])) == save_places.TWO_SAVES)
(client / "7.sav").unlink()
steam_account.connected = lambda: None

fx.put(client, 8, AMON)
found = save_places.find(AMON_GAME, [documents])
check("a save whose start names the game opened whole",
      isinstance(found, save_places.Save) and found.slot == 8 and found.text == AMON)
fx.put(client, 8, AMON.replace(b"  char_name: Amon\n", b""))
check("a save whose start names the game refused as SAVE_DAMAGED when its header does not",
      why(save_places.find(AMON_GAME, [documents])) == save_places.SAVE_DAMAGED)
cut = zlib.compress(AMON) + (len(AMON) + 1).to_bytes(4, "little")
pad = -len(cut) % 16
(client / "8.sav").write_bytes(save_codec.aes_ecb(cut + bytes([pad]) * pad, save_codec.steam_key(fx.ACCOUNT), False))
check("a save whose start names the game refused as SAVE_DAMAGED when the whole save is damaged",
      why(save_places.find(AMON_GAME, [documents])) == save_places.SAVE_DAMAGED)
(client / "8.sav").unlink()

real_header = save_text.header
save_text.header = lambda text: int("²")  # raises ValueError, as a level written "²" once did
since = len(state["logs"])
try:
    answer, raised = save_places.find(fx.HARLOWE_GAME, [documents]), False
except ValueError:
    answer, raised = None, True
finally:
    save_text.header = real_header
check("a header that raises refuses the save as SAVE_DAMAGED, said with its slot, never raised",
      not raised and why(answer) == save_places.SAVE_DAMAGED and said(since, "slot 4 "))

# A field before the id line, as a game patch could add one: the id then past the first start read, or the ceiling.
pushed = HARLOWE.replace(b"state: \n", b"state: \n  added: " + b"a" * 300 + b"\n", 1)
fx.put(client, 9, pushed)
since = len(state["logs"])
check("a copy whose id line is past the first start but within the ceiling still counted, so refused",
      pushed.index(b"  char_guid: ") > save_places.FIRST_START
      and why(save_places.find(fx.HARLOWE_GAME, [documents])) == save_places.TWO_SAVES and said(since, "2 saves"))
fx.put(client, 9, HARLOWE.replace(b"state: \n", b"state: \n  added: " + b"a" * save_places.START_CEILING + b"\n", 1))
since = len(state["logs"])
check("a save whose id line is past the ceiling refuses the search as SAVES_UNSURE, its slot said",
      why(save_places.find(fx.HARLOWE_GAME, [documents])) == save_places.SAVES_UNSURE and said(since, "slot 9 "))
fx.put(client, 9, b"domains: \n")
fx.put(client, 10, b"state: \n  class: Char_Gravitar\n")
since = len(state["logs"])
check("a save not a game's text, or whose whole text ends without an id, said with its slot, the search going on",
      harlowe_found() and said(since, "slot 9 is not a game's") and said(since, "slot 10 is not a game's"))
(client / "9.sav").unlink()
(client / "10.sav").unlink()

crowded = save_games / "76561190000000003" / "Profiles" / "client"
crowded.mkdir(parents=True)
for slot in range(save_places.MAX_SAVES + 1):
    (crowded / f"{slot}.sav").write_bytes(b"x" * 16)
since = len(state["logs"])
check("more than MAX_SAVES saves in an account refuse the search as SAVES_UNSURE, their count said",
      why(save_places.find(fx.HARLOWE_GAME, [documents])) == save_places.SAVES_UNSURE
      and said(since, f"{save_places.MAX_SAVES + 1} saves"))
(crowded / "0.sav").unlink()
since = len(state["logs"])
check("MAX_SAVES saves in an account read", harlowe_found())
check("a save that does not open said with its slot, the search going on", said(since, "slot 10 does not open"))
shutil.rmtree(crowded.parents[1])

extra = [save_games / str(76561190000000010 + number) for number in range(save_places.MAX_ACCOUNTS - 1)]
for folder in extra:
    folder.mkdir()
since = len(state["logs"])
check("more than MAX_ACCOUNTS accounts refuse the search as SAVES_UNSURE, their count said",
      why(save_places.find(fx.HARLOWE_GAME, [documents])) == save_places.SAVES_UNSURE
      and said(since, f"{save_places.MAX_ACCOUNTS + 1} accounts"))
extra.pop().rmdir()
check("MAX_ACCOUNTS accounts read", harlowe_found())
for folder in extra:
    folder.rmdir()

read: list[str] = []
starts: list[int] = []
wholes: list[int] = []
real_read, real_start, real_decode = save_places._read, save_codec.decode_start, save_codec.decode


def counted_read(path: pathlib.Path) -> bytes:
    read.append(path.name)
    return real_read(path)


save_places._read = counted_read
save_codec.decode_start = lambda data, account, size: starts.append(size) or real_start(data, account, size)
save_codec.decode = lambda data, account: wholes.append(account) or real_decode(data, account)
save_places.find(fx.HARLOWE_GAME, [documents])
check("every save's start read once at the first size, only the game's save opened whole",
      sorted(read) == ["1.sav", "1.sav", "4.sav"] and starts == [save_places.FIRST_START] * 3
      and wholes == [fx.ACCOUNT])
check("the profile not read as a game", "profile.sav" not in read)
chunks: list[int] = []
real_aes = save_codec.aes_ecb
save_codec.aes_ecb = lambda data, keys, decrypt: chunks.append(len(data)) or real_aes(data, keys, decrypt)
save_places.find("E" * 32, [documents])
save_codec.decode_start, save_codec.decode, save_codec.aes_ecb = real_start, real_decode, real_aes
check("a search decrypts one chunk of each save, a real-size one included",
      len((client / "1.sav").read_bytes()) > 12_000 and len(chunks) == 3
      and all(size <= save_codec.START_CHUNK for size in chunks) and save_codec.START_CHUNK in chunks)

held: dict[str, int] = {}
pauses: list[float] = []


def held_read(path: pathlib.Path) -> bytes:
    if held.get(path.name, 0):
        held[path.name] -= 1
        raise PermissionError(13, "The process cannot access the file", path.name)
    return real_read(path)


save_places._read = held_read
held["4.sav"] = 1
found = save_places.find(fx.HARLOWE_GAME, [documents], sleep=pauses.append)
check("a save held an instant tried again and found",
      isinstance(found, save_places.Save) and found.slot == 4 and pauses == [held_file.PAUSES_S[0]])
held["1.sav"] = 99
pauses.clear()
since = len(state["logs"])
check("a save held for good refuses the search as SAVES_UNSURE, though another slot carries the game, and says it",
      why(save_places.find(fx.HARLOWE_GAME, [documents], sleep=pauses.append)) == save_places.SAVES_UNSURE
      and pauses == list(held_file.PAUSES_S) and said(since, "slot 1 "))
save_places._read = real_read

real_iterdir = pathlib.Path.iterdir


def denied(self):
    raise PermissionError(13, "Access is denied", str(self))


def search_with(iterdir) -> tuple[object, bool]:
    """The search's answer while folders are listed this way, and whether it raised."""
    pathlib.Path.iterdir = iterdir
    try:
        return save_places.find(fx.HARLOWE_GAME, [documents]), False
    except OSError:
        return None, True
    finally:
        pathlib.Path.iterdir = real_iterdir


since = len(state["logs"])
answer, raised = search_with(lambda self: denied(self) if self.name == "client" else real_iterdir(self))
check("an unreadable account refuses the search as SAVES_UNSURE and says it",
      not raised and why(answer) == save_places.SAVES_UNSURE and said(since, "an account's saves are not readable"))

real_clock = time.monotonic
ticks = iter([0.0, 0.0])
time.monotonic = lambda: next(ticks, 99.0)
since = len(state["logs"])
try:
    stopped = save_places.find(fx.HARLOWE_GAME, [documents])
finally:
    time.monotonic = real_clock
check("the search stopped at MAX_SECONDS as SAVES_UNSURE and said",
      why(stopped) == save_places.SAVES_UNSURE and said(since, "stopped"))

# Each start read costing 3 s, as a forged save of empty deflate blocks can make it: the bound passes inside one save.
slow_documents, slow_client = fx.saves_folder()
fx.put(slow_client, 1, pushed)
clock = [0.0]


def slow_start(data: bytes, account: int, size: int) -> bytes:
    clock[0] += 3.0
    return real_start(data, account, size)


time.monotonic, save_codec.decode_start = (lambda: clock[0]), slow_start
since = len(state["logs"])
try:
    stopped = save_places.find(fx.HARLOWE_GAME, [slow_documents])
finally:
    time.monotonic, save_codec.decode_start = real_clock, real_start
check("the bound passed while a save's start is read longer refuses the search, never skips the save, and says it",
      why(stopped) == save_places.SAVES_UNSURE and said(since, "refused: stopped"))

fx.put(client, 9, HARLOWE.replace(b"state: \n", b"state: \n  added: " + b"a" * save_places.START_CEILING + b"\n", 1))
sizes: list[int] = []
first_start, save_places.FIRST_START = save_places.FIRST_START, 100
save_codec.decode_start = lambda data, account, size: sizes.append(size) or real_start(data, account, size)
since = len(state["logs"])
try:
    beyond = save_places.find(fx.HARLOWE_GAME, [documents])
finally:
    save_places.FIRST_START, save_codec.decode_start = first_start, real_start
(client / "9.sav").unlink()
check("a first start that does not reach the ceiling by doubling: never read past it, the search refused",
      why(beyond) == save_places.SAVES_UNSURE and max(sizes) == save_places.START_CEILING and said(since, "slot 9 "))

stamp_documents, stamp_client = fx.saves_folder()
stamp_path = fx.put(stamp_client, 4, HARLOWE)
stamped = save_places.find(fx.HARLOWE_GAME, [stamp_documents])
status = stamp_path.stat()
first_stamp = save_places.stamp(stamped)
check("a found save's stamp: when it was last written and its size",
      first_stamp == (status.st_mtime_ns, status.st_size))
fx.put(stamp_client, 4, fx.full_size(HARLOWE))
check("the stamp changes when the save is written again with another size",
      save_places.stamp(stamped) not in (None, first_stamp))
stamp_path.unlink()
check("no stamp once the save is gone", save_places.stamp(stamped) is None)

check("no save without a save folder",
      why(save_places.find(fx.HARLOWE_GAME, [documents / "nowhere"])) == save_places.NO_SAVE)
since = len(state["logs"])
answer, raised = search_with(denied)
check("an unreadable saves folder said as SAVES_UNSURE, never raised",
      not raised and why(answer) == save_places.SAVES_UNSURE and said(since, "the saves folder is not readable"))
check("no Steam ID and no path in the whole log",
      not any(re.search(r"\d{17}", line) or str(documents) in line or ".sav" in line
              for line in state["logs"] + state["errors"]))
check("the places Windows gives for Documents listed without failing",
      all(isinstance(place, pathlib.Path) for place in save_places.documents_candidates()))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
