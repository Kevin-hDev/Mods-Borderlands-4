# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Builds the Mod Settings pak from the game's newest pause and main menus, our page script and stylesheet.

python build_pak.py   (game open or closed: it only reads the game's paks)
The .sdkmod is built apart, by borderlands_4/outils/deploy_sdkmods.py; this pak holds the page.
Output: build/<pak name> and build/manifest.json. Nothing is installed here; see install_pak.py.
"""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import build_history
import pak_recipe
from game_tools import GAME_FILES, GAME_FILES_TIMEOUT_S, REPAK, REPAK_TIMEOUT_S

HERE = pak_recipe.HERE
BUILD = HERE / "build"
STAGING = BUILD / "input"
HISTORY = BUILD / "history.json"


def run(args: list, timeout: int = REPAK_TIMEOUT_S) -> bytes:
    result = subprocess.run(args, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise pak_recipe.RecipeError(f"repak failed: {Path(args[1]).name} {result.returncode}")
    return result.stdout


def entries_of(pak: Path) -> list:
    return run([str(REPAK), "list", str(pak)]).decode("utf-8").splitlines()


def read_entry(pak: Path, entry: str) -> bytes:
    return run([str(REPAK), "get", str(pak), entry])


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def newest_menus(constants: dict) -> tuple:
    """({path: game pak}, {path: bytes}) for each menu of the recipe, in their newest copies."""
    wanted = [menu["path"] for menu in constants["pak"]["menus"]]
    output = BUILD / "game_copy"
    if output.exists():
        shutil.rmtree(output)
    # The reader only writes under its working folder, so it runs from build/.
    result = subprocess.run([str(GAME_FILES), output.name, *wanted], cwd=BUILD, capture_output=True,
                            timeout=GAME_FILES_TIMEOUT_S, check=False)
    if result.returncode != 0:
        raise pak_recipe.RecipeError("game_files refused or failed: a menu's newest copy is unknown.")
    sources = pak_recipe.newest_sources(result.stdout.decode("utf-8"), wanted)
    return sources, {path: (output / Path(path).name).read_bytes() for path in wanted}


def patched_html(raw: bytes, menu: dict, constants: dict) -> bytes:
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    html = raw[len(bom):].decode("utf-8")
    entry = (pak_recipe.PAGE / menu["entry"]).read_text(encoding="utf-8")
    return bom + pak_recipe.patch_menu(html, entry, menu, constants).encode("utf-8")


def page_script(constants: dict) -> bytes:
    sources = {name: (pak_recipe.PAGE / name).read_text(encoding="utf-8") for name in pak_recipe.SOURCES}
    return pak_recipe.page_script(constants, sources).encode("utf-8")


def stage(files: dict) -> None:
    if STAGING.exists():
        shutil.rmtree(STAGING)
    for entry, data in files.items():
        target = STAGING / entry
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def pack(constants: dict, files: dict) -> Path:
    pak_settings = constants["pak"]
    pak = BUILD / pak_settings["name"]
    if pak.exists():
        pak.unlink()
    run([str(REPAK), "pack", "--mount-point", pak_settings["mountPoint"], "--version", pak_settings["pakVersion"],
         "--path-hash-seed", pak_settings["pathHashSeed"], str(STAGING), str(pak)])
    listed = sorted(entries_of(pak))
    if listed != sorted(files):
        raise pak_recipe.RecipeError(f"Pak entries differ: {listed}")
    for entry, data in files.items():
        if read_entry(pak, entry) != data:
            raise pak_recipe.RecipeError(f"Pak entry differs from the staged bytes: {entry}")
    return pak


def main() -> int:
    constants = pak_recipe.load_constants()
    if not REPAK.is_file() or not GAME_FILES.is_file():
        raise pak_recipe.RecipeError("repak or game_files is missing (game_files: see its README to build it).")
    BUILD.mkdir(exist_ok=True)
    sources, raws = newest_menus(constants)
    files = {menu["path"]: patched_html(raws[menu["path"]], menu, constants) for menu in constants["pak"]["menus"]}
    files[constants["pak"]["scriptPath"]] = page_script(constants)
    files[constants["pak"]["cssPath"]] = (pak_recipe.PAGE / pak_recipe.STYLESHEET).read_bytes()
    stage(files)
    pak = pack(constants, files)
    manifest = {
        "version": 2,
        "pak": pak.name,
        "pakSha256": sha256(pak.read_bytes()),
        "sources": {path: {"pak": sources[path], "sha256": sha256(raws[path])} for path in sources},
        "entries": {entry: sha256(data) for entry, data in files.items()},
    }
    (BUILD / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    note = build_history.remember(HISTORY, manifest["pakSha256"])
    if note:
        print(f"NOTE: {note}")
    origin = ", ".join(f"{Path(path).name} from {pak_name}" for path, pak_name in sources.items())
    print(f"RESULTAT: OK {pak.name} {manifest['pakSha256']} ({origin})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (pak_recipe.RecipeError, OSError, subprocess.TimeoutExpired, UnicodeError) as error:
        print(f"RESULTAT: ECHEC {error}")
        sys.exit(1)
