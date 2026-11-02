# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of conflicts.py: the sections in order of severity under one bound, and what each source adds.
python test_conflicts.py"""

import copy
import sys
import tempfile
from pathlib import Path

import package_path  # noqa: F401
from logs_conflicts import conflicts as c, log_file, masking, protocol

FAILURES = []
C = protocol.load_constants()
TEMP = tempfile.TemporaryDirectory()
LOADER = "2026-10-18 10:03:35.391Z   1ad4   ~ Win64/Plugins/../../../../sdk_mods/__main__.py@"


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


class Key:
    def __init__(self, key):
        self.key, self.is_enabled, self.display_name, self.identifier, self.is_rebindable = key, True, None, key, True


class Command:
    def __init__(self, cmd):
        self.cmd = cmd


class Mod:
    def __init__(self, name, keys=(), commands=(), settings=None):
        self.name, self.is_enabled = name, True
        self.keybinds = [Key(key) for key in keys]
        self.commands = [Command(text) for text in commands]
        self.settings_file = Path(f"C:/sdk_mods/settings/{settings}") if settings else None


class Paks:
    def __init__(self, found):
        self.found = found

    def find(self):
        return self.found


def paks(entries=(), missing=False, fresh=True, failures=()):
    return Paks({"entries": list(entries), "containers": 3, "unreadable": len(failures), "missing": missing,
                 "failures": list(failures), "fresh": fresh})


def entry(name, items=1):
    return {"name": name, "items": [f"line {index}" for index in range(items)], "more": 0}


def sections(**given):
    return {name: list(given.get(name, [])) for name in C["conflicts"]["sections"]}


def test_fit():
    kept, cut = c.fit(sections(failed=[entry("a")], keys=[entry("k")]), C)
    expect(kept["failed"][0]["name"] == "a" and kept["keys"][0]["name"] == "k" and not cut, "everything fits")
    small = copy.deepcopy(C)
    small["conflicts"]["maxListedLines"] = 7
    kept, cut = c.fit(sections(failed=[entry("a", 2), entry("b", 2)], files=[entry("f", 1)]), small)
    expect([e["name"] for e in kept["failed"]] == ["a"] and kept["files"] == [] and cut,
           "an entry fits whole or not at all, and the first that does not stops the list, later sections too")
    expect(c.entry_lines(entry("x", 3)) == 5 and c.entry_lines(dict(entry("x", 3), more=2)) == 6,
           "an entry's lines: title, what it is, its items and the line of those left out")
    small["conflicts"]["maxListedLines"] = 4
    kept, cut = c.fit(sections(failed=[entry("a", 2)]), small)
    expect(kept["failed"] and not cut, "exactly the bound of lines fits")
    one = entry("a", 2)
    small = copy.deepcopy(C)
    small["http"]["maxConflictsResponseBytes"] = small["conflicts"]["answerMarginBytes"] + c.encoded_size(one)
    kept, cut = c.fit(sections(twice=[one], keys=[entry("k")]), small)
    expect(kept["twice"] == [one] and kept["keys"] == [] and cut, "the bound of bytes, shared by all sections")
    wide = entry("名" * 30)
    expect(c.encoded_size(wide) > 30 * 6, "a character outside ASCII costs its escape in the answer")


def parts(log_text=None, mods=(), found_paks=None, modules=()):
    path = None
    if log_text is not None:
        path = Path(TEMP.name) / "unrealsdk.log"
        path.write_text(log_text, encoding="utf-8")
    return {"mods": lambda: list(mods), "modules": lambda: list(modules), "modClass": Mod,
            "paks": found_paks or paks(), "log_file": log_file, "log_path": path, "masking": masking,
            "mask_patterns": masking.home_patterns(["C:\\Users\\Kevin"])}


def clock():
    ticks = iter(range(0, 100))
    return lambda: next(ticks) / 1000


def test_gather():
    text = (f"{LOADER}347   ERR| Failed to import mod 'broken'\n"
            f"{LOADER}353   ERR| FileNotFoundError: C:\\Users\\Kevin\\x.json\n"
            f"{LOADER}460  WARN| Found multiple versions of mod 'weather'. In order of priority:\n"
            f"{LOADER}465  WARN| C:\\Users\\Kevin\\sdk_mods\\weather\n"
            f"{LOADER}465  WARN| C:\\Users\\Kevin\\sdk_mods\\weather.sdkmod\n")
    odd = Mod("Odd")
    odd.commands = [object()]
    mods = [Mod("A", keys=["F5"], commands=["spawn"], settings="a.json"),
            Mod("B", keys=["F5"], commands=["SPAWN"], settings="A.json"), object(), odd]
    files = {"containers": ["C:/Users/Kevin/x_P.pak", "y.pak"], "moreContainers": 0, "winner": "C:/Users/Kevin/x_P.pak",
             "count": 1, "identical": 0, "items": ["C:/Users/Kevin/f"], "more": 0}
    answer, trace = c.gather(parts(text, mods, paks([files], failures=[("bad_P.pak", "encrypted index")])), C,
                             clock())
    found = answer["sections"]
    expect(found["failed"][0]["items"] == ["FileNotFoundError: C:\\Users\\<user>\\x.json"],
           "a mod that did not load, its error masked like the log")
    expect([item["copy"] for item in found["twice"][0]["items"]] == ["weather", "weather.sdkmod"],
           "a mod installed twice")
    expect(found["files"] == [dict(files, containers=["C:/Users/<user>/x_P.pak", "y.pak"],
                                   winner="C:/Users/<user>/x_P.pak", items=["C:/Users/<user>/f"])]
           and files["items"] == ["C:/Users/Kevin/f"],
           "files in common, the player's name masked in a copy, the kept scan left as it is")
    expect(found["commands"][0]["name"] == "spawn" and found["settings"][0]["name"] == "a.json"
           and found["keys"][0]["name"] == "F5", "commands, settings and keys, each in its section")
    expect(answer["checked"] == {"mods": 3, "keys": 2, "commands": 2, "containers": 3}
           and answer["unreadable"] == {"mods": 2, "containers": 1},
           "what was looked at, and what could not be read, a mod counted once whatever part of it failed")
    expect(answer["log"] == "read" and answer["paks"] == "read" and not answer["cut"] and not answer["partial"],
           "both sources read, every list whole")
    expect(trace["failures"] == [("bad_P.pak", "encrypted index")] and trace["modsMs"] == 1
           and trace["logMs"] == 1 and trace["paksMs"] == 1, "the trace names the unreadable container and the times")
    expect("failures" not in answer and "fresh" not in answer, "the trace never goes to the page")


def test_shown_files():
    """Names and paths masked, then cut: cut first, a home path could lose the start that tells it."""
    entry = {"containers": ["C:/Users/Kevin/abc_P.pak", "b" * 100 + "_P.pak"], "moreContainers": 0,
             "winner": "b" * 100 + "_P.pak", "count": 1, "identical": 0, "items": ["C:/Users/Kevin/abc.js"], "more": 0}
    shown = c.shown_files([entry], c.masker(parts(), C), dict(C["conflicts"], maxName=18, maxPath=15))
    expect(shown[0]["items"] == ["...user>/abc.js"]
           and shown[0]["containers"] == ["...user>/abc_P.pak", "...bbbbbbbbb_P.pak"]
           and shown[0]["winner"] == "...bbbbbbbbb_P.pak", f"masked, then cut from their start ({shown})")
    expect(entry["items"] == ["C:/Users/Kevin/abc.js"] and c.tail("a_P.pak", 7) == "a_P.pak",
           "the kept scan left as it is; a text within its bound kept whole")


def test_missing_sources():
    answer, trace = c.gather(parts(None, [], paks(missing=True, fresh=False, failures=[("old_P.pak", "x")])), C,
                             clock())
    expect(answer["log"] == "log_missing" and answer["sections"]["failed"] == [] and answer["sections"]["twice"] == []
           and answer["paks"] == "missing", "no log, no Paks folder: said, never guessed")
    expect(trace["failures"] == [], "failures of a listing already seen are not written again")
    cut_log = (f"{LOADER}347   ERR| Failed to import mod 'a'\n") + "".join(
        f"{LOADER}347   ERR| Failed to import mod 'm{index}'\n" for index in range(C["conflicts"]["maxMods"]))
    roomy = copy.deepcopy(C)
    roomy["conflicts"]["maxListedLines"] = 10 ** 6
    roomy["http"]["maxConflictsResponseBytes"] = 10 ** 7
    answer, _trace = c.gather(parts(cut_log), roomy, clock())
    expect(answer["cut"] and len(answer["sections"]["failed"]) == C["conflicts"]["maxMods"],
           "a log with more failed mods than the bound: the list says it is cut, though every entry kept fits")
    many = [Mod(f"M{index}") for index in range(C["conflicts"]["maxMods"] + 1)]
    answer, _trace = c.gather(parts("", many), C, clock())
    expect(answer["partial"] and not answer["cut"] and answer["log"] == "read",
           "more mods than the bound: partial, not cut, nothing found being left out")
    chatty = [Mod("C", commands=[f"c{index}" for index in range(C["conflicts"]["maxCommandsPerMod"] + 1)])]
    answer, _trace = c.gather(parts("", chatty), C, clock())
    expect(answer["partial"], "a mod with more commands than the bound: partial")
    keyed = [Mod("K", keys=[f"F{index}" for index in range(C["conflicts"]["maxKeysPerMod"] + 1)])]
    answer, _trace = c.gather(parts("", keyed), C, clock())
    expect(answer["partial"], "a mod with more keys than the bound: partial")


for test in (test_fit, test_gather, test_shown_files, test_missing_sources):
    test()
TEMP.cleanup()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
