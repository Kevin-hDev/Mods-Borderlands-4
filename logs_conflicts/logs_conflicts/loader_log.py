# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What the SDK's mod loader (sdk_mods/__main__.py) wrote at launch: the mods that did not load and the mods installed
twice (conception, section 5, « Le journal »). Its lines are told by their file, written with forward slashes where
the mods' have backslashes, and its messages by their text, never by their line number, which changes with the SDK.
Messages read in the loader on 1 November 2026; line shapes seen in players' logs."""

import re
from pathlib import PureWindowsPath

# Matched before the line's first "|", where a message cannot reach: Windows refuses "|" in a file name. Searched
# anywhere in the line, another mod's message quoting a loader line passed for one (review, 2 November 2026).
LOADER_LINE = re.compile(r"[^|]*sdk_mods/__main__\.py@(\d+)\s+(ERR|WARN)\| ?(.*)$")
FAILED = re.compile(r"^Failed to import mod '(.+)'$")
REFUSED = (
    ("folder", re.compile(r"^'(.+)' is not a valid python module")),
    ("file", re.compile(r"^'(.+)' does not appear to be valid, and has been ignored\.(?: Is it supposed to be called "
                        r"'(.+)'\?)?$")),
    ("nested", re.compile(r"^'(.+)' appears to be double nested")),
)
TWICE = re.compile(r"^Found multiple versions of mod '(.+)'\. In order of priority:$")
SDKMOD = ".sdkmod"


def loader_lines(text: str) -> list:
    """[(line number in the loader, level, message)] of the loader's lines, in order."""
    found = []
    for line in text.splitlines():
        match = LOADER_LINE.match(line)
        if match:
            found.append((match.group(1), match.group(2), match.group(3).rstrip()))
    return found


def block(lines: list, start: int, level: str) -> list:
    """The messages of the block starting at start: the following lines of that level written by one same line of
    the loader."""
    if start >= len(lines):
        return []
    number = lines[start][0]
    found = []
    for line_number, line_level, message in lines[start:]:
        if line_number != number or line_level != level:
            break
        found.append(message)
    return found


def parse(text: str, limits: dict, mask) -> dict:
    """{'failed': [{'name', 'reason', 'items'}], 'twice': [{'name', 'items': [{'copy', 'folder'}], 'more'}], 'cut'}.
    mask: the text with the player's name hidden. Errors keep their last line only: the lines of the traceback
    carry paths. A mod is listed once: the SDK writes its first lines a second time once the console is ready (a
    player's log of 15 October 2026 holds each of them twice, to the millisecond)."""
    lines = loader_lines(text)
    found = {"failed": {}, "twice": {}}
    most, cut = limits["maxMods"], False

    def clean(value: str, limit: int) -> str:
        return mask(value)[:limit]

    def keep(section: str, key: tuple, entry) -> None:
        nonlocal cut
        if key in found[section]:
            return
        if len(found[section]) == most:
            cut = True
            return
        found[section][key] = entry()

    for at, (_number, level, message) in enumerate(lines):
        # A loader message names one file or folder; a longer one is none of them, and the patterns' cost grows with
        # the square of a message's length (review, 2 November 2026: 3 s for 320 KiB).
        if len(message) > limits["maxLoaderMessage"]:
            continue
        if level == "ERR" and (match := FAILED.match(message)):
            errors = [line for line in block(lines, at + 1, "ERR") if line.strip()]
            keep("failed", ("import", match.group(1)),
                 lambda: {"name": clean(match.group(1), limits["maxName"]), "reason": "import",
                          "items": [clean(errors[-1].strip(), limits["maxError"])] if errors else []})
            continue
        for reason, pattern in REFUSED:
            refused = pattern.match(message) if level == "ERR" else None
            if refused:
                hint = refused.group(2) if reason == "file" else None
                keep("failed", (reason, refused.group(1)),
                     lambda: {"name": clean(refused.group(1), limits["maxName"]), "reason": reason,
                              "items": [clean(hint, limits["maxName"])] if hint else []})
                break
        if level == "WARN" and (match := TWICE.match(message)):
            # A path's last part only: the folders above it hold the player's name.
            copies = [PureWindowsPath(path).name for path in block(lines, at + 1, "WARN")]
            keep("twice", (match.group(1),),
                 lambda: {"name": clean(match.group(1), limits["maxName"]),
                          "items": [{"copy": clean(copy, limits["maxName"]),
                                     "folder": not copy.lower().endswith(SDKMOD)}
                                    for copy in copies[:limits["maxItems"]]],
                          "more": max(0, len(copies) - limits["maxItems"])})
    return {"failed": list(found["failed"].values()), "twice": list(found["twice"].values()), "cut": cut}
