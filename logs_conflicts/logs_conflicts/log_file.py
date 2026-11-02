# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Where the SDK writes its log, and reading it: the service's only border with the disk (conception, section 5).

The folder is the one unrealsdk.dll was loaded from; the name is the SDK's log_file setting, relative to that folder,
else unrealsdk.log. Both checked in game at the feasibility gate (1 November 2026). The path is found once, at the
service's start, and never taken from the page. A long log is shown by its start (the SDK's versions and the mods'
loading) and its end, cut at line ends."""

import os
from pathlib import Path


class LogError(Exception):
    """code: what the page tells the player (constants texts.errors)."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def log_path(dll_folder, config, constants: dict) -> tuple:
    """(path or None, how it was found). config is unrealsdk.config, a dict-like of the SDK's settings."""
    settings = constants["log"]
    if dll_folder is None:
        return None, "no_dll"
    section = config.get("unrealsdk") if hasattr(config, "get") else None
    name = section.get("log_file") if hasattr(section, "get") else None
    if name is None:
        return Path(dll_folder) / settings["defaultFile"], "default"
    if not isinstance(name, str) or not name.strip() or len(name) > settings["maxFileNameLength"] or "\0" in name:
        return None, "bad_setting"
    # An absolute name stays as it is: joining keeps the right-hand side when it is absolute.
    return Path(dll_folder) / name.strip(), "set"


def revision_of(info) -> str:
    return f"{info.st_size}-{info.st_mtime_ns}"


def read(path, known_revision, constants: dict, stat=os.stat, opener=open) -> dict:
    """{'unchanged': True, 'revision'} when the page holds this revision already, else {'head', 'tail', 'afterHead',
    'beforeTail', 'cut', 'size', 'revision'}: the whole log in head, or its start and end with the number of bytes cut
    between them (afterHead and beforeTail: see read_parts; never shown).
    Raises LogError. The SDK writes while we read: only the size taken at stat is read, never more."""
    if path is None:
        raise LogError("log_missing")
    try:
        info = stat(path)
        revision = revision_of(info)
        if revision == known_revision:
            return {"unchanged": True, "revision": revision}
        with opener(path, "rb") as file:
            head, tail, after_head, before_tail = read_parts(file, info.st_size, constants["log"])
    except FileNotFoundError:
        raise LogError("log_missing") from None
    except OSError:
        raise LogError("log_refused") from None
    cut = max(0, info.st_size - len(head) - len(tail))
    text = {name: part.decode("utf-8", "replace")
            for name, part in (("head", head), ("tail", tail), ("afterHead", after_head), ("beforeTail", before_tail))}
    return {**text, "cut": cut, "size": info.st_size, "revision": revision}


def read_start(path, limit: int, opener=open) -> str:
    """The log's first limit bytes as text, cut at its last line end when the log is longer: the mod loader writes
    only at launch, at the start (conception, section 5, « Le journal »). Raises LogError."""
    if path is None:
        raise LogError("log_missing")
    try:
        with opener(path, "rb") as file:
            data = file.read(limit + 1)
    except FileNotFoundError:
        raise LogError("log_missing") from None
    except OSError:
        raise LogError("log_refused") from None
    if len(data) > limit:
        end = data.rfind(b"\n", 0, limit)
        data = data[:end + 1] if end >= 0 else data[:limit]
    return data.decode("utf-8", "replace")


def read_parts(file, size: int, settings: dict) -> tuple:
    """(head, tail, after head, before tail) bytes; tail is empty when the whole file fits. A part cut inside a line
    comes with the bytes on the other side of its cut, for the masking only: a path cut in two must be masked whole
    (security audit, 1 November 2026)."""
    limit = settings["maxBytes"]
    if size <= limit:
        return file.read(size), b"", b"", b""
    head_bytes, margin = settings["headBytes"], settings["maskMarginBytes"]
    start = file.read(head_bytes + margin)
    end = start.rfind(b"\n", 0, head_bytes)
    head_end = end + 1 if end >= 0 else character_start(start, head_bytes, -1)
    head, after_head = start[:head_end], start[head_end:] if end < 0 else b""
    tail_at = size - (limit - len(head))
    before_at = max(len(head), tail_at - margin)
    file.seek(before_at)
    data = file.read(size - before_at)
    split = tail_at - before_at
    line_end = data.find(b"\n", split)
    if 0 <= line_end < len(data) - 1:
        return head, data[line_end + 1:], after_head, b""
    # A tail without a line end is one long line: kept whole rather than shown empty.
    split = character_start(data, split, 1)
    return head, data[split:], after_head, data[:split]


def character_start(data: bytes, at: int, step: int) -> int:
    """at moved, by step (-1 or 1), to the first byte of a UTF-8 character. A cut inside a character decodes each side
    to a replacement mark: the user's name split there escaped the masking (review, 1 November 2026). Three steps at
    most: a character has at most three bytes after its first."""
    for _ in range(3):
        if not 0 < at < len(data) or data[at] & 0xC0 != 0x80:
            break
        at += step
    return at
