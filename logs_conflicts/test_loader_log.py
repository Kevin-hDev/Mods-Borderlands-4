# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of loader_log.py on lines shaped as players' logs show them (releves/apex_movement/2026-10-18-touche-f10/,
docs/bug/save-editor/2026-10-16-niveau-130/). python test_loader_log.py"""

import sys

import package_path  # noqa: F401
from logs_conflicts import loader_log as l, protocol

FAILURES = []
LIMITS = protocol.load_constants()["conflicts"]
LOADER = "Win64/Plugins/../../../../sdk_mods/__main__.py"


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


def line(number, level, message, where=LOADER):
    return f"2026-10-18 10:03:35.391Z   1ad4   ~ {where}@{number} {level:>6}| {message}"


def log(*lines):
    return "\n".join(["date       time          thread    location@line    v|"] + list(lines)) + "\n"


def same(value):
    return value


FAILED = [line(347, "ERR", "Failed to import mod 'hud_editor'"),
          line(353, "ERR", "RuntimeError: HUD service is unavailable."),
          line(353, "ERR", ""),
          line(354, "ERR", '  File "C:\\Users\\Kevin\\sdk_mods\\hud_editor.sdkmod\\hud_editor\\__init__.py", line 43'),
          line(354, "ERR", '    raise RuntimeError("HUD service is unavailable.")')]
TWICE = [line(460, "WARN", "Found multiple versions of mod 'weather'. In order of priority:"),
         line(465, "WARN", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Borderlands 4\\sdk_mods\\weather"),
         line(465, "WARN", "C:\\Users\\Kevin\\Games\\Borderlands 4\\sdk_mods\\weather.sdkmod")]


def test_failed():
    found = l.parse(log(*FAILED), LIMITS, same)
    expect(found["failed"] == [{"name": "hud_editor", "reason": "import",
                                "items": ["RuntimeError: HUD service is unavailable."]}],
           "a mod that failed to load, with its error's last line, never the traceback and its paths")
    syntax = l.parse(log(line(347, "ERR", "Failed to import mod 'broken'"),
                         line(353, "ERR", '  File "C:\\Users\\Kevin\\broken\\__init__.py", line 3'),
                         line(353, "ERR", "    def ("),
                         line(353, "ERR", "        ^"),
                         line(353, "ERR", "SyntaxError: invalid syntax"),
                         line(353, "ERR", ""),
                         line(354, "ERR", "  File ...")), LIMITS, same)
    expect(syntax["failed"][0]["items"] == ["SyntaxError: invalid syntax"],
           "an error written over several lines gives its last one")
    bare = l.parse(log(line(347, "ERR", "Failed to import mod 'bare'"), line(460, "WARN", "x")), LIMITS, same)
    expect(bare["failed"] == [{"name": "bare", "reason": "import", "items": []}], "no error line, no detail")
    moved = l.parse(log(line(350, "ERR", "Failed to import mod 'later_sdk'"), line(356, "ERR", "ValueError: x")),
                    LIMITS, same)
    expect(moved["failed"][0]["items"] == ["ValueError: x"], "told by their text, whatever the loader's line numbers")
    spaced = l.parse(log(line(347, "ERR", "Failed to import mod 'spaced'   ")), LIMITS, same)
    expect([entry["name"] for entry in spaced["failed"]] == ["spaced"], "spaces after a message are not part of it")
    warned = l.parse(log(line(347, "WARN", "Failed to import mod 'x'")), LIMITS, same)
    expect(warned["failed"] == [], "a failure is an error line")


def test_refused():
    found = l.parse(log(
        line(232, "ERR", "'Apex Movement 1.1.7 317' is not a valid python module - have you extracted the right "
                         "folder?"),
        line(280, "ERR", "'MyMod (1).sdkmod' does not appear to be valid, and has been ignored. Is it supposed to be "
                         "called 'MyMod.sdkmod'?"),
        line(280, "ERR", "'Odd.sdkmod' does not appear to be valid, and has been ignored."),
        line(218, "ERR", "'Nested' appears to be double nested, which may prevent it from being it from being "
                         "loaded.")),
        LIMITS, same)
    expect([(entry["reason"], entry["name"], entry["items"]) for entry in found["failed"]] ==
           [("folder", "Apex Movement 1.1.7 317", []), ("file", "MyMod (1).sdkmod", ["MyMod.sdkmod"]),
            ("file", "Odd.sdkmod", []), ("nested", "Nested", [])],
           "folder names refused, files ignored with the name the SDK expects, double nested folders")
    warned = l.parse(log(line(232, "WARN", "'Folder.v2' is not a valid python module")), LIMITS, same)
    expect(warned["failed"] == [], "the refusals are errors only")


def test_twice():
    found = l.parse(log(*TWICE), LIMITS, same)
    expect(found["twice"] == [{"name": "weather", "items": [{"copy": "weather", "folder": True},
                                                             {"copy": "weather.sdkmod", "folder": False}],
                               "more": 0}],
           "each copy by its last part only, in the loader's order, folders told apart")
    expect(l.parse(log(line(460, "ERR", TWICE[0].split("| ")[1])), LIMITS, same)["twice"] == [],
           "the duplicates' warning is a warning")


def test_others_and_repeats():
    mod_line = line(16, "ERR", "Failed to import mod 'fake'", where="sdk_mods\\other.sdkmod\\other\\__main__.py")
    found = l.parse(log(mod_line, *FAILED, *TWICE, *FAILED, *TWICE), LIMITS, same)
    expect([entry["name"] for entry in found["failed"]] == ["hud_editor"] and len(found["twice"]) == 1,
           "a mod's own line is not the loader's; lines written twice by the SDK give one entry each")
    expect(not found["cut"], "nothing cut")
    quoted = line(16, "ERR", f"copied: ~ {LOADER}@347   ERR| Failed to import mod 'quoted'",
                  where="sdk_mods\\other.sdkmod\\other\\__main__.py")
    expect(l.parse(log(quoted), LIMITS, same)["failed"] == [],
           "a mod's message quoting a loader line is not one: the loader's file comes before the line's first |")
    most = LIMITS["maxLoaderMessage"]
    name = "x" * (most - len("Failed to import mod ''"))
    kept = l.parse(log(line(347, "ERR", f"Failed to import mod '{name}'")), LIMITS, same)["failed"]
    skipped = l.parse(log(line(347, "ERR", f"Failed to import mod '{name}x'")), LIMITS, same)["failed"]
    expect(len(kept) == 1 and skipped == [],
           "a message within the bound is read; a longer one is no loader message, and is skipped unread")


def test_masking_and_bounds():
    masked = l.parse(log(line(347, "ERR", "Failed to import mod 'x'"),
                         line(353, "ERR", "FileNotFoundError: C:\\Users\\Kevin\\a.json")), LIMITS,
                     lambda value: value.replace("Kevin", "<user>"))
    expect(masked["failed"][0]["items"] == ["FileNotFoundError: C:\\Users\\<user>\\a.json"], "errors masked")
    small = dict(LIMITS, maxName=4, maxError=10, maxItems=1, maxMods=1)
    found = l.parse(log(*FAILED, line(347, "ERR", "Failed to import mod 'second'"), *TWICE), small, same)
    expect(found["failed"] == [{"name": "hud_", "reason": "import", "items": ["RuntimeErr"]}],
           "names and errors cut to their bounds")
    expect(found["twice"][0]["items"] == [{"copy": "weat", "folder": True}] and found["twice"][0]["more"] == 1,
           "copies bounded, the rest counted")
    expect(found["cut"], "mods past the bound: the list says it is cut")
    expect(not l.parse(log(*FAILED), small, same)["cut"], "exactly the bound is not cut")
    expect(not l.parse(log(*FAILED, *FAILED), small, same)["cut"],
           "the SDK's second copy of its lines does not cut a list at its bound")


for test in (test_failed, test_refused, test_twice, test_others_and_repeats, test_masking_and_bounds):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
