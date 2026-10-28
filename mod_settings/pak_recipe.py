# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Recipe of the Mod Settings pak: which game pak holds the newest copy of each menu, and how our entry and script
are inserted into it. No process access and, but for load_constants, no file access: the tests drive it directly."""

import json
import re
from pathlib import Path

import package_path  # noqa: F401  (before the package's modules)
import protocol

HERE = Path(__file__).resolve().parent
PAGE = HERE / "page"
# In dependency order: one script, the constants first (page_script).
SOURCES = ("language.js", "models.js", "logic.js", "layout.js", "sender.js", "transport.js",
           "data.js", "pieces.js", "rows.js", "details.js", "tabs.js", "frame.js",
           "screens.js", "scroll.js", "focus.js", "capture.js", "settings.js",
           "borrow.js", "page.js", "entry.js")
STYLESHEET = "mod_settings.css"
PAK_NUMBER = re.compile(r"^pakchunk0-Windows_(\d+)_P\.pak$")
CONTENT_ROOT = "OakGame/Content/"


class RecipeError(RuntimeError):
    """The game changed what the recipe relies on: refuse to build rather than guess."""


def load_constants() -> dict:
    """The mod's constants, by the mod's own loader (protocol.py), with the pak's name checked."""
    try:
        constants = protocol.load_constants()
    except ValueError as error:
        raise RecipeError(str(error)) from None
    pak = constants["pak"]
    if not pak["name"].endswith("_999_P.pak"):
        # Only the _999_P suffix has been seen loaded over the game's patches (HUD Editor, reinforcements).
        raise RecipeError("Pak name must keep the _999_P suffix.")
    return constants


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
                and PAK_NUMBER.match(item.get("latest", "")):
            sources[item["path"]] = item["latest"]
    if sorted(sources) != sorted(wanted):
        raise RecipeError("game_files gave no newest copy of a menu.")
    return sources


def newline_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def insert_once(text: str, needle: str, addition: str, before: bool) -> str:
    if text.count(needle) != 1:
        raise RecipeError("Official UI insertion point changed.")
    replacement = addition + needle if before else needle + addition
    return text.replace(needle, replacement)


def patch_menu(html: str, entry: str, menu: dict, constants: dict) -> str:
    newline = newline_of(html)
    entry = entry.replace("\r\n", "\n").rstrip("\n").replace("\n", newline) + newline
    script = newline + '<script src="' + coui_url(constants["pak"]["scriptPath"]) + '"></script>'
    patched = insert_once(html, menu["entryNeedle"], entry, before=True)
    return insert_once(patched, menu["scriptNeedle"], script, before=False)


def page_config(constants: dict) -> dict:
    config = {key: constants[key] for key in ("version", "marker", "events", "eventFields", "codePattern",
                                              "timingNames", "http", "catalog", "page", "capture", "languages",
                                              "texts")}
    config["page"] = dict(config["page"], ownStylesheet=coui_url(constants["pak"]["cssPath"]))
    return config


def page_script(constants: dict, sources: dict, config: dict = None) -> str:
    """sources maps each name of SOURCES to its text; the config comes first, as one JSON authority. The browser
    test passes its own config, page_config's with local addresses."""
    config = json.dumps(config or page_config(constants), separators=(",", ":"), ensure_ascii=True)
    parts = ["window.ModSettingsConfig=" + config + ";"]
    parts.extend(sources[name] for name in SOURCES)
    return "\n".join(parts)
