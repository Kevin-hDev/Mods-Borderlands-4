# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests of pak_legacy.py on .pak files built as the engine writes them (fixture_paks.py). python test_pak_legacy.py"""

import hashlib
import struct
import sys
import tempfile
from pathlib import Path

import package_path  # noqa: F401
from logs_conflicts import pak_legacy as p, pak_reading, protocol
from fixture_paks import PAK_MAGIC, fstring, pak_flat, pak_footer, pak_v11

FAILURES = []
LIMITS = protocol.load_constants()["conflicts"]["paks"]
FILES = [("OakGame/Content/uiresources/menu_pause/menu_pause.html", b"<html>pause</html>"),
         ("OakGame/Content/uiresources/menu_main/menu_main.html", b"<html>main</html>"),
         ("Root.txt", b"root")]


def expect(condition, label):
    if not condition:
        FAILURES.append(label)
        print(f"ECHEC: {label}")


def reason(data: bytes) -> str:
    """The cause an unreadable container gives: the service writes it in its log."""
    found = read(data)
    return str(found) if isinstance(found, pak_reading.Unreadable) else ""


def read(data: bytes, most: int = 1000, limits: dict = LIMITS):
    """(files, hashes) or the Unreadable raised."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "mod_P.pak"
        path.write_bytes(data)
        container = pak_reading.ContainerFile(path, limits)
        try:
            files = p.read_files(container, most)
            return files, [p.stored_hash(container, locator) for _path, locator in files]
        except pak_reading.Unreadable as error:
            return error
        finally:
            container.close()


def test_version_11():
    files, hashes = read(pak_v11(FILES))
    expect([path for path, _locator in files] == [path for path, _data in FILES],
           "every path, as the game names it, mount removed")
    expect(hashes == [hashlib.sha1(data).hexdigest() for _path, data in FILES],
           "each hash read in front of its data")
    files, hashes = read(pak_v11(FILES, wrong_size={FILES[1][0]}))
    expect(hashes[1] is None and hashes[0] is not None, "an entry in front of the data that disagrees gives no hash")
    files, _hashes = read(pak_v11([("Équipe/模组.txt", b"x")]))
    expect(files[0][0] == "Équipe/模组.txt", "names in UTF-16")
    expect(read(pak_v11(FILES, path_hash=True)) == read(pak_v11(FILES)), "a path hash index skipped")
    files, hashes = read(pak_v11(FILES, deleted={FILES[0][0]}))
    expect(files[0][1] is None and hashes[0] is None and hashes[1] is not None,
           "a file listed without an entry: no hash, the others read")
    expect(p.stored_hash(None, None) is None, "no entry, no hash, nothing read")
    one_folder = [("A/a1.txt", b"1"), ("A/a2.txt", b"2")]
    expect(isinstance(read(pak_v11(one_folder, repeat=2), most=3), pak_reading.Unreadable)
           and not isinstance(read(pak_v11(one_folder), most=3), pak_reading.Unreadable),
           "the budget of files is shared by all folders, even when the directory lists more names than the index")


def test_encoded_entry():
    """Each form of an encoded entry (IPlatformFilePak.cpp, DecodePakEntry): 32 or 64-bit offset and sizes, the
    stored size only for a compressed file, the block size written apart when it does not fit in six bits."""
    small = (1 << 31) | (1 << 30)
    expect(p.decode_entry(struct.pack("<III", small, 5, 9), 0, LIMITS) == (5, 9), "32-bit offset and size")
    expect(p.decode_entry(b"pad!" + struct.pack("<III", small, 5, 9), 4, LIMITS) == (5, 9), "read where it starts")
    expect(p.decode_entry(struct.pack("<IqI", 1 << 30, 2 ** 33, 9), 0, LIMITS) == (2 ** 33, 9), "a 64-bit offset")
    expect(p.decode_entry(struct.pack("<IIq", 1 << 31, 5, 2 ** 33), 0, LIMITS) == (5, 2 ** 33), "a 64-bit size")
    packed = small | (1 << 29) | (1 << 23)
    expect(p.decode_entry(struct.pack("<IIII", packed, 5, 9, 4), 0, LIMITS) == (5, 4),
           "a compressed file: its stored size")
    expect(p.decode_entry(struct.pack("<IIIq", small | (1 << 23), 5, 9, 2 ** 33 + 1), 0, LIMITS) == (5, 2 ** 33 + 1),
           "a compressed file: its stored size on 64 bits")
    expect(p.decode_entry(struct.pack("<IIII", small | 0x3F, 65536, 5, 9), 0, LIMITS) == (5, 9),
           "a block size written apart")


def test_flat_versions():
    for version, compressed in ((1, False), (2, False), (3, False), (8, False), (8, True)):
        files, hashes = read(pak_flat(FILES, version, compressed=compressed))
        expect([path for path, _locator in files] == [path for path, _data in FILES]
               and hashes == [hashlib.sha1(data).hexdigest() for _path, data in FILES],
               f"a flat index, version {version}{', compressed' if compressed else ''}: paths and stored hashes")


def test_refused():
    expect(isinstance(read(pak_v11(FILES, encrypted=True)), pak_reading.Unreadable), "an encrypted index")
    expect(reason(pak_v11(FILES, full_directory=False)) == "no full directory index",
           "an index without full directory: names are only hashes")
    expect(reason(b"not a pak at all" * 4) == "no pak footer", "no footer")
    expect(reason(b"\0" * 40 + struct.pack("<I", PAK_MAGIC) + b"\0" * 10) == "no pak footer",
           "a footer cut short after its magic")
    frozen = pak_v11(FILES)[:-len(pak_footer(11, 0, 0))] + pak_footer(9, 0, 0)
    expect(reason(frozen) == "unknown pak version", "version 9, frozen index")
    outside = pak_v11(FILES)[:-len(pak_footer(11, 0, 0))] + pak_footer(11, 10 ** 9, 100)
    expect(isinstance(read(outside), pak_reading.Unreadable), "an index outside the file")
    expect(isinstance(read(pak_v11(FILES), most=2), pak_reading.Unreadable)
           and isinstance(read(pak_flat(FILES), most=2), pak_reading.Unreadable),
           "more files than the budget left, in both forms")
    expect(not isinstance(read(pak_v11(FILES), most=3), pak_reading.Unreadable), "exactly the budget is read")
    long_name = [("x" * 50, b"data")]
    expect(isinstance(read(pak_flat(long_name), limits=dict(LIMITS, maxStringBytes=16)), pak_reading.Unreadable),
           "a name above its bound")
    index = fstring("../../../") + struct.pack("<i", 1) + fstring("a.txt") + struct.pack("<qqqI", 0, 1, 1, 1)
    index += b"\0" * 20 + struct.pack("<i", 10 ** 6)
    blocks = b"x" * 40 + index + pak_footer(8, 40, len(index))
    expect(isinstance(read(blocks), pak_reading.Unreadable), "compression blocks counted beyond the index")


for test in (test_version_11, test_encoded_entry, test_flat_versions, test_refused):
    test()
print("RESULTAT: TOUS LES TESTS PASSENT" if not FAILURES else f"RESULTAT: {len(FAILURES)} ECHEC(S)")
sys.exit(1 if FAILURES else 0)
