# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Hides the player's user name in the log, once, as it is read: the page shows and copies the same masked text
(Kevin, 28 October 2026: "yes, we will mask the name"). Only the name inside a path of the player's home folder is
replaced, written with either kind of slash, URL-encoded or not, on any drive and in any case: a user name can be a
common word ("Game", "Admin"), and replacing it everywhere would damage the log (conception, section 5)."""

import re
from pathlib import PureWindowsPath

SEPARATOR = r"(?:[\\/]+|%5[cC]|%2[fF])"
DRIVE = re.compile(r"^[A-Za-z]:$")


def home_pattern(home: str):
    """The pattern of the home folder's path with the user name in group 2, or None when the home cannot be read."""
    if not isinstance(home, str) or not home.strip():
        return None
    path = PureWindowsPath(home.strip())
    parts = [part.rstrip("\\/") for part in path.parts if part.rstrip("\\/")]
    if len(parts) < 2:
        return None
    # The same home on another drive is the same name.
    parent = SEPARATOR.join("[A-Za-z]:" if DRIVE.match(part) else re.escape(part) for part in parts[:-1])
    name = re.escape(parts[-1]).replace(r"\ ", "(?: |%20)")
    # The name ends at a separator, a space or the line's end: "Kevin2" and "Kevin.doe" are other names, while the
    # dot of "C:\Users\Kevin." ends a sentence.
    return re.compile(f"({parent}{SEPARATOR})({name})(?![\\w-]|\\.[\\w-])", re.IGNORECASE)


def home_patterns(homes) -> tuple:
    """One pattern per distinct readable home, in the order given; homes differing only in case are one."""
    patterns = []
    for home in homes:
        pattern = home_pattern(home)
        if pattern is not None and all(pattern.pattern.lower() != known.pattern.lower() for known in patterns):
            patterns.append(pattern)
    return tuple(patterns)


def linux_homes(environ) -> list:
    """Under Proton (Steam Deck, Linux), the player's real home, as Wine names it: the game's own paths go through
    Z:\\home\\<name> or /home/<name>, while Windows' home is C:\\users\\steamuser (security audit, 1 November 2026;
    names from Wine's environment, not seen in game)."""
    homes = []
    wine_home = environ.get("WINEHOMEDIR", "")
    if wine_home:
        homes.append(wine_home[4:] if wine_home.startswith("\\??\\") else wine_home)
    user = environ.get("WINEUSERNAME", "")
    if user and "\\" not in user and "/" not in user:
        homes.append("/home/" + user)
    return homes


def mask(text: str, patterns, replacement: str) -> tuple:
    """(masked text, number of replacements)."""
    masked, _join, count, _after = mask_joined(text, "", patterns, replacement)
    return masked, count


def mask_joined(first: str, second: str, patterns, replacement: str) -> tuple:
    """(masked text, where first ends in it, replacements in first, replacements in second). The log is cut between
    first and second: a path cut in two is masked whole before the cut is made again, and a name masked across the
    cut stays with the text before it."""
    text, join, before, after = first + second, len(first), 0, 0
    for pattern in patterns:
        pieces, last, length = [], 0, 0
        moved = join
        for found in pattern.finditer(text):
            pieces.append(text[last:found.start()])
            length += found.start() - last
            new = found.group(1) + replacement
            if found.end() <= join:
                moved += len(new) - (found.end() - found.start())
                before += 1
            elif found.start() < join:
                moved = length + len(new)
                before += 1
            else:
                after += 1
            pieces.append(new)
            length += len(new)
            last = found.end()
        pieces.append(text[last:])
        text, join = "".join(pieces), moved
    return text, join, before, after
