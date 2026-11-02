# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The conflicts between the player's mods, section by section in order of severity, as the page lists them
(conception, section 5, « Les conflits entre mods »; Kevin, 1 November 2026: « oui je suis d'accord on va ajouter tout
ça, go »). Runs on the service's thread and touches no game object: mods_base's objects are read statically, the log
and the paks from the disk."""

import json

from . import commands, keys, loader_log, settings_files


def encoded_size(value) -> int:
    """Its size in the answer, as protocol.payload writes it, with the comma that follows it in a list."""
    return len(json.dumps(value, separators=(",", ":"), ensure_ascii=True)) + 1


def entry_lines(entry: dict) -> int:
    """The page's lines for an entry, at most: its title, the line saying what it is, its items, and the line of
    those not listed."""
    return 2 + len(entry["items"]) + (1 if entry.get("more") else 0)


def fit(sections: dict, constants: dict) -> tuple:
    """(sections kept, cut). One bound for the whole list, in lines and in bytes: an entry is kept whole or not at all,
    in order of severity, and the first one that does not fit cuts the list there (conception: two bounds side by side
    would let the answer pass their sum, and the order keeps what matters most)."""
    limits = constants["conflicts"]
    lines = limits["maxListedLines"]
    budget = constants["http"]["maxConflictsResponseBytes"] - limits["answerMarginBytes"]
    kept = {name: [] for name in limits["sections"]}
    for name in limits["sections"]:
        for entry in sections[name]:
            need, size = entry_lines(entry), encoded_size(entry)
            if need > lines or size > budget:
                return kept, True
            kept[name].append(entry)
            lines -= need
            budget -= size
    return kept, False


def masker(parts: dict, constants: dict):
    """The Windows user name hidden in a text the page shows, as in the log view."""
    replacement, patterns, mask = constants["masking"]["replacement"], parts["mask_patterns"], parts["masking"].mask
    return lambda value: mask(value, patterns, replacement)[0]


def loader_report(parts: dict, constants: dict, mask) -> tuple:
    """(the loader's findings, the log's state: 'read', or the log module's code)."""
    log_file = parts["log_file"]
    try:
        text = log_file.read_start(parts["log_path"], constants["conflicts"]["logStartBytes"])
    except log_file.LogError as error:
        return {"failed": [], "twice": [], "cut": False}, error.code
    return loader_log.parse(text, constants["conflicts"], mask), "read"


def tail(text: str, most: int) -> str:
    """The text's end within most characters: a file's or a container's own name is at its end."""
    return text if len(text) <= most else "..." + text[-(most - 3):]


def shown_files(entries: list, mask, limits: dict) -> list:
    """New entries, the kept scan left as it is: names and paths masked as the log is, then cut to their bounds, so
    that one entry alone cannot pass the answer's bound. Masked first: cut first, a home path could lose the start
    that tells it (review, 2 November 2026)."""
    def name(value: str) -> str:
        return tail(mask(value), limits["maxName"])

    return [{**entry, "containers": [name(value) for value in entry["containers"]], "winner": name(entry["winner"]),
             "items": [tail(mask(path), limits["maxPath"]) for path in entry["items"]]} for entry in entries]


def gather(parts: dict, constants: dict, clock) -> tuple:
    """(answer, trace). parts: 'mods' and 'modules' (callables giving mods_base's list and a copy of sys.modules),
    'modClass', 'paks' (pak_overlaps.PakScan), 'log_file', 'log_path', 'masking', 'mask_patterns'. trace: what the
    service's log line says, never sent to the page."""
    limits = constants["conflicts"]
    started = clock()
    mods = list(parts["mods"]())
    found_keys = keys.find(mods, limits)
    found_commands = commands.find(mods, limits)
    found_settings = settings_files.find(mods, parts["modules"](), parts["modClass"], limits)
    mods_done = clock()
    mask = masker(parts, constants)
    loader, log_state = loader_report(parts, constants, mask)
    log_done = clock()
    paks = parts["paks"].find()
    paks_done = clock()
    sections, cut = fit({"failed": loader["failed"], "twice": loader["twice"],
                         "files": shown_files(paks["entries"], mask, limits),
                         "commands": found_commands["entries"], "settings": found_settings["entries"],
                         "keys": found_keys["entries"]}, constants)
    unreadable = found_keys["unreadable"] | found_commands["unreadable"] | found_settings["unreadable"]
    answer = {"sections": sections,
              "checked": {"mods": found_keys["mods"], "keys": found_keys["keys"],
                          "commands": found_commands["commands"], "containers": paks["containers"]},
              "unreadable": {"mods": len(unreadable), "containers": paks["unreadable"]},
              "log": log_state, "paks": "missing" if paks["missing"] else "read",
              # partial: lists past their bounds, not looked at; cut: conflicts found but not all shown.
              "partial": found_keys["partial"] or found_commands["partial"], "cut": cut or loader["cut"]}
    trace = {"failures": paks["failures"] if paks["fresh"] else [], "modsMs": ms(mods_done - started),
             "logMs": ms(log_done - mods_done), "paksMs": ms(paks_done - log_done)}
    return answer, trace


def ms(seconds: float) -> int:
    return round(seconds * 1000)
