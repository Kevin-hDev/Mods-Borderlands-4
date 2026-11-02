# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of mod_fields.py: fields read without running any mod's code. python test_mod_fields.py"""

import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

import package_path  # noqa: F401
from logs_conflicts import mod_fields as f, protocol

FAILURES = []
LIMITS = protocol.load_constants()["conflicts"]
RAN = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


class Plain:
    def __init__(self, **fields):
        self.__dict__.update(fields)


class Runs:
    @property
    def name(self):
        RAN.append("name")
        return "ran"

    @property
    def settings_file(self):
        RAN.append("settings_file")
        return Path("x.json")


class OwnPath(type(Path())):
    """A path of another class could run its own code when turned into text."""


class OwnText(str):
    """A text of another class runs its own code when sliced or compared."""


class OwnList(list):
    """A list of another class runs its own code when indexed or sliced."""


def test_plain_fields():
    expect(f.plain_fields(Plain(a="x", b=True, c=None, d=[1], e=(2,)), ("a", "b", "c", "d", "e"))
           == ["x", True, None, [1], (2,)], "plain values read")
    expect(f.plain_fields(Plain(a="x"), ("a", "missing")) is None, "a missing field: unreadable")
    expect(f.plain_fields(Plain(a=3), ("a",)) is None and f.plain_fields(Plain(a={}), ("a",)) is None,
           "numbers and other objects are not plain values here")
    expect(f.plain_fields(Runs(), ("name",)) is None and not RAN, "a property is never run")
    expect(f.plain_fields(Plain(a=OwnText("x")), ("a",)) is None and f.plain_fields(Plain(a=OwnList()), ("a",)) is None,
           "a text or a list of another class is not a plain value: exact types only (review, 2 November 2026)")
    expect(f.short("abcdef", 3) == "abc" and f.short(None, 3) == "", "texts cut, non-texts empty")


def test_enabled_list():
    expect(f.enabled_list(Plain(name="Mod", is_enabled=True, keybinds=[1, 2]), "keybinds", LIMITS) == ("Mod", [1, 2]),
           "an enabled mod's list")
    expect(f.enabled_list(Plain(name="Mod", is_enabled=False, keybinds=[1]), "keybinds", LIMITS) == (None, ()),
           "a disabled mod gives nothing")
    for broken in (Plain(name=1, is_enabled=True, keybinds=[]), Plain(name=None, is_enabled=True, keybinds=[]),
                   Plain(name="M", is_enabled="yes", keybinds=[]),
                   Plain(name="M", is_enabled=True, keybinds="F5"), Plain(name="M", is_enabled=True)):
        try:
            f.enabled_list(broken, "keybinds", LIMITS)
            expect(False, f"unreadable mod refused ({broken.__dict__})")
        except ValueError:
            pass
    expect(f.enabled_list(Plain(name="x" * 200, is_enabled=True, commands=()), "commands", LIMITS)[0]
           == "x" * LIMITS["maxName"], "the name bounded")


def test_path_field():
    expect(f.path_field(Plain(settings_file=PureWindowsPath("C:/Games/sdk_mods/settings/Weather.json")),
                        "settings_file") == ("Weather.json", "c:/games/sdk_mods/settings/weather.json"),
           "a path's name, and a key compared in any case and with either slash")
    expect(f.path_field(Plain(settings_file=PurePosixPath("/a/B.json")), "settings_file") == ("B.json", "/a/b.json"),
           "a POSIX path")
    expect(f.path_field(Plain(settings_file=None), "settings_file") is None, "no settings file")
    for value in ("C:/a.json", OwnPath("a.json")):
        try:
            f.path_field(Plain(settings_file=value), "settings_file")
            expect(False, f"not a path of the standard library: refused ({value!r})")
        except ValueError:
            pass
    try:
        f.path_field(Runs(), "settings_file")
        expect(False, "a property refused")
    except ValueError:
        expect(not RAN, "a property refused without being run")
    try:
        f.path_field(Plain(), "settings_file")
        expect(False, "a missing field refused")
    except ValueError:
        pass


for test in (test_plain_fields, test_enabled_list, test_path_field):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
