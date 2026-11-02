/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// Tests of page/texts.js and page/language.js (the conflicts' view: test_conflicts_view.js), with the page's config
// as the pak carries it (pak_recipe.py builds it). node test_texts.js   (Python runs the recipe: PYTHON, else python)

const childProcess = require("child_process");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const constants = JSON.parse(childProcess.execFileSync(process.env.PYTHON || "python",
    [path.join(__dirname, "pak_recipe.py"), "config"],
    { encoding: "utf8", env: Object.assign({}, process.env, { PYTHONDONTWRITEBYTECODE: "1" }) }));
const context = {};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, "page", "texts.js"), "utf8") +
    fs.readFileSync(path.join(__dirname, "page", "language.js"), "utf8") +
    "\nthis.lcFill = lcFill; this.lcSize = lcSize; this.lcLogStatus = lcLogStatus; this.lcCutLine = lcCutLine;" +
    "\nthis.lcCode = lcCode; this.lcKeyName = lcKeyName;" +
    "\nthis.lcLocalized = lcLocalized; this.lcGameLanguage = lcGameLanguage;", context);
const failures = [];

function expect(condition, label) {
    if (!condition) {
        failures.push(label);
        console.log("ECHEC: " + label);
    }
}

// The page's texts as the page gets them: language.js merges each language over English.
function page(code) {
    return context.lcLocalized(constants, code).page;
}

const en = page("en");
const fr = page("fr");
const zh = page("zh");
expect(context.lcSize(512, en) === "512 B" && context.lcSize(2048, en) === "2 KB", "bytes and kilobytes");
expect(context.lcSize(1258291, en) === "1.2 MB" && context.lcSize(1258291, fr) === "1,2 Mo", "megabytes by language");
expect(context.lcSize(35 * 1048576, en) === "35 MB", "large sizes without decimals");
expect(context.lcFill("{a} and {b} and {c}", { a: 1, b: "x" }) === "1 and x and {c}", "unknown fields kept");

const whole = context.lcLogStatus({ size: 2048, cut: 0, masked: 0, readAt: "14:32:05" }, en);
expect(whole.length === 1 && whole[0] === "Log of this session, 2 KB. Read at 14:32:05.", "whole log state");
const cut = context.lcLogStatus({ size: 1258291, cut: 983040, masked: 2, readAt: "14:32:05" }, fr);
expect(cut[0] === "Journal de cette séance, 1,2 Mo. Lu à 14:32:05." &&
       cut[1] === "Le début et la fin sont affichés ; 960 Ko coupés au milieu." &&
       cut[2] === fr.states.masked.replace("{replacement}", constants.page.maskReplacement) &&
       cut[2].indexOf("{") === -1, "cut and masked log state, in French, the mask named");
expect(context.lcLogStatus({ size: 0, cut: 0, masked: 0, readAt: "x" }, en)[0] === en.states.logEmpty, "empty log");
expect(context.lcCutLine({ cut: 2048 }, en) === "[... 2 KB cut here ...]" && context.lcCutLine({ cut: 0 }, en) === "",
       "cut line only when something is cut");

// The game's own key names (Engine.locres, InputKeys), by device.
expect(context.lcKeyName("Gamepad_LeftThumbstick", en) === "Gamepad Left Thumbstick Button" &&
       context.lcKeyName("Gamepad_FaceButton_Bottom", fr) === "Manette : A" &&
       context.lcKeyName("LeftMouseButton", zh) === "鼠标左键", "gamepad and mouse names say their device");
expect(context.lcKeyName("SpaceBar", fr) === "Clavier : Espace" && context.lcKeyName("A", zh) === "键盘：A" &&
       context.lcKeyName("F12", en) === "Keyboard: F12", "keyboard keys say they are keyboard keys");
expect(context.lcKeyName("Tab", fr) === "Clavier : Tab", "a name missing in French is the English one");
expect(context.lcKeyName("E_AccentAigu", fr) === "Clavier : é" && context.lcKeyName("One", en) === "Keyboard: 1",
       "keys the game does not name show the sign they type");
expect(context.lcKeyName("E_AccentGrave", zh) === "键盘：E_AccentGrave"
       && context.lcKeyName("Section", zh) === "键盘：Section" && context.lcKeyName("Hyphen", zh) === "键盘：-"
       && context.lcKeyName("E_AccentGrave", fr) === "Clavier : è",
       "no accented sign where the font cannot draw it: Chinese shows the SDK's name (trial 4)");
expect(context.lcKeyName("leftshift", en) === "Keyboard: Left Shift" && context.lcKeyName("q", fr) === "Clavier : Q",
       "in any case, as the conflicts are grouped");
expect(context.lcKeyName("PageUp", fr) === "Clavier : Haut de page" &&
       context.lcKeyName("PageDown", fr) === "Clavier : Bas de page", "the engine's swapped French Page Up/Down fixed");
expect(context.lcKeyName("MouseX", en) === "MouseX" && context.lcKeyName("Gamepad_Strange", fr) === "Gamepad_Strange"
       && context.lcKeyName("constructor", en) === "constructor" && context.lcKeyName("F123", en) === "F123",
       "a key the game does not name stays as the SDK writes it");
expect(context.lcCode("Input.Action.Menu.NavUp") === "input_action_menu_navup" && context.lcCode("") === "none",
       "action codes");

// The game's language, told by its own translation of its Quit Game entry: engine.translate first, else the entry.
const sample = constants.languages.sample;
const told = (text) => ({ translate: () => text });
const entryDoc = (text) => ({ querySelector: (selector) => (selector.indexOf(sample.key) !== -1
    ? { textContent: text } : null) });
const language = (engineApi, doc) => context.lcGameLanguage(constants, engineApi, doc);
expect(language(told(" " + sample.texts.fr.toUpperCase() + " "), null).code === "fr" &&
       language(told(sample.texts.zh), null).code === "zh" && language(told(sample.english), null).code === "en",
       "French, Chinese and English told by engine.translate");
const other = language(told("Salir del juego"), null);
expect(other.code === "en" && other.source === "translate_other", "any other language stays English, and says so");
const fromEntry = language({ translate: () => { throw new Error("no"); } }, entryDoc(sample.texts.fr));
expect(fromEntry.code === "fr" && fromEntry.source === "element", "translate failing, the entry's text tells");
expect(language(null, null).source === "none" && language(told(""), entryDoc("")).code === "en",
       "nothing told: English");
expect(context.lcLocalized(constants, "es").language === "en" && context.lcLocalized(constants, "fr").language === "fr",
       "a language without texts is English");

console.log(failures.length === 0 ? "RESULTAT: TOUS LES TESTS PASSENT" : "RESULTAT: " + failures.length + " ECHEC(S)");
process.exit(failures.length === 0 ? 0 : 1);
