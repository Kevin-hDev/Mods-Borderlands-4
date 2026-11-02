# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Bounded reads in the game's containers (.pak, .utoc), shared by pak_legacy.py and pak_iostore.py. A container
downloaded with a mod is untrusted data: every offset, size and count read from it is checked before use, and a
container that breaks a check is unreadable, never trusted further (conception, section 5, « Les paquets »)."""

import os
import struct


class Unreadable(Exception):
    """The container does not have a layout this reader knows, or breaks one of its bounds."""


class ContainerFile:
    """A container opened for reading. Reads only inside the file, never more than the index bound at once."""

    def __init__(self, path, limits: dict, opener=open):
        self.limits = limits
        self.file = opener(path, "rb")
        try:
            self.size = os.fstat(self.file.fileno()).st_size
        except BaseException:
            self.file.close()
            raise

    def read_at(self, offset: int, size: int) -> bytes:
        if offset < 0 or size < 0 or offset + size > self.size or size > self.limits["maxIndexBytes"]:
            raise Unreadable("read outside the file or beyond the index bound")
        self.file.seek(offset)
        data = self.file.read(size)
        if len(data) != size:
            raise Unreadable("file shorter than it said")
        return data

    def close(self) -> None:
        self.file.close()


class Cursor:
    """Sequential reads in a buffer, each one bounded by the buffer."""

    def __init__(self, data: bytes, limits: dict, pos: int = 0):
        self.data = data
        self.limits = limits
        self.pos = pos

    def take(self, size: int) -> bytes:
        if size < 0 or self.pos + size > len(self.data):
            raise Unreadable("truncated buffer")
        chunk = self.data[self.pos:self.pos + size]
        self.pos += size
        return chunk

    def unpack(self, fmt: str) -> tuple:
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))

    def i32(self) -> int:
        return self.unpack("<i")[0]

    def u32(self) -> int:
        return self.unpack("<I")[0]

    def i64(self) -> int:
        return self.unpack("<q")[0]

    def u64(self) -> int:
        return self.unpack("<Q")[0]

    def count(self, most: int) -> int:
        """A count of items, refused above most: the caller's remaining budget, never the file's word."""
        value = self.i32()
        if not 0 <= value <= most:
            raise Unreadable("count out of bounds")
        return value

    def left(self) -> int:
        return len(self.data) - self.pos

    def fstring(self) -> str:
        """An Unreal FString: positive length for Latin-1 bytes, negative for UTF-16 units, both with a final zero."""
        length = self.i32()
        if length == 0:
            return ""
        most = self.limits["maxStringBytes"]
        if length > 0:
            if length > most:
                raise Unreadable("string too long")
            return self.take(length)[:-1].decode("latin-1")
        if -length * 2 > most:
            raise Unreadable("string too long")
        return self.take(-length * 2)[:-2].decode("utf-16-le")


def strip_mount(mount_point: str, path: str) -> str:
    """The path as the game names it, without the "../../../" every container mounts at."""
    full = (mount_point + path).replace("\\", "/")
    while full.startswith("../"):
        full = full[3:]
    return full.lstrip("/")
