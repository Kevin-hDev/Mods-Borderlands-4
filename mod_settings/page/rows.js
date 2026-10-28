/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// One screen's rows, assembled as menu_options.js does in OnEntriesListUpdated: the options screen's own row
// markup, a piece cloned from the game's component store, and the game's CursorHandler on each row, on which
// every hover style hangs (orange pip, light frame of the card). Built off-document, inserted once by the page.
// A row that fails is left out and counted (failed), told once per screen instead of once per row.

function msComponent(config, kind) {
    if (typeof CompStore === "undefined" || !CompStore || !CompStore.GetComponent) return null;
    for (const id of config.page.components[kind] || []) {
        const content = CompStore.GetComponent(id);
        if (content && content.firstElementChild) return { id: id, element: content.firstElementChild.cloneNode(true) };
    }
    return null;
}

function msFromMarkup(markup) {
    if (!markup) return null;
    const holder = document.createElement("div");
    holder.innerHTML = markup;
    return holder.firstElementChild;
}

// Same classes as the options screen's markup, for a game file that would lose its templates.
function msFallbackRow(title) {
    const row = document.createElement("div");
    if (title) {
        row.className = "menu_options_title_entry menu_options_entry_list_inner";
        row.innerHTML = '<div class="category_divider flex_start_margin"><div class="cat_divider_title"></div></div>';
        return row;
    }
    row.className = "menu_options_regular_entry menu_options_entry_list_inner";
    row.innerHTML = '<div class="menu_options_entry"><div class="list_entry_panel">' +
        '<p class="menu_options_entry_text small_text_1"></p></div><div class="list_entry_interacts_comp">' +
        '<div class="menu_options_entry_component"></div></div></div>';
    return row;
}

class MsRows {
    constructor(page) {
        this.page = page;
        this.config = page.config;
        this.items = [];
        this.failed = 0;
    }

    // Returns the rows' container, not yet in the document.
    build(templates, rows) {
        const list = document.createElement("div");
        list.className = "ms_rows";
        for (const row of rows) {
            const node = row.kind === "title" ? this.title(row, templates) : this.regular(row, templates);
            if (node) list.appendChild(node);
            else if (row.kind !== "title") this.failed += 1;
        }
        return list;
    }

    title(row, templates) {
        const node = msFromMarkup(templates.title) || msFallbackRow(true);
        node.classList.add("menu_options_entry_cntr");
        const text = node.querySelector(".cat_divider_title");
        if (text) text.textContent = row.label;
        return node;
    }

    regular(row, templates) {
        const node = msFromMarkup(templates.regular) || msFallbackRow(false);
        node.classList.add("menu_options_entry_cntr");
        const entry = node.querySelector(".menu_options_entry");
        const text = node.querySelector(".menu_options_entry_text");
        const holder = node.querySelector(".menu_options_entry_component");
        const found = msComponent(this.config, row.kind);
        if (!entry || !holder || !found) return null;
        if (text) text.textContent = row.label;
        if (row.locked && row.kind !== "link") node.classList.add("ms_locked");
        const extra = this.config.page.componentClasses[row.kind];
        if (extra) holder.classList.add(extra);
        const prepare = MS_PIECES[row.kind].prepare;
        const target = holder.appendChild(prepare ? prepare(found.element) : found.element);
        const piece = new MsPiece(this.page.settings, row, target);
        piece.entry = entry;
        try {
            piece.setup(row.initial);
        } catch (error) {
            return null;
        }
        this.hover(piece, this.items.length);
        this.items.push(piece);
        return node;
    }

    // Mouse hover as the options screen (OnEnterEntry, OnLeaveEntry); the gamepad reuses it (focus.js).
    hover(piece, index) {
        const entry = piece.entry;
        entry.dataset.inputElem = "true";
        entry.dataset.inputDefault = "true";
        entry.CursorHandler = new CursorHandler({
            element: entry,
            onEnter: () => {
                entry.dataset.hasCursorFocus = "true";
                this.page.focus.entered(index);
                this.page.sound(entry, "ElementFocused");
            },
            onLeave: () => {
                entry.dataset.hasCursorFocus = "false";
                this.page.focus.left(index);
                this.page.sound(entry, "ElementUnfocused");
            }
        });
    }

    connected() {
        for (const piece of this.items) piece.connected();
    }

    find(ident) {
        return this.items.find((piece) => piece.row.ident === ident) || null;
    }
}
