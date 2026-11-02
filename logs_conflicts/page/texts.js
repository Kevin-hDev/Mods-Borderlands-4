/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// What the page writes from the service's answers, as plain text: the log's state sentence, sizes, the keys' names
// (the conflicts' lines are conflicts_view.js's). Pure, tested in node. Each sentence says exactly what it measures
// (interface rule 7): the time is the time of the read, not of the log's last line, since the SDK may write late.

function lcFill(template, values) {
    return String(template).replace(/\{(\w+)\}/g, (all, key) => (key in values ? String(values[key]) : all));
}

// Sizes as the player reads them: whole bytes and kilobytes, megabytes with one decimal under ten.
function lcSize(bytes, page) {
    const units = page.units;
    if (bytes < 1024) return bytes + " " + units[0];
    if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + " " + units[1];
    const megabytes = bytes / (1024 * 1024);
    const shown = megabytes < 10 ? megabytes.toFixed(1) : String(Math.round(megabytes));
    return shown.replace(".", page.decimal) + " " + units[2];
}

// The state lines of a log the service sent (state "ok").
function lcLogStatus(read, page) {
    const states = page.states;
    if (!read.size) return [states.logEmpty];
    const lines = [lcFill(states.logShown, { size: lcSize(read.size, page), time: read.readAt })];
    if (read.cut > 0) lines.push(lcFill(states.logCut, { cut: lcSize(read.cut, page) }));
    if (read.masked > 0) lines.push(lcFill(states.masked, { replacement: page.maskReplacement }));
    return lines;
}

function lcCutLine(read, page) {
    return read.cut > 0 ? lcFill(page.states.cutLine, { cut: lcSize(read.cut, page) }) : "";
}

// The key as the game names it in its own menus (Engine.locres, InputKeys): gamepad and mouse names already say
// their device, keyboard keys get "Keyboard: ". In any case, as keys.py groups them. A key the game does not
// name, and that is no letter, function key or sign, stays as the SDK writes it rather than being guessed.
function lcKeyName(key, page) {
    const keys = page.keys;
    const lower = String(key).toLowerCase();
    const named = lcLookup(page.keyNames, lower);
    if (lower.indexOf(keys.gamepadPrefix.toLowerCase()) === 0
        || keys.mouse.some((name) => name.toLowerCase() === lower)) return named || key;
    const typed = named || lcSign(lcLookup(keys.characters, lower), key, page)
        || (new RegExp(keys.keyboardPattern, "i").test(key) ? String(key).toUpperCase() : "");
    return typed ? lcFill(page.states.keyboardKey, { key: typed }) : key;
}

// The sign a key types, where the language's font draws it. The game's Chinese font has no accented letters: "è"
// showed as an empty box (trial 4). There, a sign outside plain ASCII gives way to the SDK's name of the key.
function lcSign(sign, key, page) {
    if (!sign || page.accentedSigns !== false || /^[ -~]+$/.test(sign)) return sign;
    return String(key);
}

// Own entries only: a key named "constructor" by a mod must not find the object's own functions.
function lcLookup(table, lower) {
    for (const name of Object.keys(table)) {
        if (name.toLowerCase() === lower) return table[name];
    }
    return "";
}

// A short code for the log, from any action name: Input.Action.Menu.NavUp -> input_action_menu_navup.
function lcCode(name) {
    return String(name || "none").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 48)
        || "none";
}
