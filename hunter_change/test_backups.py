"""The backups: in the mods' settings folder, never the saves'; a copy written whole, named by the game's id and the
UTC time, no temporary file left; the last MAX_PER_GAME copies of a game kept; MAX_GAMES games, the game backed up
longest ago forgotten first; the copy just written kept when the clock went back; a temporary file a crash left
removed by the next copy; a failed write said and None given, no temporary file left; a copy that cannot be removed
passed over and said once, the rest of the pruning still done; a folder that cannot be listed: the copy written and
given, said once, nothing removed; an id that is not a game's refused."""

import os
import stat
import sys
import time
from pathlib import Path

import sdk_stubs

state = sdk_stubs.install()

import save_fixture as fx  # noqa: E402
from hunter_change import backups, file_replace, report  # noqa: E402

fails: list[str] = []
G = fx.HARLOWE_GAME


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def copies(game: str) -> list[bytes]:
    return [path.read_bytes() for path in sorted(backups.folder().glob(f"{game}_*.sav"))]


check("in the mods' settings folder", backups.folder().parent == state["settings_dir"])
NOW = 1790625312.25
path = backups.save(G, b"save bytes", now=NOW)
check("a copy written whole, named by the game's id and the time", path is not None
      and path.read_bytes() == b"save bytes"
      and path.name == f"{G}_{time.strftime('%Y%m%d-%H%M%S', time.gmtime(NOW))}-250.sav")
check("no temporary file left", not list(backups.folder().glob("*.tmp")))

for index in range(8):
    backups.save(G, bytes([index]), now=NOW + 10 + index)
check("the last MAX_PER_GAME copies of a game kept",
      copies(G) == [bytes([index]) for index in range(8 - backups.MAX_PER_GAME, 8)])

others = [f"{index:032X}" for index in range(1, backups.MAX_GAMES + 1)]
for index, game in enumerate(others):
    backups.save(game, b"x", now=NOW + 100 + index)
check("MAX_GAMES games, the game backed up longest ago forgotten first",
      copies(G) == [] and all(copies(game) == [b"x"] for game in others))

for index in range(backups.MAX_PER_GAME):
    backups.save(G, b"later", now=NOW + 500 + index)
earlier = backups.save(G, b"clock went back", now=NOW + 400)
check("the copy just written kept when the clock went back", earlier is not None and earlier.exists())

leftover = backups.folder() / f"{G}_20260101-000000-000.sav{file_replace.TEMPORARY_SUFFIX}"
leftover.write_bytes(b"cut")
backups.save(G, b"after a crash", now=NOW + 600)
check("a temporary file a crash left removed by the next copy", not leftover.exists())

real_replace = os.replace
os.replace = lambda *_args: (_ for _ in ()).throw(OSError("disk full"))
report.reset()
state["errors"].clear()
failed = backups.save(G, b"y", now=NOW + 999)
os.replace = real_replace
check("a failed write said and None given, no temporary file left", failed is None and len(state["errors"]) == 1
      and b"y" not in copies(G) and not list(backups.folder().glob("*.tmp")))

# Windows refuses to delete a read-only file: G's oldest copy, past the bound, stuck before H's surplus in the pruning.
stuck = backups.folder() / f"{G}_20260101-000000-000.sav"
stuck.write_bytes(b"stuck")
os.chmod(stuck, stat.S_IREAD)
report.reset()
state["errors"].clear()
H = f"{backups.MAX_GAMES + 1:032X}"
try:
    written = [backups.save(H, bytes([index]), now=NOW + 700 + index) for index in range(backups.MAX_PER_GAME + 3)]
except OSError:
    written = []
finally:
    os.chmod(stuck, stat.S_IREAD | stat.S_IWRITE)
check("a copy that cannot be removed: every copy written, the other game's surplus still removed, said once",
      len(written) == backups.MAX_PER_GAME + 3 and None not in written and written[-1].exists()
      and copies(H) == [bytes([index]) for index in range(3, backups.MAX_PER_GAME + 3)]
      and stuck.exists() and len(state["errors"]) == 1)

before = set(backups.folder().iterdir())
real_iterdir = Path.iterdir
Path.iterdir = lambda *_args: (_ for _ in ()).throw(PermissionError("folder unreadable"))
report.reset()
state["errors"].clear()
try:
    kept = backups.save(H, b"unlisted", now=NOW + 800)
except OSError:
    kept = None
finally:
    Path.iterdir = real_iterdir
check("a folder that cannot be listed: the copy written and given, said once, nothing removed", kept is not None
      and kept.read_bytes() == b"unlisted" and len(state["errors"]) == 1
      and set(backups.folder().iterdir()) == before | {kept})

refused = 0
for game in (G.lower(), "../x", ""):
    try:
        backups.save(game, b"z")
    except ValueError:
        refused += 1
check("an id that is not a game's refused", refused == 3)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
