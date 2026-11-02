# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Keys used by more than one enabled mod, the last section of the conflicts (conception, section 5, « Les conflits de
touches »). A key's fields read in mods_base 1.12 (keybinds.py): key, is_enabled, display_name, identifier and
is_rebindable."""

from .mod_fields import enabled_list, plain_fields, short

KEY_FIELDS = ("key", "is_enabled", "display_name", "identifier", "is_rebindable")


def mod_keys(mod, limits: dict) -> tuple:
    """(mod name, [(key, key's name, fixed)], cut) for an enabled mod; (None, [], False) for a disabled one.
    Raises ValueError for an unreadable one."""
    name, binds = enabled_list(mod, "keybinds", limits)
    if name is None:
        return None, [], False
    keys = []
    for bind in binds[:limits["maxKeysPerMod"]]:
        values = plain_fields(bind, KEY_FIELDS)
        if values is None:
            raise ValueError("unreadable key")
        key, key_enabled, display, identifier, rebindable = values
        if key_enabled is True and isinstance(key, str) and key:
            keys.append((short(key, limits["maxName"]), short(display or identifier, limits["maxName"]),
                         rebindable is False))
    return name, keys, len(binds) > limits["maxKeysPerMod"]


def find(mods: list, limits: dict) -> dict:
    """{'entries': [{'name': key, 'items': [{'mod', 'name', 'fixed'}], 'more'}], 'mods', 'keys', 'unreadable' (the
    mods' places in the list), 'partial': mods or keys past their bounds were not looked at}. Two keys are the same when their names match in any case, as the engine
    compares key names (deduction). Two keys of one mod on the same key are its author's choice (one on press, one on
    release), not a conflict."""
    by_key, unreadable = {}, set()
    counted = keys_seen = 0
    partial = len(mods) > limits["maxMods"]
    for index, mod in enumerate(mods[:limits["maxMods"]]):
        try:
            name, keys, keys_cut = mod_keys(mod, limits)
        except ValueError:
            unreadable.add(index)
            continue
        if name is None:
            continue
        counted += 1
        keys_seen += len(keys)
        partial = partial or keys_cut
        for key, key_name, fixed in keys:
            entry = by_key.setdefault(key.lower(), {"key": key, "first": [], "again": [], "owners": set()})
            # Each mod's first use comes first: a key cut to its first lines still shows two mods (second review,
            # 1 November 2026: one mod's two actions on a key are no conflict).
            entry["again" if index in entry["owners"] else "first"].append({"mod": name, "name": key_name,
                                                                            "fixed": fixed})
            entry["owners"].add(index)
    most = limits["maxItems"]
    entries = []
    for _lower, entry in sorted(by_key.items()):
        uses = entry["first"] + entry["again"]
        if len(entry["owners"]) >= 2:
            entries.append({"name": entry["key"], "items": uses[:most], "more": max(0, len(uses) - most)})
    return {"entries": entries, "mods": counted, "keys": keys_seen, "unreadable": unreadable, "partial": partial}
