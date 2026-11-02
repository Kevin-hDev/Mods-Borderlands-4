# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of copy_texts.py: what COPY puts in the clipboard, in English. python test_copy_texts.py"""

import sys

import package_path  # noqa: F401
from logs_conflicts import copy_texts as t, protocol

FAILURES = []
C = protocol.load_constants()
EN = C["texts"]["en"]["states"]
HEADER = "Logs & Conflicts 1.0.0 | conflicts between mods | checked at 14:32:05"
CHECKED = "3 enabled mods, 4 keys, 5 console commands and 6 mod package files (.pak, .utoc) checked."


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


def shown(**given):
    sections = {name: [] for name in C["conflicts"]["sections"]}
    sections.update(given.pop("sections", {}))
    return {"sections": sections, "checked": {"mods": 3, "keys": 4, "commands": 5, "containers": 6},
            "unreadable": {"mods": 0, "containers": 0}, "log": "read", "paks": "read", "partial": False, "cut": False,
            "readAt": "14:32:05", **given}


def test_log():
    whole = t.log_text({"readAt": "1", "size": 4, "cut": 0, "head": "ab\n", "tail": ""}, C, "1.0.0", "unrealsdk.log")
    expect(whole == "Logs & Conflicts 1.0.0 | unrealsdk.log | read at 1 | 4 bytes\nab\n", "a whole log")
    cut = t.log_text({"readAt": "1", "size": 9, "cut": 5, "head": "a\n", "tail": "z\n"}, C, "1.0.0", "x.log")
    expect(cut.endswith(" | 5 bytes cut in the middle\na\n\n[... 5 bytes cut by Logs & Conflicts ...]\nz\n"),
           "a cut log says where")


def test_sections():
    text = t.conflicts_text(shown(sections={
        "failed": [{"name": "hud_editor", "reason": "import", "items": ["RuntimeError: no"]},
                   {"name": "MyMod (1).sdkmod", "reason": "file", "items": ["MyMod.sdkmod"]},
                   {"name": "Odd.v2", "reason": "folder", "items": []},
                   {"name": "later", "reason": "unknown", "items": []}],
        "twice": [{"name": "weather", "items": [{"copy": "weather", "folder": True},
                                                 {"copy": "weather.sdkmod", "folder": False}], "more": 0}],
        "files": [{"containers": ["b_5_P.pak", "a_P.pak"], "moreContainers": 0, "winner": "b_5_P.pak", "count": 3,
                   "identical": 1, "items": ["x.js", "y.js"], "more": 1},
                  {"containers": ["c_P.pak", "d_P.pak"], "moreContainers": 2, "winner": "c_P.pak", "count": 1,
                   "identical": 0, "items": ["z.js"], "more": 0}],
        "commands": [{"name": "spawn", "items": ["Arena", "Spawner"], "more": 0}],
        "settings": [{"name": "w.json", "items": [{"mod": "New", "dropped": False}, {"mod": "Old", "dropped": True}],
                      "more": 0}],
        "keys": [{"name": "F5", "items": [{"mod": "A", "name": "Dash", "fixed": False},
                                          {"mod": "B", "name": "View", "fixed": True}], "more": 2}]}), C, "1.0.0")
    expect(text.split("\n") == [
        HEADER,
        "10 conflict(s) found between your mods.",
        CHECKED,
        EN["failedTitle"],
        "hud_editor: Error while loading. | Error: RuntimeError: no",
        "MyMod (1).sdkmod: Not a valid .sdkmod file: the SDK ignored it. | Its name should probably be MyMod.sdkmod.",
        "Odd.v2: " + EN["reasonFolder"],
        "later: ",
        EN["twiceTitle"],
        "weather: Loaded: weather (folder) | Ignored: weather.sdkmod",
        EN["filesTitle"],
        "b_5_P.pak, a_P.pak: b_5_P.pak goes first: 3 file(s) in common, 1 of them identical, with no effect. | x.js "
        "| y.js | ... and 1 more",
        "c_P.pak, d_P.pak ... and 2 more: c_P.pak goes first: 1 file(s) in common. | z.js",
        EN["commandsTitle"],
        "spawn: Arena | Spawner",
        EN["settingsTitle"],
        "w.json: New | Old (removed from the mod list)",
        EN["keysTitle"],
        'F5: A, action "Dash" | B, action "View" (cannot be changed) | ... and 2 more',
        ""], "the page's English lines, a title per section with conflicts, one line per conflict, the SDK's key names")


def test_status():
    text = t.conflicts_text(shown(log="log_missing", paks="missing", partial=True, cut=True,
                                  unreadable={"mods": 2, "containers": 1}), C, "1.0.0")
    expect(text.split("\n") == [
        HEADER, EN["conflictsNone"], CHECKED, EN["logNotRead"], EN["paksMissing"], "2 mod(s) could not be read.",
        "1 mod package file(s) or folder(s) could not be read.",
        "Only the first 128 mods, and the first 64 keys and 64 console commands of each, were checked.",
        EN["listCut"], ""], "what could not be looked at, said as the page says it, in its order")
    expect(t.conflicts_text(shown(), C, "1.0.0").split("\n") == [HEADER, EN["conflictsNone"], CHECKED, ""],
           "nothing found, everything read: the two first lines only")
    expect(t.bounds(C) == {"mods": C["conflicts"]["maxMods"], "keys": C["conflicts"]["maxKeysPerMod"],
                           "commands": C["conflicts"]["maxCommandsPerMod"]}, "the bounds the partial line names")


for test in (test_log, test_sections, test_status):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
