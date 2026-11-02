# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Builds the shared menu file from the game's newest pause and main menus. Each mod's pak builder calls
shared_files(); run alone, it writes the result in build/ to be read, and installs nothing.

python build_menus.py   (game open or closed: it only reads the game's paks)"""

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import menu_recipe

HERE = menu_recipe.HERE
# The workshop's pak tools (borderlands_4/outils/pak_tools.py), loaded by path: this folder is no package of it.
TOOLS_FILE = HERE.parents[2] / "outils" / "pak_tools.py"


def pak_tools():
    if not TOOLS_FILE.is_file():
        raise menu_recipe.RecipeError("The workshop's pak_tools.py is missing: the game's menus cannot be read.")
    spec = importlib.util.spec_from_file_location("menu_entries_pak_tools", TOOLS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def newest_menus(constants: dict, work: Path) -> tuple:
    """({path: game pak}, {path: bytes}) for each menu, in their newest copies, read under work/."""
    tools = pak_tools()
    if not tools.GAME_FILES.is_file():
        raise menu_recipe.RecipeError("game_files is missing (see its README to build it).")
    wanted = [menu["path"] for menu in constants["menus"]]
    output = work / "game_menus"
    if output.exists():
        shutil.rmtree(output)
    work.mkdir(parents=True, exist_ok=True)
    # The reader only writes under its working folder.
    result = subprocess.run([str(tools.GAME_FILES), output.name, *wanted], cwd=work, capture_output=True,
                            timeout=tools.GAME_FILES_TIMEOUT_S, check=False)
    if result.returncode != 0:
        raise menu_recipe.RecipeError("game_files refused or failed: a menu's newest copy is unknown.")
    sources = menu_recipe.newest_sources(result.stdout.decode("utf-8"), wanted)
    return sources, {path: (output / Path(path).name).read_bytes() for path in wanted}


def patched(raw: bytes, menu: dict, constants: dict) -> bytes:
    # "utf-8", not "utf-8-sig": a menu's byte order mark stays a character of the text, written back as found.
    entries = [(menu_recipe.ENTRIES / name).read_text(encoding="utf-8") for name in menu["entries"]]
    return menu_recipe.patch_menu(raw.decode("utf-8"), menu, entries, constants).encode("utf-8")


def shared_files(work: Path) -> tuple:
    """({pak path: bytes} of the two menus and the shared script, {menu path: game pak it came from}, constants)."""
    constants = menu_recipe.load_constants()
    sources, raws = newest_menus(constants, work)
    files = {menu["path"]: patched(raws[menu["path"]], menu, constants) for menu in constants["menus"]}
    files[constants["scriptPath"]] = menu_recipe.SCRIPT.read_bytes()
    return files, sources, constants


def main() -> int:
    build = HERE / "build"
    files, sources, constants = shared_files(build)
    manifest = {"version": constants["version"], "sources": sources,
                "files": {path: hashlib.sha256(data).hexdigest().upper() for path, data in files.items()}}
    for path, data in files.items():
        (build / Path(path).name).write_bytes(data)
    (build / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"RESULTAT: OK shared menu file {constants['version']} "
          f"({', '.join(f'{Path(p).name} from {s}' for p, s in sources.items())})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (menu_recipe.RecipeError, OSError, subprocess.TimeoutExpired, UnicodeError, ValueError) as error:
        print(f"RESULTAT: ECHEC {error}")
        sys.exit(1)
