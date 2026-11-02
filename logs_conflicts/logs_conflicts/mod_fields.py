# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Fields of mods_base's objects read statically, without running any mod's code: the service's thread reads them,
and another mod's code must not touch the game from there (conception, section 5). A field that is not a plain value
(a property, say) makes its object unreadable. Field names read in mods_base 1.12 (mod.py, keybinds.py, command.py,
1 and 2 November 2026)."""

import inspect
from pathlib import PosixPath, PurePosixPath, PureWindowsPath, WindowsPath

# Exact types only: a subclass runs its own code when read, indexed or turned into text.
PLAIN = (str, bool, type(None), list, tuple)
PATHS = (PosixPath, PurePosixPath, PureWindowsPath, WindowsPath)


def plain_fields(owner, names: tuple):
    """The fields' values, or None when one is missing or not a plain value."""
    values = []
    for name in names:
        try:
            value = inspect.getattr_static(owner, name)
        except AttributeError:
            return None
        if type(value) not in PLAIN:
            return None
        values.append(value)
    return values


def short(text, limit: int) -> str:
    return text[:limit] if isinstance(text, str) else ""


def enabled_list(mod, field: str, limits: dict) -> tuple:
    """(mod name, the list in field) for an enabled mod, (None, ()) for a disabled one. Raises ValueError for an
    unreadable one."""
    fields = plain_fields(mod, ("name", "is_enabled", field))
    if fields is None or not isinstance(fields[0], str) or not isinstance(fields[1], bool) \
            or not isinstance(fields[2], (list, tuple)):
        raise ValueError("unreadable mod")
    name, enabled, items = fields
    return (short(name, limits["maxName"]), items) if enabled else (None, ())


def path_field(owner, name: str):
    """(file name, key to compare) of a path field, None when it is unset. Raises ValueError when it is not a path."""
    try:
        value = inspect.getattr_static(owner, name)
    except AttributeError:
        raise ValueError("no such field") from None
    if value is None:
        return None
    if type(value) not in PATHS:
        raise ValueError("not a path")
    return value.name, str(value).replace("\\", "/").lower()
