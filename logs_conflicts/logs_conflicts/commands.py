# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Console commands declared by more than one enabled mod: the SDK keeps one handler per command, the one of the mod
enabled last, and drops the other without a word (mods_base 1.12, command.py: enable() replaces the command). Only the
commands a mod declares to mods_base are seen; one added straight to unrealsdk is not (conception, section 5,
« Commandes et réglages »)."""

from .mod_fields import enabled_list, plain_fields, short


def find(mods: list, limits: dict) -> dict:
    """{'entries': [{'name': command, 'items': [mod name], 'more'}], 'commands', 'unreadable' (the mods' places in the
    list), 'partial': mods or commands past their bounds were not looked at}. Two commands are the same in any case,
    as unrealsdk compares them (inventory, 1 November 2026)."""
    by_command, unreadable, seen = {}, set(), 0
    partial = len(mods) > limits["maxMods"]
    for index, mod in enumerate(mods[:limits["maxMods"]]):
        try:
            name, commands = enabled_list(mod, "commands", limits)
            partial = partial or len(commands) > limits["maxCommandsPerMod"]
            texts = []
            for command in commands[:limits["maxCommandsPerMod"]]:
                fields = plain_fields(command, ("cmd",))
                if fields is None or not isinstance(fields[0], str) or not fields[0]:
                    raise ValueError("unreadable command")
                texts.append(short(fields[0], limits["maxName"]))
        except ValueError:
            unreadable.add(index)
            continue
        if name is None:
            continue
        seen += len(texts)
        for text in texts:
            entry = by_command.setdefault(text.lower(), {"name": text, "mods": [], "owners": set()})
            if index not in entry["owners"]:
                entry["owners"].add(index)
                entry["mods"].append(name)
    most = limits["maxItems"]
    entries = [{"name": entry["name"], "items": entry["mods"][:most], "more": max(0, len(entry["mods"]) - most)}
               for _lower, entry in sorted(by_command.items()) if len(entry["owners"]) >= 2]
    return {"entries": entries, "commands": seen, "unreadable": unreadable, "partial": partial}
