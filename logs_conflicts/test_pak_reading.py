# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of pak_reading.py: every read stays inside its file and its bounds. python test_pak_reading.py"""

import struct
import sys
import tempfile
from pathlib import Path

import package_path  # noqa: F401
from logs_conflicts import pak_reading as r, protocol
from fixture_paks import fstring

FAILURES = []
LIMITS = protocol.load_constants()["conflicts"]["paks"]


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


def refused(action) -> bool:
    try:
        action()
    except r.Unreadable:
        return True
    return False


def test_container_file():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "a.pak"
        path.write_bytes(b"0123456789")
        container = r.ContainerFile(path, LIMITS)
        try:
            expect(container.size == 10 and container.read_at(2, 3) == b"234", "a read inside the file")
            expect(refused(lambda: container.read_at(8, 3)) and refused(lambda: container.read_at(-1, 2))
                   and refused(lambda: container.read_at(0, -1)), "reads outside the file refused")
        finally:
            container.close()
        small = r.ContainerFile(path, dict(LIMITS, maxIndexBytes=4))
        try:
            expect(refused(lambda: small.read_at(0, 5)) and small.read_at(0, 4) == b"0123",
                   "no read beyond the index bound, even inside the file")
        finally:
            small.close()

        class Short:
            def __init__(self, inner):
                self.inner = inner

            def fileno(self):
                return self.inner.fileno()

            def seek(self, offset):
                self.inner.seek(offset)

            def read(self, size):
                return self.inner.read(size)[:-1]

            def close(self):
                self.inner.close()

        lying = r.ContainerFile(path, LIMITS, opener=lambda name, mode: Short(open(name, mode)))
        try:
            expect(refused(lambda: lying.read_at(0, 4)), "a file shorter than it said is unreadable")
        finally:
            lying.close()

        class Counted(Short):
            asked = []

            def read(self, size):
                Counted.asked.append(size)
                return self.inner.read(size)

        counted = r.ContainerFile(path, LIMITS, opener=lambda name, mode: Counted(open(name, mode)))
        try:
            expect(refused(lambda: counted.read_at(0, -1)) and Counted.asked == [],
                   "a negative size refused before any read: read(-1) would load the whole container")
        finally:
            counted.close()

        class NoNumber:
            closed = False

            def fileno(self):
                raise OSError("no descriptor")

            def close(self):
                self.closed = True

        handle = NoNumber()
        try:
            r.ContainerFile(path, LIMITS, opener=lambda _name, _mode: handle)
            expect(False, "a file whose size cannot be read is refused")
        except OSError:
            expect(handle.closed, "a file whose size cannot be read is closed, not left open")


def test_cursor():
    cursor = r.Cursor(struct.pack("<iIqQ", -5, 7, -9, 11), LIMITS)
    expect((cursor.i32(), cursor.u32(), cursor.i64(), cursor.u64()) == (-5, 7, -9, 11), "numbers read in order")
    expect(refused(lambda: cursor.take(1)), "past the buffer refused")
    expect(refused(lambda: r.Cursor(b"abc", LIMITS).take(-1)), "a negative size refused")
    counts = r.Cursor(struct.pack("<ii", 3, -1), LIMITS)
    expect(refused(lambda: r.Cursor(struct.pack("<i", 4), LIMITS).count(3)) and counts.count(3) == 3
           and refused(lambda: counts.count(3)), "a count above its bound, or negative, refused")


def test_strings():
    cursor = r.Cursor(fstring("Abc") + fstring("") + fstring("Équipe") + fstring("模组"), LIMITS)
    expect([cursor.fstring() for _ in range(4)] == ["Abc", "", "Équipe", "模组"],
           "Latin-1 and UTF-16 strings, and the empty one")
    expect(refused(lambda: r.Cursor(fstring("x" * 20), dict(LIMITS, maxStringBytes=8)).fstring())
           and refused(lambda: r.Cursor(fstring("模" * 5), dict(LIMITS, maxStringBytes=8)).fstring()),
           "strings above their bound refused, in both forms")
    expect(refused(lambda: r.Cursor(struct.pack("<i", 50) + b"short", LIMITS).fstring()), "a cut string refused")


def test_strip_mount():
    expect(r.strip_mount("../../../", "OakGame/Content/a.js") == "OakGame/Content/a.js", "the mount's steps up removed")
    expect(r.strip_mount("../../../", "/x") == "x" and r.strip_mount("", "a\\b.js") == "a/b.js",
           "a root name and backslashes")


for test in (test_container_file, test_cursor, test_strings, test_strip_mount):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
