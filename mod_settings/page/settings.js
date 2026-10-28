/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The page's settings: what the pieces report (the listener the options screen is for its own pieces), what
// goes to Python, and Python's model coming back. A value the player changed since the page opened is never
// replaced by an older one from Python. A locked row never sends anything.

function msRowsById(screen, into) {
    for (const row of screen.rows) {
        if (row.ident) into.set(row.ident, row);
        if (row.target) msRowsById(row.target, into);
    }
    return into;
}

class MsSettings {
    constructor(page) {
        this.page = page;
        this.config = page.config;
        this.changed = new Set();
        this.sounds = 0;
        this.presses = 0;
        this.listener = {
            OnSliderValueChanged: (ident, value) => {
                const piece = this.piece(ident);
                if (!piece) return;
                const clean = msCleanValue(piece.row, value);
                piece.target.SetDisplayTextValue(msValueText(piece.row, clean));
                this.valueChanged(piece, clean);
            },
            OnToggleValueChanged: (ident, value) => this.valueChanged(this.piece(ident), value),
            OnStepperValueChanged: (ident, index) => this.valueChanged(this.piece(ident), index),
            OnDropdownItemSelected: (ident, index) => this.valueChanged(this.piece(ident), index),
            OnDropdownClicked: () => {},
            PlaySoundAtNode: (node, id) => {
                this.page.sound(node, id);
                if (this.sounds < this.config.page.limits.maxSoundReports && typeof id === "string") {
                    this.sounds += 1;
                    this.page.report("sound", { name: id.toLowerCase() });
                }
            }
        };
        // The dropdowns' widget: only the Escape claim reaches the real menu, so the list can close on Escape;
        // the native focus calls are dropped; opening and closing go to the gamepad navigation.
        this.dropdownWidget = {
            WidgetIdent: "mod_settings",
            TriggerWidgetEvent: (name, ident) => {
                const escape = this.config.page.escape;
                if ((name === escape.added || name === escape.removed) && this.page.widget) {
                    this.page.widget.TriggerWidgetEvent(name, ident);
                }
            },
            PlaySoundAtNode: (node, id) => this.page.sound(node, id),
            dispatchEvent: (event) => {
                if (event && event.type === "Event_DropdownNavigationUpdate" && event.detail) {
                    const open = event.detail.navigationEnabled === true;
                    this.page.focus.dropdownChanged(open, event.detail.dropdownInputContainer);
                    this.page.report("dropdown", { state: open ? "open" : "closed" });
                }
                return true;
            },
            addEventListener: () => {},
            removeEventListener: () => {}
        };
    }

    piece(ident) {
        return this.page.screens.find(ident);
    }

    opened() {
        this.changed.clear();
        this.sounds = 0;
    }

    valueChanged(piece, value) {
        if (!piece) return;
        if (piece.row.locked) {
            piece.set(piece.row.initial);
            return;
        }
        const clean = msCleanValue(piece.row, value);
        this.changed.add(piece.row.ident);
        piece.row.initial = clean;
        this.page.sender.sendValue(piece.row.ident, msValueBody(this.config, piece.row, clean, this.page.data.revision));
    }

    // Every row of the pages open over the list, in all their tabs: a tab not shown builds its pieces again from
    // these rows when it comes back, so they must hold the mod's values too (a refused change on another tab).
    openRows() {
        const into = new Map();
        for (const shown of this.page.screens.stack) {
            for (const tab of shown.view.tabs) msRowsById({ rows: tab.rows }, into);
        }
        return into;
    }

    // A newer model: the list is built again; the open page keeps the values the player changed, takes the
    // others, and goes back to the list if its rows are no longer those of the model.
    applyModel(model) {
        const rows = msRowsById(model.root, new Map());
        for (const [ident, row] of this.openRows()) {
            const fresh = rows.get(ident);
            if (fresh && fresh.kind === row.kind && row.kind !== "link" && !this.changed.has(ident)) {
                row.initial = fresh.initial;
            }
        }
        let stale = false;
        for (const piece of this.page.screens.items()) {
            const row = rows.get(piece.row.ident);
            if (!row || row.kind !== piece.row.kind) {
                stale = true;
                continue;
            }
            if (this.changed.has(row.ident) || row.kind === "link") continue;
            piece.row.initial = row.initial;
            piece.set(row.initial);
        }
        if (stale) this.page.screens.reset();
        this.page.showModel(model);
    }

    startCapture(piece, event) {
        if (event) event.stopPropagation();
        if (piece.row.locked) return;
        this.page.capture.start(piece);
    }

    // Python already holds the captured key: the page only shows it.
    keyCaptured(piece, key) {
        this.changed.add(piece.row.ident);
        piece.row.initial = key;
        piece.set(key);
    }

    clearKey(piece, event) {
        if (event) event.stopPropagation();
        if (this.page.capture.active || piece.row.locked) return;
        this.changed.add(piece.row.ident);
        piece.row.initial = null;
        piece.set(null);
        this.page.sender.sendValue(piece.row.ident, msValueBody(this.config, piece.row, null, this.page.data.revision));
    }

    // A link opens its page; a button is counted on screen, so each press shows even without Python.
    pressButton(piece) {
        this.page.sound(piece.target, "ElementClicked");
        if (piece.row.kind === "link") return this.page.openScreen(piece.row);
        if (piece.row.locked) return;
        this.presses += 1;
        this.page.notify(this.config.page.statusTexts.buttonPressed + " (" + this.presses + ")");
        this.page.sender.sendPress(msPressBody(this.config, piece.row, this.page.data.revision));
    }
}
