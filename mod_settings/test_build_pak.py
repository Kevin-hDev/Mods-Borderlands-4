# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of build_pak.py's own steps, without the game's paks nor the outside tools: a menu patched with its byte
order mark kept, the page's one script, a failing tool refused. python test_build_pak.py"""

import sys

import build_pak
import pak_recipe

C = pak_recipe.load_constants()
FAILURES = []


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


menu = C["pak"]["menus"][0]
html = f"<html>{menu['entryNeedle']}<body>{menu['scriptNeedle']}</body></html>"
for bom in (b"", b"\xef\xbb\xbf"):
    patched = build_pak.patched_html(bom + html.encode("utf-8"), menu, C)
    text = patched[len(bom):].decode("utf-8")
    check(f"byte order mark kept as found ({len(bom)} bytes)", patched.startswith(bom)
          and not text.startswith("﻿"))
    check("entry inserted before its needle, once", text.count("<mod-settings-hook") == 1
          and text.index("<mod-settings-hook") < text.index(menu["entryNeedle"]))
    check("our script after the menu's", text.index(pak_recipe.coui_url(C["pak"]["scriptPath"]))
          > text.index(menu["scriptNeedle"]))

script = build_pak.page_script(C).decode("utf-8")
check("one script: the config first, then every source", script.startswith("window.ModSettingsConfig=")
      and all((pak_recipe.PAGE / name).read_text(encoding="utf-8") in script for name in pak_recipe.SOURCES))

try:
    build_pak.run([sys.executable, "-c", "raise SystemExit(3)"])
    check("a failing tool refused", False)
except pak_recipe.RecipeError:
    check("a failing tool refused", True)
check("a tool's output returned", build_pak.run([sys.executable, "-c", "print('listed')"]).strip() == b"listed")

print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
sys.exit(1 if FAILURES else 0)
