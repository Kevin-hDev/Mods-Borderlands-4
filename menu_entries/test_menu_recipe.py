# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of menu_recipe.py on a menu shaped like the game's pause menu. python test_menu_recipe.py"""

import copy
import json
import sys

import menu_recipe as r

FAILURES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


def refused(action, label):
    try:
        action()
        expect(False, f"refused: {label}")
    except r.RecipeError:
        pass


C = r.load_constants()
PAUSE = C["menus"][0]
BASE = ("<div>\n<div>Options</div>\n<!-- Shift -->\n<div>Quit</div>\n</div>\n" + PAUSE["scriptNeedle"] + "\n"
        "</body>\n")
ENTRIES = [(r.ENTRIES / name).read_text(encoding="utf-8") for name in PAUSE["entries"]]


def test_patch():
    patched = r.patch_menu(BASE, PAUSE, ENTRIES, C)
    ms, lc, shift = (patched.index("<!-- Mod Settings -->"), patched.index("<!-- Logs & Conflicts -->"),
                     patched.index("<!-- Shift -->"))
    expect(ms < lc < shift, "both entries before the mark, Mod Settings first")
    expect(patched.count('style="display: none;">\n') == 2, "both entries hidden in the menu file")
    expect(patched.count(f'data-menu-entries="{C["version"]}"') == 2 and C["versionToken"] not in patched,
           "each entry names the shared file's version")
    order = [patched.index(name) for name in ("mod_settings.js", "logs_conflicts.js", "menu_entries.js")]
    expect(patched.index(PAUSE["scriptNeedle"]) < order[0] < order[1] < order[2],
           "scripts after the menu's own: Mod Settings, Logs & Conflicts, the shared one")
    expect('src="coui://uiresources/menu_entries/js/menu_entries.js"' in patched, "game addresses")
    crlf = r.patch_menu(BASE.replace("\n", "\r\n"), PAUSE, ENTRIES, C)
    expect("\n" not in crlf.replace("\r\n", ""), "a CRLF menu stays CRLF")
    refused(lambda: r.patch_menu(BASE.replace("<!-- Shift -->", ""), PAUSE, ENTRIES, C), "mark missing")
    refused(lambda: r.patch_menu(BASE + "<!-- Shift -->", PAUSE, ENTRIES, C), "mark twice")
    refused(lambda: r.patch_menu(BASE.replace(PAUSE["scriptNeedle"], ""), PAUSE, ENTRIES, C), "menu script missing")
    refused(lambda: r.patch_menu(BASE, PAUSE, [ENTRIES[0].replace(C["versionToken"], "1")], C), "entry without version")


def test_files_and_names():
    for menu in C["menus"]:
        texts = [(r.ENTRIES / name).read_text(encoding="utf-8") for name in menu["entries"]]
        host = "pause" if "pause" in menu["path"] else "main"
        expect(all(f'host="{host}"' in text for text in texts), f"{host} entries name their menu")
        # MODS is shown by the shared file's hook: without it, MODS stays hidden (trial 1, 1 November 2026).
        shared = [text for text in texts if "<mod-settings-hook" in text]
        expect(len(shared) == 1 and '<menu-entries-hook mod="mod_settings"' in shared[0],
               f"{host}: MODS carries the shared file's hook")
    expect(r.pak_number(C) == 1000 and r.pak_name("logs-conflicts", C) == "logs-conflicts_1000_P.pak",
           "pak number follows the shared file's version")
    later = copy.deepcopy(C)
    later["version"] = 2
    expect(r.pak_number(later) == 1001, "a newer shared file gets a higher number")
    refused(lambda: r.coui_url("Other/file.js"), "address outside the content folder")
    expect(r.script_path("logs_conflicts", C).endswith("logs_conflicts/js/logs_conflicts.js"), "a mod's script path")
    refused(lambda: r.script_path("other_mod", C), "a mod the shared file does not load")


def test_newest_sources():
    wanted = [menu["path"] for menu in C["menus"]]
    report = json.dumps({"files": [{"path": wanted[0], "latest": "pakchunk0-Windows_7_P.pak"},
                                   {"path": wanted[1], "latest": "pakchunk0-Windows_0_P.pak"}]}) + "\nRESULTAT: OK"
    expect(r.newest_sources(report, wanted) == {wanted[0]: "pakchunk0-Windows_7_P.pak",
                                                 wanted[1]: "pakchunk0-Windows_0_P.pak"}, "newest copies read")
    refused(lambda: r.newest_sources(report.replace("RESULTAT: OK", ""), wanted), "report without its last line")
    refused(lambda: r.newest_sources(report.replace("_7_P", "_7_X"), wanted), "copy from another kind of pak")


for test in (test_patch, test_files_and_names, test_newest_sources):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
