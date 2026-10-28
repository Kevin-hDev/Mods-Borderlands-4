# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Installs, checks or removes the Mod Settings pak in a copy of the game, game closed only.
python install_pak.py --verifier | --installer | --retirer  [--jeu neuf|ancien|epic]
The game copies are those of borderlands_4/outils/deploy_sdkmods.py (GAMES), named there only; without --jeu, its
default. Only the pak named in build/manifest.json, with the exact bytes built, is ever written or deleted.
--verifier exits with 0 only when that pak is installed."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import build_history
import game_tools
import pak_recipe

MANIFEST = pak_recipe.HERE / "build" / "manifest.json"
PROCESS = "Borderlands4"
CHECK_TIMEOUT_S = 30
ACTIONS = ("--verifier", "--installer", "--retirer")


class InstallError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def game_running() -> bool:
    """Two independent answers, both must say closed: an empty output alone once hid a running game."""
    shell = subprocess.run(["powershell", "-NoProfile", "-Command",
                            f"Get-Process {PROCESS} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
                           capture_output=True, timeout=CHECK_TIMEOUT_S, check=False)
    tasks = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {PROCESS}.exe", "/FO", "CSV", "/NH"],
                           capture_output=True, timeout=CHECK_TIMEOUT_S, check=False)
    if tasks.returncode != 0:
        raise InstallError("tasklist failed: game state unknown.")
    by_shell = shell.stdout.decode("ascii", "replace").strip() != ""
    by_tasks = f'"{PROCESS}.exe"'.lower() in tasks.stdout.decode("cp850", "replace").lower()
    return by_shell or by_tasks


def known_games() -> tuple:
    """({name: game folder}, default name), from deploy_sdkmods.py (game_tools.py)."""
    games = game_tools.known_games()
    if games is None:
        raise InstallError("deploy_sdkmods.py not found: it names the game folders.")
    return games


def parse(argv: list, games: dict, default: str):
    """(action, game folder) or None for a command line that is not exactly expected."""
    if not argv or argv[0] not in ACTIONS:
        return None
    if len(argv) == 1:
        return argv[0], games[default]
    if len(argv) == 3 and argv[1] == "--jeu" and argv[2] in games:
        return argv[0], games[argv[2]]
    return None


def plan(constants: dict, manifest: dict, game: str) -> tuple:
    built = MANIFEST.parent / manifest["pak"]
    target = Path(game) / constants["pak"]["paksFolder"] / constants["pak"]["name"]
    if manifest["pak"] != constants["pak"]["name"] or not built.is_file():
        raise InstallError("Built pak missing or renamed: build it again.")
    if sha256(built) != manifest["pakSha256"]:
        raise InstallError("Built pak differs from its manifest: build it again.")
    return built, target


def earlier_builds() -> set:
    hashes, note = build_history.read(MANIFEST.parent / "history.json")
    if note:
        print(f"NOTE: {note}")
    return set(hashes)


def state(target: Path, expected: str, earlier: set = frozenset()) -> str:
    if not target.exists():
        return "absent"
    found = sha256(target)
    if found == expected:
        return "installed"
    return "earlier" if found in earlier else "foreign"


def install(built: Path, target: Path, expected: str, earlier: set = frozenset()) -> str:
    current = state(target, expected, earlier)
    if current == "installed":
        return "already installed"
    if current == "foreign":
        raise InstallError("Another file has the pak's name in the game: nothing written.")
    partial = target.with_name(target.name + ".partial")
    shutil.copyfile(built, partial)
    if sha256(partial) != expected:
        partial.unlink()
        raise InstallError("Copy differs from the built pak: nothing installed.")
    os.replace(partial, target)
    return "replaced an earlier build" if current == "earlier" else "installed"


def remove(target: Path, expected: str, earlier: set = frozenset()) -> str:
    current = state(target, expected, earlier)
    if current == "absent":
        return "already absent"
    if current == "foreign":
        raise InstallError("The file in the game is not the built pak: not deleted.")
    target.unlink()
    return "removed"


def main(argv: list, running=game_running, games=None) -> int:
    folders, default = games or known_games()
    command = parse(argv, folders, default)
    if command is None:
        print(__doc__)
        return 2
    action, game = command
    constants = pak_recipe.load_constants()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    built, target = plan(constants, manifest, game)
    expected = manifest["pakSha256"]
    earlier = earlier_builds()
    if action == "--verifier":
        found = state(target, expected, earlier)
        print(f"RESULTAT: {found} {target} game_running={running()}")
        return 0 if found == "installed" else 1
    if running():
        raise InstallError("The game is running: close it first.")
    if action == "--installer":
        outcome = install(built, target, expected, earlier)
    else:
        outcome = remove(target, expected, earlier)
    print(f"RESULTAT: {outcome} {target} {expected}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (InstallError, pak_recipe.RecipeError, OSError, subprocess.TimeoutExpired, KeyError, ValueError) as error:
        print(f"RESULTAT: ECHEC {error}")
        sys.exit(1)
