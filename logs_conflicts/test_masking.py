# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of masking.py. python test_masking.py"""

import sys

import package_path  # noqa: F401
from logs_conflicts import masking as m

FAILURES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


def test_one_home():
    patterns = m.home_patterns([r"C:\Users\Kevin"])
    text = ("opened C:\\Users\\Kevin\\OneDrive\\save.sav\n"
            "json c:/users/kevin/AppData and C:\\\\Users\\\\KEVIN\\\\x\n"
            "Kevin wrote this; C:\\Users\\Kevin2\\other stays; C:\\Users\\Kevin.doe too.\n")
    masked, count = m.mask(text, patterns, "<user>")
    expect("C:\\Users\\<user>\\OneDrive" in masked, "backslash path masked")
    expect("c:/users/<user>/AppData" in masked, "forward slashes and lower case masked, case kept")
    expect("C:\\\\Users\\\\<user>\\\\x" in masked, "escaped backslashes masked")
    expect(masked.startswith("opened") and "Kevin wrote this" in masked, "the name alone, outside a path, is kept")
    expect("Kevin2" in masked and "Kevin.doe" in masked, "a longer name is not cut")
    expect(count == 3, f"replacements counted ({count})")
    expect(m.mask("saved in C:\\Users\\Kevin.\n", patterns, "<user>")[0] == "saved in C:\\Users\\<user>.\n",
           "a dot ending the sentence ends the name")
    expect(m.mask("C:\\Users\\Kevin\n", patterns, "<user>") == ("C:\\Users\\<user>\n", 1), "name at the end of a path")
    expect(m.mask(r"D:\Users\Kevin\Games", patterns, "<user>")[0] == r"D:\Users\<user>\Games",
           "the same home on another drive")
    expect(m.mask("file:///C:%5CUsers%5CKevin%2Fx", patterns, "<user>")[0] == "file:///C:%5CUsers%5C<user>%2Fx",
           "URL-encoded separators")


def test_odd_names():
    spaced = m.home_patterns([r"C:\Users\Jane Doe"])
    expect(m.mask("C:\\Users\\Jane Doe\\x and C:%5CUsers%5CJane%20Doe%5Cy", spaced, "<user>")
           == ("C:\\Users\\<user>\\x and C:%5CUsers%5C<user>%5Cy", 2), "a name with a space, plain and encoded")
    odd = m.home_patterns([r"D:\Profils (x)\J+K"])
    expect(m.mask(r"D:\Profils (x)\J+K\file", odd, "<user>")[0] == r"D:\Profils (x)\<user>\file",
           "characters special to patterns are taken as text")
    for bad in ("", "   ", None, "C:\\"):
        expect(m.home_pattern(bad) is None, f"no pattern for {bad!r}")
    expect(m.mask("text", (), "<user>") == ("text", 0), "no pattern: text unchanged")
    expect(len(m.home_patterns([r"C:\Users\Kevin", r"c:\users\kevin", None])) == 1, "one pattern per home")


def test_short_and_linux_homes():
    both = m.home_patterns([r"C:\Users\Jane Doe", r"C:\Users\JANEDO~1"])
    expect(m.mask(r"temp C:\Users\JANEDO~1\AppData\Local\Temp", both, "<user>")[0]
           == r"temp C:\Users\<user>\AppData\Local\Temp", "the short 8.3 name masked")
    homes = m.linux_homes({"WINEHOMEDIR": "\\??\\Z:\\home\\deck", "WINEUSERNAME": "deck"})
    expect(homes == ["Z:\\home\\deck", "/home/deck"], f"Wine's names of the real home ({homes})")
    linux = m.home_patterns(homes)
    expect(m.mask("Z:\\home\\deck\\steam and /home/deck/.local", linux, "<user>")
           == ("Z:\\home\\<user>\\steam and /home/<user>/.local", 2), "the Linux home masked in both writings")
    expect(m.linux_homes({}) == [] and m.linux_homes({"WINEUSERNAME": "a/b"}) == [], "no Wine, or an odd name: none")


def test_cut_paths():
    patterns = m.home_patterns([r"C:\Users\Jane Doe"])
    head, join, first, second = m.mask_joined("start C:\\Users\\Jane D", "oe\\AppData", patterns, "<user>")
    expect(head[:join] == "start C:\\Users\\<user>" and (first, second) == (1, 0),
           "a path cut at the head's end masked whole, kept with the head")
    tail, join, first, second = m.mask_joined("x C:\\Us", "ers\\Jane Doe\\AppData", patterns, "<user>")
    expect(tail[join:] == "\\AppData" and (first, second) == (1, 0), "a path cut at the tail's start leaves no name")
    tail, join, first, second = m.mask_joined("C:\\Users\\Jane Doe\\a ", "C:\\Users\\Jane Doe\\b",
                                              patterns, "<user>")
    expect(tail[:join] == "C:\\Users\\<user>\\a " and tail[join:] == "C:\\Users\\<user>\\b"
           and (first, second) == (1, 1), "each side counts its own names")


test_one_home()
test_odd_names()
test_short_and_linux_homes()
test_cut_paths()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
