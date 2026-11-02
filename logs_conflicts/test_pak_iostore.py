# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of pak_iostore.py on .utoc files built as the engine writes them (fixture_paks.py).
python test_pak_iostore.py"""

import struct
import sys
import tempfile
from pathlib import Path

import package_path  # noqa: F401
from logs_conflicts import pak_iostore as t, pak_reading, protocol
from fixture_paks import FLAG_ENCRYPTED, FLAG_INDEXED, MOUNT, NO_INDEX, digest, fstring, utoc

FAILURES = []
LIMITS = protocol.load_constants()["conflicts"]["paks"]
FILES = [("OakGame/Content/ApexGrapple/SM_Hook.uasset", digest("hook")),
         ("OakGame/Content/ApexGrapple/SM_Hook.ubulk", digest("bulk")),
         ("OakGame/Content/Other/T_Rope.uasset", digest("rope"))]


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


def read(data: bytes, most: int = 1000):
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "mod_P.utoc"
        path.write_bytes(data)
        container = pak_reading.ContainerFile(path, LIMITS)
        try:
            return t.read_files(container, most)
        except pak_reading.Unreadable as error:
            return error
        finally:
            container.close()


def unreadable(data: bytes, most: int = 1000) -> bool:
    return isinstance(read(data, most), pak_reading.Unreadable)


EXPECTED = sorted((path, value.hex()) for path, value in FILES)


def test_read():
    found = read(utoc(FILES))
    expect(sorted(found) == EXPECTED, "every file with the hash its chunk's meta stores")
    expect(read(utoc(FILES, flags=0)) == [] and read(utoc(FILES, no_directory=True)) == [],
           "a container without directory index, or with an empty one, lists no file")
    expect(not unreadable(utoc(FILES), most=3), "exactly the budget is read")
    for version, tables in ((3, {}), (4, {}), (5, {}), (8, {"blocks": 2, "methods": 1})):
        expect(sorted(read(utoc(FILES, version=version, seeds=2, without_hash=3, **tables))) == EXPECTED,
               f"version {version}: the tables before the directory skipped, each from the version that has it")
    expect(sorted(read(utoc(FILES, signature=32, blocks=2))) == EXPECTED,
           "a signed container: its two hashes and one per block skipped")
    expect([value for _path, value in read(utoc(FILES, meta_bytes=10))] == [None] * 3,
           "metas too short for a hash: no hash")

    def far_chunk(_folders, entries, _strings):
        entries[0][2] = 99

    found = dict(read(utoc(FILES, edit=far_chunk)))
    expect(found[FILES[0][0]] is None and found[FILES[1][0]] == FILES[1][1].hex(),
           "a file on a chunk outside the table: no hash, the others read")


def test_refused():
    expect(unreadable(utoc(FILES, flags=FLAG_INDEXED | FLAG_ENCRYPTED)), "an encrypted directory index")
    expect(unreadable(b"X" * 16 + utoc(FILES)[16:]), "a known version byte behind another magic")
    expect(unreadable(b"-==--==--==--==-" + bytes(200)), "a version this reader does not know")
    expect(unreadable(utoc(FILES, version=9)) and unreadable(b"x" * 300), "another version, another magic")
    expect(unreadable(utoc(FILES), most=2), "more files than the budget left")
    expect(unreadable(utoc(FILES, header_size=100)), "a header of another size")
    expect(sorted(path for path, _hash in read(utoc(FILES, signature=32))) == sorted(path for path, _ in FILES)
           and str(read(utoc(FILES, signature=-1))) == "negative signature size",
           "a signed container read past its signature; a negative one refused")
    negative = fstring(MOUNT) + struct.pack("<iii", -1, 0, 0)
    try:
        t.walk(negative, LIMITS, 10)
        expect(False, "a negative count of folders refused")
    except pak_reading.Unreadable:
        pass

    def walked(buffer):
        try:
            t.walk(buffer, LIMITS, 10)
        except pak_reading.Unreadable as error:
            return str(error)
        return "read"

    folder = struct.pack("<4I", NO_INDEX, NO_INDEX, NO_INDEX, NO_INDEX)
    one = struct.pack("<i", 1) + folder
    expect(walked(fstring(MOUNT) + struct.pack("<i", 1000) + folder * 2) == "count out of bounds"
           and walked(fstring(MOUNT) + one + struct.pack("<i", 5) + bytes(24)) == "count out of bounds"
           and walked(fstring(MOUNT) + one + struct.pack("<ii", 0, 1000) + bytes(8)) == "count out of bounds",
           "a count of folders, files or names the bytes left cannot hold, refused as such before its table")
    expect(walked(fstring(MOUNT) + one + struct.pack("<ii", 0, 0)) == "read",
           "the same index with counts its bytes hold is read")

    def sibling_loop(folders, _entries, _strings):
        folders[1][2] = 1

    def file_loop(_folders, entries, _strings):
        entries[1][1] = 0

    def child_outside(folders, _entries, _strings):
        folders[0][1] = 40

    def name_outside(_folders, entries, _strings):
        entries[0][0] = 99

    def file_outside(folders, _entries, _strings):
        folders[1][3] = 50

    def child_loop(folders, _entries, _strings):
        folders[2][1] = 1

    def empty_loop(folders, _entries, _strings):
        folders.append([NO_INDEX, len(folders), NO_INDEX, NO_INDEX])
        folders[2][2] = len(folders) - 1

    for edit, label in ((sibling_loop, "folders that are their own sibling"), (file_loop, "a file list that loops"),
                        (child_outside, "a child outside the table"), (name_outside, "a name outside the strings"),
                        (file_outside, "a file outside the table"), (child_loop, "a folder that is its own child"),
                        (empty_loop, "an empty folder that is its own child")):
        expect(unreadable(utoc(FILES, edit=edit)), label)

    def empty_root(folders, _entries, _strings):
        folders[0][1] = NO_INDEX

    expect(read(utoc(FILES, edit=empty_root)) == [], "a root without children lists nothing")


for test in (test_read, test_refused):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
