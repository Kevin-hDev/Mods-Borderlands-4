# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of build_pak.py's own steps, without the game's paks nor repak: the page's files, a failing tool refused,
a missing tool refused. python test_build_pak.py"""

import sys
from pathlib import Path
from types import SimpleNamespace

import build_pak
import pak_recipe

C = pak_recipe.load_constants()
FAILURES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


def test_page_files():
    files = build_pak.page_files(C, "OakGame/Content/uiresources/logs_conflicts/js/logs_conflicts.js")
    script = files["OakGame/Content/uiresources/logs_conflicts/js/logs_conflicts.js"].decode("utf-8")
    expect(sorted(files) == sorted(["OakGame/Content/uiresources/logs_conflicts/js/logs_conflicts.js",
                                    C["pak"]["cssPath"]]), "the page's script and stylesheet, nothing else")
    expect(script == pak_recipe.page_script(C, pak_recipe.read_sources()), "the script as the recipe builds it")
    expect(files[C["pak"]["cssPath"]] == (pak_recipe.PAGE / pak_recipe.STYLESHEET).read_bytes(),
           "the stylesheet byte for byte")


def test_tool():
    tool = build_pak.Repak(SimpleNamespace(REPAK=Path(sys.executable), REPAK_TIMEOUT_S=30))
    try:
        tool.run(["-c", "raise SystemExit(3)"])
        expect(False, "a failing tool refused")
    except pak_recipe.RecipeError as error:
        expect("3" in str(error), "a failing tool refused, with its code")
    expect(tool.run(["-c", "print('listed')"]).strip() == b"listed", "a tool's output given back")
    try:
        build_pak.Repak(SimpleNamespace(REPAK=Path(sys.executable).parent / "absent.exe", REPAK_TIMEOUT_S=30))
        expect(False, "a missing repak refused")
    except pak_recipe.RecipeError:
        pass


for test in (test_page_files, test_tool):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
