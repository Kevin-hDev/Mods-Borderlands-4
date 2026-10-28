# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of game_tools.py: the outside tools are where it says, in the working repository (its docs/ folder holds
the two pak tools, its outils/ folder deploy_sdkmods.py; the public copy has none, and says so).
python test_game_tools.py"""

import sys
import tempfile
from pathlib import Path

import game_tools

FAILURES = []


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


check("each tool has a bound", game_tools.REPAK_TIMEOUT_S > 0 and game_tools.GAME_FILES_TIMEOUT_S > 0)
if game_tools.DOCS.is_dir():
    check("repak where it is named", game_tools.REPAK.is_file())
    check("game_files where it is named", game_tools.GAME_FILES.is_file())
else:
    print("NOTE: docs/ absent (public copy): the tools' places not checked")
games = game_tools.known_games()
if game_tools.DOCS.is_dir():
    check("in the workshop, the game copies come from deploy_sdkmods.py, with its default among them",
          games is not None and games[1] in games[0])
else:
    check("no deploy_sdkmods.py (public copy): no game copies", games is None)
real_tools = game_tools.TOOLS
with tempfile.TemporaryDirectory() as folder:
    game_tools.TOOLS = Path(folder)
    check("without deploy_sdkmods.py, known_games says None, not a guess", game_tools.known_games() is None)
game_tools.TOOLS = real_tools

print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
sys.exit(1 if FAILURES else 0)
