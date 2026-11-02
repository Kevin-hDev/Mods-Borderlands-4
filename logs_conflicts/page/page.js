/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The page: opened from the entry over the pause or the main menu, closed by Escape, the gamepad's back button or the
// menu's own closing. It shows one view at a time, the log or the conflicts, asked from the service when shown.
// While a view reloads, its previous content stays and the state says so (interface rule 9). Gamepad: the moves go to
// focus.js, the tab actions switch views, the select button presses the button in focus.

function lcNow() {
    return typeof performance !== "undefined" && performance.now ? performance.now() : Date.now();
}

class LcPage {
    constructor(config, transport) {
        this.config = config;
        this.transport = transport;
        this.frame = new LcFrame(this);
        this.focus = new LcFocus(this.frame, config.page.scrollStepPx);
        this.isOpen = false;
        this.release = null;
        this.view = "logs";
        // The log the page shows: its revision lets the service answer "unchanged" without sending it again.
        this.revision = null;
        this.lastLog = null;
        this.loading = { logs: false, conflicts: false };
        this.inputReports = 0;
    }

    report(event, fields) {
        const body = { marker: this.config.marker, event: event };
        for (const key of Object.keys(fields || {})) body[key] = String(fields[key]);
        this.transport.event(body);
    }

    reportTimings(values) {
        const body = { marker: this.config.marker, event: "timings" };
        for (const key of Object.keys(values)) body[key] = Math.max(0, Math.round(values[key]));
        this.transport.event(body);
    }

    inputDevice() {
        const input = typeof InputMgr !== "undefined" && InputMgr ? InputMgr : null;
        return (input && this.config.page.input.devices[String(input.InputDeviceType)]) || "unknown";
    }

    open(widget, host) {
        if (this.isOpen) return;
        const hostConfig = this.config.page.hosts[host];
        if (!hostConfig || !widget || typeof widget.TriggerWidgetEvent !== "function" || !widget.querySelector) {
            this.report("error", { code: "no_widget" });
            return;
        }
        // A menu closed between the click and the service's answer leaves nothing to open over. Expected, so not an
        // error: the log shows the click without a page opened (second review, 1 November 2026).
        if (lcMenuClosed(widget, this.config.page)) return;
        const start = lcNow();
        this.release = lcBorrowMenu(this.config, widget, hostConfig, {
            onEscape: () => this.close("escape"),
            onClose: (reason) => this.close(reason),
            onNav: (move, via) => this.nav(move, via)
        });
        if (!this.release) {
            this.report("error", { code: "menu_borrow_failed" });
            return;
        }
        if (this.frame.widget !== widget || !this.frame.root) {
            this.frame.build(widget);
            this.revision = null;
            this.lastLog = null;
        }
        this.isOpen = true;
        this.frame.show(true);
        this.focus.hide();
        this.report("page_opened", { host: host });
        this.showView(this.view);
        this.reportTimings({ shown: lcNow() - start });
    }

    close(reason) {
        if (!this.isOpen) return;
        const failure = this.release ? this.release() : null;
        this.release = null;
        this.isOpen = false;
        this.frame.show(false);
        this.frame.stop();
        this.report("page_closed", { reason: reason });
        if (failure) this.report("error", { code: failure });
    }

    showView(view) {
        const page = this.config.page;
        this.view = view;
        this.frame.select(view, view === "logs" ? page.logsTitle : page.conflictsTitle);
        this.focus.settle();
        this.frame.setNotice("");
        this.report("view", { view: view });
        if (view === "logs") this.loadLog();
        else this.loadConflicts();
    }

    showError(code) {
        const errors = this.config.page.errors;
        this.frame.setNotice(errors[code] || errors.no_answer, true);
    }

    loadLog() {
        if (this.loading.logs) return;
        const page = this.config.page;
        this.loading.logs = true;
        this.frame.setStatus([page.states.reading]);
        const asked = lcNow();
        this.transport.log(this.revision, (answer) => {
            this.loading.logs = false;
            if (!this.isOpen || this.view !== "logs") return;
            const previous = this.lastLog ? lcLogStatus(this.lastLog, page) : [];
            if (answer && answer.state === "unchanged" && this.lastLog) {
                this.frame.setStatus(previous);
                // The scroll box is shared with the conflicts, which leave it at their top (audit, 1 November 2026).
                this.afterLayout(() => {
                    this.attachBar();
                    this.frame.scrollTo(true);
                });
                return;
            }
            if (!answer || answer.state !== "ok" || typeof answer.head !== "string"
                || typeof answer.tail !== "string") {
                this.frame.setStatus(previous);
                this.showError(answer && answer.state === "error" ? answer.code : "no_answer");
                return;
            }
            const received = lcNow();
            const cut = lcCutLine(answer, page);
            this.frame.setLog(answer.head + (cut ? "\n" + cut + "\n" : "") + answer.tail);
            this.revision = answer.revision;
            this.lastLog = { size: answer.size, cut: answer.cut, masked: answer.masked, readAt: answer.readAt };
            this.frame.setStatus(lcLogStatus(this.lastLog, page));
            this.afterLayout(() => {
                this.attachBar();
                this.frame.scrollTo(true);
                this.reportTimings({ request: received - asked, render: lcNow() - received });
            });
        });
    }

    // Two frames: the first runs before the new text's layout, the second after it is painted. Nothing runs if the
    // page closed or left the log meanwhile.
    afterLayout(action) {
        requestAnimationFrame(() => requestAnimationFrame(() => {
            if (this.isOpen && this.view === "logs") action();
        }));
    }

    loadConflicts() {
        if (this.loading.conflicts) return;
        const page = this.config.page;
        this.loading.conflicts = true;
        this.frame.setStatus([page.states.reading]);
        this.transport.conflicts((answer) => {
            this.loading.conflicts = false;
            if (!this.isOpen || this.view !== "conflicts") return;
            if (!lcConflictsAnswer(answer, page)) {
                this.frame.setStatus([]);
                this.showError("no_answer");
                return;
            }
            const shown = lcConflictsView(answer, page);
            this.frame.setStatus(shown.status);
            this.frame.setConflicts(shown.sections);
            this.attachBar();
            this.frame.scrollTo(false);
        });
    }

    attachBar() {
        const source = this.frame.ensureBar();
        if (source) this.report("scroll", { source: source });
    }

    // A view button pressed again reads its view again: a log grows while the game runs. COPY copies the view shown:
    // the service keeps what it last sent of each, so the page never says what is copied (conception, section 6).
    press(name) {
        const page = this.config.page;
        if (name === "logs" || name === "conflicts") {
            this.showView(name);
            return;
        }
        if (name === "folder" && this.view !== "logs") return;
        this.frame.setNotice(page.workingNotice);
        // An answer is told in the view it was asked from only (audit, 1 November 2026).
        const view = this.view;
        const done = (answer, success) => {
            if (!this.isOpen || this.view !== view) return;
            if (answer && answer.state === "ok") this.frame.setNotice(success(answer));
            else this.showError(answer && answer.state === "error" ? answer.code : "no_answer");
        };
        if (name === "copy") {
            const copied = (answer) => done(answer,
                (ok) => lcFill(page.states.copied, { size: lcSize(ok.bytes, page) }));
            if (this.view === "logs") this.transport.copy(copied);
            else this.transport.copyConflicts(copied);
        } else if (name === "folder") {
            this.transport.openFolder((answer) => done(answer, () => page.states.folderOpened));
        }
    }

    // via: the game's action name, reported for the first presses only, with or without a move: the trial reads
    // which names the gamepad sends.
    nav(move, via) {
        if (this.inputReports < this.config.page.input.maxReports) {
            this.inputReports += 1;
            this.report("input_action", { name: lcCode(via), device: this.inputDevice() });
        }
        if (!move) return;
        if (move === "view") {
            this.press(this.view === "logs" ? "conflicts" : "logs");
        } else if (move === "select") {
            const name = this.focus.pressable();
            if (name) this.press(name);
        } else {
            this.focus.move(move);
        }
    }
}
