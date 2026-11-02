# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of commands.py with mods and commands shaped like mods_base's. python test_commands.py"""

import sys

import package_path  # noqa: F401
from logs_conflicts import commands as c, protocol

FAILURES = []
LIMITS = protocol.load_constants()["conflicts"]
RAN = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


class Command:
    def __init__(self, cmd):
        self.cmd = cmd


class Mod:
    def __init__(self, name, commands, enabled=True):
        self.name, self.commands, self.is_enabled = name, [Command(text) for text in commands], enabled


class Tricky(Command):
    @property
    def cmd(self):
        RAN.append(True)
        return "spawn"

    @cmd.setter
    def cmd(self, _value):
        pass


def test_found():
    found = c.find([Mod("Spawner", ["spawn", "kill", "Spawn"]), Mod("Arena", ["SPAWN"]), Mod("Twice", ["save", "save"]),
                    Mod("Off", ["kill"], enabled=False), Mod("Third", ["Spawn"])], LIMITS)
    expect(found["entries"] == [{"name": "spawn", "items": ["Spawner", "Arena", "Third"], "more": 0}],
           "a command of several enabled mods, in any case, each mod once; a disabled mod and one mod's own two are "
           "no conflict")
    expect(found["commands"] == 7 and found["unreadable"] == set() and found["partial"] is False,
           "commands counted for enabled mods, all looked at")


def test_unreadable_and_bounds():
    odd = Mod("Odd", [])
    odd.commands = [Tricky("x")]
    found = c.find([odd, Mod("Empty", [""]), Mod("Quiet", []), object(), Mod("Fine", ["spawn"])], LIMITS)
    quiet = c.find([Mod("Quiet", [])], LIMITS)
    expect(found["unreadable"] == {0, 1, 3} and not RAN, "a property, an empty command, a non-mod: unreadable, unrun")
    expect(quiet["unreadable"] == set(), "a mod without commands is readable")
    small = dict(LIMITS, maxItems=2, maxCommandsPerMod=1, maxMods=3, maxName=3)
    found = c.find([Mod("Alpha", ["spawn", "kill"]), Mod("B", ["spawn"]), Mod("C", ["spawn"]),
                    Mod("D", ["spawn"])], small)
    expect(found["entries"] == [{"name": "spa", "items": ["Alp", "B"], "more": 1}] and found["commands"] == 3,
           "commands per mod, mods, names and lines bounded, the rest counted")
    expect(c.find([Mod("A", ["x"]), Mod("B", ["y"]), Mod("C", [])], dict(LIMITS, maxMods=2))["partial"],
           "mods past their bound: partial")
    exact = dict(LIMITS, maxCommandsPerMod=2, maxMods=2)
    expect(c.find([Mod("A", ["spawn", "kill"]), Mod("B", ["spawn"])], exact)["partial"] is False
           and c.find([Mod("A", ["spawn", "kill", "save"])], exact)["partial"],
           "lists of exactly their bounds are whole; a mod with more commands than its bound leaves the list partial")


for test in (test_found, test_unreadable_and_bounds):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
