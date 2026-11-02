# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What COPY puts in the clipboard: the view the page shows, in English whatever the game's language, under a header
line, with the SDK's own key names (conception, section 5, « Copier »): it goes to mod authors. Its lines are the page's
English texts, laid out as page/conflicts_view.js lays them out: a second set of texts drifted from the page's (review,
2 November 2026)."""


def log_text(shown: dict, constants: dict, version: str, file_name: str) -> str:
    """The log shown, the cut said where it happened."""
    texts, mod = constants["copyTexts"], constants["modName"]
    header = texts["logHeader"].format(mod=mod, version=version, time=shown["readAt"], file=file_name,
                                       size=shown["size"])
    if not shown["cut"]:
        return header + "\n" + shown["head"] + shown["tail"]
    middle = texts["middle"].format(cut=shown["cut"], mod=mod)
    return (header + texts["logCut"].format(cut=shown["cut"]) + "\n" + shown["head"] + "\n" + middle + "\n"
            + shown["tail"])


def bounds(constants: dict) -> dict:
    """The bounds the partial state names, for the page and for COPY."""
    limits = constants["conflicts"]
    return {"mods": limits["maxMods"], "keys": limits["maxKeysPerMod"], "commands": limits["maxCommandsPerMod"]}


def status_lines(shown: dict, constants: dict, states: dict) -> list:
    """The view's state lines, as lcConflictsView writes them."""
    count = sum(len(shown["sections"][name]) for name in constants["conflicts"]["sections"])
    lines = [states["conflictsFound"].format(count=count) if count else states["conflictsNone"],
             states["checked"].format(**shown["checked"])]
    if shown["log"] != "read":
        lines.append(states["logNotRead"])
    if shown["paks"] != "read":
        lines.append(states["paksMissing"])
    for name in ("mods", "containers"):
        if shown["unreadable"][name] > 0:
            text = states["unreadable" if name == "mods" else "containersUnreadable"]
            lines.append(text.format(count=shown["unreadable"][name]))
    if shown["partial"]:
        lines.append(states["partial"].format(**bounds(constants)))
    if shown["cut"]:
        lines.append(states["listCut"])
    return lines


def entry_line(section: str, entry: dict, states: dict, reasons: dict) -> str:
    """An entry on one line, as lcBlock lays it out: its key, then its lines."""
    items, key = entry["items"], entry.get("name", "")
    if section == "failed":
        reason = reasons.get(entry["reason"], ["", ""])
        lines = [states.get(reason[0], "")]
        if items and reason[1]:
            lines.append(states[reason[1]].format(detail=items[0]))
    elif section == "twice":
        lines = [states["loadedCopy" if at == 0 else "ignoredCopy"].format(
            copy=states["folderCopy"].format(copy=item["copy"]) if item["folder"] else item["copy"])
            for at, item in enumerate(items)]
    elif section == "files":
        key = ", ".join(entry["containers"])
        if entry["moreContainers"] > 0:
            key += " " + states["moreLine"].format(more=entry["moreContainers"])
        summary = states["filesSummaryIdentical" if entry["identical"] else "filesSummary"]
        lines = [summary.format(winner=entry["winner"], count=entry["count"], identical=entry["identical"])] + items
    elif section == "settings":
        lines = [states["droppedLine"].format(mod=item["mod"]) if item["dropped"] else item["mod"] for item in items]
    elif section == "keys":
        lines = [states["fixedLine" if use["fixed"] else "useLine"].format(mod=use["mod"], name=use["name"])
                 for use in items]
    else:
        lines = list(items)
    if entry.get("more"):
        lines.append(states["moreLine"].format(more=entry["more"]))
    return key + ": " + " | ".join(lines)


def conflicts_text(shown: dict, constants: dict, version: str) -> str:
    """The header, the state lines, then a title line per section with conflicts and one line per conflict."""
    states, reasons = constants["texts"]["en"]["states"], constants["conflicts"]["reasons"]
    header = constants["copyTexts"]["conflictsHeader"].format(mod=constants["modName"], version=version,
                                                              time=shown["readAt"])
    lines = [header] + status_lines(shown, constants, states)
    for section in constants["conflicts"]["sections"]:
        if shown["sections"][section]:
            lines.append(states[section + "Title"])
            lines.extend(entry_line(section, entry, states, reasons) for entry in shown["sections"][section])
    return "\n".join(lines) + "\n"
