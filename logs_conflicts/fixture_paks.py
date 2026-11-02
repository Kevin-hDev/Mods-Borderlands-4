# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests only: small game containers built in memory, laid out as the engine writes them (IPlatformFilePak.h and
IoContainerHeader.h, UE 5.5.4): legacy .pak versions 1 to 8 (flat index) and 11 (full directory index, each file's
entry written in front of its data), and IoStore .utoc versions 2 to 8. The reader was checked on real containers at the
inventory; these let each of its checks be broken on purpose."""

import hashlib
import struct

PAK_MAGIC = 0x5A6F12E1
TOC_MAGIC = b"-==--==--==--==-"
NO_INDEX = 0xFFFFFFFF
FLAG_ENCRYPTED, FLAG_SIGNED, FLAG_INDEXED = 0x2, 0x4, 0x8
MOUNT = "../../../"


def fstring(text: str) -> bytes:
    if not text:
        return struct.pack("<i", 0)
    try:
        raw = text.encode("latin-1") + b"\0"
        return struct.pack("<i", len(raw)) + raw
    except UnicodeEncodeError:
        raw = text.encode("utf-16-le") + b"\0\0"
        return struct.pack("<i", -(len(raw) // 2)) + raw


def pak_footer(version: int, index_offset: int, index_size: int, encrypted: bool = False) -> bytes:
    """FPakInfo: key guid, encrypted flag, magic, version, index offset and size, index hash, method names."""
    names = b"".join(name.ljust(32, b"\0") for name in (b"Zlib", b"", b"", b"", b""))
    return (b"\0" * 16 + bytes([int(encrypted)]) + struct.pack("<IIQQ", PAK_MAGIC, version, index_offset, index_size)
            + b"\0" * 20 + names)


def pak_entry(size: int, digest: bytes, stored_size: int = None) -> bytes:
    """FPakEntry as written in front of a file's data, and in a flat index: offset, sizes, method, hash, flags,
    block size."""
    stored = size if stored_size is None else stored_size
    return struct.pack("<qqqI", 0, stored, size, 0) + digest + b"\0" + struct.pack("<I", 0)


def pak_v11(files, mount: str = MOUNT, encrypted: bool = False, full_directory: bool = True, wrong_size=(),
            path_hash: bool = False, deleted=(), outside=(), repeat: int = 1) -> bytes:
    """files: [(path under the mount, bytes)]. wrong_size: paths whose entry in front of the data says another size.
    path_hash: the index also holds a path hash index. deleted: paths listed without an entry (-1). outside: paths
    whose entry points past the end of the file. repeat: the directory lists every folder that many times, more
    names than the index has entries, as a lying index could."""
    body, placed = b"", []
    for path, data in files:
        placed.append((path, len(body), len(data)))
        body += pak_entry(len(data), hashlib.sha1(data).digest(),
                          len(data) + 1 if path in wrong_size else None) + data
    encoded, where = b"", {}
    for path, offset, size in placed:
        where[path] = len(encoded)
        # Offset and size fit in 32 bits, no compression, no block size.
        encoded += struct.pack("<III", (1 << 31) | (1 << 30), 10 ** 9 if path in outside else offset, size)
    folders = {}
    for path, _offset, _size in placed:
        folder, _slash, name = path.rpartition("/")
        folders.setdefault(folder + "/" if folder else "/", []).append((name, -1 if path in deleted else where[path]))
    directory = struct.pack("<i", len(folders) * repeat)
    for folder, names in list(folders.items()) * repeat:
        directory += fstring(folder) + struct.pack("<i", len(names))
        directory += b"".join(fstring(name) + struct.pack("<i", at) for name, at in names)
    directory_offset = len(body)
    body += directory
    index = fstring(mount) + struct.pack("<iQI", len(placed), 0, int(path_hash)) + b"\0" * (36 if path_hash else 0)
    index += struct.pack("<I", int(full_directory))
    if full_directory:
        index += struct.pack("<qq", directory_offset, len(directory)) + b"\0" * 20
    index += struct.pack("<i", len(encoded)) + encoded + struct.pack("<i", 0)
    index_offset = len(body)
    return body + index + pak_footer(11, index_offset, len(index), encrypted)


def flat_entry(data: bytes, version: int, compressed: bool) -> bytes:
    """FPakEntry as a flat index stores it: a timestamp up to version 1; from version 3, the compression blocks of a
    compressed file, then flags and block size."""
    entry = struct.pack("<qqqI", 0, len(data), len(data), int(compressed)) + (b"\0" * 8 if version <= 1 else b"")
    entry += hashlib.sha1(data).digest()
    if version >= 3:
        entry += (struct.pack("<i", 2) + b"\0" * 32 if compressed else b"") + b"\0" + struct.pack("<I", 0)
    return entry


def pak_flat(files, version: int = 8, mount: str = MOUNT, compressed: bool = False) -> bytes:
    """A flat index (versions 1 to 8): each file's name and entry, the hash stored in the index."""
    body, index = b"", b""
    for path, data in files:
        index += fstring(path) + flat_entry(data, version, compressed)
        body += pak_entry(len(data), hashlib.sha1(data).digest()) + data
    index = fstring(mount) + struct.pack("<i", len(files)) + index
    return body + index + pak_footer(version, len(body), len(index))


def toc_directory(files, mount: str, edit=None) -> bytes:
    """FIoDirectoryIndexResource: folders (name, first child, next sibling, first file), files (name, next file,
    chunk), strings. Every folder hangs from the root. edit(folders, entries, strings) may break the tables."""
    strings, folders, entries = [], [[NO_INDEX] * 4], []

    def named(text):
        if text not in strings:
            strings.append(text)
        return strings.index(text)

    groups = {}
    for chunk, (path, _digest) in enumerate(files):
        folder, _slash, name = path.rpartition("/")
        groups.setdefault(folder, []).append((name, chunk))
    last_folder = None
    for folder, names in groups.items():
        at = len(folders)
        folders.append([named(folder), NO_INDEX, NO_INDEX, NO_INDEX])
        if last_folder is None:
            folders[0][1] = at
        else:
            folders[last_folder][2] = at
        last_folder, last_file = at, None
        for name, chunk in names:
            entries.append([named(name), NO_INDEX, chunk])
            if last_file is None:
                folders[at][3] = len(entries) - 1
            else:
                entries[last_file][1] = len(entries) - 1
            last_file = len(entries) - 1
    if edit:
        edit(folders, entries, strings)
    buffer = fstring(mount) + struct.pack("<i", len(folders)) + b"".join(struct.pack("<4I", *f) for f in folders)
    buffer += struct.pack("<i", len(entries)) + b"".join(struct.pack("<3I", *e) for e in entries)
    return buffer + struct.pack("<i", len(strings)) + b"".join(fstring(text) for text in strings)


def utoc(files, mount: str = MOUNT, flags: int = FLAG_INDEXED, version: int = 8, edit=None, signature=None,
         header_size: int = 144, seeds: int = 0, without_hash: int = 0, blocks: int = 0, methods: int = 0,
         no_directory: bool = False, meta_bytes: int = 21) -> bytes:
    """files: [(path under the mount, 20-byte hash)], one chunk each, its meta the hash and a flag byte.
    signature: the signature's hash size when the container is signed (its two hashes and one per block come before
    the directory). seeds, without_hash, blocks, methods: the counts of the tables before the directory, each table
    written only from the version that has it (seeds from 4, chunks without hash from 5). no_directory: the index
    flag set, the index empty. meta_bytes: each chunk's meta, cut below a hash's 20 bytes to make the hashes
    unreadable."""
    directory = b"" if no_directory else toc_directory(files, mount, edit)
    count = len(files)
    head = bytearray(144)
    head[0:16] = TOC_MAGIC
    head[16] = version
    struct.pack_into("<9I", head, 20, header_size, count, blocks, 12, methods, 32, 65536, len(directory), 1)
    struct.pack_into("<Q", head, 56, 0x1234)
    head[80] = flags | (FLAG_SIGNED if signature is not None else 0)
    struct.pack_into("<I", head, 84, seeds)
    struct.pack_into("<I", head, 96, without_hash)
    tables = b"".join(struct.pack("<Q", chunk) + b"\0\0\0\x01" for chunk in range(count)) + b"\0" * (10 * count)
    tables += b"\0" * ((4 * seeds if version >= 4 else 0) + (4 * without_hash if version >= 5 else 0))
    tables += b"\0" * (12 * blocks + 32 * methods)
    signed = b"" if signature is None else (struct.pack("<i", signature)
                                            + b"\0" * (2 * max(signature, 0) + 20 * blocks))
    metas = b"".join((digest + b"\0")[:meta_bytes] for _path, digest in files)
    return bytes(head) + tables + signed + directory + metas


def digest(text: str) -> bytes:
    return hashlib.sha1(text.encode("utf-8")).digest()
