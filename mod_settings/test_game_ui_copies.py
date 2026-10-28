# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of game_ui_copies.py in a temporary folder, without the game's paks. python test_game_ui_copies.py"""

import sys
import tempfile
from pathlib import Path

import game_ui_copies

FAILURES = []


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


with tempfile.TemporaryDirectory() as folder:
    game_ui_copies.CACHE = Path(folder) / "test_game_ui"
    reader = game_ui_copies.GAME_FILES
    game_ui_copies.GAME_FILES = Path(folder) / "absent.exe"
    check("no reader and no copies (the public copy): not available", not game_ui_copies.available())
    game_ui_copies.GAME_FILES.write_bytes(b"")
    check("a reader: available", game_ui_copies.available())
    game_ui_copies.GAME_FILES = reader
    fetched = []
    game_ui_copies.fetch = lambda: fetched.append(True)
    try:
        game_ui_copies.copies()
        check("missing copies, still missing after a read: refused", False)
    except RuntimeError as error:
        check("missing copies, still missing after a read: refused", "missing" in str(error) and fetched == [True])
    game_ui_copies.CACHE.mkdir()
    for path in game_ui_copies.FILES:
        (game_ui_copies.CACHE / Path(path).name).write_text("// copy", encoding="utf-8")
    fetched.clear()
    found = game_ui_copies.copies()
    check("every copy present: none read again", fetched == [] and len(found) == len(game_ui_copies.FILES)
          and all(path.is_file() for path in found.values()))
    game_ui_copies.GAME_FILES = Path(folder) / "absent.exe"
    check("every copy present, no reader: available", game_ui_copies.available())
    game_ui_copies.GAME_FILES = reader
    game_ui_copies.copies(refresh=True)
    check("refresh reads the paks again", fetched == [True])
    check("the scripts listed are those of the files", set(game_ui_copies.SCRIPTS) ==
          {Path(path).name for path in game_ui_copies.FILES if path.endswith(".js")})

print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
sys.exit(1 if FAILURES else 0)
