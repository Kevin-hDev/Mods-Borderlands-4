/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// Tests of page/conflicts_view.js, with the page's config as the pak carries it (pak_recipe.py builds it).
// node test_conflicts_view.js   (Python runs the recipe: PYTHON, else python)

const childProcess = require("child_process");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const constants = JSON.parse(childProcess.execFileSync(process.env.PYTHON || "python",
    [path.join(__dirname, "pak_recipe.py"), "config"],
    { encoding: "utf8", env: Object.assign({}, process.env, { PYTHONDONTWRITEBYTECODE: "1" }) }));
const context = {};
vm.createContext(context);
vm.runInContext(["texts.js", "conflicts_view.js", "language.js"]
    .map((name) => fs.readFileSync(path.join(__dirname, "page", name), "utf8")).join("\n") +
    "\nthis.lcConflictsView = lcConflictsView; this.lcConflictsAnswer = lcConflictsAnswer;" +
    "\nthis.lcLocalized = lcLocalized;", context);
const failures = [];

function expect(condition, label) {
    if (!condition) {
        failures.push(label);
        console.log("ECHEC: " + label);
    }
}

function page(code) {
    return context.lcLocalized(constants, code).page;
}

const en = page("en");
const fr = page("fr");
const zh = page("zh");
const order = constants.page.conflictSections;

function answer(sections, fields) {
    const all = {};
    for (const name of order) all[name] = (sections && sections[name]) || [];
    return Object.assign({ state: "ok", sections: all, checked: { mods: 3, keys: 9, commands: 2, containers: 7 },
                           unreadable: { mods: 0, containers: 0 }, log: "read", paks: "read", partial: false,
                           cut: false },
                         fields || {});
}

const FOUND = {
    failed: [{ name: "hud_editor", reason: "import", items: ["RuntimeError: no"] },
             { name: "Odd.v2", reason: "folder", items: [] },
             { name: "MyMod (1).sdkmod", reason: "file", items: ["MyMod.sdkmod"] },
             { name: "Nested", reason: "nested", items: [] }],
    twice: [{ name: "weather", items: [{ copy: "weather", folder: true }, { copy: "weather.sdkmod", folder: false }],
              more: 0 }],
    files: [{ containers: ["b_5_P.pak", "a_P.pak"], moreContainers: 0, winner: "b_5_P.pak", count: 3, identical: 1,
              items: ["x.js", "y.js"], more: 1 },
            { containers: ["c_P.pak", "d.pak"], moreContainers: 2, winner: "c_P.pak", count: 1, identical: 0,
              items: ["z.js"], more: 0 }],
    commands: [{ name: "spawn", items: ["Arena", "Spawner"], more: 0 }],
    settings: [{ name: "w.json", items: [{ mod: "New", dropped: false }, { mod: "Old", dropped: true }], more: 0 }],
    keys: [{ name: "F5", items: [{ mod: "A", name: "Dash", fixed: false }, { mod: "B", name: "View", fixed: true }],
             more: 0 }]
};

function testShape() {
    expect(context.lcConflictsAnswer(answer(), en), "an answer with every section");
    const missing = answer();
    delete missing.sections.keys;
    expect(!context.lcConflictsAnswer(missing, en) && !context.lcConflictsAnswer(null, en)
           && !context.lcConflictsAnswer(answer({}, { state: "error" }), en)
           && !context.lcConflictsAnswer(answer({}, { checked: null }), en)
           && !context.lcConflictsAnswer(answer({}, { sections: { failed: "x" } }), en),
           "a section missing or not a list, an error, or counts missing: refused");
}

function testStatus() {
    const shown = context.lcConflictsView(answer(FOUND), en);
    expect(shown.status[0] === "10 conflict(s) found between your mods."
           && shown.status[1] === "3 enabled mods, 9 keys, 2 console commands and 7 mod package files (.pak, .utoc) "
           + "checked." && shown.status.length === 2, "every section's conflicts counted, and what was looked at");
    const none = context.lcConflictsView(answer({}, { log: "log_refused", paks: "missing", partial: true, cut: true,
                                                       unreadable: { mods: 2, containers: 1 } }), fr);
    expect(none.status[0] === fr.states.conflictsNone && none.status[2] === fr.states.logNotRead
           && none.status[3] === fr.states.paksMissing && none.status[4] === "2 mod(s) illisible(s)."
           && none.status[5] === "1 fichier(s) ou dossier(s) de paquets de mods n'ont pas pu être lus."
           && none.status[6] === "Seuls les 128 premiers mods, et les 64 premières touches et 64 premières commandes "
           + "console de chacun, ont été regardés."
           && none.status[7] === fr.states.listCut && none.status.length === 8
           && none.sections.length === 0, "what could not be looked at, said; no section without conflicts");
}

function testSections() {
    const shown = context.lcConflictsView(answer(FOUND), en);
    expect(shown.sections.map((section) => section.title).join("|") ===
           order.map((name) => en.states[name + "Title"]).join("|"), "the sections in order of severity");
    expect(shown.sections[5].help.join("|") === en.states.keysHelp + "|" + en.states.keysFix
           && shown.sections[0].help.join("|") === en.states.failedHelp, "what each conflict does, and what to do");
    const failed = shown.sections[0].blocks;
    expect(failed[0].key === "hud_editor"
           && failed[0].lines.join("|") === en.states.reasonImport + "|Error: RuntimeError: no"
           && failed[1].lines.join("|") === en.states.reasonFolder
           && failed[2].lines.join("|") === en.states.reasonFile + "|Its name should probably be MyMod.sdkmod."
           && failed[3].lines.join("|") === en.states.reasonNested, "each reason, with its detail when it has one");
    expect(shown.sections[1].blocks[0].lines.join("|") === "Loaded: weather (folder)|Ignored: weather.sdkmod",
           "the copy loaded first, folders told apart");
    const files = shown.sections[2].blocks;
    expect(files[0].key === "b_5_P.pak, a_P.pak" && files[0].lines.join("|") ===
           "b_5_P.pak goes first: 3 file(s) in common, 1 of them identical, with no effect.|x.js|y.js|... and 1 more"
           && files[1].lines[0] === "c_P.pak goes first: 1 file(s) in common."
           && files[1].key === "c_P.pak, d.pak ... and 2 more",
           "the containers, those past the bound counted, who goes first, files");
    expect(shown.sections[3].blocks[0].lines.join("|") === "Arena|Spawner"
           && shown.sections[4].blocks[0].lines.join("|") === "New|Old (removed from the mod list)",
           "commands and settings files by mod");
    expect(shown.sections[5].blocks[0].key === "Keyboard: F5" && shown.sections[5].blocks[0].lines.join("|") ===
           'A, action "Dash"|B, action "View" (cannot be changed)', "keys by the game's names");
    const odd = context.lcConflictsView(answer({ failed: [{ name: "x", reason: "new", items: ["y"] }] }), en);
    expect(odd.sections[0].blocks[0].lines.join("|") === "", "a reason the page does not know adds no guess");
    const reasons = constants.page.conflictReasons;
    expect(Object.keys(reasons).sort().join("|") === "file|folder|import|nested"
           && Object.values(reasons).every((pair) => pair.every((name) => !name
                                                                 || typeof en.states[name] === "string")),
           "each reason the loader's log gives has its texts");
}

function testLanguages() {
    for (const [code, texts] of [["fr", fr], ["zh", zh]]) {
        const shown = context.lcConflictsView(answer(FOUND, { log: "x", paks: "x", partial: true, cut: true,
                                                              unreadable: { mods: 1, containers: 1 } }), texts);
        const all = shown.status.concat(...shown.sections.map((section) =>
            [section.title].concat(section.help, ...section.blocks.map((block) => [block.key].concat(block.lines)))));
        expect(all.every((line) => typeof line === "string" && line && line.indexOf("{") === -1),
               code + ": every line filled");
        expect(Object.keys(constants.texts.en.states).every((key) => key in constants.texts[code].states),
               code + ": every state translated");
    }
}

testShape();
testStatus();
testSections();
testLanguages();
console.log(failures.length === 0 ? "RESULTAT: TOUS LES TESTS PASSENT" : "RESULTAT: " + failures.length + " ECHEC(S)");
process.exit(failures.length === 0 ? 0 : 1);
