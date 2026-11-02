# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What the pak tools of this mod take from outside its folder, found here and nowhere else: the shared menu file's
folder (menu_entries, which also loads the workshop's pak tools, borderlands_4/outils/pak_tools.py), the game
copies named in deploy_sdkmods.py, and the name of Mod Settings' pak, the other pak that carries the shared menu file.
The public copy has menu_entries and Mod Settings beside the mod and no workshop tools: each is asked for only when
used, and its absence is said plainly."""

import importlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The workshop's tools: this file sits in borderlands_4/mods/perso/logs_conflicts/source.
TOOLS = HERE.parents[3] / "outils"
# Beside the mod's folder in the public copy, first: there, the folder above is outside the repository. Then beside
# the mod's folder in the workshop (mods/perso/menu_entries).
MENU_ENTRIES_PLACES = (HERE.parent / "menu_entries", HERE.parents[1] / "menu_entries")
# Mod Settings' constants, in the same two layouts: its folder holds its package in the public copy, its source/ folder
# in the workshop.
MOD_SETTINGS_FOLDERS = (HERE.parent / "mod_settings", HERE.parents[1] / "mod_settings" / "source")
MOD_SETTINGS_CONSTANTS = tuple(folder / "mod_settings" / "assets" / "mod_settings.constants.json"
                               for folder in MOD_SETTINGS_FOLDERS)


class MissingTool(RuntimeError):
    pass


def menu_entries():
    """(menu_recipe, build_menus) of the shared menu file."""
    folder = next((place for place in MENU_ENTRIES_PLACES if (place / "menu_recipe.py").is_file()), None)
    if folder is None:
        raise MissingTool("The shared menu file's folder (menu_entries) is missing.")
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
    return importlib.import_module("menu_recipe"), importlib.import_module("build_menus")


def mod_settings_pak() -> str:
    """The name of Mod Settings' pak, which conflicts.paks.sharedMenu must know: read from its constants."""
    path = next((place for place in MOD_SETTINGS_CONSTANTS if place.is_file()), None)
    if path is None:
        raise MissingTool("Mod Settings' constants are missing.")
    return json.loads(path.read_text(encoding="utf-8"))["pak"]["name"]


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
