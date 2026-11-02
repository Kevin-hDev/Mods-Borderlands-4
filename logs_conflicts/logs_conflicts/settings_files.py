# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Mods saving their settings in the same file (conception, section 5, « Commandes et réglages »). Two forms: both
stay in the mod list and overwrite each other's settings, or mods_base drops the first from the list without a word,
its default (mod_factory.py, deregister_using_settings_file, mods_base 1.12). A dropped mod is seen only while a
top-level module keeps it in one of its variables; it is recognised by its class alone, nothing of it is run."""

import types

from .mod_fields import path_field, plain_fields, short


def described(mod, limits: dict):
    """(mod name, (file name, key)) or None when the mod saves no settings. Raises ValueError when unreadable."""
    fields = plain_fields(mod, ("name",))
    if fields is None or not isinstance(fields[0], str):
        raise ValueError("unreadable mod")
    found = path_field(mod, "settings_file")
    if found is None:
        return None
    file_name, key = found
    return short(fields[0], limits["maxName"]), (short(file_name, limits["maxName"]), key)


def dropped(modules: list, mod_class: type, kept: list, limits: dict) -> list:
    """The mods found in top-level modules' variables that are not in the mod list. modules: [(name, module)], a copy
    of sys.modules taken by the caller."""
    known = {id(mod) for mod in kept}
    found, seen = [], set()
    for name, module in modules[:limits["maxModules"]]:
        # Exact type: a module object of another class could run code when its variables are read.
        if "." in name or type(module) is not types.ModuleType:
            continue
        for value in list(module.__dict__.values())[:limits["maxModuleValues"]]:
            # mods_base's Mod is a plain dataclass: issubclass walks the value's class order without running code.
            if issubclass(type(value), mod_class) and id(value) not in known and id(value) not in seen:
                seen.add(id(value))
                found.append(value)
    return found


def find(mods: list, modules: list, mod_class: type, limits: dict) -> dict:
    """{'entries': [{'name': file name, 'items': [{'mod', 'dropped'}], 'more'}], 'unreadable' (the mods' places in
    the list)}."""
    by_file, unreadable = {}, set()
    for index, mod in enumerate(mods[:limits["maxMods"]]):
        try:
            found = described(mod, limits)
        except ValueError:
            unreadable.add(index)
            continue
        if found is not None:
            name, (file_name, key) = found
            by_file.setdefault(key, {"name": file_name, "items": []})["items"].append({"mod": name, "dropped": False})
    for mod in dropped(modules, mod_class, mods, limits):
        try:
            found = described(mod, limits)
        except ValueError:
            continue
        # Only a file a listed mod uses: a mod object no one listed is no conflict of the player's mods.
        if found is not None and found[1][1] in by_file:
            by_file[found[1][1]]["items"].append({"mod": found[0], "dropped": True})
    most = limits["maxItems"]
    entries = [{"name": entry["name"], "items": entry["items"][:most], "more": max(0, len(entry["items"]) - most)}
               for _key, entry in sorted(by_file.items()) if len(entry["items"]) >= 2]
    return {"entries": entries, "unreadable": unreadable}
