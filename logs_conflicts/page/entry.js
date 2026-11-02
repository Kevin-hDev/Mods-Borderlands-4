/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The entry of the pause menu and of the main menu, in the shared menu file (conception, section 3). It is shown only
// while the service answers: without Python this mod can read nothing, and a feature is shown working or not at all.
// It asks when the menu loads (a few tries), each time the menu comes back from another page (MODS may have turned
// this mod off or on meanwhile: audit of 1 November 2026), and when clicked. The hook acts in Init(), after
// super.Init(), as Mod Settings' does (the HUD Editor learned not to touch the page from connectedCallback).

class LcEntry {
    constructor(page, entry, host, widget) {
        this.page = page;
        this.entry = entry;
        this.host = host;
        // A function: the hook's parentWidget, read when needed.
        this.widget = widget;
        this.button = null;
        this.shown = false;
        this.watching = false;
        this.checking = false;
    }

    start() {
        this.show(false);
        // The gamepad confirms an entry with a bubbling click (input_manager.js): one listener serves mouse and
        // gamepad.
        this.entry.addEventListener("click", (event) => this.click(event));
        this.whenBuilt();
        this.ask(0, null);
    }

    // Hidden, the entry also leaves the game's list navigation, which skips an input element marked
    // data-input-disabled and never a hidden one (input_behaviors.js, GetNextNode): the gamepad stopped on it unseen.
    show(shown) {
        this.shown = shown;
        this.entry.style.display = shown ? "" : "none";
        if (!this.button) return;
        if (shown) delete this.button.dataset.inputDisabled;
        else this.button.dataset.inputDisabled = "true";
    }

    // The game fills its button after the hook: the label and the input element are set once they exist, and the
    // watch stops then, or after entryWaitMs.
    whenBuilt() {
        const page = this.page.config.page;
        const apply = () => {
            const label = page.entryTextSelectors.map((selector) => this.entry.querySelector(selector)).find(Boolean);
            // Only when it differs: writing the text is itself a change the observer would see again.
            if (label && label.textContent !== page.entryLabel) label.textContent = page.entryLabel;
            this.button = this.entry.querySelector(page.entryInput);
            this.show(this.shown);
            if (!label || !this.button) return false;
            this.watch();
            return true;
        };
        if (apply()) return;
        const observer = new MutationObserver(() => { if (apply()) observer.disconnect(); });
        observer.observe(this.entry, { childList: true, subtree: true });
        setTimeout(() => observer.disconnect(), page.entryWaitMs);
    }

    // attempt: the try at the menu's load (a few, each after a longer wait), or null for a single ask.
    // then(ready), when given, runs with the answer.
    ask(attempt, then) {
        this.page.transport.hello((answer) => {
            const ready = Boolean(answer && answer.state === "ready");
            if (ready && !this.shown) {
                this.page.report("entry_shown", { host: this.host, menu_entries: lcSharedVersion(this.entry) });
            }
            this.show(ready);
            if (then) then(ready);
            const waits = this.page.config.http.helloRetriesMs;
            if (!ready && attempt !== null && attempt < waits.length) {
                setTimeout(() => this.ask(attempt + 1, null), waits[attempt]);
            }
        });
    }

    // Back from another page, the menu shows its layers again or loses the game's inactive class: asked again then,
    // once per return, not at each change of these attributes (review, 1 November 2026). The observer lives as long
    // as the menu, an exception to OPTI.md rule 1 written in the conception (section 8): it runs only when the game
    // changes these attributes of these few elements, never on its own.
    watch() {
        const widget = this.widget();
        if (this.watching || !widget || !widget.querySelector) return;
        this.watching = true;
        const config = this.page.config.page;
        const targets = [widget.WidgetDiv || widget].concat(config.hosts[this.host].layers
            .map((selector) => widget.querySelector(selector)).filter(Boolean));
        const shown = () => !lcMenuClosed(widget, config)
            && targets.slice(1).every((layer) => layer.style.display !== "none");
        let wasShown = shown();
        const observer = new MutationObserver(() => {
            const now = shown();
            const back = now && !wasShown;
            wasShown = now;
            if (!back || this.page.isOpen || this.checking) return;
            this.checking = true;
            this.ask(null, () => { this.checking = false; });
        });
        const watched = { attributes: true, attributeFilter: ["class", "style"] };
        for (const target of targets) observer.observe(target, watched);
    }

    // While the page is open the game may still click this hidden entry, and a hidden entry reached anyway must do
    // nothing: both stopped here. The page opens only if the service still answers.
    click(event) {
        // The menu's widget may be known only now: the watch starts here then.
        this.watch();
        if (this.page.isOpen || !this.shown) {
            event.stopPropagation();
            return;
        }
        this.page.report("entry_clicked", { host: this.host, device: this.page.inputDevice() });
        const widget = this.widget();
        this.ask(null, (ready) => { if (ready) this.page.open(widget, this.host); });
    }
}

// The shared menu file's version, as its entries carry it: a gap between the two mods' versions shows in the log.
// Read on the entry once built: looked up when the script loads, it was not there yet (trial 1).
function lcSharedVersion(entry) {
    const version = entry.getAttribute ? entry.getAttribute("data-menu-entries") : null;
    return version && /^[0-9]{1,4}$/.test(version) ? version : "none";
}

function lcInstall(shared) {
    const language = lcGameLanguage(shared, typeof engine !== "undefined" ? engine : null, document);
    const config = lcLocalized(shared, language.code);
    let page = null;
    page = new LcPage(config, lcTransport(config, () => page.report("error", { code: "answer_failed" })));

    class LogsConflictsHook extends GbxCustomElement {
        Init() {
            super.Init();
            const entry = this.parentElement;
            if (!entry || entry.logsConflictsReady) return;
            entry.logsConflictsReady = true;
            new LcEntry(page, entry, this.getAttribute("host"), () => this.parentWidget).start();
        }
    }

    window.customElements.define("logs-conflicts-hook", LogsConflictsHook);
    page.report("script_loaded");
    page.report("language", { code: config.language, source: language.source });
    return { page: page };
}
