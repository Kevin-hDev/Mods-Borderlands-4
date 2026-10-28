/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The key capture of the keybind row. The game does not hand a menu page the keys (only menu actions and
// Escape), and the SDK's keybinds ignore keys while the cursor shows (HUD Editor, raccourci-integre/README.md):
// Python reads the keyboard through Windows, the reading the HUD Editor proved in game, for capture.maxSeconds at
// most, the same bound on both sides. The page asks it to start, naming the model its row belongs to, then asks for
// the result every pollMs while the capture lasts, and only then.
// The page also notes what keydown and mousedown it receives itself: does Gameface give them to a menu page?

class MsCapture {
    constructor(page) {
        this.page = page;
        this.config = page.config;
        this.piece = null;
        // True once Python answered that its capture started: only then is its state this capture's.
        this.started = false;
        this.timer = null;
        this.deadline = 0;
        this.label = "";
        this.inputs = 0;
        this.onKey = (event) => this.noteInput("keydown", event.code);
        this.onMouse = (event) => this.noteInput("mousedown", "mouse" + event.button);
    }

    get active() { return this.piece !== null; }

    start(piece) {
        if (this.piece) return;
        if (this.page.data.python !== true) {
            this.page.report("capture", { state: "no_python", ident: piece.row.ident });
            this.page.notify(this.config.page.statusTexts.captureNeedsPython);
            return;
        }
        this.piece = piece;
        this.started = false;
        this.deadline = msNow() + this.config.capture.maxSeconds * 1000;
        const text = piece.entry.querySelector(".menu_options_entry_text");
        this.label = text ? text.textContent : "";
        if (text) text.textContent = this.config.page.captureLabel;
        document.addEventListener("keydown", this.onKey, true);
        document.addEventListener("mousedown", this.onMouse, true);
        this.page.report("capture", { state: "start", ident: piece.row.ident });
        const body = msCaptureBody(this.config, "start", piece.row.ident, this.page.data.revision);
        this.page.transport.capture(body, (reply) => {
            const state = msParseCapture(reply, this.config);
            if (!this.piece) return;
            if (state && state.state === "started") {
                this.started = true;
                return this.poll();
            }
            this.finish(state ? state.state : "refused", null);
            // No answer (the page's own timer): Python may still start it afterwards, and a cancel then stops it.
            if (!state) this.stopPython();
            // The row belongs to an older model: the page takes the new one, its rows with it.
            if (state && state.state === "old_model") this.page.refresh();
        });
    }

    poll() {
        this.timer = setTimeout(() => {
            this.timer = null;
            if (!this.piece) return;
            if (msNow() > this.deadline) return this.cancel("timeout");
            this.page.transport.captureState((reply) => {
                if (!this.piece) return;
                const state = msParseCapture(reply, this.config);
                if (state && state.state === "waiting") this.poll();
                else this.finish(state ? state.state : "failed", state ? state.key : null);
            });
        }, this.config.page.capture.pollMs);
    }

    // Python applies a key as soon as it reads it. Once its capture has started, a key pressed just before the page
    // ends the capture (a tab clicked, Escape) is already the mod's: read once, it is shown on its row, shown or not;
    // then Python's capture, if still waiting, is stopped. Before that, its state may still be an older capture's.
    cancel(reason) {
        const piece = this.piece;
        if (!piece) return;
        const started = this.started;
        this.finish(reason, null);
        if (!started) return this.stopPython();
        this.page.transport.captureState((reply) => {
            const state = msParseCapture(reply, this.config);
            if (state && state.state === "done" && state.key) this.page.settings.keyCaptured(piece, state.key);
            this.stopPython();
        });
    }

    stopPython() {
        this.page.transport.capture(msCaptureBody(this.config, "cancel", null), () => {});
    }

    finish(state, key) {
        const piece = this.piece;
        this.piece = null;
        this.started = false;
        if (this.timer !== null) clearTimeout(this.timer);
        this.timer = null;
        document.removeEventListener("keydown", this.onKey, true);
        document.removeEventListener("mousedown", this.onMouse, true);
        const text = piece.entry.querySelector(".menu_options_entry_text");
        if (text) text.textContent = this.label;
        this.page.report("capture", { state: state, ident: piece.row.ident });
        if (state === "done" && key) this.page.settings.keyCaptured(piece, key);
    }

    noteInput(kind, code) {
        if (this.inputs >= this.config.page.limits.maxInputReports) return;
        this.inputs += 1;
        const clean = String(code || "none").toLowerCase().replace(/[^a-z0-9_]/g, "").slice(0, 32) || "none";
        this.page.report("js_input", { name: kind, code: clean });
    }
}
