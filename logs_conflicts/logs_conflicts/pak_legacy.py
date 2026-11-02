# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The file list of a legacy .pak, versions 1 to 8 (flat index) and 10 to 11 (full directory index), as written by
the engine (IPlatformFilePak.h, UE 5.5.4) and by repak. Read only; checked against repak on the game's own paks and
our mods' at the inventory (1 November 2026). Version 9 (frozen index) and encrypted indexes are unreadable."""

import struct

from .pak_reading import Cursor, Unreadable, strip_mount

MAGIC = struct.pack("<I", 0x5A6F12E1)
FOOTER_SEARCH_BYTES = 512
KNOWN_VERSIONS = (1, 2, 3, 4, 5, 6, 7, 8, 10, 11)
# Entry header written in front of each file's data: Offset, Size, UncompressedSize, CompressionMethodIndex, Hash.
ENTRY_HEAD_BYTES = 48
ENTRY_HASH = slice(28, 48)


def read_footer(container) -> tuple:
    """(version, index offset, index size). Raises Unreadable."""
    tail_size = min(container.size, FOOTER_SEARCH_BYTES)
    tail = container.read_at(container.size - tail_size, tail_size)
    at = tail.rfind(MAGIC)
    if at < 0 or at + 24 > len(tail):
        raise Unreadable("no pak footer")
    version, index_offset, index_size = struct.unpack_from("<IQQ", tail, at + 4)
    if version not in KNOWN_VERSIONS:
        raise Unreadable("unknown pak version")
    if version >= 4 and at >= 1 and tail[at - 1]:
        raise Unreadable("encrypted index")
    return version, index_offset, index_size


def skip_flat_entry(cursor, version: int) -> str:
    """One FPakEntry of a flat index; returns the hash it stores for the file. A count read only to size a take is
    bounded by the take itself, which refuses a negative size or one past the buffer."""
    cursor.i64()
    cursor.i64()
    cursor.i64()
    method = cursor.u32()
    if version <= 1:
        cursor.i64()
    sha1 = cursor.take(20)
    if version >= 3:
        if method != 0:
            cursor.take(16 * cursor.i32())
        cursor.take(1)
        cursor.u32()
    return sha1.hex()


def decode_entry(encoded: bytes, at: int, limits: dict) -> tuple:
    """(offset, stored size) of one encoded entry (versions 10 and 11): IPlatformFilePak, DecodePakEntry."""
    cursor = Cursor(encoded, limits, at)
    value = cursor.u32()
    if value & 0x3F == 0x3F:
        cursor.u32()
    method = (value >> 23) & 0x3F
    offset = cursor.u32() if value & (1 << 31) else cursor.i64()
    uncompressed = cursor.u32() if value & (1 << 30) else cursor.i64()
    size = (cursor.u32() if value & (1 << 29) else cursor.i64()) if method else uncompressed
    return offset, size


def read_files(container, most_files: int) -> list:
    """[(path, locator)]: locator is ("hash", hex) when the index stores the hash, ("entry", offset, size) when it
    sits in front of the data (stored_hash reads it), None when the reader cannot tell. Raises Unreadable."""
    limits = container.limits
    version, index_offset, index_size = read_footer(container)
    cursor = Cursor(container.read_at(index_offset, index_size), limits)
    mount = cursor.fstring()
    entries = cursor.count(most_files)
    if version < 10:
        return [(strip_mount(mount, cursor.fstring()), ("hash", skip_flat_entry(cursor, version)))
                for _ in range(entries)]
    cursor.u64()
    if cursor.u32():
        cursor.take(8 + 8 + 20)
    if not cursor.u32():
        raise Unreadable("no full directory index")
    directory_offset, directory_size = cursor.i64(), cursor.i64()
    cursor.take(20)
    encoded = cursor.take(cursor.i32())
    directory = Cursor(container.read_at(directory_offset, directory_size), limits)
    files = []
    for _ in range(directory.count(most_files)):
        folder = directory.fstring()
        for _ in range(directory.count(most_files - len(files))):
            name = directory.fstring()
            where = directory.i32()
            locator = ("entry", *decode_entry(encoded, where, limits)) if where >= 0 else None
            files.append((strip_mount(mount, folder + name), locator))
    return files


def stored_hash(container, locator):
    """The hash the pak stores for one file's bytes, or None when the entry in front of its data does not match."""
    if locator is None:
        return None
    if locator[0] == "hash":
        return locator[1]
    _kind, offset, size = locator
    head = container.read_at(offset, ENTRY_HEAD_BYTES)
    return head[ENTRY_HASH].hex() if struct.unpack_from("<q", head, 8)[0] == size else None
