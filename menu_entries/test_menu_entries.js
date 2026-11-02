/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// Tests of menu_entries.js with a fake game element class and a fake page. node test_menu_entries.js

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const source = fs.readFileSync(path.join(__dirname, "menu_entries.js"), "utf8");
const failures = [];

function expect(condition, label) {
    if (!condition) {
        failures.push(label);
        console.log("ECHEC: " + label);
    }
}

// A page where the script runs once or twice; hook(mod) builds an entry in the menu's list and calls its Init, as
// the game does once the menu is built.
function page(globals) {
    const defined = {};
    const context = {
        GbxCustomElement: class {
            Init() { this.started = true; }
            getAttribute(name) { return this.attributes[name]; }
        },
        customElements: {
            define(name, made) {
                if (defined[name]) throw new Error("already defined");
                defined[name] = made;
            }
        }
    };
    context.window = Object.assign(context, globals);
    vm.createContext(context);
    const list = {
        children: [],
        removeChild(child) {
            this.children = this.children.filter((other) => other !== child);
            child.parentNode = null;
        }
    };
    return {
        load() { vm.runInContext(source, context); },
        defined: defined,
        list: list,
        hook(mod) {
            const entry = { style: { display: "none" }, parentNode: list };
            list.children.push(entry);
            const made = new defined["menu-entries-hook"]();
            Object.assign(made, { attributes: { mod: mod }, parentElement: entry });
            made.Init();
            return { entry: entry, made: made };
        }
    };
}

const withSettings = page({ ModSettings: {} });
withSettings.load();
withSettings.load();
const shown = withSettings.hook("mod_settings");
expect(shown.entry.style.display === "" && shown.made.started && withSettings.list.children.includes(shown.entry),
       "MODS shown at Init when Mod Settings' script is there");
expect(Object.keys(withSettings.defined).length === 1, "loaded twice, defined once");
const unknown = withSettings.hook("other");
expect(!withSettings.list.children.includes(unknown.entry), "an unknown mod's entry leaves the menu");
const without = page({});
without.load();
const absent = without.hook("mod_settings");
expect(absent.entry.style.display === "none" && without.list.children.length === 0,
       "without Mod Settings' script, MODS leaves the menu: the gamepad cannot stop on it");

console.log(failures.length === 0 ? "RESULTAT: TOUS LES TESTS PASSENT" : "RESULTAT: " + failures.length + " ECHEC(S)");
process.exit(failures.length === 0 ? 0 : 1);
