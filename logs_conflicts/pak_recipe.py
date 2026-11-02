# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Recipe of the Logs & Conflicts pak: the shared menu file (menu_entries), the page script made of page/'s sources
in one scope, and the page's stylesheet. Pure but for load_constants: the tests drive it directly.

python pak_recipe.py          prints the page script as the pak carries it (test_page.js runs it)
python pak_recipe.py config   prints the page's config (test_texts.js reads it)"""

import json
import sys
from pathlib import Path

import package_path  # noqa: F401  (before the package's modules)
import game_tools
from logs_conflicts import copy_texts, protocol

HERE = Path(__file__).resolve().parent
PAGE = HERE / "page"
# In dependency order. The build closes them in one function scope: the page's only global is window.LogsConflicts,
# since Mod Settings' script, in the same menu page, puts its names at the page's root (conception, section 3).
SOURCES = ("language.js", "transport.js", "texts.js", "conflicts_view.js", "borrow.js", "frame.js", "focus.js",
           "page.js", "entry.js")
STYLESHEET = "logs_conflicts.css"
PAKS_FOLDER = "OakGame/Content/Paks"
HTTP_KEYS = ("host", "port", "basePath", "routes", "timeoutMs", "helloRetriesMs", "maxQueued", "maxResponseBytes",
             "maxLogResponseBytes", "maxConflictsResponseBytes")


class RecipeError(RuntimeError):
    """What the recipe relies on changed: refuse to build rather than guess."""


def load_constants() -> dict:
    try:
        return protocol.load_constants()
    except ValueError as error:
        raise RecipeError(str(error)) from None


def page_config(constants: dict) -> dict:
    """What the page needs, as one JSON authority built from the constants; no game path."""
    menu_recipe, _build_menus = game_tools.menu_entries()
    config = {key: constants[key] for key in ("version", "marker", "languages", "texts")}
    config["http"] = {key: constants["http"][key] for key in HTTP_KEYS}
    config["page"] = dict(constants["page"], ownStylesheet=menu_recipe.coui_url(constants["pak"]["cssPath"]),
                          maskReplacement=constants["masking"]["replacement"],
                          conflictSections=constants["conflicts"]["sections"],
                          conflictReasons=constants["conflicts"]["reasons"],
                          conflictBounds=copy_texts.bounds(constants))
    return config


def read_sources() -> dict:
    return {name: (PAGE / name).read_text(encoding="utf-8") for name in SOURCES}


def page_script(constants: dict, sources: dict) -> str:
    """sources maps each name of SOURCES to its text (read_sources)."""
    config = json.dumps(page_config(constants), separators=(",", ":"), ensure_ascii=True)
    parts = ["(function () {", '"use strict";', "const LC_CONFIG = " + config + ";"]
    parts.extend(sources[name] for name in SOURCES)
    parts.append("if (!window.LogsConflicts) window.LogsConflicts = lcInstall(LC_CONFIG);")
    parts.append("})();")
    return "\n".join(parts)


if __name__ == "__main__":
    made = (json.dumps(page_config(load_constants()), ensure_ascii=True) if sys.argv[1:] == ["config"]
            else page_script(load_constants(), read_sources()))
    sys.stdout.buffer.write(made.encode("utf-8"))
