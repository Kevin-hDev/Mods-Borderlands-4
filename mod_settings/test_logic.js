/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";
// Tests of the page's pure parts (models.js, logic.js, sender.js), loaded together as the pak
// joins them. node test_logic.js

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const shared = JSON.parse(fs.readFileSync(path.join(__dirname, "mod_settings", "assets", "mod_settings.constants.json"), "utf8"));
const context = vm.createContext({ console: console });
for (const name of ["language.js", "models.js", "logic.js", "sender.js"]) {
    vm.runInContext(fs.readFileSync(path.join(__dirname, "page", name), "utf8"), context, { filename: name });
}
// The page as an English game shows it (language.js).
const constants = vm.runInContext("msLocalized", context)(shared, "en");
const api = vm.runInContext("({ msSliderModel, msToggleModel, msStepperModel, msDropdownModel, " +
    "msRebindModel, msCleanValue, msValueText, msExtractTemplate, msParseModel, msParseCapture, " +
    "msEventBody, msValueBody, msPressBody, msTimingsBody, msCaptureBody, msActionCode, " +
    "msKeysCode, msStatusText, MsSender })", context);
const MAX_PENDING = constants.page.limits.maxPendingMessages;
const failures = [];
const check = (name, condition) => {
    if (!condition) {
        failures.push(name);
        console.log("ECHEC: " + name);
    }
};
const NL = String.fromCharCode(10);
const wrap = (fields) => JSON.stringify(Object.assign({ marker: constants.marker, version: constants.version }, fields));

// A model as Python writes it (catalog.py): one writable mod with each kind, one locked mod.
const testMod = { id: "m0", name: "Sample Mod", writable: true, description: "First line" + NL + "Second",
    version: "1.0", author: "Sample author", entries: [
    { kind: "toggle", id: "m0_on", value: false },
    { kind: "title", label: "Sample group" },
    { kind: "slider", id: "m0_1", label: "Whole number", min: 0, max: 100, step: 5, decimals: 0, value: 50, default: 50,
        description: "From 0 to 100." },
    { kind: "stepper", id: "m0_2", label: "Arrows", items: ["Low", "Medium", "High", "Ultra"], value: 1,
        descriptionTitle: "Arrows title", description: 7 },
    { kind: "dropdown", id: "m0_3", label: "List", items: ["Red", "Green", "Blue", "Yellow"], value: 2 },
    { kind: "keybind", id: "m0_4", label: "Key", value: "F7", rebindable: true },
    { kind: "button", id: "m0_5", label: "Button" },
    { kind: "nested", id: "m0_6", label: "More settings", description: "Inner page", entries: [
        { kind: "toggle", id: "m0_7", label: "Inner switch", value: true, trueText: "Yes", falseText: "No" }] },
    { kind: "slider", id: "m0_8", label: "Broken", min: 5, max: 1, step: 1, decimals: 0, value: 2, default: 2 },
    { kind: "mystery", id: "m0_9", label: "Unknown kind" },
    { kind: "toggle", id: "../evil", label: "Bad id", value: true }
] };
const realMod = { id: "m1", name: "Real", writable: false, entries: [
    { kind: "slider", id: "m1_1", label: "Speed", min: 0, max: 10, step: 0.5, decimals: 1, value: 2, default: 2 },
    { kind: "keybind", id: "m1_2", label: "Fixed key", value: null, rebindable: false },
    { kind: "nested", id: "m1_3", label: "Real more", entries: [
        { kind: "toggle", id: "m1_4", label: "Inner", value: true }] }
] };
const parsed = api.msParseModel(wrap({ revision: 3, mods: [testMod, realMod, { id: "x9", name: "bad" }] }), constants);
check("model read", parsed && parsed.revision === 3 && parsed.root.title === constants.page.title);
check("one link per valid mod", parsed.root.rows.length === 2 && parsed.root.rows.every((row) => row.kind === "link"));
const testRows = parsed.root.rows[0].target.rows;
check("writable mod not locked", parsed.root.rows[0].target.locked === false && testRows.every((row) => !row.locked));
check("malformed, unknown and badly named rows left out", testRows.length === 8 &&
    !testRows.some((row) => ["Broken", "Unknown kind", "Bad id"].indexOf(row.label) >= 0));
const byLabel = (rows, label) => rows.find((row) => row.label === label);
const slider = byLabel(testRows, "Whole number");
check("slider row as the pieces take it", slider.kind === "slider" && slider.minvalue === 0 && slider.maxvalue === 100 &&
    slider.stepvalue === 5 && slider.initial === 50 && slider.defaultValue === 50 && slider.ident === "m0_1");
const nested = byLabel(testRows, "More settings");
check("nested page as a link with its rows", nested.kind === "link" && nested.text === constants.page.openLabel &&
    nested.target.rows[0].trueText === "Yes");
check("button text from the constants", byLabel(testRows, "Button").text === constants.page.buttonLabel);
check("the on/off row labelled by the page, in its language", testRows.find((row) => row.ident === "m0_on").label
    === constants.page.enabledLabel && constants.page.enabledLabel === shared.texts.en.enabledLabel);
const realRows = parsed.root.rows[1].target.rows;
check("real mod's rows locked", parsed.root.rows[1].target.locked === true &&
    realRows.every((row) => row.kind === "link" || row.locked));
const realMore = byLabel(realRows, "Real more");
check("a locked mod's sub-page opens, its rows locked", realMore.locked === false && realMore.target.locked === true &&
    realMore.target.rows.length === 1 && realMore.target.rows.every((row) => row.locked));
check("unbound key is null", byLabel(realRows, "Fixed key").initial === null);
// What the details panel shows (details.js)
const modLink = parsed.root.rows[0];
check("a mod's details: name, description with its line break, version and author", modLink.details.title ===
    "Sample Mod" && modLink.details.text === "First line" + NL + "Second" &&
    modLink.details.meta === constants.page.versionPrefix + "1.0" + constants.page.metaSeparator + "Sample author" &&
    modLink.target.details === modLink.details);
check("a mod without version or author has no line under", parsed.root.rows[1].details.meta === "" &&
    parsed.root.rows[1].details.text === "");
check("the list's own details", parsed.root.details.title === constants.page.title);
check("row details default to the label", slider.details.title === "Whole number" &&
    slider.details.text === "From 0 to 100.");
check("own title kept, a description not text dropped", byLabel(testRows, "Arrows").details.title ===
    "Arrows title" && byLabel(testRows, "Arrows").details.text === "");
check("a page's details go with it", nested.details.text === "Inner page" && nested.target.details === nested.details);
check("model of another marker refused", api.msParseModel(JSON.stringify({ marker: "x", version: 3, revision: 1,
    mods: [] }), constants) === null);
check("model without revision refused", api.msParseModel(wrap({ mods: [] }), constants) === null);
check("model too long refused", api.msParseModel("x".repeat(constants.http.maxModelBytes + 1), constants) === null);
const tight = JSON.parse(JSON.stringify(constants));
tight.catalog.maxEntries = 2;
tight.catalog.maxLabel = 4;
tight.catalog.maxDepth = 0;
tight.catalog.maxDescription = 5;
const bounded = api.msParseModel(wrap({ revision: 1, mods: [testMod] }), tight);
const boundedRows = bounded.root.rows[0].target.rows;
check("entries bounded across the model", boundedRows.filter((row) => row.ident).length === 2);
// The on/off row's label is the page's own text, not Python's: no bound applies to it.
check("labels bounded", boundedRows.every((row) => row.label === tight.page.enabledLabel || row.label.length <= 4)
    && bounded.root.rows[0].label === "Samp");
check("depth bounded", !boundedRows.some((row) => row.kind === "link"));
check("descriptions bounded", bounded.root.rows[0].details.text === "First" &&
    boundedRows.every((row) => !row.details || row.details.text.length <= 5));

// Piece models, with the fields the options screen passes
const sliderModel = api.msSliderModel(slider, 55.00000001);
check("slider value rounded", sliderModel.initialvalue === 55 && sliderModel.valuedisplaytext === "55");
check("slider default from Python", sliderModel.defaultvalue === 50);
check("slider clamped", api.msSliderModel(slider, 400).initialvalue === 100);
const stepper = byLabel(testRows, "Arrows");
check("stepper items", api.msStepperModel(stepper, 3).displayitems[3].label === "Ultra");
check("stepper out of range gives the row's value", api.msStepperModel(stepper, 9).initialvalue === stepper.initial);
const dropdownModel = api.msDropdownModel(byLabel(testRows, "List"), 2);
check("dropdown header shows the value", dropdownModel.headerlabel === "Blue" && dropdownModel.displayitems[2].isselected);
const keybind = byLabel(testRows, "Key");
// The glyph tables are lowercase (glyph_map_keyboard_mouse.js).
check("rebind key, lowercase for the glyph", api.msRebindModel(keybind, "F8").primarybind === "f8");
check("rebind cleared", api.msRebindModel(keybind, null).primarybind === "");

// Template markup, counted by divs
const html = '<x><div name="Regular Entry Template" class="a"><div><p>t</p></div></div><div name="Other"></div></x>';
check("template whole", api.msExtractTemplate(html, constants.page.regularMarker) ===
    '<div name="Regular Entry Template" class="a"><div><p>t</p></div></div>');
check("template twice refused", api.msExtractTemplate(html + html, constants.page.regularMarker) === null);

// Capture states
const state = (fields) => api.msParseCapture(wrap(fields), constants);
check("capture done with a key", state({ state: "done", key: "F8" }).key === "F8");
check("capture unknown key refused", state({ state: "done", key: "Nuke" }) === null);

// Messages
const change = JSON.parse(api.msValueBody(constants, slider, 35.0000001, 3));
check("change carries the model's revision", change.action === "value" && change.id === "m0_1" && change.value === 35 &&
    change.revision === 3);
check("key cleared as null", JSON.parse(api.msValueBody(constants, keybind, null, 3)).value === null);
check("no change for a locked row", api.msValueBody(constants, realRows[0], 3, 3) === null);
check("press body", JSON.parse(api.msPressBody(constants, byLabel(testRows, "Button"), 3)).action === "press");
check("no press for a slider", api.msPressBody(constants, slider, 3) === null);
check("event body", JSON.parse(api.msEventBody(constants, "screen_opened", { screen: "mod", code: "rows_8" })).screen
    === "mod");
check("free text refused", api.msEventBody(constants, "gamepad", { name: "Big Text" }) === null);
const timings = JSON.parse(api.msTimingsBody(constants, { template: 3.6, screen: 0.2, other: 9 }));
check("timings rounded, known only", timings.template === 4 && timings.screen === 0 && !("other" in timings));
const captureStart = JSON.parse(api.msCaptureBody(constants, "start", "m0_4", 7));
check("capture start body names its row and its model", captureStart.id === "m0_4" && captureStart.revision === 7);
check("capture cancel body names nothing", JSON.stringify(Object.keys(JSON.parse(api.msCaptureBody(constants,
    "cancel", null))).sort()) === '["action","marker"]');
check("action names as codes", api.msActionCode("Input.Action.Menu.OpenOptionsMenu") ===
    "input_action_menu_openoptionsmenu" && api.msActionCode(undefined) === "none");
check("a pair's keys as one code", api.msKeysCode([{ km_keys: ["Q"] }, { km_keys: ["E", "Right"] }], "km_keys") ===
    "q_e" && api.msKeysCode([{ km_keys: [] }, null], "km_keys") === "none_none");
check("glyph keys fit the log's codes", constants.codePattern && new RegExp(constants.codePattern).test(
    api.msKeysCode([{ g: ["Gamepad_Left_Shoulder_And_Much_More"] }, { g: ["Gamepad_Right_Shoulder"] }], "g")));

// A block whose code throws counts as one failure, so the test still ends with its RESULTAT line.
const section = (name, run) => {
    try {
        run();
    } catch (error) {
        check(name + " ran without error: " + error.message, false);
    }
};

// Sender: one request at a time, bounded queue, values coalesced per row and spaced, refusals told
section("sender", () => {
    let now = 0;
    const timers = [];
    const sent = [];
    const refused = [];
    let pendingDone = null;
    const transport = {
        post(body, done) { sent.push("event:" + body); pendingDone = () => done(); },
        change(body, done) { sent.push("change:" + body); pendingDone = (status) => done(status === undefined ? 200 : status); }
    };
    const sender = new api.MsSender(transport, 100, MAX_PENDING, () => now,
        (callback, ms) => { timers.push({ callback: callback, at: now + ms }); return timers.length; },
        (status, ident, newer) => refused.push([status, ident, newer]));
    const finish = (status) => { const done = pendingDone; pendingDone = null; done(status); };
    sender.send("a");
    sender.send("b");
    check("one request at a time", sent.length === 1 && sent[0] === "event:a");
    finish();
    finish();
    sender.sendValue("m0_1", "v1");
    check("first value leaves at once, as a change", sent[2] === "change:v1");
    sender.sendValue("m0_1", "v2");
    sender.sendValue("m0_1", "v3");
    finish();
    check("next value waits for the interval", sent.length === 3 && timers.length === 1 && timers[0].at === 100);
    now = 100;
    timers.shift().callback();
    check("only the latest value leaves", sent.length === 4 && sent[3] === "change:v3");
    finish(409);
    check("a refused change is told with its row", refused.length === 1 && refused[0][0] === 409
        && refused[0][1] === "m0_1");
    sender.sendPress("p");
    check("a press is a change", sent[4] === "change:p");
    finish(503);
    check("a refused press is told without a row", refused.length === 2 && refused[1][0] === 503 && refused[1][1] === null);
    // The page closes during a drag: Python saves on page_closed, so the values still waiting leave before it.
    now = 250;
    sender.sendValue("m0_2", "w1");
    check("a value leaves at once after its interval", sent[5] === "change:w1");
    sender.sendValue("m0_2", "w2");
    sender.sendValue("m0_3", "x1");
    sender.sendAfterValues("closed");
    finish(200);
    finish(200);
    finish(200);
    check("waiting values leave before the page's last word", sent.slice(6).join(",") === "change:w2,change:x1,event:closed");
    finish();
    // A refusal while a newer value of the same row still waits: told, so the page leaves that row alone.
    now = 1000;
    sender.sendValue("m0_4", "y1");
    sender.sendValue("m0_4", "y2");
    finish(503);
    check("a refusal says a newer value of its row waits", refused[2][1] === "m0_4" && refused[2][2] === true);
    now = 1200;
    timers.shift().callback();
    finish(409);
    check("and says when none waits", refused[3][1] === "m0_4" && refused[3][2] === false);
    for (let i = 0; i < MAX_PENDING + 5; i += 1) sender.send("q" + i);
    check("queue bounded (one in flight, the rest queued, the excess dropped)",
        sender.pending.length === MAX_PENDING && sender.dropped === 4);
});

// Requests (transport.js): the page's own timer ends a request that never answers, as the engine may not apply
section("requests", () => {
    // xhr.timeout (review, 26 October 2026); an answer in time stops that timer.
    const timeouts = [];
    const requests = [];
    const requestContext = vm.createContext({
        setTimeout: (callback, ms) => timeouts.push({ callback: callback, ms: ms, cleared: false }),
        clearTimeout: (id) => { timeouts[id - 1].cleared = true; },
        XMLHttpRequest: function () {
            requests.push(this);
            this.open = () => {};
            this.send = () => {};
            this.abort = () => { this.aborted = true; };
        }
    });
    vm.runInContext(fs.readFileSync(path.join(__dirname, "page", "transport.js"), "utf8"), requestContext);
    const msRequest = vm.runInContext("msRequest", requestContext);
    const answers = [];
    msRequest("GET", "http://127.0.0.1:1/model", null, 2000, (text, status) => answers.push([text, status]));
    check("each request bounded by a timer of the page", timeouts.length === 1 && timeouts[0].ms === 2000);
    timeouts[0].callback();
    check("a request that never answers ends as nothing answered, and is stopped", answers.length === 1
        && answers[0][0] === null && answers[0][1] === 0 && requests[0].aborted === true);
    requests[0].status = 200;
    requests[0].responseText = "late";
    requests[0].onload();
    check("its late answer is ignored", answers.length === 1);
    msRequest("GET", "http://127.0.0.1:1/model", null, 2000, (text, status) => answers.push([text, status]));
    requests[1].status = 200;
    requests[1].responseText = "in time";
    requests[1].onload();
    check("an answer in time: given once, its timer stopped", answers.length === 2 && answers[1][0] === "in time"
        && timeouts[1].cleared === true);
});

// Key capture (capture.js), on a stand-in page: a capture ended by the page asks Python once whether it already
// holds a key, and stops Python's capture; a start left without an answer stops it too (review, 26 October 2026).
section("capture", () => {
    const captureContext = vm.createContext({
        console: console,
        performance: { now: () => 0 },
        setTimeout: () => 1,
        clearTimeout: () => {},
        document: { addEventListener: () => {}, removeEventListener: () => {} }
    });
    for (const name of ["models.js", "logic.js", "data.js", "capture.js"]) {
        vm.runInContext(fs.readFileSync(path.join(__dirname, "page", name), "utf8"), captureContext);
    }
    const MsCapture = vm.runInContext("MsCapture", captureContext);
    const calls = [];
    const captured = [];
    const stand = {
        config: constants, data: { python: true, revision: 3 },
        report: () => {}, notify: () => {}, refresh: () => {},
        settings: { keyCaptured: (piece, key) => captured.push([piece.row.ident, key]) },
        transport: {
            capture: (body, done) => calls.push({ kind: JSON.parse(body).action, body: JSON.parse(body), done: done }),
            captureState: (done) => calls.push({ kind: "state", done: done })
        }
    };
    const piece = (ident) => ({ row: { ident: ident }, entry: { querySelector: () => ({ textContent: "Key" }) } });
    const capture = new MsCapture(stand);
    capture.start(piece("m0_6"));
    check("a start names its row and its model", calls[0].kind === "start" && calls[0].body.id === "m0_6"
        && calls[0].body.revision === 3);
    calls[0].done(wrap({ state: "started" }));
    capture.cancel("screen_changed");
    check("ended at once by the page", capture.active === false);
    check("then Python asked once whether it holds a key", calls[1].kind === "state");
    calls[1].done(wrap({ state: "done", key: "K" }));
    check("a key Python already holds is shown on its row", captured.length === 1 && captured[0][0] === "m0_6"
        && captured[0][1] === "K");
    check("and Python's capture stopped after", calls[2].kind === "cancel");
    capture.start(piece("m0_7"));
    capture.cancel("escape");
    check("ended before Python said it started: stopped at once, its state not read",
        calls[3].kind === "start" && calls[4].kind === "cancel" && calls.length === 5 && captured.length === 1);
    capture.start(piece("m0_8"));
    calls[5].done(null, 0);
    check("a start left without an answer: ended, and Python told to stop", capture.active === false
        && calls[6].kind === "cancel");
});

// Python's model (data.js): a 503 is loading, asked again a bounded number of times; once those are spent the page
// says the list is not ready instead of "wait" for ever (second review, 26 October 2026).
section("model", () => {
    const dataContext = vm.createContext({ console: console, performance: { now: () => 0 },
        setTimeout: (callback) => callback() });
    for (const name of ["models.js", "logic.js", "data.js"]) {
        vm.runInContext(fs.readFileSync(path.join(__dirname, "page", name), "utf8"), dataContext);
    }
    const MsData = vm.runInContext("MsData", dataContext);
    let answer = [null, 503];
    let asked = 0;
    const data = new MsData(constants, { getModel: (done) => { asked += 1; done(answer[0], answer[1]); } }, () => {});
    data.refresh(() => {}, () => {});
    check("a 503 asked again, a bounded number of times", asked === constants.page.model.retries + 1);
    check("then still loading, said not ready", data.python === null && data.notReady === true);
    answer = [null, 0];
    data.refresh(() => {}, () => {});
    check("nothing answering is absent, no longer not ready", data.python === false && data.notReady === false);
});

// The status line (logic.js msStatusText): what Python's state is, in the player's words.
const statusTexts = constants.page.statusTexts;
const statusOf = (python, notReady, model, notice) => api.msStatusText(statusTexts,
    { python: python, notReady: notReady, model: model }, notice || "");
check("waiting for Python: please wait", statusOf(null, false, null) === statusTexts.loading);
check("Python answered, the list never ready: said so", statusOf(null, true, null) === statusTexts.notReady);
check("Python with its list: nothing but the notice", statusOf(true, false, {}, "N") === "N");
check("nothing answering, no list: says what to do, and no list", statusOf(false, false, null) ===
    statusTexts.pythonAbsent + " | " + statusTexts.noMods);

// A refused change (page.js changeRefused), on a stand-in page: its row shows the mod's value again by a forced
// model, unless a newer value of that row still waits to leave, which then decides (second review).
section("refusal", () => {
    const pageContext = vm.createContext({ console: console });
    vm.runInContext(fs.readFileSync(path.join(__dirname, "page", "page.js"), "utf8"), pageContext);
    const changeRefused = vm.runInContext("MsPage.prototype.changeRefused", pageContext);
    let refreshed = 0;
    const stand = { config: constants, notify: () => {}, refresh: () => { refreshed += 1; },
        settings: { changed: new Set(["m0_1"]) }, data: { forceNext: false } };
    changeRefused.call(stand, 503, "m0_1", true);
    check("a newer value waits: the row left as it is", stand.settings.changed.has("m0_1") && refreshed === 0
        && stand.data.forceNext === false);
    changeRefused.call(stand, 409, "m0_1", false);
    check("none waits: the row no longer changed, the model forced and asked", !stand.settings.changed.has("m0_1")
        && stand.data.forceNext === true && refreshed === 1);
});

// The game's language (language.js): English, French, Chinese; any other stays English.
const localized = vm.runInContext("msLocalized", context);
const gameLanguage = vm.runInContext("msGameLanguage", context);
const french = localized(shared, "fr");
check("French texts", french.language === "fr" && french.page.closeLabel === shared.texts.fr.closeLabel
    && french.page.statusTexts.loading === shared.texts.fr.statusTexts.loading);
const chinese = localized(shared, "zh");
check("Chinese texts", chinese.page.entryLabel === shared.texts.zh.entryLabel
    && chinese.page.generalLabel === shared.texts.zh.generalLabel);
const other = localized(shared, "de");
check("any other language stays English", other.language === "en" && other.page.closeLabel === shared.texts.en.closeLabel);
const gaps = JSON.parse(JSON.stringify(shared));
delete gaps.texts.fr.openLabel;
delete gaps.texts.fr.statusTexts.refused;
const patched = localized(gaps, "fr");
check("a missing French text falls back to English", patched.page.openLabel === shared.texts.en.openLabel
    && patched.page.statusTexts.refused === shared.texts.en.statusTexts.refused
    && patched.page.closeLabel === shared.texts.fr.closeLabel);
check("shared config left untouched", shared.page.closeLabel === undefined && !("language" in shared));
const every = ["en", "fr", "zh"].every((code) => Object.keys(shared.texts.en).every((key) => key in shared.texts[code])
    && Object.keys(shared.texts.en.statusTexts).every((key) => key in shared.texts[code].statusTexts));
check("each language has every text", every);
// The game's own translation of its Quit Game entry, as engine.translate gives it (.locres of the Steam copy).
const engineSaying = (text) => ({ translate: (key) => (key === shared.languages.sample.key ? text : key) });
const said = (text) => JSON.stringify(gameLanguage(shared, engineSaying(text), null));
check("French game", said("Quitter le jeu") === '{"code":"fr","source":"translate"}');
check("Simplified Chinese game", said("退出游戏") === '{"code":"zh","source":"translate"}');
check("English game", said("Quit Game") === '{"code":"en","source":"translate"}');
check("case and spaces do not matter", gameLanguage(shared, engineSaying(" QUITTER LE JEU "), null).code === "fr");
check("Traditional Chinese game stays English", said("退出遊戲") === '{"code":"en","source":"translate_other"}');
check("German game stays English", said("Spiel beenden") === '{"code":"en","source":"translate_other"}');
const entryDoc = (text) => ({ querySelector: (selector) =>
    (selector === '[data-l10n-id="' + shared.languages.sample.key + '"]' ? { textContent: text } : null) });
check("no translate: the menu entry's text", JSON.stringify(gameLanguage(shared, null, entryDoc("Quitter le jeu")))
    === '{"code":"fr","source":"element"}');
check("translate gives nothing: the menu entry's text", gameLanguage(shared, engineSaying(""), entryDoc("退出游戏")).code
    === "zh");
const throwing = { translate: () => { throw new Error("no"); } };
check("a failing translate: the entry's text, never a crash", gameLanguage(shared, throwing, entryDoc("Quitter le jeu"))
    .code === "fr");
check("no way to read the language: English", JSON.stringify(gameLanguage(shared, null, null))
    === '{"code":"en","source":"none"}');

console.log(failures.length === 0 ? "RESULTAT: OK" : "RESULTAT: ECHEC " + failures.length);
process.exit(failures.length === 0 ? 0 : 1);
