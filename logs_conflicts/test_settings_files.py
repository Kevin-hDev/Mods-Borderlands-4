# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of settings_files.py with mods shaped like mods_base's and modules holding them.
python test_settings_files.py"""

import sys
import types
from pathlib import PureWindowsPath

import package_path  # noqa: F401
from logs_conflicts import protocol, settings_files as s

FAILURES = []
LIMITS = protocol.load_constants()["conflicts"]
SETTINGS = "C:/Games/Borderlands 4/sdk_mods/settings/"


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


class Mod:
    def __init__(self, name, settings=None):
        self.name = name
        self.settings_file = PureWindowsPath(SETTINGS + settings) if settings else None


class LoudModule(types.ModuleType):
    """A module of another class: its variables are not read."""


def module(name, **variables):
    made = types.ModuleType(name)
    made.__dict__.update(variables)
    return made


def test_listed():
    mods = [Mod("Weather", "weather.json"), Mod("Rain", "Weather.JSON"), Mod("Sun", "sun.json"), Mod("None")]
    found = s.find(mods, [], Mod, LIMITS)
    expect(found["entries"] == [{"name": "weather.json", "items": [{"mod": "Weather", "dropped": False},
                                                                    {"mod": "Rain", "dropped": False}], "more": 0}],
           "two listed mods on one file, in any case; a mod alone or without settings is no conflict")
    expect(found["unreadable"] == set(), "all readable")


def test_dropped():
    kept, gone = Mod("Weather 2", "weather.json"), Mod("Weather", "weather.json")
    other = Mod("Old", "old.json")
    loud = LoudModule("loud")
    loud.mod = Mod("Hidden", "weather.json")
    modules = [("weather", module("weather", mod=gone, again=gone, kept=kept)), ("old", module("old", mod=other)),
               ("weather.sub", module("weather.sub", copy=Mod("Sub", "weather.json"))), ("loud", loud),
               ("plain", module("plain", value=3, text="weather.json"))]
    found = s.find([kept], modules, Mod, LIMITS)
    expect(found["entries"] == [{"name": "weather.json", "items": [{"mod": "Weather 2", "dropped": False},
                                                                    {"mod": "Weather", "dropped": True}], "more": 0}],
           "a mod dropped from the list, still in its module, shown once against the one kept")
    expect(all(item["mod"] not in ("Old", "Sub", "Hidden") for item in found["entries"][0]["items"]),
           "a dropped mod on a file no listed mod uses, a submodule, a module of another class: left out")


class Disguised:
    """Claims to be a mod through __class__, which isinstance would ask, running its code."""
    asked = []

    @property
    def __class__(self):
        Disguised.asked.append(True)
        return Mod


def test_disguised():
    found = s.dropped([("disguise", module("disguise", value=Disguised()))], Mod, [], LIMITS)
    expect(found == [] and Disguised.asked == [], "a mod is told by its class alone, nothing of it asked")


def test_unreadable_and_bounds():
    class Odd(Mod):
        @property
        def settings_file(self):
            raise AssertionError("must not run")

        @settings_file.setter
        def settings_file(self, _value):
            pass

    found = s.find([Odd("Odd"), object(), Mod("A", "a.json"), Mod(None, "a.json")], [], Mod, LIMITS)
    expect(found["unreadable"] == {0, 1, 3} and found["entries"] == [], "unreadable mods counted by their place")
    bad = Mod("Bad")
    bad.settings_file = "C:/Games/sdk_mods/settings/a.json"
    found = s.find([Mod("A", "a.json")], [("bad", module("bad", gone=bad))], Mod, LIMITS)
    expect(found["entries"] == [], "a dropped mod that cannot be read is left out")
    found = s.find([Mod("A", "a.json")], [("first", module("first", x=1)),
                                          ("second", module("second", gone=Mod("E", "a.json")))],
                   Mod, dict(LIMITS, maxModules=1))
    expect(found["entries"] == [], "modules past their bound are not read")
    small = dict(LIMITS, maxItems=1, maxModules=1, maxModuleValues=1)
    mods = [Mod("A", "a.json"), Mod("B", "a.json"), Mod("C", "a.json")]
    found = s.find(mods, [("first", module("first", x=1, gone=Mod("D", "a.json"))),
                          ("second", module("second", gone=Mod("E", "a.json")))], Mod, small)
    expect(found["entries"] == [{"name": "a.json", "items": [{"mod": "A", "dropped": False}], "more": 2}],
           "lines, modules and each module's variables bounded")
    long_file = "w" * 30 + ".json"
    found = s.find([Mod("A", long_file), Mod("B", long_file)], [], Mod, dict(LIMITS, maxName=10))
    expect([entry["name"] for entry in found["entries"]] == ["w" * 10],
           "a settings file's name cut to its bound, as a mod's name is")


for test in (test_listed, test_dropped, test_disguised, test_unreadable_and_bounds):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
