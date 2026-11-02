# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Builds the Logs & Conflicts pak: the shared menu file made from the game's newest menus, our page script and its
stylesheet.

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
import game_tools
import pak_recipe

HERE = pak_recipe.HERE
BUILD = HERE / "build"
STAGING = BUILD / "input"
HISTORY = BUILD / "history.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


class Repak:
    def __init__(self, tools):
        self.exe, self.timeout = tools.REPAK, tools.REPAK_TIMEOUT_S
        if not self.exe.is_file():
            raise pak_recipe.RecipeError("repak is missing.")

    def run(self, args: list) -> bytes:
        result = subprocess.run([str(self.exe), *args], capture_output=True, timeout=self.timeout, check=False)
        if result.returncode != 0:
            raise pak_recipe.RecipeError(f"repak failed: {args[0]} {result.returncode}")
        return result.stdout

    def entries(self, pak: Path) -> list:
        return self.run(["list", str(pak)]).decode("utf-8").splitlines()

    def entry(self, pak: Path, name: str) -> bytes:
        return self.run(["get", str(pak), name])


def page_files(constants: dict, script_path: str) -> dict:
    return {script_path: pak_recipe.page_script(constants, pak_recipe.read_sources()).encode("utf-8"),
            constants["pak"]["cssPath"]: (pak_recipe.PAGE / pak_recipe.STYLESHEET).read_bytes()}


def stage(files: dict) -> None:
    if STAGING.exists():
        shutil.rmtree(STAGING)
    for entry, data in files.items():
        target = STAGING / entry
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def pack(repak: Repak, constants: dict, name: str, files: dict) -> Path:
    settings = constants["pak"]
    pak = BUILD / name
    if pak.exists():
        pak.unlink()
    repak.run(["pack", "--mount-point", settings["mountPoint"], "--version", settings["pakVersion"],
               "--path-hash-seed", settings["pathHashSeed"], str(STAGING), str(pak)])
    listed = sorted(repak.entries(pak))
    if listed != sorted(files):
        raise pak_recipe.RecipeError(f"Pak entries differ: {listed}")
    for entry, data in files.items():
        if repak.entry(pak, entry) != data:
            raise pak_recipe.RecipeError(f"Pak entry differs from the staged bytes: {entry}")
    return pak


def main() -> int:
    constants = pak_recipe.load_constants()
    menu_recipe, build_menus = game_tools.menu_entries()
    repak = Repak(build_menus.pak_tools())
    BUILD.mkdir(exist_ok=True)
    files, sources, shared = build_menus.shared_files(BUILD)
    name = menu_recipe.pak_name(constants["pak"]["stem"], shared)
    files.update(page_files(constants, menu_recipe.script_path("logs_conflicts", shared)))
    stage(files)
    pak = pack(repak, constants, name, files)
    manifest = {
        "version": 1,
        "pak": pak.name,
        "pakSha256": sha256(pak.read_bytes()),
        "menuEntries": shared["version"],
        "sources": sources,
        "entries": {entry: sha256(data) for entry, data in files.items()},
    }
    (BUILD / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    note = build_history.remember(HISTORY, manifest["pakSha256"])
    if note:
        print(f"NOTE: {note}")
    print(f"RESULTAT: OK {pak.name} {manifest['pakSha256']} (shared menu file {shared['version']})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    # RuntimeError: this recipe's, the shared menu file's (menu_recipe.RecipeError) and a missing tool's refusals.
    except (RuntimeError, OSError, subprocess.TimeoutExpired, UnicodeError, ValueError) as error:
        print(f"RESULTAT: ECHEC {error}")
        sys.exit(1)
