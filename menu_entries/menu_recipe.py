# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Recipe of the shared menu file of Mod Settings and Logs & Conflicts: each mod's hidden entry before the same mark
of the game's pause and main menus, then the mods' scripts and the shared script after the menu's own script.
Both mods' paks carry the result, byte for byte (docs/tools/journaux-et-conflits/conception.md, section 3).
Pure but for load_constants: the tests drive it directly."""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENTRIES = HERE / "entries"
CONSTANTS = HERE / "menu_entries.constants.json"
SCRIPT = HERE / "menu_entries.js"
CONTENT_ROOT = "OakGame/Content/"
GAME_PAK = re.compile(r"^pakchunk0-Windows_(\d+)_P\.pak$")
VERSION = 1


class RecipeError(RuntimeError):
    """The game changed what the recipe relies on: refuse to build rather than guess."""


def load_constants(path: Path = CONSTANTS) -> dict:
    constants = json.loads(path.read_text(encoding="utf-8"))
    if constants.get("version") != VERSION:
        raise RecipeError("Unknown shared menu file version.")
    return constants


def pak_number(constants: dict) -> int:
    """The number both mods' paks carry: the newest shared file then always wins over an older one (conception,
    section 3). The game loading _1000_P over _999_P was seen in game (feasibility gate, 1 November 2026)."""
    return constants["pakBase"] + constants["version"]


def pak_name(stem: str, constants: dict) -> str:
    return f"{stem}_{pak_number(constants)}_P.pak"


def script_path(mod: str, constants: dict) -> str:
    """Where the shared file loads that mod's script from: the mod's pak must put it there."""
    for script in constants["modScripts"]:
        if script["mod"] == mod:
            return script["path"]
    raise RecipeError(f"The shared menu file loads no script for {mod}.")


def coui_url(path: str) -> str:
    """The address the game's UI gives a file of its content folder (coui://uiresources/...)."""
    if not path.startswith(CONTENT_ROOT):
        raise RecipeError("Pak path outside the game's content folder.")
    return "coui://" + path[len(CONTENT_ROOT):]


def newest_sources(report: str, wanted: list) -> dict:
    """The game pak game_files took each newest copy from. Its report is JSON, then one RESULTAT line."""
    lines = report.strip().splitlines()
    if not lines or not lines[-1].startswith("RESULTAT:"):
        raise RecipeError("game_files report is incomplete.")
    try:
        files = json.loads("\n".join(lines[:-1]))["files"]
    except (ValueError, KeyError, TypeError):
        raise RecipeError("game_files report is unreadable.") from None
    sources = {}
    for item in files:
        if isinstance(item, dict) and item.get("path") in wanted and "refused" not in item \
                and GAME_PAK.match(item.get("latest", "")):
            sources[item["path"]] = item["latest"]
    if sorted(sources) != sorted(wanted):
        raise RecipeError("game_files gave no newest copy of a menu.")
    return sources


def entry_text(raw: str, constants: dict) -> str:
    token = constants["versionToken"]
    if raw.count(token) != 1:
        raise RecipeError("An entry must name the shared file's version once.")
    return raw.replace(token, str(constants["version"]))


def insert_once(text: str, needle: str, addition: str, before: bool) -> str:
    if text.count(needle) != 1:
        raise RecipeError("Official UI insertion point changed.")
    return text.replace(needle, addition + needle if before else needle + addition)


def patch_menu(html: str, menu: dict, entries: list, constants: dict) -> str:
    """entries: the raw text of each entry file of the menu, in the menu's order."""
    newline = "\r\n" if "\r\n" in html else "\n"
    block = "".join(entry_text(raw, constants).replace("\r\n", "\n").rstrip("\n").replace("\n", newline) + newline
                    for raw in entries)
    scripts = [*(script["path"] for script in constants["modScripts"]), constants["scriptPath"]]
    tags = "".join(newline + '<script src="' + coui_url(path) + '"></script>' for path in scripts)
    patched = insert_once(html, menu["entryNeedle"], block, before=True)
    return insert_once(patched, menu["scriptNeedle"], tags, before=False)
