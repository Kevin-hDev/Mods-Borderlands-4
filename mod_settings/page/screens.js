/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The page's screens (layout.js): the list of mods, then a mod's page, then the pages opened from its
// sub-tabs. Only the rows of the tab shown exist (OPTI.md, rule 7): a tab's rows are built when it is chosen and
// removed when another is. The list is the exception: built once per model and kept, hidden by display: none while a
// mod's page shows (rules 5 and 8). A screen left for a deeper one keeps its tab, sub-tab, scroll and gamepad row,
// and gets its rows again on the way back.

class MsScreens {
    constructor(page) {
        this.page = page;
        this.config = page.config;
        this.holder = null;
        this.list = null;
        this.stack = [];
    }

    get current() { return this.stack.length > 0 ? this.stack[this.stack.length - 1] : this.list; }

    get depth() { return this.stack.length; }

    items() { return this.current && this.current.rows ? this.current.rows.items : []; }

    find(ident) { return this.current && this.current.rows ? this.current.rows.find(ident) : null; }

    // holder: the page's element for the rows, already in the document.
    attach(holder) { this.holder = holder; }

    record(view) {
        return { view: view, tab: 0, sub: 0, selection: null, rows: null, node: null, top: 0, focusIndex: -1 };
    }

    // A new model: the list is built again, at the place it was scrolled to; an open mod page stays until the
    // player leaves it.
    showRoot(model) {
        if (!this.holder) return;
        const onList = this.stack.length === 0;
        const top = onList ? this.page.scroll.top() : (this.list ? this.list.top : 0);
        if (this.list) this.drop(this.list);
        this.list = this.record(msView("list", model.root, [], this.config));
        this.list.top = top;
        this.fill(this.list, "list");
        if (!onList) {
            this.list.node.classList.add("ms_hidden");
            return;
        }
        this.page.showScreen(this.list);
        this.page.scroll.shown(top);
    }

    // link: a row that opens a page (a mod in the list, a page in a sub-tab).
    open(link) {
        const below = this.current;
        if (!this.holder || !below || !link || !link.target) return;
        // A capture belongs to a row of the screen left: its key must not land on a row no longer shown.
        this.page.capture.cancel("screen_changed");
        below.top = this.page.scroll.top();
        below.focusIndex = this.page.focus.index;
        this.page.closeList();
        this.page.focus.reset();
        const shown = this.record(msChildView(below.view, below.tab, below.sub, link, this.config));
        if (below === this.list) below.node.classList.add("ms_hidden");
        else this.drop(below);
        this.stack.push(shown);
        this.fill(shown, "mod");
        this.page.showScreen(shown);
        this.page.scroll.shown(0);
    }

    // A tab ("top") or sub-tab ("sub") chosen: its rows replace the shown ones, at the top, as the options screen
    // starts each tab. From the gamepad, the first row is lit. Ignored while a list is open: it holds the gamepad.
    choose(level, index, fromPad) {
        const shown = this.current;
        if (!shown || shown === this.list || this.page.focus.list) return;
        const tabs = level === "top" ? shown.view.tabs : shown.selection.subtabs;
        if (!tabs || index < 0 || index >= tabs.length || index === (level === "top" ? shown.tab : shown.sub)) return;
        if (level === "top") {
            shown.tab = index;
            shown.sub = 0;
        } else {
            shown.sub = index;
        }
        this.page.capture.cancel("screen_changed");
        this.page.focus.reset();
        this.drop(shown);
        this.fill(shown, "tab");
        this.page.showScreen(shown);
        this.page.scroll.shown(0);
        this.page.report("tab", { state: level, code: "i" + index });
        if (fromPad) this.page.focus.nav("down");
    }

    // False when there is no page to go back from: the page then closes.
    back() {
        if (this.stack.length === 0) return false;
        this.page.closeList();
        this.page.focus.reset();
        this.drop(this.stack.pop());
        const current = this.current;
        if (current === this.list) current.node.classList.remove("ms_hidden");
        else this.fill(current, "back");
        this.page.showScreen(current);
        this.page.scroll.shown(current.top);
        this.page.focus.restore(current.focusIndex);
        return true;
    }

    // Every page closed at once: what the page shows at its next opening is the list.
    reset() {
        if (this.stack.length === 0) return;
        this.page.capture.cancel("screen_changed");
        this.page.closeList();
        this.page.focus.reset();
        while (this.stack.length > 0) this.drop(this.stack.pop());
        this.list.node.classList.remove("ms_hidden");
        this.page.showScreen(this.list);
        this.page.scroll.shown(this.list.top);
    }

    fill(shown, kind) {
        const start = msNow();
        shown.selection = msSelection(shown.view, shown.tab, shown.sub, this.config);
        const rows = new MsRows(this.page);
        const node = rows.build(this.page.data.templates, shown.selection.rows);
        if (shown.selection.rows.length === 0) {
            node.appendChild(this.page.text(this.config.page.noSettingsLabel, "ms_empty small_text_1"));
        }
        this.holder.appendChild(node);
        rows.connected();
        shown.rows = rows;
        shown.node = node;
        this.page.report("screen_opened", { screen: kind, code: "rows_" + rows.items.length });
        if (rows.failed > 0) this.page.report("error", { code: "rows_failed_" + rows.failed });
        this.page.reportTimings({ screen: msNow() - start });
    }

    drop(shown) {
        if (shown.node && shown.node.parentNode) shown.node.parentNode.removeChild(shown.node);
        shown.node = null;
        shown.rows = null;
    }
}
