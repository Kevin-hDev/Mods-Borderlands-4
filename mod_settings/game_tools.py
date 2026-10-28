# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The outside tools, named here and nowhere else: the two that read and write the game's paks (build_pak.py,
game_ui_copies.py), with how long each may run, and the workshop's deploy_sdkmods.py, which names the game copies
(install_pak.py, the tests' SDK). The public copy has none of them."""

import importlib
import sys
from pathlib import Path

# borderlands_4/docs and borderlands_4/outils: this file sits in borderlands_4/mods/perso/mod_settings/source.
DOCS = Path(__file__).resolve().parents[4] / "docs"
TOOLS = Path(__file__).resolve().parents[4] / "outils"
# The HUD Editor's pinned repak, the one whose paks the game has loaded (docs/candidats/HUD/README.md).
REPAK = DOCS / "candidats" / "HUD" / ".tools" / "repak" / "0.2.3" / "repak.exe"
# repak 0.2.3 cannot list the game's paks 5, 14, 15 and 23 (update of 22 October 2026); this CUE4Parse reader
# can, and refuses when an unreadable pak numbered higher could hide a newer copy (its README).
GAME_FILES = DOCS / "renforts" / "outils" / "game_files" / "bin" / "game_files.exe"
REPAK_TIMEOUT_S = 60
GAME_FILES_TIMEOUT_S = 600


def known_games():
    """({name: game folder}, default name) from deploy_sdkmods.py, the one place they are named; None without it."""
    if not (TOOLS / "deploy_sdkmods.py").is_file():
        return None
    sys.path.insert(0, str(TOOLS))
    try:
        deploy_sdkmods = importlib.import_module("deploy_sdkmods")
    finally:
        sys.path.pop(0)
    return deploy_sdkmods.GAMES, deploy_sdkmods.DEFAULT_GAME
