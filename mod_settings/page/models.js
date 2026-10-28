/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// What each game piece is given, built from a row of Python's model (logic.js, msParseModel) and its
// current value. Pure: no DOM, so the node tests drive it. The field names are those menu_options.js passes (slider_values, toggle_values...).

// slider_alt has a single value box and fills it only from valuedisplaytext: its owner writes the number
// (menu_options.js, Event_SliderValueUpdate). Without it the slider stops before keeping its new value (trial 2).
function msSliderModel(row, value) {
    const current = msCleanValue(row, value);
    return {
        ident: row.ident, minvalue: row.minvalue, maxvalue: row.maxvalue, stepvalue: row.stepvalue,
        initialvalue: current, defaultvalue: msCleanValue(row, row.defaultValue), decimals: row.decimals,
        showdefaultvalue: true, showcurrentvaluelabel: true,
        showvaluedisplaytext: true, valuedisplaytext: msValueText(row, current)
    };
}

function msToggleModel(row, value) {
    return { ident: row.ident, initialvalue: msCleanValue(row, value) };
}

function msStepperModel(row, value) {
    return {
        ident: row.ident, initialvalue: msCleanValue(row, value), nowrap: false, mouseholdenabled: true,
        showcolorpreview: false, supportstring: "", displayitems: row.items.map((label) => ({ label: label }))
    };
}

// headerlabel is the header's text until the player picks an item (dropdown_options.js, RefreshHeaderText).
function msDropdownModel(row, value) {
    const current = msCleanValue(row, value);
    return {
        ident: row.ident, headerlabel: row.items[current], isdisabled: false,
        displayitems: row.items.map((label, index) => ({
            label: label, isselected: index === current, depth: 0, haschildren: false, ischeckbox: true,
            isdisabled: false, iscollapsedchild: false, isblacklisted: false, isexpanded: false, islocked: false
        }))
    };
}

// The reset button stays hidden: the page has no default binding to give back. The glyph looks the key up in
// the game's tables, written in lowercase (glyph_map_keyboard_mouse.js: "f7"), and draws nothing for "F7"
// (trial 6): lowered here only, Python keeps the engine's name.
function msRebindModel(row, value) {
    const key = msCleanValue(row, value);
    return {
        ident: row.ident, primarybind: key ? key.toLowerCase() : "", secondarybind: "",
        bisgamepadbinding: false, bisvehiclebinding: false, bshowresetbinding: false
    };
}

const MS_MODELS = {
    slider: msSliderModel, toggle: msToggleModel, stepper: msStepperModel,
    dropdown: msDropdownModel, keybind: msRebindModel
};

// The value a row may hold, or its initial value: Python and the pieces never get anything else.
function msCleanValue(row, value) {
    switch (row.kind) {
    case "slider":
        if (typeof value !== "number" || !isFinite(value)) return row.initial;
        return Number(Math.min(row.maxvalue, Math.max(row.minvalue, value)).toFixed(row.decimals));
    case "toggle":
        return typeof value === "boolean" ? value : row.initial;
    case "stepper":
    case "dropdown":
        return Number.isInteger(value) && value >= 0 && value < row.items.length ? value : row.initial;
    case "keybind":
        return value === null || (typeof value === "string" && /^[A-Za-z0-9]{1,32}$/.test(value)) ? value : row.initial;
    default:
        return null;
    }
}

function msValueText(row, value) {
    return msCleanValue(row, value).toFixed(row.decimals);
}
