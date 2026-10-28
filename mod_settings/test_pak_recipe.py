# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of pak_recipe.py. python test_pak_recipe.py"""

import json
import sys
import tempfile
from pathlib import Path

import pak_recipe as r

C = r.load_constants()
P = C["pak"]
PAUSE, MAIN = P["menus"]
FAILURES = []

PAUSE_HTML = ("<widget-menu-pause>\n<div class=\"list\">\n"
              "<div name=\"Options Button\"></div><!-- Shift -->\n<div name=\"Shift Button\"></div>\n"
              "</div>\n</widget-menu-pause>\n"
              "<script src=\"coui://uiresources/menu_pause/js/menu_pause.js\"></script>\n"
              "<script src=\"coui://uiresources/menu_pause/data/menu_pause.data\"></script>\n")
MAIN_HTML = ("<widget-menu-main>\n<div name=\"Options Button\"></div><!-- Shift -->\n"
             "<div name=\"Shift Button\"></div>\n</widget-menu-main>\n"
             "<link href=\"coui://uiresources/menu_main/css/menu_main.css\" />\n"
             "<script src=\"coui://uiresources/menu_main/js/menu_main.js\"></script>\n"
             "<script src=\"coui://uiresources/menu_main/data/menu_main.data\"></script>\n")
ENTRY = "<!-- Mod Settings -->\n<div name=\"Mod Settings Button\"></div>\n"
SCRIPT_URL = "coui://uiresources/mod_settings/js/mod_settings.js"


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


def raises(action):
    try:
        action()
    except r.RecipeError:
        return True
    return False


# Newest copies, as game_files reports them (JSON, then one RESULTAT line)
def report(files, result="RESULTAT: 2 fichier(s) ecrit(s)"):
    return json.dumps({"unreadable": [], "files": files}, indent=2) + "\n" + result + "\n"


WANTED = [PAUSE["path"], MAIN["path"]]
pause_found = {"path": PAUSE["path"], "latest": "pakchunk0-Windows_16_P.pak", "sha256": "AB", "copies": []}
main_found = {"path": MAIN["path"], "latest": "pakchunk0-Windows_0_P.pak", "sha256": "CD", "copies": []}
check("sources read from the report", r.newest_sources(report([pause_found, main_found]), WANTED) ==
      {PAUSE["path"]: "pakchunk0-Windows_16_P.pak", MAIN["path"]: "pakchunk0-Windows_0_P.pak"})
check("one menu missing refused", raises(lambda: r.newest_sources(report([pause_found]), WANTED)))
check("refused path refused", raises(lambda: r.newest_sources(
    report([dict(pause_found, refused="unreadable archives above"), main_found]), WANTED)))
check("odd archive name refused", raises(lambda: r.newest_sources(
    report([dict(pause_found, latest="x.pak"), main_found]), WANTED)))
check("missing result line refused", raises(lambda: r.newest_sources(report([pause_found, main_found], ""), WANTED)))
check("broken json refused", raises(lambda: r.newest_sources("{oops\nRESULTAT: x", WANTED)))

# Addresses derived from the pak paths: one authority
check("script address", r.coui_url(P["scriptPath"]) == SCRIPT_URL)
check("path outside the content folder refused", raises(lambda: r.coui_url("Other/uiresources/x.js")))

# Insertion, in each menu
for name, html, menu, after in (("pause", PAUSE_HTML, PAUSE, "menu_pause.data"), ("main", MAIN_HTML, MAIN,
                                                                                    "menu_main.data")):
    patched = r.patch_menu(html, ENTRY, menu, C)
    check(f"{name}: entry between options and shift",
          patched.index("Options Button") < patched.index("Mod Settings Button") < patched.index("<!-- Shift -->"))
    check(f"{name}: script right after the menu's script",
          patched.index(menu["scriptNeedle"]) < patched.index(SCRIPT_URL) < patched.index(after))
    check(f"{name}: original kept",
          patched.replace(ENTRY, "").replace("\n<script src=\"" + SCRIPT_URL + "\"></script>", "") == html)
    crlf = r.patch_menu(html.replace("\n", "\r\n"), ENTRY, menu, C)
    check(f"{name}: crlf file stays crlf", "\n" not in crlf.replace("\r\n", ""))
    check(f"{name}: needle missing refused", raises(lambda: r.patch_menu(html.replace("<!-- Shift -->", ""), ENTRY,
                                                                         menu, C)))
    check(f"{name}: needle doubled refused", raises(lambda: r.patch_menu(html + "<!-- Shift -->", ENTRY, menu, C)))
    check(f"{name}: script needle missing refused",
          raises(lambda: r.patch_menu(html.replace(menu["scriptNeedle"], "<script></script>"), ENTRY, menu, C)))

# Entry files: each names its menu for the page
for menu, host in ((PAUSE, "pause"), (MAIN, "main")):
    text = (r.PAGE / menu["entry"]).read_text(encoding="utf-8")
    check(f"{host} entry names its menu", f'<mod-settings-hook host="{host}"' in text)
    check(f"{host} menu known to the page", host in C["page"]["hosts"])

# Page script: one config first, then the sources in order
sources = {name: f"// {name}" for name in r.SOURCES}
script = r.page_script(C, sources)
first, rest = script.split("\n", 1)
config = json.loads(first[len("window.ModSettingsConfig="):-1])
check("config first", first.startswith("window.ModSettingsConfig="))
check("config carries the shared lists", config["events"] == C["events"] and config["catalog"] == C["catalog"])
check("config gives the page its stylesheet", config["page"]["ownStylesheet"] == r.coui_url(P["cssPath"]))
check("config leaves the pak recipe out", "pak" not in config)
check("sources in order", rest == "\n".join(f"// {name}" for name in r.SOURCES))
check("every source exists", all((r.PAGE / name).is_file() for name in r.SOURCES + (r.STYLESHEET,)))

# Constants guard: the mod's own loader, then the pak's name
mod_loader = r.protocol.load_constants
r.protocol.load_constants = lambda: dict(C, pak=dict(P, name="mod-settings.pak"))
check("pak without _999_P refused", raises(r.load_constants))
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "c.json"
    path.write_text(json.dumps(dict(C, version=2)), encoding="utf-8")
    r.protocol.load_constants = lambda: mod_loader(path)
    check("unknown constants version refused by the one loader", raises(r.load_constants))
r.protocol.load_constants = mod_loader

print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
sys.exit(1 if FAILURES else 0)
