# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of log_file.py on files in a temporary folder. python test_log_file.py"""

import copy
import os
import sys
import tempfile
from pathlib import Path

import package_path  # noqa: F401
from logs_conflicts import log_file as f, protocol

FAILURES = []


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


C = protocol.load_constants()
SMALL = copy.deepcopy(C)
SMALL["log"]["maxBytes"], SMALL["log"]["headBytes"], SMALL["log"]["maskMarginBytes"] = 100, 30, 10


def code_of(action) -> str:
    try:
        action()
    except f.LogError as error:
        return error.code
    return "none"


def test_path():
    folder = Path(r"W:\Game\Plugins")
    expect(f.log_path(folder, {"unrealsdk": {}}, C) == (folder / "unrealsdk.log", "default"), "default name")
    expect(f.log_path(folder, {}, C) == (folder / "unrealsdk.log", "default"), "no section: default name")
    expect(f.log_path(folder, None, C) == (folder / "unrealsdk.log", "default"), "no config: default name")
    expect(f.log_path(folder, {"unrealsdk": {"log_file": "logs/sdk.log"}}, C) == (folder / "logs/sdk.log", "set"),
           "relative name from the DLL's folder")
    expect(f.log_path(folder, {"unrealsdk": {"log_file": r"D:\Logs\sdk.log"}}, C)[0] == Path(r"D:\Logs\sdk.log"),
           "absolute name kept")
    for bad in ("", "   ", 5, "x" * 300, "a\0b"):
        expect(f.log_path(folder, {"unrealsdk": {"log_file": bad}}, C) == (None, "bad_setting"), f"bad name {bad!r}")
    expect(f.log_path(None, {}, C) == (None, "no_dll"), "no DLL: no path")


def test_read(folder: Path):
    log = folder / "unrealsdk.log"
    log.write_bytes(b"line one\nline two \xc3\xa9\n")
    whole = f.read(log, None, C)
    expect(whole["head"] == "line one\nline two \u00e9\n" and whole["tail"] == "" and whole["cut"] == 0, "whole log")
    expect(f.read(log, whole["revision"], C) == {"unchanged": True, "revision": whole["revision"]},
           "same revision: nothing read again")
    lines = b"".join(b"%02d-abcdefgh\n" % index for index in range(40))
    log.write_bytes(lines)
    os.utime(log, ns=(1, 2))
    long = f.read(log, whole["revision"], SMALL)
    expect(long["head"] == "00-abcdefgh\n01-abcdefgh\n", "start cut at a line end")
    first = long["tail"].split("\n")[0]
    expect(long["tail"].endswith("39-abcdefgh\n") and len(first) == 11 and first.endswith("-abcdefgh")
           and len(long["tail"]) <= 100 - len(long["head"]), "end starts at a whole line, within the bound")
    expect(long["cut"] == len(lines) - len(long["head"]) - len(long["tail"]) and long["size"] == len(lines),
           "cut size counted")
    # The head would be cut at its 30th byte, inside the "\u00e9" of bytes 29 and 30: it ends before it instead.
    log.write_bytes(b"x" * 29 + "\u00e9".encode() + b"y" * 222)
    broken = f.read(log, None, SMALL)
    expect(broken["head"] == "x" * 29, "the head's cut never splits a character")
    expect(broken["tail"] == "y" * 71 and broken["cut"] == 253 - 29 - 71, "an end without a line end kept whole")
    expect(broken["afterHead"] == "\u00e9" + "y" * 9 and broken["beforeTail"] == "y" * 10,
           "a part cut inside a line comes with the bytes across its cut, for the masking")
    # The end would start at byte 131, inside the "\u00e9" of bytes 130 and 131: it starts after it instead.
    log.write_bytes(b"a" * 29 + b"\n" + b"y" * 100 + "\u00e9".encode() + b"y" * 69)
    late = f.read(log, None, SMALL)
    expect(late["tail"] == "y" * 69 and late["beforeTail"] == "y" * 9 + "\u00e9",
           "the end of one long line starts where a character starts")
    # The longest characters, 4 bytes (an emoji; a Chinese name's take 3): three steps back, and three forward.
    emoji = "\U0001F600".encode("utf-8")
    log.write_bytes(b"x" * 27 + emoji + b"y" * 222)
    expect(f.read(log, None, SMALL)["head"] == "x" * 27, "a 4-byte character is not split at the head's cut")
    log.write_bytes(b"a" * 29 + b"\n" + b"y" * 100 + emoji + b"y" * 67)
    far = f.read(log, None, SMALL)
    expect(far["tail"] == "y" * 67 and far["beforeTail"].endswith("\U0001F600"),
           "a 4-byte character is not split at the end's cut")
    log.write_bytes(b"bad \xff byte\n")
    expect(f.read(log, None, C)["head"] == "bad \ufffd byte\n", "a byte that is no UTF-8 is replaced")
    expect(long.get("afterHead") == "" and long.get("beforeTail") == "", "parts cut at line ends come alone")
    expect(code_of(lambda: f.read(folder / "absent.log", None, C)) == "log_missing", "missing log")
    expect(code_of(lambda: f.read(None, None, C)) == "log_missing", "no path")

    def refuse(_path, _mode):
        raise PermissionError(13, "denied")

    expect(code_of(lambda: f.read(log, None, C, opener=refuse)) == "log_refused", "Windows refuses the read")


def test_growing(folder: Path):
    log = folder / "growing.log"
    log.write_bytes(b"first\n")
    info = os.stat(log)
    with open(log, "ab") as file:
        file.write(b"written after the stat\n")
    read = f.read(log, None, C, stat=lambda _path: info)
    expect(read["head"] == "first\n", "only the size taken at stat is read")


def test_read_start(folder: Path):
    """The log's start, where the mod loader writes (conception, section 5, « Le journal »)."""
    log = folder / "start.log"
    log.write_bytes("first line\nsecond é line\nthird\n".encode("utf-8"))
    expect(f.read_start(log, 1000) == "first line\nsecond é line\nthird\n", "a short log whole")
    expect(f.read_start(log, 20) == "first line\n", "a longer log cut at its last line end within the bound")
    log.write_bytes(b"no line end at all here")
    expect(f.read_start(log, 5) == "no li", "one long line cut at the bound")
    log.write_bytes(b"a\nb\n")
    expect(f.read_start(log, 4) == "a\nb\n", "exactly the bound: kept whole")
    log.write_bytes(b"ab\ncd\nef")
    expect(f.read_start(log, 5) == "ab\n", "a line end just past the bound is not taken")
    log.write_bytes(b"bad \xff byte\n")
    expect(f.read_start(log, 100) == "bad \ufffd byte\n", "bytes that are not UTF-8 replaced, never refused")
    expect(code_of(lambda: f.read_start(folder / "absent.log", 10)) == "log_missing"
           and code_of(lambda: f.read_start(None, 10)) == "log_missing", "missing log, or no path")

    def refuse(_path, _mode):
        raise PermissionError(13, "denied")

    expect(code_of(lambda: f.read_start(log, 10, opener=refuse)) == "log_refused", "Windows refuses the read")


test_path()
with tempfile.TemporaryDirectory() as temporary:
    test_read(Path(temporary))
    test_growing(Path(temporary))
    test_read_start(Path(temporary))
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
