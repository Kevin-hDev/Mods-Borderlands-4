# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The file list of an IoStore container (.utoc), versions 2 to 8, as written by the engine (IoContainerHeader.h,
IoStore.cpp, UE 5.5.4) and by retoc: the header, then its tables in order, the directory index and the chunk metas.
Read only; checked against retoc on the game's containers and our mods' at the inventory (1 November 2026). An
encrypted directory index is unreadable."""

import struct

from .pak_reading import Cursor, Unreadable, strip_mount

MAGIC = b"-==--==--==--==-"
HEADER_BYTES = 144
KNOWN_VERSIONS = range(2, 9)
FLAG_ENCRYPTED = 0x2
FLAG_SIGNED = 0x4
FLAG_INDEXED = 0x8
NO_INDEX = 0xFFFFFFFF
CHUNK_ID_BYTES = 12
CHUNK_PLACE_BYTES = 10
HASH_BYTES = 20


def walk(buffer: bytes, limits: dict, most_files: int) -> list:
    """[(path, chunk index)] of a directory index (FIoDirectoryIndexResource). Raises Unreadable on a loop, an index
    outside its table, or more files than most_files."""
    cursor = Cursor(buffer, limits)
    mount = cursor.fstring()
    # Each count bounded by what the bytes left can hold (16 a folder, 12 a file, 4 at least a string), and the files
    # by the budget: a count the index cannot back is refused before its table is built (review, 2 November 2026).
    folders = [cursor.unpack("<4I") for _ in range(cursor.count(cursor.left() // 16))]
    files = [cursor.unpack("<3I") for _ in range(cursor.count(min(most_files, cursor.left() // 12)))]
    strings = [cursor.fstring() for _ in range(cursor.count(cursor.left() // 4))]
    # Every index pushed below was checked against the table first, and the root exists when the table is not empty.
    found, seen, stack = [], set(), [(0, "")] if folders else []
    while stack:
        index, prefix = stack.pop()
        if index in seen:
            raise Unreadable("directory index loops")
        seen.add(index)
        name, first_child, _sibling, first_file = folders[index]
        here = prefix if name == NO_INDEX else f"{prefix}{text(strings, name)}/"
        file_index = first_file
        while file_index != NO_INDEX:
            if file_index >= len(files) or len(found) >= len(files):
                raise Unreadable("file list loops or points outside")
            file_name, next_file, chunk = files[file_index]
            found.append((strip_mount(mount, here + text(strings, file_name)), chunk))
            file_index = next_file
        child, steps = first_child, 0
        while child != NO_INDEX:
            steps += 1
            if child >= len(folders) or steps > len(folders):
                raise Unreadable("directory siblings loop or point outside")
            stack.append((child, here))
            child = folders[child][2]
    return found


def text(strings: list, index: int) -> str:
    if index >= len(strings):
        raise Unreadable("name outside the string table")
    return strings[index]


def read_files(container, most_files: int) -> list:
    """[(path, hash hex or None)]: the hash the container stores for the file's chunk. Raises Unreadable."""
    limits = container.limits
    head = container.read_at(0, HEADER_BYTES)
    if head[:16] != MAGIC or head[16] not in KNOWN_VERSIONS:
        raise Unreadable("no utoc header of a known version")
    version = head[16]
    header_size, chunks, blocks, block_bytes, methods, method_bytes, _block_size, directory_size, _parts = \
        struct.unpack_from("<9I", head, 20)
    flags = head[80]
    seeds, = struct.unpack_from("<I", head, 84)
    without_hash, = struct.unpack_from("<I", head, 96)
    if header_size != HEADER_BYTES:
        raise Unreadable("unknown header size")
    if not flags & FLAG_INDEXED or not directory_size:
        return []
    if flags & FLAG_ENCRYPTED:
        raise Unreadable("encrypted directory index")
    pos = HEADER_BYTES + chunks * (CHUNK_ID_BYTES + CHUNK_PLACE_BYTES)
    pos += (seeds * 4 if version >= 4 else 0) + (without_hash * 4 if version >= 5 else 0)
    pos += blocks * block_bytes + methods * method_bytes
    if flags & FLAG_SIGNED:
        hash_size = struct.unpack("<i", container.read_at(pos, 4))[0]
        if hash_size < 0:
            raise Unreadable("negative signature size")
        pos += 4 + 2 * hash_size + blocks * HASH_BYTES
    found = walk(container.read_at(pos, directory_size), limits, most_files)
    pos += directory_size
    meta_bytes = (container.size - pos) // chunks if chunks else 0
    metas = container.read_at(pos, meta_bytes * chunks) if meta_bytes >= HASH_BYTES else b""
    return [(path, metas[chunk * meta_bytes:chunk * meta_bytes + HASH_BYTES].hex()
             if metas and chunk < chunks else None) for path, chunk in found]
