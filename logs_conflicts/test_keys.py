# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of keys.py with mods shaped like mods_base's. python test_keys.py"""

import copy
import sys

import package_path  # noqa: F401
from logs_conflicts import keys as c, protocol

FAILURES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


LIMITS = protocol.load_constants()["conflicts"]


class Key:
    def __init__(self, key, identifier="Bind", enabled=True, display_name=None, rebindable=True):
        self.key, self.identifier, self.is_enabled = key, identifier, enabled
        self.display_name, self.is_rebindable = display_name, rebindable


class Mod:
    def __init__(self, name, keybinds, enabled=True):
        self.name, self.keybinds, self.is_enabled = name, keybinds, enabled


class Tricky(Mod):
    """A mod whose key list runs code when read: must be skipped without running it."""
    ran = []

    @property
    def keybinds(self):
        Tricky.ran.append(True)
        return []

    @keybinds.setter
    def keybinds(self, _value):
        pass


def test_found():
    mods = [Mod("Apex Movement", [Key("F5", "Dash", display_name="Dash"), Key("G", "Grapple")]),
            Mod("Camera", [Key("f5", "Toggle view"), Key("V", "Zoom", rebindable=False)]),
            Mod("Weather", [Key("V", "Rain", rebindable=None)]),
            Mod("Same author", [Key("H", "Press"), Key("H", "Release")])]
    found = c.find(mods, LIMITS)
    keys = {entry["name"].lower(): entry for entry in found["entries"]}
    expect(sorted(keys) == ["f5", "v"], f"two keys in conflict ({sorted(keys)})")
    expect([use["mod"] for use in keys["f5"]["items"]] == ["Apex Movement", "Camera"], "F5 and f5 are the same key")
    expect(keys["v"]["items"][0] == {"mod": "Camera", "name": "Zoom", "fixed": True}
           and keys["v"]["items"][1]["fixed"] is False, "a key that cannot change is told, and only one said so")
    expect(keys["f5"]["items"][0]["name"] == "Dash", "the key's shown name first")
    expect("h" not in keys, "one mod twice on a key is no conflict")
    expect(all(entry["more"] == 0 for entry in found["entries"]), "nothing left out of a short entry")
    expect(found["mods"] == 4 and found["keys"] == 7 and found["unreadable"] == set() and not found["partial"],
           "counts")


def test_ignored():
    mods = [Mod("On", [Key("F1"), Key("F2", enabled=False), Key(None), Key("")]),
            Mod("Off", [Key("F1")], enabled=False),
            Mod("Other", [Key("F2"), Key("F3")])]
    found = c.find(mods, LIMITS)
    expect(found["entries"] == [] and found["mods"] == 2 and found["keys"] == 3,
           "disabled mod, disabled key and unbound keys ignored")


def test_unreadable_and_bounds():
    Tricky.ran.clear()
    found = c.find([Tricky("Tricky", []), Mod("Fine", [Key("F1")]), object()], LIMITS)
    expect(found["unreadable"] == {0, 2} and found["mods"] == 1 and not Tricky.ran,
           "a property is not run, the mod is counted unreadable by its place in the list")
    small = dict(LIMITS, maxMods=2, maxKeysPerMod=1, maxName=4)
    bounded = c.find([Mod("Long name", [Key("F1", "Long key"), Key("F2")]), Mod("B", [Key("F1")]),
                      Mod("C", [Key("F1")])], small)
    expect(bounded["partial"] and bounded["mods"] == 2 and bounded["keys"] == 2, "mods and keys bounded")
    expect(bounded["entries"][0]["items"][0] == {"mod": "Long", "name": "Long", "fixed": False}, "names bounded")
    expect(c.find([Mod("A", [Key("F1")]), Mod("B", [Key("F1")])], dict(LIMITS, maxMods=2))["partial"] is False,
           "a list of exactly the bound is looked at whole")
    expect(c.find([Mod("A", []), Mod("B", []), Mod("C", [])], dict(LIMITS, maxMods=2))["partial"]
           and c.find([Mod("A", [Key("F1"), Key("F2")])], dict(LIMITS, maxKeysPerMod=1))["partial"],
           "more mods than the bound, or a mod with more keys than its bound: each leaves the list partial")

    class TrickyKey(Key):
        @property
        def key(self):
            return "F9"

        @key.setter
        def key(self, _value):
            pass

    found = c.find([Mod("Odd key", [TrickyKey("F9")]), Mod("Fine", [Key("F9")])], LIMITS)
    expect(found["unreadable"] == {0} and found["mods"] == 1, "a key whose field runs code makes its mod unreadable")


def test_items_bound():
    small = dict(LIMITS, maxItems=3)
    mods = [Mod("A", [Key("F1", "Press"), Key("F1", "Hold"), Key("F1", "Release")]), Mod("B", [Key("F1", "Use")]),
            Mod("C", [Key("F1", "Jump")])]
    entry = c.find(mods, small)["entries"][0]
    expect([use["mod"] for use in entry["items"]] == ["A", "B", "C"] and entry["more"] == 2,
           "each mod's first use comes first: a key cut to its first lines still shows two mods, the rest counted")
    many = copy.deepcopy([Mod(f"M{index}", [Key("F1")]) for index in range(5)])
    entry = c.find(many, small)["entries"][0]
    expect(len(entry["items"]) == 3 and entry["more"] == 2, "an entry keeps its bound of lines")


for test in (test_found, test_ignored, test_unreadable_and_bounds, test_items_bound):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
