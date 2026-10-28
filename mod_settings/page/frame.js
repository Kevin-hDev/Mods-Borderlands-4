/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The page's frame, laid out as the game's options screen (menu_options.html, navigationbar.html): the tabs and
// sub-tabs at the top with the path to the screen shown, the rows on the left, the lit row's details on the right,
// and between the tabs and the details Python's state and CLOSE or BACK. Built once, at the first opening, in the
// menu's widget (OPTI.md, rules 5 and 6); a screen shown only changes its texts and classes (rule 9).

class MsFrame {
    constructor(page) {
        this.page = page;
        this.config = page.config;
        this.details = new MsDetails(page);
        this.topBar = new MsTabBar(page, "top_nav", (index, fromPad) => page.screens.choose("top", index, fromPad));
        this.subBar = new MsTabBar(page, "sub_nav", (index, fromPad) => page.screens.choose("sub", index, fromPad));
        this.root = null;
        this.holder = null;
        this.crumb = null;
        this.subWrapper = null;
        this.status = null;
        this.closeButton = null;
    }

    // Returns the element the rows go in. The holder comes first in its parent: OAKScroll puts its bar right after
    // it (oakscroll.js, Scrollbar.create).
    build(widget) {
        const page = this.page;
        const root = page.element("div", "ms_root");
        for (const href of this.config.page.stylesheets.concat([this.config.page.ownStylesheet])) {
            root.appendChild(this.stylesheet(href, href === this.config.page.stylesheets[0]));
        }
        root.appendChild(page.element("div", "fill_content menu_bg_nostandin"));
        root.appendChild(this.header());
        const main = root.appendChild(page.element("div", "menu_options_container menu_screen_boundaries"))
            .appendChild(page.element("div", "menu_options_main"));
        this.holder = main.appendChild(page.element("div", "menu_options_entry_wrapper"))
            .appendChild(page.element("div", "menu_options_entry_grid"))
            .appendChild(page.element("div", "menu_options_entry_content full_size"))
            .appendChild(page.element("div", "menu_options_entry_list grid-container ms_screens"));
        main.appendChild(this.details.build());
        const corner = root.appendChild(page.element("div", "ms_corner"));
        this.status = corner.appendChild(page.text("", "ms_status"));
        this.closeButton = corner.appendChild(page.text(this.config.page.closeLabel, "ms_close"));
        this.closeButton.addEventListener("click", () => page.escape());
        widget.appendChild(root);
        this.root = root;
        return this.holder;
    }

    header() {
        const page = this.page;
        const header = page.element("div", "nb_header ms_header");
        const band = header.appendChild(page.element("div", "top_navbar_wrapper"));
        this.crumb = band.appendChild(page.text("", "ms_crumb"));
        band.appendChild(this.topBar.build());
        header.appendChild(page.element("div", "top_navbar_underline"));
        this.subWrapper = header.appendChild(page.element("div", "sub_nav_wrapper ms_hidden"));
        this.subWrapper.appendChild(this.subBar.build());
        return header;
    }

    // No model yet (Python loading or absent): the MODS tab alone, the corner says which.
    showEmpty() {
        this.topBar.show([{ label: this.config.page.title }], 0);
        this.details.show({ title: this.config.page.title, text: "", meta: "" });
    }

    // The path, the tabs, the details and CLOSE or BACK of the screen shown (screens.js).
    showScreen(shown, depth) {
        const page = this.config.page;
        const selection = shown.selection;
        this.crumb.textContent = shown.view.crumb.join(page.crumbSeparator).toUpperCase();
        this.topBar.show(shown.view.tabs, shown.tab);
        if (selection.subtabs) this.subBar.show(selection.subtabs, shown.sub);
        this.subWrapper.classList.toggle("ms_hidden", !selection.subtabs);
        this.details.show(selection.details);
        this.closeButton.textContent = depth > 0 ? page.backLabel : page.closeLabel;
    }

    showStatus(text) {
        if (this.status) this.status.textContent = text;
    }

    stop() {
        this.topBar.stop();
        this.subBar.stop();
    }

    remove() {
        if (this.root && this.root.parentNode) this.root.parentNode.removeChild(this.root);
        this.stop();
    }

    // Loaded with the page, so the options screen's rules never touch the menu under it. The first one's load
    // time is measured: an unstyled first frame would show as a flash.
    stylesheet(href, measured) {
        const start = msNow();
        const css = document.createElement("link");
        css.rel = "stylesheet";
        css.type = "text/css";
        if (measured) css.onload = () => { this.page.data.timings.css = Math.max(0, msNow() - start); };
        css.href = href;
        return css;
    }
}
