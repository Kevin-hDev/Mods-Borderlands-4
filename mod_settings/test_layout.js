/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";
// Tests of layout.js: how a mod's rows become tabs, sub-tabs and pages, on a model read as the page reads
// Python's (logic.js). node test_layout.js

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const shared = JSON.parse(fs.readFileSync(path.join(__dirname, "mod_settings", "assets", "mod_settings.constants.json"), "utf8"));
const context = vm.createContext({ console: console });
for (const name of ["language.js", "models.js", "logic.js", "layout.js"]) {
    vm.runInContext(fs.readFileSync(path.join(__dirname, "page", name), "utf8"), context, { filename: name });
}
// The page as an English game shows it (language.js).
const constants = vm.runInContext("msLocalized", context)(shared, "en");
const api = vm.runInContext("({ msParseModel, msTabs, msView, msSubtabs, msSelection, " +
    "msChildView })", context);
const failures = [];
const check = (name, condition) => {
    if (!condition) {
        failures.push(name);
        console.log("ECHEC: " + name);
    }
};
const page = constants.page;
const labels = (rows) => rows.map((row) => row.label);
const toggle = (id, label) => ({ kind: "toggle", id: id, label: label, value: true });

// The test mod as Python sends it (fixture_test_mod.py): the SDK wraps its options in an "Options" group, its first
// option is a group, two pages, one of which has pages of its own, one of those opening a deeper page.
const mod = { id: "m0", name: "Sample Mod", writable: true, description: "Sample mod", entries: [
    toggle("m0_on", "Enabled"),
    { kind: "title", label: "Options" },
    { kind: "title", label: "Sample group" },
    { kind: "slider", id: "m0_1", label: "Whole number", min: 0, max: 100, step: 5, decimals: 0, value: 50, default: 50 },
    toggle("m0_2", "Switch"),
    { kind: "nested", id: "m0_3", label: "More settings", description: "No page of its own",
        entries: [toggle("m0_4", "Inner switch")] },
    { kind: "nested", id: "m0_5", label: "Pages", description: "Pages of its own", entries: [
        toggle("m0_6", "Pages switch"),
        { kind: "nested", id: "m0_7", label: "Page A", entries: [toggle("m0_8", "Page A switch")] },
        { kind: "nested", id: "m0_9", label: "Page B", description: "Opens a deeper one", entries: [
            toggle("m0_10", "Page B switch"),
            { kind: "nested", id: "m0_11", label: "Deep page", entries: [toggle("m0_12", "Deep switch")] }] }] },
    { kind: "title", label: "Keybinds" },
    { kind: "keybind", id: "m0_13", label: "Key", value: "F7", rebindable: true }
] };
const model = api.msParseModel(JSON.stringify({ marker: constants.marker, version: constants.version, revision: 1,
    mods: [mod] }), constants);

// The list: one tab, its rows the mods; a mod opens as its own screen.
const list = api.msView("list", model.root, [], constants);
check("list is one MODS tab of the mods", list.tabs.length === 1 && list.tabs[0].label === page.title &&
    labels(list.tabs[0].rows).join() === "Sample Mod" && api.msSubtabs(list, 0, constants) === null);
check("list shows its own details", api.msSelection(list, 0, 0, constants).details.title === page.title);
const modLink = list.tabs[0].rows[0];
const view = api.msChildView(list, 0, 0, modLink, constants);
check("a mod opens as its page, its path from MODS", view.kind === "mod" &&
    view.crumb.join("|") === page.title + "|Sample Mod" && view.locked === false);

// The mod's page: loose rows under General, each page a tab.
check("General then one tab per page", labels(view.tabs).join("|") === page.generalLabel + "|More settings|Pages");
const general = view.tabs[0].rows;
check("General keeps the loose rows and their groups' titles", labels(general).join("|") ===
    "Enabled|Sample group|Whole number|Switch|Keybinds|Key");
check("a title followed at once by another leaves none", general.filter((row) => row.label === "Options").length === 0);
check("General has no sub-tabs", api.msSubtabs(view, 0, constants) === null);
check("General shows the mod's details", api.msSelection(view, 0, 0, constants).details.text === "Sample mod");
check("a page with no page of its own has no sub-tabs", api.msSubtabs(view, 1, constants) === null &&
    labels(api.msSelection(view, 1, 0, constants).rows).join() === "Inner switch");
check("a tab shows its page's details", api.msSelection(view, 1, 0, constants).details.text === "No page of its own");

// A page with pages of its own: its loose rows under General, its pages as sub-tabs.
const subtabs = api.msSubtabs(view, 2, constants);
check("its pages as sub-tabs", labels(subtabs).join("|") === page.generalLabel + "|Page A|Page B");
check("sub-tabs worked out once", api.msSubtabs(view, 2, constants) === subtabs);
const pagesGeneral = api.msSelection(view, 2, 0, constants);
check("its General sub-tab holds its loose rows", labels(pagesGeneral.rows).join() === "Pages switch" &&
    pagesGeneral.details.text === "Pages of its own");
const pageB = api.msSelection(view, 2, 2, constants);
check("a sub-tab shows its page, a deeper page as a row that opens it", labels(pageB.rows).join("|") ===
    "Page B switch|Deep page" && pageB.rows[1].kind === "link" && pageB.details.text === "Opens a deeper one");

// A deeper page: a screen laid out the same way, its path the tabs it was reached through.
const deep = api.msChildView(view, 2, 2, pageB.rows[1], constants);
check("a deeper page opens as a screen", deep.kind === "page" && deep.crumb.join("|") ===
    page.title + "|Sample Mod|Pages|Page B|Deep page" && labels(deep.tabs[0].rows).join() === "Deep switch");
const fromGeneral = api.msChildView(view, 0, 0, pageB.rows[1], constants);
check("General adds nothing to the path", fromGeneral.crumb.join("|") === page.title + "|Sample Mod|Deep page");

// Shapes other mods may have.
const link = (label, rows) => ({ kind: "link", label: label, target: { title: label, rows: rows, locked: false } });
const loose = { kind: "toggle", label: "Loose" };
check("pages only: no General", labels(api.msTabs([link("X", []), link("Y", [])], constants)).join() === "X,Y");
check("nothing: an empty General", api.msTabs([], constants).length === 1 &&
    api.msTabs([], constants)[0].rows.length === 0);
check("a group of pages leaves no title", labels(api.msTabs([{ kind: "title", label: "G" }, link("X", []),
    { kind: "title", label: "H" }, loose], constants)[0].rows).join() === "H,Loose");
const single = api.msView("mod", { title: "S", rows: [link("Only", [link("Inner", [loose])])], locked: true,
    details: { title: "S", text: "", meta: "" } }, ["MODS", "S"], constants);
check("one page inside a tab is a sub-tab", labels(api.msSubtabs(single, 0, constants)).join() === "Inner" &&
    labels(api.msSelection(single, 0, 0, constants).rows).join() === "Loose" && single.locked === true);

console.log(failures.length === 0 ? "RESULTAT: OK" : "RESULTAT: ECHEC " + failures.length);
process.exit(failures.length === 0 ? 0 : 1);
