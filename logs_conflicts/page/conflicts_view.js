/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The conflicts view as plain text, from the service's answer: the state lines, then each section that has conflicts,
// in order of severity, with its title, what the conflict does and what to do, then its entries (conception,
// section 5, « Les conflits entre mods »). A section without conflicts is not shown: six titles followed by "none"
// read as six problems. Pure, tested in node.

// The answer's shape, checked before any of it is shown: a list per section, and the counts.
function lcConflictsAnswer(answer, page) {
    return Boolean(answer && answer.state === "ok" && answer.sections && answer.checked && answer.unreadable
        && page.conflictSections.every((name) => Array.isArray(answer.sections[name])));
}

// {status: [lines], sections: [{title, help: [lines], blocks: [{key, lines}]}]}
function lcConflictsView(found, page) {
    const states = page.states;
    const order = page.conflictSections;
    let count = 0;
    for (const name of order) count += found.sections[name].length;
    const status = [count ? lcFill(states.conflictsFound, { count: count }) : states.conflictsNone,
                    lcFill(states.checked, found.checked)];
    if (found.log !== "read") status.push(states.logNotRead);
    if (found.paks !== "read") status.push(states.paksMissing);
    if (found.unreadable.mods > 0) status.push(lcFill(states.unreadable, { count: found.unreadable.mods }));
    if (found.unreadable.containers > 0) {
        status.push(lcFill(states.containersUnreadable, { count: found.unreadable.containers }));
    }
    if (found.partial) status.push(lcFill(states.partial, page.conflictBounds));
    if (found.cut) status.push(states.listCut);
    const sections = [];
    for (const name of order) {
        const entries = found.sections[name];
        if (!entries.length) continue;
        // What a conflict does and how to fix it, right above its entries: the bare list was not understood (Kevin,
        // after trial 2: "I don't understand what the lines mean").
        sections.push({ title: states[name + "Title"],
                        help: name === "keys" ? [states.keysHelp, states.keysFix] : [states[name + "Help"]],
                        blocks: entries.map((entry) => lcBlock(name, entry, page)) });
    }
    return { status: status, sections: sections };
}

function lcBlock(name, entry, page) {
    const states = page.states;
    const items = entry.items;
    let key = entry.name;
    let lines;
    if (name === "failed") {
        const reason = page.conflictReasons[entry.reason] || ["", ""];
        lines = [states[reason[0]] || ""];
        if (items.length && reason[1]) lines.push(lcFill(states[reason[1]], { detail: items[0] }));
    } else if (name === "twice") {
        lines = items.map((item, at) => lcFill(at === 0 ? states.loadedCopy : states.ignoredCopy,
            { copy: item.folder ? lcFill(states.folderCopy, { copy: item.copy }) : item.copy }));
    } else if (name === "files") {
        key = entry.containers.join(", ");
        if (entry.moreContainers > 0) key += " " + lcFill(states.moreLine, { more: entry.moreContainers });
        lines = [lcFill(entry.identical ? states.filesSummaryIdentical : states.filesSummary,
            { winner: entry.winner, count: entry.count, identical: entry.identical })].concat(items);
    } else if (name === "settings") {
        lines = items.map((item) => (item.dropped ? lcFill(states.droppedLine, { mod: item.mod }) : item.mod));
    } else if (name === "keys") {
        key = lcKeyName(entry.name, page);
        lines = items.map((use) => lcFill(use.fixed ? states.fixedLine : states.useLine,
            { mod: use.mod, name: use.name }));
    } else {
        lines = items.slice();
    }
    if (entry.more > 0) lines.push(lcFill(states.moreLine, { more: entry.more }));
    return { key: key, lines: lines };
}
