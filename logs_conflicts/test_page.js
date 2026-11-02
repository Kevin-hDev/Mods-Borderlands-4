/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// Tests of the page script as the pak carries it (pak_recipe.py builds it: one scope, the config the pak sends) on a
// fake menu, a fake document and a fake service. node test_page.js   (Python runs the recipe: PYTHON, else python)

const childProcess = require("child_process");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const constants = JSON.parse(fs.readFileSync(path.join(__dirname, "logs_conflicts", "assets",
    "logs_conflicts.constants.json"), "utf8"));
const built = childProcess.execFileSync(process.env.PYTHON || "python", [path.join(__dirname, "pak_recipe.py")],
    { encoding: "utf8", env: Object.assign({}, process.env, { PYTHONDONTWRITEBYTECODE: "1" }) });
const failures = [];

function expect(condition, label) {
    if (!condition) {
        failures.push(label);
        console.log("ECHEC: " + label);
    }
}

// The height a new element gets: 0 stands for a box not laid out yet.
let layoutHeight = 400;

function element(tag) {
    const node = {
        tag: tag, className: "", text: "", style: { display: "" }, dataset: {}, children: [], listeners: {},
        parentNode: null, attributes: {}, scrollTop: 0, scrollHeight: 5000, offsetHeight: layoutHeight,
        get textContent() { return this.text + this.children.map((child) => child.textContent).join(""); },
        set textContent(value) { this.text = String(value); this.children = []; },
        get firstChild() { return this.children[0] || null; },
        appendChild(child) {
            if (child.tag === "#fragment") {
                for (const moved of child.children.slice()) this.appendChild(moved);
                child.children = [];
                return child;
            }
            child.parentNode = this;
            this.children.push(child);
            return child;
        },
        removeChild(child) { this.children = this.children.filter((c) => c !== child); child.parentNode = null; },
        addEventListener(type, handler) { (this.listeners[type] = this.listeners[type] || []).push(handler); },
        dispatchEvent() {},
        getAttribute(name) { return name in this.attributes ? this.attributes[name] : null; },
        querySelector(selector) {
            const attribute = selector.match(/^\[data-([a-z-]+)="([^"]*)"\]$/);
            if (!attribute) return find(this, (n) => n.classList.contains(selector.slice(1)));
            const key = attribute[1].replace(/-([a-z])/g, (_all, letter) => letter.toUpperCase());
            return find(this, (n) => n.dataset[key] === attribute[2]);
        },
        fire(type, event) { for (const handler of this.listeners[type] || []) handler(event || {}); }
    };
    node.classList = {
        names: () => node.className.split(/\s+/).filter(Boolean),
        contains(name) { return this.names().includes(name); },
        toggle(name, on) {
            const wanted = on === undefined ? !this.contains(name) : on;
            node.className = (wanted ? this.names().filter((n) => n !== name).concat([name])
                                     : this.names().filter((n) => n !== name)).join(" ");
            return wanted;
        },
        add(name) { this.toggle(name, true); }
    };
    return node;
}

function find(node, test) {
    for (const child of node.children) {
        if (test(child)) return child;
        const found = find(child, test);
        if (found) return found;
    }
    return null;
}

const sent = [];
const answers = {
    hello: { state: "ready", mod: "1.0.0" },
    log: { state: "ok", revision: "10-1", size: 10, cut: 0, masked: 1, readAt: "14:32:05",
           head: "line <b>bold</b>\n", tail: "" },
    "log?rev=10-1": { state: "unchanged", revision: "10-1" },
    conflicts: { state: "ok", sections: { failed: [], twice: [], files: [], commands: [], settings: [],
                 keys: [{ name: "F5", items: [{ mod: "A", name: "Dash", fixed: false },
                 { mod: "B", name: "View", fixed: true }], more: 0 }] },
                 checked: { mods: 2, keys: 3, commands: 0, containers: 4 }, unreadable: { mods: 0, containers: 0 },
                 log: "read", paks: "read", partial: false, cut: false },
    copy: { state: "ok", bytes: 120 },
    "copy-conflicts": { state: "ok", bytes: 80 },
    "open-folder": { state: "error", code: "folder_failed" },
    event: {}
};
const documentListeners = {};
const observers = [];
const defined = {};
const bars = [];
// Every timer runs at once; its wait is recorded (the entry's tries wait longer each time).
const delays = [];
// null: the service answers at once; an array: answers wait there until flush() (the queue's tests).
let held = null;
// null: frames run at once; an array: they wait there until frames() (a view left before its frame).
let frameQueue = null;
// The other widgets document.querySelectorAll finds, by selector (the main menu's).
let otherWidgets = {};
let inFlight = 0;
let mostInFlight = 0;

function flush() {
    while (held && held.length) held.shift()();
}

function frames() {
    while (frameQueue && frameQueue.length) frameQueue.shift()();
}

const context = {
    console: console,
    setTimeout: (callback, ms) => { delays.push(ms); return setTimeout(callback, 0); },
    clearTimeout: clearTimeout,
    performance: { now: () => 0 },
    requestAnimationFrame: (callback) => (frameQueue ? frameQueue.push(callback) : callback()),
    CustomEvent: class {},
    InputMgr: { InputDeviceType: 1 },
    OAKScroll: class { constructor(holder) { bars.push(holder); } },
    GbxCustomElement: class { Init() {} getAttribute() { return this.host; } },
    MutationObserver: class {
        constructor(callback) { this.callback = callback; this.target = null; this.targets = []; observers.push(this); }
        observe(target) { this.target = target; this.targets.push(target); }
        disconnect() { this.target = null; this.targets = []; }
    },
    XMLHttpRequest: class {
        open(method, url) { this.route = url.split(constants.http.basePath)[1]; }
        send(body) {
            sent.push({ route: this.route, body: body ? JSON.parse(body) : null });
            inFlight += 1;
            mostInFlight = Math.max(mostInFlight, inFlight);
            const answer = () => {
                inFlight -= 1;
                this.status = 200;
                const found = answers[this.route];
                this.responseText = JSON.stringify(found && typeof found === "object"
                    ? Object.assign({ marker: constants.marker }, found) : found);
                this.onload();
            };
            if (held) held.push(answer);
            else answer();
        }
        abort() {}
    },
    document: {
        createElement: element,
        createDocumentFragment: () => element("#fragment"),
        addEventListener(type, handler) { (documentListeners[type] = documentListeners[type] || []).push(handler); },
        removeEventListener(type, handler) {
            documentListeners[type] = (documentListeners[type] || []).filter((h) => h !== handler);
        },
        querySelector() { return null; },
        querySelectorAll(selector) { return otherWidgets[selector] || []; }
    }
};
context.window = context;
context.customElements = { define(name, made) { defined[name] = made; } };
vm.createContext(context);
vm.runInContext(built, context);
const en = constants.texts.en;
const masked = en.states.masked.replace("{replacement}", constants.masking.replacement);

function events(name) {
    return sent.filter((s) => s.route === "event" && s.body.event === name).map((s) => s.body);
}

function menu(withRoute, host = "pause") {
    const widget = element("widget");
    const layer = element("div");
    widget.querySelector = (selector) => (selector === constants.page.hosts[host].layers[0] ? layer : null);
    widget.claims = [];
    if (withRoute) widget.TriggerWidgetEvent = (name, ident) => widget.claims.push(name + ":" + ident);
    const entry = element("entry");
    const button = element("gbx-list-button");
    button.dataset.inputElem = "true";
    const label = element("p");
    label.className = "button_txt";
    button.appendChild(label);
    entry.appendChild(button);
    entry.style.display = "none";
    entry.attributes["data-menu-entries"] = "1";
    const made = new defined["logs-conflicts-hook"]();
    Object.assign(made, { parentElement: entry, parentWidget: widget, host: host });
    return { widget: widget, layer: layer, entry: entry, label: label, button: button, hook: made };
}

// The entry's observer, called as the game's changes to the menu's layer would call it.
function layerChanged(m) {
    for (const observer of observers) if (observer.targets.includes(m.layer)) observer.callback();
}

// The menu leaves for another page and comes back: its layer hidden, then shown again.
function menuBack(m) {
    m.layer.style.display = "none";
    layerChanged(m);
    m.layer.style.display = "";
    layerChanged(m);
}

function click(node) {
    let stopped = false;
    node.fire("click", { stopPropagation() { stopped = true; } });
    return stopped;
}

function input(name) {
    for (const handler of (documentListeners[constants.page.input.event] || []).slice()) {
        handler({ detail: { inputActionType: 1, inputActionName: name } });
    }
}

function escape() {
    for (const handler of (documentListeners[constants.page.escape.event] || []).slice()) {
        handler({ detail: { ident: "LogsConflicts" } });
    }
}

function root(m) { return m.widget.children[0]; }
function byClass(m, name) { return find(root(m), (n) => n.classList.contains(name)); }
function button(m, index) {
    return byClass(m, "lc_column").children.filter((c) => c.classList.contains("lc_nav_entry"))[index];
}

function testLoadAndEntry(m) {
    expect(events("script_loaded").length === 1 && events("language")[0].code === "en", "load and language reported");
    m.hook.Init();
    expect(m.entry.style.display === "" && events("entry_shown").length === 1, "entry shown once the service answers");
    expect(events("entry_shown")[0].menu_entries === "1", "the shared file's version read on the built entry");
    expect(m.label.textContent === en.entryLabel, "entry renamed");
    expect(m.button.dataset.inputDisabled === undefined, "shown, the entry is in the list's navigation");
    expect(typeof context.lcInstall === "undefined" && typeof context.LcPage === "undefined" &&
           context.LogsConflicts && context.LogsConflicts.page, "the built script's one global");
}

function testOpenLog(m) {
    click(m.entry);
    expect(events("entry_clicked")[0].device === "gamepad", "entry click logged with the input device");
    expect(m.layer.style.display === "none"
           && m.widget.claims[0] === "Event_OnCohEscapeInputHandlerAdded:LogsConflicts",
           "menu hidden and Escape claimed");
    expect(button(m, 0).firstChild.classList.contains("selected") && byClass(m, "lc_panel_title").textContent ===
           en.logsTitle, "logs view selected first");
    expect(byClass(m, "lc_log").textContent === "line <b>bold</b>\n", "the log set as text, markup shown as it is");
    const status = byClass(m, "lc_status").textContent;
    expect(status === "Log of this session, 10 B. Read at 14:32:05." + masked, "log state, the mask named");
    expect(bars.length === 1 && events("scroll")[0].source === "game", "the game's bar made once");
    expect(byClass(m, "lc_scroll").scrollTop === 5000, "the log opens on its end");
    expect(events("timings").some((t) => "request" in t && "render" in t), "times measured");
}

function testViewsAndActions(m) {
    click(button(m, 1));
    expect(button(m, 1).firstChild.classList.contains("selected")
           && !button(m, 0).firstChild.classList.contains("selected"), "conflicts selected");
    expect(byClass(m, "lc_conflicts").textContent === en.states.keysTitle + en.states.keysHelp + en.states.keysFix +
           'Keyboard: F5A, action "Dash"B, action "View" (cannot be changed)' &&
           byClass(m, "lc_log").classList.contains("lc_hidden"),
           "conflicts shown by section, with what they do, the key's name, log hidden");
    expect(byClass(m, "lc_section").textContent === en.states.keysTitle
           && byClass(m, "lc_help").textContent === en.states.keysHelp, "a section's title and help have their look");
    expect(byClass(m, "lc_key").textContent === "Keyboard: F5"
           && byClass(m, "lc_use").textContent === 'A, action "Dash"',
           "a conflict's name and its lines have their look");
    const listed = byClass(m, "lc_conflicts").textContent;
    click(button(m, 1));
    expect(byClass(m, "lc_conflicts").textContent === listed, "the conflicts read again replace the list shown");
    expect(byClass(m, "lc_status").textContent === "1 conflict(s) found between your mods." +
           "2 enabled mods, 3 keys, 0 console commands and 4 mod package files (.pak, .utoc) checked.",
           "the conflicts' state");
    expect(button(m, 3).classList.contains("lc_hidden") && !button(m, 2).classList.contains("lc_hidden"),
           "OPEN FOLDER hidden with the conflicts, COPY kept");
    click(button(m, 2));
    expect(sent.filter((s) => s.route === "copy-conflicts").length === 1 &&
           byClass(m, "lc_notice").textContent === "Copied: 80 B.",
           "COPY copies the conflicts in their view");
    click(button(m, 0));
    expect(!button(m, 3).classList.contains("lc_hidden"), "OPEN FOLDER back with the log");
    click(button(m, 2));
    expect(sent.filter((s) => s.route === "copy").length === 1 && byClass(m, "lc_notice").textContent ===
           "Copied: 120 B.", "COPY copies the log in its view");
    click(button(m, 3));
    expect(byClass(m, "lc_notice").textContent === en.errors.folder_failed &&
           byClass(m, "lc_notice").classList.contains("lc_error"), "folder failure told as an error");
    click(button(m, 1));
    click(button(m, 0));
    expect(sent.some((s) => s.route === "log?rev=10-1") && byClass(m, "lc_log").textContent === "line <b>bold</b>\n" &&
           byClass(m, "lc_notice").textContent === "", "log asked with its revision, text kept when unchanged");
    expect(byClass(m, "lc_scroll").scrollTop === 5000, "back from the conflicts, an unchanged log shows its end again");
    answers["log?rev=10-1"] = { state: "error", code: "log_refused" };
    click(button(m, 0));
    expect(byClass(m, "lc_log").textContent === "line <b>bold</b>\n" &&
           byClass(m, "lc_notice").textContent === en.errors.log_refused,
           "an error keeps the text and says what to do");
    answers["log?rev=10-1"] = { state: "unchanged", revision: "10-1" };
    held = [];
    click(button(m, 2));
    click(button(m, 1));
    flush();
    held = null;
    expect(byClass(m, "lc_notice").textContent === "", "a copy's answer is not told in another view");
    click(button(m, 0));
}

function testGamepad(m) {
    input("Input.Action.Menu.Unknown");
    expect(events("input_action")[0].name === "input_action_menu_unknown" &&
           !button(m, 0).firstChild.classList.contains("hover_effect"), "an action without a move is reported only");
    input("Input.Action.Menu.NavDown");
    expect(button(m, 0).firstChild.classList.contains("hover_effect"), "first move shows the focus");
    input("Input.Action.Menu.NavDown");
    expect(button(m, 1).firstChild.classList.contains("hover_effect") &&
           !button(m, 0).firstChild.classList.contains("hover_effect"), "down moves along the buttons");
    input("Input.Action.Menu.NavRight");
    expect(byClass(m, "lc_panel").classList.contains("lc_focused"), "right goes to the panel");
    const holder = byClass(m, "lc_scroll");
    holder.scrollTop = 0;
    input("Input.Action.Menu.NavDown");
    expect(holder.scrollTop === constants.page.scrollStepPx, "down scrolls the panel");
    input("Input.Action.Menu.NavLeft");
    expect(button(m, 1).firstChild.classList.contains("hover_effect"), "left comes back to the button left");
    input("Input.Action.Menu.NavSelect");
    expect(byClass(m, "lc_panel_title").textContent === en.conflictsTitle, "select presses the button in focus");
    input("Input.Action.UI.Lobby.TabRight");
    expect(byClass(m, "lc_panel_title").textContent === en.logsTitle, "a tab action switches views");
    testPointerAndHidden(m);
    for (let press = 0; press < constants.page.input.maxReports; press += 1) input("Input.Action.Menu.Unknown");
    expect(events("input_action").length === constants.page.input.maxReports, "input reports bounded");
}

// A mouse click sends the game's select action too (trial 1): it must not press the button under the pointer again,
// nor the button the focus was on. The gamepad skips OPEN FOLDER while the conflicts hide it.
function testPointerAndHidden(m) {
    const highlighted = (index) => button(m, index).firstChild.classList.contains("hover_effect");
    const copies = sent.filter((s) => s.route === "copy").length;
    button(m, 2).fire("mouseenter");
    input("Input.Action.Menu.NavSelect");
    expect(sent.filter((s) => s.route === "copy").length === copies && highlighted(2),
           "the select action of a mouse click presses nothing more");
    button(m, 2).fire("mouseleave");
    input("Input.Action.Menu.NavSelect");
    expect(!highlighted(2) && byClass(m, "lc_panel_title").textContent === en.logsTitle &&
           sent.filter((s) => s.route === "copy").length === copies, "a click away from the buttons presses nothing");
    input("Input.Action.Menu.NavDown");
    input("Input.Action.Menu.NavDown");
    expect(highlighted(3), "the gamepad reaches OPEN FOLDER with the log");
    input("Input.Action.Menu.TabRight");
    expect(highlighted(2) && !highlighted(3), "shown the conflicts, the focus leaves OPEN FOLDER for COPY");
    input("Input.Action.Menu.NavDown");
    expect(highlighted(2), "down stays on COPY: OPEN FOLDER is skipped");
    input("Input.Action.Menu.NavUp");
    expect(highlighted(1), "up goes on to CONFLICTS");
}

function testCloseAndReopen(m) {
    expect(click(m.entry) && events("page_opened").length === 1, "the hidden entry clicked while open does nothing");
    for (const handler of (documentListeners[constants.page.escape.event] || []).slice()) {
        handler({ detail: { ident: "LogsConflicts" } });
    }
    expect(events("page_closed")[0].reason === "escape" && m.layer.style.display === "" &&
           root(m).classList.contains("lc_hidden"), "Escape closes the page and gives the menu back");
    expect((documentListeners[constants.page.input.event] || []).length === 0 &&
           (documentListeners[constants.page.escape.event] || []).length === 0 &&
           !observers.some((observer) => observer.target === m.widget), "closed, the page leaves no listener behind");
    const built = root(m);
    click(m.entry);
    expect(root(m) === built && m.widget.children.length === 1 && !built.classList.contains("lc_hidden"),
           "opened again without building again");
    m.widget.classList.add("inactive");
    for (const observer of observers) if (observer.target === m.widget) observer.callback();
    expect(events("page_closed")[1].reason === "menu_closed", "closes with the menu");
    const bare = menu(false);
    bare.hook.Init();
    click(bare.entry);
    expect(events("error").some((e) => e.code === "no_widget") && bare.layer.style.display === "",
           "a menu without its event route is refused and left as it was");
}

function testHelloRetries(done) {
    answers.hello = { state: "busy" };
    const before = sent.filter((s) => s.route === "hello").length;
    const late = menu(true);
    late.hook.Init();
    setTimeout(() => {
        const retries = constants.http.helloRetriesMs;
        expect(sent.filter((s) => s.route === "hello").length - before === retries.length + 1 &&
               late.entry.style.display === "none" && late.button.dataset.inputDisabled === "true",
               "tries bounded, the entry left hidden and out of the navigation without an answer");
        expect(delays.filter((ms) => retries.includes(ms)).join() === retries.join(), "each try waits longer");
        done();
    }, 100);
}

// MODS may turn this mod off, or on, while the menu stays loaded: the entry follows when the menu comes back, and a
// click on an entry whose service stopped opens nothing (audit, 1 November 2026).
function testServiceTurnedOff() {
    answers.hello = { state: "ready", mod: "1.0.0" };
    const m = menu(true);
    m.hook.Init();
    const hellos = () => sent.filter((s) => s.route === "hello").length;
    const asked = hellos();
    layerChanged(m);
    m.layer.style.display = "none";
    layerChanged(m);
    expect(hellos() === asked, "a change while the menu stays shown, or while it is hidden, asks nothing");
    menuBack(m);
    expect(hellos() === asked + 1, "the menu shown again asks once");
    answers.hello = { state: "busy" };
    menuBack(m);
    expect(m.entry.style.display === "none" && m.button.dataset.inputDisabled === "true",
           "turned off meanwhile: hidden when the menu comes back");
    answers.hello = { state: "ready", mod: "1.0.0" };
    menuBack(m);
    expect(m.entry.style.display === "" && m.button.dataset.inputDisabled === undefined,
           "turned on meanwhile: shown when the menu comes back");
    // The menu may also come back by losing the game's inactive class alone (widget_class.js), its layer left shown.
    const classBack = () => {
        for (const on of [true, false]) {
            m.widget.classList.toggle("inactive", on);
            for (const observer of observers) if (observer.targets.includes(m.widget)) observer.callback();
        }
    };
    answers.hello = { state: "busy" };
    classBack();
    expect(m.entry.style.display === "none", "a menu back by losing its inactive class asks again: hidden");
    answers.hello = { state: "ready", mod: "1.0.0" };
    classBack();
    expect(m.entry.style.display === "", "a menu back by losing its inactive class asks again: shown");
    const opened = events("page_opened").length;
    answers.hello = { state: "busy" };
    click(m.entry);
    expect(events("page_opened").length === opened && m.entry.style.display === "none",
           "a click on a stopped service opens nothing and hides the entry");
    expect(click(m.entry) && events("page_opened").length === opened, "a hidden entry reached anyway does nothing");
    answers.hello = { state: "ready", mod: "1.0.0" };
    expect(observers.filter((observer) => observer.targets.includes(m.layer)).length === 1,
           "one watch of the menu, however many clicks");
}

// A menu closed between the click and the service's answer: the page does not open over it (review).
function testClosedMenu() {
    const m = menu(true);
    m.hook.Init();
    const opened = events("page_opened").length;
    const shown = events("entry_shown").length;
    const errors = events("error").length;
    held = [];
    click(m.entry);
    m.widget.classList.add("inactive");
    flush();
    held = null;
    expect(events("page_opened").length === opened && m.layer.style.display === ""
           && !context.LogsConflicts.page.isOpen, "a menu closed before the service answers is left as it was");
    expect(events("entry_shown").length === shown, "an entry already shown is not reported shown again");
    expect(events("error").length === errors, "a menu closed before the answer is expected: no error in the log");
}

// A label the game already wrote right is not written again: writing it is a change the entry's observer would see.
function testLabelWrittenOnce() {
    const m = menu(true);
    m.button.removeChild(m.label);
    m.hook.Init();
    const label = element("p");
    label.className = "button_txt";
    label.textContent = en.entryLabel;
    const own = Object.getOwnPropertyDescriptor(label, "textContent");
    let writes = 0;
    Object.defineProperty(label, "textContent", {
        get: own.get,
        set(value) { writes += 1; own.set.call(this, value); }
    });
    m.button.appendChild(label);
    for (const observer of observers) if (observer.target === m.entry) observer.callback();
    expect(writes === 0 && m.button.dataset.inputDisabled === undefined, "a label already right is left alone");
}

// After the tries' test: this entry's own tries would be counted with them.
function testRefused(answer, label, done) {
    answers.hello = answer;
    const other = menu(true);
    other.hook.Init();
    setTimeout(() => {
        expect(other.entry.style.display === "none", label);
        answers.hello = { state: "ready", mod: "1.0.0" };
        done();
    }, 100);
}

// A request the service never answers ends at the page's own timer, once: a late answer changes nothing.
function testNoAnswer(done) {
    const before = sent.filter((s) => s.route === "hello").length;
    held = [];
    const m = menu(true);
    m.hook.Init();
    setTimeout(() => {
        const tries = sent.filter((s) => s.route === "hello").length - before;
        flush();
        held = null;
        expect(tries === constants.http.helloRetriesMs.length + 1 && m.entry.style.display === "none",
               "each unanswered request ends at its timer, and the next try goes; a late answer is ignored");
        done();
    }, 100);
}

// An entry the game never fills is watched for a bounded time only.
function testEntryWait(done) {
    const m = menu(true);
    m.entry.removeChild(m.button);
    m.hook.Init();
    setTimeout(() => {
        expect(!observers.some((observer) => observer.target === m.entry), "the entry's watch ends after its wait");
        done();
    }, 100);
}

function testQueueAndHandlers() {
    const m = menu(true);
    m.hook.Init();
    held = [];
    mostInFlight = inFlight;
    click(m.entry);
    flush();
    held = null;
    expect(mostInFlight <= 1, "one request at a time: the service has one thread");
    const errors = events("error").length;
    const conflicts = answers.conflicts;
    answers.conflicts = JSON.parse(JSON.stringify(conflicts));
    answers.conflicts.sections.keys = [null];
    click(button(m, 1));
    answers.conflicts = conflicts;
    expect(events("error").slice(errors).some((e) => e.code === "answer_failed"),
           "an answer's handler that throws is reported, not lost");
    answers.conflicts = JSON.parse(JSON.stringify(conflicts));
    delete answers.conflicts.sections.files;
    click(button(m, 1));
    answers.conflicts = conflicts;
    expect(byClass(m, "lc_notice").textContent === en.errors.no_answer,
           "an answer without one of its sections refused");
    const askedFor = (route) => sent.filter((s) => s.route === route).length;
    const conflictsAsked = askedFor("conflicts");
    held = [];
    click(button(m, 0));
    click(button(m, 1));
    click(button(m, 1));
    flush();
    held = null;
    expect(askedFor("conflicts") - conflictsAsked === 1, "the conflicts pressed again while they load are asked once");
    answers.conflicts = JSON.parse(JSON.stringify(conflicts));
    answers.conflicts.sections.commands = [{ name: "late_command", items: ["A", "B"], more: 0 }];
    held = [];
    click(button(m, 1));
    click(button(m, 0));
    flush();
    held = null;
    answers.conflicts = conflicts;
    expect(byClass(m, "lc_conflicts").textContent.indexOf("late_command") < 0,
           "conflicts answered after the player left their view are not drawn");
    const logs = () => sent.filter((s) => s.route.indexOf("log") === 0).length;
    const asked = logs();
    held = [];
    click(button(m, 0));
    click(button(m, 0));
    flush();
    held = null;
    expect(logs() - asked === 1, "a view pressed again while it loads asks once");
    const reported = sent.filter((s) => s.route === "event").length;
    held = [];
    for (let at = 0; at < constants.http.maxQueued + 10; at += 1) context.LogsConflicts.page.report("view");
    flush();
    held = null;
    expect(sent.filter((s) => s.route === "event").length - reported === constants.http.maxQueued + 1,
           "the queue is bounded: past it, a request is dropped");
    frameQueue = [];
    click(button(m, 0));
    click(button(m, 1));
    frames();
    frameQueue = null;
    expect(byClass(m, "lc_scroll").scrollTop === 0, "a log's frame does not scroll the conflicts shown meanwhile");
    escape();
}

// The bar is made once its box has a size; without the game's bar, the log says so.
function testScrollBar() {
    const made = bars.length;
    const scrolls = events("scroll").length;
    layoutHeight = 0;
    const flat = menu(true);
    flat.hook.Init();
    click(flat.entry);
    layoutHeight = 400;
    expect(bars.length === made && events("scroll").length === scrolls, "no bar on a box not laid out yet");
    escape();
    const gameBar = context.OAKScroll;
    context.OAKScroll = undefined;
    const bare = menu(true);
    bare.hook.Init();
    click(bare.entry);
    context.OAKScroll = gameBar;
    expect(events("scroll").slice(scrolls).some((e) => e.source === "absent"), "without the game's bar, said once");
    escape();
}

// Over the main menu: its group panel and news card hidden too, and Escape comes as an input action.
function testMainMenu() {
    const lobby = element("widget-lobby-info");
    const news = element("widget-news");
    news.style.display = "flex";
    otherWidgets = { "widget-lobby-info": [lobby], "widget-news": [news] };
    const m = menu(true, "main");
    m.hook.Init();
    click(m.entry);
    expect(lobby.style.display === "none" && news.style.display === "none" && m.layer.style.display === "none",
           "over the main menu, its other widgets are hidden too");
    input(constants.page.hosts.main.escapeAction);
    expect(events("page_closed").slice(-1)[0].reason === "escape" && lobby.style.display === "" &&
           news.style.display === "flex" && m.layer.style.display === "", "the main menu's Escape action closes the "
           + "page and gives everything back as it was");
    otherWidgets = {};
}

const main = menu(true);
testLoadAndEntry(main);
testOpenLog(main);
testViewsAndActions(main);
testGamepad(main);
testCloseAndReopen(main);
testServiceTurnedOff();
testClosedMenu();
testLabelWrittenOnce();
testQueueAndHandlers();
testScrollBar();
testMainMenu();
const pad = "x".repeat(constants.http.maxResponseBytes);
testHelloRetries(() => testRefused({ state: "ready", mod: "1.0.0", marker: "SOMEONE_ELSE" },
    "an answer without this mod's marker is no answer, every try",
    () => testRefused({ state: "ready", mod: "1.0.0", pad: pad }, "an answer over its bound is no answer",
    () => testNoAnswer(() => testEntryWait(() => {
    console.log(failures.length === 0 ? "RESULTAT: TOUS LES TESTS PASSENT"
                                      : "RESULTAT: " + failures.length + " ECHEC(S)");
    process.exit(failures.length === 0 ? 0 : 1);
})))));
