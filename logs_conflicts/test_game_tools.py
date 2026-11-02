# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of game_tools.py: the shared menu file's folder found in the workshop's layout and in the public copy's,
its absence said plainly, Mod Settings' pak name, and the game copies taken from deploy_sdkmods.py or not at all.
python test_game_tools.py"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import game_tools

FAILURES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


PROBE = """import game_tools
recipe, _builder = game_tools.menu_entries()
print(recipe.__file__)
"""


def test_public_layout():
    """A copy laid out as the public repository: the mod's files in logs_conflicts/, the shared folder and Mod
    Settings' package beside it, and nothing of the workshop around. Both are found there, and the tests that build
    from the shared folder or read Mod Settings' pak name pass."""
    found = next(place for place in game_tools.MENU_ENTRIES_PLACES if (place / "menu_recipe.py").is_file())
    settings = next(place for place in game_tools.MOD_SETTINGS_CONSTANTS if place.is_file())
    skip = shutil.ignore_patterns("build", "__pycache__")
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    with tempfile.TemporaryDirectory() as folder:
        mod, shared = Path(folder) / "logs_conflicts", Path(folder) / "menu_entries"
        shutil.copytree(game_tools.HERE, mod, ignore=skip)
        shutil.copytree(found, shared, ignore=skip)
        assets = Path(folder) / "mod_settings" / "mod_settings" / "assets"
        assets.mkdir(parents=True)
        shutil.copyfile(settings, assets / settings.name)
        (mod / "probe_layout.py").write_text(PROBE, encoding="utf-8")
        probe = subprocess.run([sys.executable, "probe_layout.py"], cwd=mod, capture_output=True, timeout=120,
                               env=environment, check=False)
        expect(probe.returncode == 0 and Path(probe.stdout.decode("utf-8").strip()).parent == shared,
               "the public copy's layout: the shared folder found beside the mod's folder")
        for test in ("test_install_pak.py", "test_pak_recipe.py", "test_build_pak.py", "test_pak_overlaps.py"):
            ran = subprocess.run([sys.executable, test], cwd=mod, capture_output=True, timeout=120, env=environment,
                                 check=False)
            expect(ran.returncode == 0, f"the public copy's layout: {test} passes")


def test_missing_shared_folder():
    real = game_tools.MENU_ENTRIES_PLACES
    with tempfile.TemporaryDirectory() as folder:
        game_tools.MENU_ENTRIES_PLACES = (Path(folder) / "absent",)
        try:
            game_tools.menu_entries()
            expect(False, "without the shared menu file's folder, refused")
        except game_tools.MissingTool:
            pass
    game_tools.MENU_ENTRIES_PLACES = real


def test_this_copy():
    found = next((place for place in game_tools.MENU_ENTRIES_PLACES if (place / "menu_recipe.py").is_file()), None)
    expect(found is not None, "the shared menu file's folder found in this copy's layout")
    recipe, builder = game_tools.menu_entries()
    expect(Path(recipe.__file__).parent == found and hasattr(builder, "shared_files"),
           "this copy's shared file's two modules")


def test_mod_settings_pak():
    expect(game_tools.mod_settings_pak().endswith("_P.pak"), "Mod Settings' pak name found in this copy's layout")
    real = game_tools.MOD_SETTINGS_CONSTANTS
    with tempfile.TemporaryDirectory() as folder:
        game_tools.MOD_SETTINGS_CONSTANTS = (Path(folder) / "absent.json",)
        try:
            game_tools.mod_settings_pak()
            expect(False, "without Mod Settings' constants, refused")
        except game_tools.MissingTool:
            pass
    game_tools.MOD_SETTINGS_CONSTANTS = real


def test_known_games():
    games = game_tools.known_games()
    if (game_tools.TOOLS / "deploy_sdkmods.py").is_file():
        expect(games is not None and games[1] in games[0],
               "the game copies from deploy_sdkmods.py, its default among them")
    real = game_tools.TOOLS
    with tempfile.TemporaryDirectory() as folder:
        game_tools.TOOLS = Path(folder)
        expect(game_tools.known_games() is None, "without deploy_sdkmods.py, None, not a guess")
    game_tools.TOOLS = real


for test in (test_public_layout, test_missing_shared_folder, test_this_copy, test_mod_settings_pak, test_known_games):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
