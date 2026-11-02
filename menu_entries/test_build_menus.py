# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of build_menus.py's own steps, without the game's paks: a menu patched with its byte order mark kept as
found, the shared files of both menus and the shared script, the workshop's pak tools missing refused.
python test_build_menus.py"""

import sys
import tempfile
from pathlib import Path

import build_menus
import menu_recipe

FAILURES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


C = menu_recipe.load_constants()


def menu_html(menu):
    return f"<html>\n{menu['entryNeedle']}\n<body>\n{menu['scriptNeedle']}\n</body></html>\n"


def test_byte_order_mark():
    menu = C["menus"][0]
    for bom in (b"", b"\xef\xbb\xbf"):
        patched = build_menus.patched(bom + menu_html(menu).encode("utf-8"), menu, C)
        text = patched[len(bom):].decode("utf-8")
        expect(patched.startswith(bom) and not text.startswith("\ufeff"),
               f"byte order mark kept as found ({len(bom)} bytes), never doubled")
        expect(text.count("<logs-conflicts-hook") == 1 and text.index("<logs-conflicts-hook")
               < text.index(menu["entryNeedle"]), "each entry once, before the mark")


def test_shared_files():
    real = build_menus.newest_menus
    raws = {menu["path"]: menu_html(menu).encode("utf-8") for menu in C["menus"]}
    sources = {path: "pakchunk0-Windows_0_P.pak" for path in raws}
    build_menus.newest_menus = lambda constants, work: (sources, raws)
    try:
        files, told, constants = build_menus.shared_files(Path("unused"))
    finally:
        build_menus.newest_menus = real
    expect(sorted(files) == sorted([*raws, C["scriptPath"]]), "both menus and the shared script, nothing else")
    expect(files[C["scriptPath"]] == menu_recipe.SCRIPT.read_bytes(), "the shared script byte for byte")
    expect(all(files[path] == build_menus.patched(raws[path], menu, C) for menu in C["menus"]
               for path in [menu["path"]]), "each menu patched by its own recipe")
    expect(told == sources and constants == C, "the menus' game paks and the constants given back")


def test_tools():
    real = build_menus.TOOLS_FILE
    with tempfile.TemporaryDirectory() as folder:
        build_menus.TOOLS_FILE = Path(folder) / "pak_tools.py"
        try:
            build_menus.pak_tools()
            expect(False, "without the workshop's pak_tools.py, refused")
        except menu_recipe.RecipeError:
            pass
    build_menus.TOOLS_FILE = real
    if real.is_file():
        tools = build_menus.pak_tools()
        expect(tools.REPAK_TIMEOUT_S > 0 and tools.GAME_FILES_TIMEOUT_S > 0, "each tool has a bound")
    else:
        print("NOTE: pak_tools.py absent (public copy): its bounds not checked")


for test in (test_byte_order_mark, test_shared_files, test_tools):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
