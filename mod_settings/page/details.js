/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The options screen's details panel (menu_options.html, Details Container): the title and description of the row
// lit, as menu_options.js fills it in OnEnterEntry, and under them a mod's version and author. Text only: the game
// writes its own texts as markup (innerHTML), the page never writes a mod's words that way. Each line of a
// description is its own block, since the panel's description is a flex column (menu_options.css).

class MsDetails {
    constructor(page) {
        this.page = page;
        this.node = null;
        this.title = null;
        this.text = null;
        this.meta = null;
        this.shown = null;
    }

    // The panel, built once with the page's frame.
    build() {
        const page = this.page;
        const node = page.element("div", "menu_options_details_container");
        node.appendChild(page.element("div", "menu_options_details_gradient_bg menu_options_details_gradient_bg_bottom"));
        const inner = node.appendChild(page.element("div", "menu_options_details_container_inner"));
        const details = inner.appendChild(page.element("div", "menu_options_details"));
        this.title = details.appendChild(page.element("div", "menu_options_details_title med_text_1"));
        this.text = details.appendChild(page.element("p", "menu_options_details_description small_text_2"));
        this.meta = details.appendChild(page.element("p", "ms_meta small_text_2"));
        this.node = node;
        return node;
    }

    // details: { title, text, meta }. The same details again change nothing (OPTI.md, rule 9).
    show(details) {
        if (!this.node || !details || details === this.shown) return;
        this.shown = details;
        this.title.textContent = details.title;
        this.meta.textContent = details.meta;
        const lines = document.createDocumentFragment();
        for (const line of details.text ? details.text.split("\n") : []) {
            const block = lines.appendChild(this.page.element("span", line ? "ms_line" : "ms_line ms_gap"));
            block.textContent = line;
        }
        this.text.textContent = "";
        this.text.appendChild(lines);
    }
}
