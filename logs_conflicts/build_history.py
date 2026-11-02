# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The paks build_pak.py has made, so install_pak.py may replace or remove an earlier one and nothing else. This module
alone reads and writes build/history.json.

Written whole through a temporary file then renamed: an interrupted write never leaves half a file. Read tolerantly:
the list of the first builds (no version) is still taken; an unreadable file gives no earlier build and a note,
which the callers print. Unknown hashes then count as another file's, which nothing replaces or deletes."""

import json
import os
from pathlib import Path

VERSION = 1
MAX_BUILDS = 50


def read(path: Path) -> tuple:
    """(hashes, note): note is None, or why the file could not be used."""
    if not path.exists():
        return [], None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        return [], f"history unreadable ({type(error).__name__}): earlier builds unknown"
    hashes = data if isinstance(data, list) else data.get("hashes") if isinstance(data, dict) else None
    if not isinstance(hashes, list) or not all(isinstance(item, str) for item in hashes):
        return [], "history malformed: earlier builds unknown"
    return hashes[-MAX_BUILDS:], None


def remember(path: Path, pak_sha256: str):
    """Adds a build; returns read()'s note, or None."""
    hashes, note = read(path)
    if pak_sha256 not in hashes:
        hashes.append(pak_sha256)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps({"version": VERSION, "hashes": hashes[-MAX_BUILDS:]}, indent=2) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)
    return note
