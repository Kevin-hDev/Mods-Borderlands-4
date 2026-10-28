/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// Pure helpers of the page: reading the game's row markup, reading Python's answers, writing the page's messages.
// No DOM and no network, so the node tests drive them.

// The options screen keeps its row markup in its own HTML file; reading it there keeps Gearbox's design the
// only authority. Divs are counted so the nested markup of the row is returned whole, or nothing.
function msExtractTemplate(html, marker) {
    if (typeof html !== "string") return null;
    const start = html.indexOf(marker);
    if (start < 0 || html.indexOf(marker, start + 1) >= 0) return null;
    const tag = /<div\b|<\/div>/g;
    tag.lastIndex = start;
    let depth = 0;
    let match;
    while ((match = tag.exec(html)) !== null) {
        depth += match[0] === "</div>" ? -1 : 1;
        if (depth === 0) return html.slice(start, tag.lastIndex);
    }
    return null;
}

function msParseJson(text, config, limit) {
    if (typeof text !== "string" || text.length > (limit || config.http.maxResponseBytes)) return null;
    try {
        const payload = JSON.parse(text);
        return payload && payload.marker === config.marker && payload.version === config.version ? payload : null;
    } catch (error) {
        return null;
    }
}

function msText(value, config) {
    return typeof value === "string" ? value.slice(0, config.catalog.maxLabel) : "";
}

function msNumber(value) {
    return typeof value === "number" && isFinite(value);
}

// Plain text from Python (catalog.py), its line breaks kept; the page shows it as text, never as markup.
function msDescription(value, config) {
    return typeof value === "string" ? value.slice(0, config.catalog.maxDescription) : "";
}

// What the details panel shows for a row, as the options screen shows a row's display and description texts.
function msDetails(entry, label, config) {
    return { title: msText(entry.descriptionTitle, config) || label, text: msDescription(entry.description, config),
        meta: "" };
}

// A mod's version and author, the line under its description.
function msModMeta(mod, config) {
    const page = config.page;
    const version = msText(mod.version, config);
    return [version ? page.versionPrefix + version : "", msText(mod.author, config)]
        .filter((part) => part).join(page.metaSeparator);
}

// A mod's own on/off row: Python gives it the id <mod>_on (catalog.py), never to an option.
function msIsEnabledRow(entry) {
    return entry.kind === "toggle" && typeof entry.id === "string" && entry.id.endsWith("_on");
}

// One of Python's rows as the pieces take it (models.js), or null when it is not exactly what it should be.
function msRow(entry, config, locked, depth, budget) {
    // A mod's on/off row comes without a label from Python: written here, in the game's language.
    const label = msIsEnabledRow(entry) ? config.page.enabledLabel : msText(entry.label, config);
    if (entry.kind === "title") return { kind: "title", label: label };
    if (!new RegExp(config.catalog.idPattern).test(entry.id) || budget.left <= 0) return null;
    budget.left -= 1;
    const row = { kind: entry.kind, ident: entry.id, label: label, locked: locked,
        details: msDetails(entry, label, config) };
    switch (entry.kind) {
    case "slider": {
        const numbers = [entry.min, entry.max, entry.step, entry.value, entry.default];
        if (!numbers.every(msNumber) || entry.min >= entry.max || !Number.isInteger(entry.decimals) ||
            entry.decimals < 0 || entry.decimals > config.catalog.maxDecimals) return null;
        return Object.assign(row, { minvalue: entry.min, maxvalue: entry.max, stepvalue: entry.step,
            decimals: entry.decimals, initial: entry.value, defaultValue: entry.default });
    }
    case "toggle":
        if (typeof entry.value !== "boolean") return null;
        return Object.assign(row, { initial: entry.value, trueText: msText(entry.trueText, config),
            falseText: msText(entry.falseText, config) });
    case "stepper":
    case "dropdown": {
        const items = Array.isArray(entry.items) ? entry.items.slice(0, config.catalog.maxChoices) : [];
        if (items.length === 0 || !items.every((item) => typeof item === "string")) return null;
        const index = Number.isInteger(entry.value) && entry.value >= 0 && entry.value < items.length ? entry.value : 0;
        return Object.assign(row, { items: items.map((item) => msText(item, config)), initial: index });
    }
    case "keybind":
        if (entry.value !== null && !(typeof entry.value === "string" && /^[A-Za-z0-9]{1,32}$/.test(entry.value))) return null;
        return Object.assign(row, { initial: entry.value, locked: locked || entry.rebindable !== true });
    case "button":
        return Object.assign(row, { text: config.page.buttonLabel });
    case "nested": {
        const rows = msRows(entry.entries, config, locked, depth + 1, budget);
        if (rows === null) return null;
        // Opening a page changes nothing: the link stays usable on a locked mod, its page's rows are locked
        // (trial 8: the gamepad could not open a locked mod's sub-page, the mouse could).
        return Object.assign(row, { kind: "link", text: config.page.openLabel, locked: false,
            target: { title: label, rows: rows, locked: locked, details: row.details } });
    }
    default:
        return null;
    }
}

function msRows(entries, config, locked, depth, budget) {
    if (!Array.isArray(entries) || depth > config.catalog.maxDepth) return null;
    const rows = [];
    for (const entry of entries.slice(0, config.catalog.maxEntriesPerPage)) {
        if (!entry || typeof entry !== "object") continue;
        const row = msRow(entry, config, locked, depth, budget);
        if (row) rows.push(row);
    }
    return rows;
}

// Python's model: its revision and the mods, each with its rows and what the details panel says of it. A mod's
// rows are locked unless Python says the page may change it. The list screen holds one link per mod. Anything
// malformed is left out, never guessed.
function msParseModel(text, config) {
    const payload = msParseJson(text, config, config.http.maxModelBytes);
    if (!payload || !Number.isInteger(payload.revision) || !Array.isArray(payload.mods)) return null;
    const budget = { left: config.catalog.maxEntries };
    const links = [];
    const modPattern = /^m[0-9]{1,2}$/;
    for (const mod of payload.mods.slice(0, config.catalog.maxMods)) {
        if (!mod || !modPattern.test(mod.id) || typeof mod.writable !== "boolean") continue;
        const name = msText(mod.name, config);
        const rows = msRows(mod.entries, config, !mod.writable, 0, budget);
        if (rows === null) continue;
        const details = { title: name, text: msDescription(mod.description, config), meta: msModMeta(mod, config) };
        links.push({ kind: "link", ident: mod.id, label: name, text: config.page.openLabel, locked: false,
            details: details, target: { title: name, rows: rows, locked: !mod.writable, details: details } });
    }
    const details = { title: config.page.title, text: "", meta: "" };
    return { revision: payload.revision, root: { title: config.page.title, rows: links, locked: false, details: details } };
}

// The status line (page.js): Python's state, then the empty list, then the player's last notice. data: MsData.
function msStatusText(texts, data, notice) {
    const waiting = data.notReady ? texts.notReady : texts.loading;
    const state = data.python === null ? waiting : (data.python ? texts.pythonOk : texts.pythonAbsent);
    const empty = data.python === false && !data.model ? texts.noMods : "";
    return [state, empty, notice].filter((part) => part).join(" | ");
}

// The state of a key capture: waiting, done (with the key), or how it ended.
function msParseCapture(text, config) {
    const payload = msParseJson(text, config);
    if (!payload || typeof payload.state !== "string" || !new RegExp(config.codePattern).test(payload.state)) return null;
    const key = payload.key === undefined ? null : payload.key;
    if (key !== null && !(typeof key === "string" && key in config.capture.keys)) return null;
    return { state: payload.state, key: key };
}

function msMessage(config, body) {
    const text = JSON.stringify(Object.assign({ marker: config.marker }, body));
    return text.length <= config.http.maxRequestBytes ? text : null;
}

// A diagnostic event: its fields are short codes from the constants, never free text.
function msEventBody(config, name, fields) {
    if (config.events.indexOf(name) < 0) return null;
    const body = { event: name };
    const code = new RegExp(config.codePattern);
    const extra = fields || {};
    for (const key of Object.keys(extra)) {
        const value = extra[key];
        if (config.eventFields.indexOf(key) < 0 || typeof value !== "string" || !code.test(value)) return null;
        body[key] = value;
    }
    return msMessage(config, body);
}

// A change of a row, counted in the model the page holds (revision): Python refuses it against another model.
function msValueBody(config, row, value, revision) {
    if (!(row.kind in MS_MODELS) || row.locked) return null;
    return msMessage(config, { action: "value", id: row.ident, revision: revision,
        value: msCleanValue(row, value) });
}

function msPressBody(config, row, revision) {
    if (row.kind !== "button" || row.locked) return null;
    return msMessage(config, { action: "press", id: row.ident, revision: revision });
}

// One message for the durations of an opening, instead of one request each (OPTI.md, rule 22).
function msTimingsBody(config, timings) {
    const body = { event: "timings" };
    for (const name of config.timingNames) {
        const ms = timings[name];
        if (typeof ms === "number" && isFinite(ms)) body[name] = Math.min(config.http.maxTimingMs, Math.max(0, Math.round(ms)));
    }
    return Object.keys(body).length > 1 ? msMessage(config, body) : null;
}

// A start names its row in the model the page holds (revision), as a change does; a cancel names nothing.
function msCaptureBody(config, action, ident, revision) {
    return msMessage(config, ident ? { action: action, id: ident, revision: revision } : { action: action });
}

// A game input action's name as a short code for the log (Input.Action.Menu.NavUp -> input_action_menu_navup).
function msActionCode(name) {
    return String(name || "none").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 48) || "none";
}

// The first key the game draws for each glyph action of a pair, as one code for the log (glyph_manager.js:
// km_keys, gamepad_keys; ["Q"] and ["E"] -> q_e).
function msKeysCode(infos, field) {
    return msActionCode(infos.map((info) => (info && Array.isArray(info[field]) && info[field][0]) || "none").join("_"));
}
