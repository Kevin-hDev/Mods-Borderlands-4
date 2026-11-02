/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The page's frame, as Kevin chose it on 1 November 2026 (conception, section 4, layout B): on the left a narrow
// column of the game's list buttons (LOGS, CONFLICTS, then COPY and OPEN FOLDER), on the right the options screen's
// details panel (menu_options.html) widened to the rest of the screen, which holds the log or the conflicts and
// scrolls with the game's bar. Built once, at the first opening, in the menu's widget; afterwards only texts and
// classes change (OPTI.md, rules 5 and 9).

const LC_BUTTONS = ["logs", "conflicts", "copy", "folder"];
// The panel comes after the buttons in the gamepad's order.
const LC_PANEL = LC_BUTTONS.length;

class LcFrame {
    constructor(page) {
        this.page = page;
        this.root = null;
        this.widget = null;
        this.buttons = [];
        this.panel = null;
        this.title = null;
        this.status = null;
        this.notice = null;
        this.holder = null;
        this.log = null;
        this.conflicts = null;
        this.bar = null;
        this.timer = 0;
    }

    element(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    build(widget) {
        const page = this.page.config.page;
        this.remove();
        this.widget = widget;
        const root = this.element("div", "lc_root");
        for (const href of page.stylesheets.concat([page.ownStylesheet])) {
            const css = this.element("link", "");
            css.rel = "stylesheet";
            css.type = "text/css";
            css.href = href;
            root.appendChild(css);
        }
        root.appendChild(this.element("div", "fill_content menu_bg_nostandin"));
        root.appendChild(this.element("div", "lc_title", page.entryLabel));
        const main = root.appendChild(this.element("div", "lc_main"));
        const column = main.appendChild(this.element("div", "lc_column"));
        const labels = [page.logsLabel, page.conflictsLabel, page.copyLabel, page.folderLabel];
        this.buttons = LC_BUTTONS.map((name, index) => {
            if (name === "copy") column.appendChild(this.element("div", "lc_gap"));
            return column.appendChild(this.button(name, index, labels[index]));
        });
        main.appendChild(this.buildPanel());
        widget.appendChild(root);
        this.root = root;
    }

    // The game's list button (components/list_button/list_button.html) as a plain div, for its look only: the game's
    // own button tells the native side on each click and could select a hidden entry of the menu (Mod Settings,
    // pieces.js). Its states are the game's classes: selected for the view shown, hover_effect for the pointer.
    button(name, index, label) {
        const entry = this.element("div", "lc_nav_entry");
        const button = entry.appendChild(this.element("div", "list_btn"));
        button.appendChild(this.element("div", "button_inner")).appendChild(this.element("p", "button_txt", label));
        const backing = button.appendChild(this.element("div", "list_btn_backing_cntr"));
        for (const part of ["list_btn_backing", "list_btn_gradient_bg", "list_btn_textures_9s", "list_btn_outline",
                            "list_btn_outline_glow"]) {
            backing.appendChild(this.element("div", part));
        }
        button.appendChild(this.element("div", "list_entry_orange_fui"))
            .appendChild(this.element("div", "list_entry_orange_fui_fill"));
        entry.addEventListener("click", (event) => {
            event.stopPropagation();
            this.page.press(name);
        });
        entry.addEventListener("mouseenter", () => this.page.focus.set(index, true));
        entry.addEventListener("mouseleave", () => this.page.focus.pointAway(index));
        return entry;
    }

    // The holder comes first in its box: the game's OAKScroll puts its bar right after it (oakscroll.js).
    buildPanel() {
        const panel = this.element("div", "lc_panel menu_options_details_container");
        panel.appendChild(this.element("div",
            "menu_options_details_gradient_bg menu_options_details_gradient_bg_bottom"));
        const inner = panel.appendChild(this.element("div", "lc_panel_inner"));
        this.title = inner.appendChild(this.element("div", "menu_options_details_title lc_panel_title"));
        this.status = inner.appendChild(this.element("div", "lc_status"));
        this.notice = inner.appendChild(this.element("div", "lc_notice"));
        const box = inner.appendChild(this.element("div", "lc_scroll_box"));
        this.holder = box.appendChild(this.element("div", "lc_scroll"));
        this.log = this.holder.appendChild(this.element("p", "lc_log"));
        this.conflicts = this.holder.appendChild(this.element("div", "lc_conflicts lc_hidden"));
        this.panel = panel;
        return panel;
    }

    show(visible) { if (this.root) this.root.classList.toggle("lc_hidden", !visible); }

    // OPEN FOLDER only with the log: the folder holds the log, and has nothing to do with the conflicts (Kevin,
    // 1 November 2026: shown there, it "is confusing"). COPY stays: it copies the view shown.
    select(view, title) {
        this.buttons[0].firstChild.classList.toggle("selected", view === "logs");
        this.buttons[1].firstChild.classList.toggle("selected", view === "conflicts");
        this.buttons[LC_BUTTONS.indexOf("folder")].classList.toggle("lc_hidden", view !== "logs");
        this.title.textContent = title;
        this.log.classList.toggle("lc_hidden", view !== "logs");
        this.conflicts.classList.toggle("lc_hidden", view !== "conflicts");
    }

    isShown(index) { return !this.buttons[index].classList.contains("lc_hidden"); }

    // index: a button, LC_PANEL for the panel, or -1 for nothing.
    highlight(index) {
        this.buttons.forEach((entry, at) => entry.firstChild.classList.toggle("hover_effect", at === index));
        this.panel.classList.toggle("lc_focused", index === LC_PANEL);
    }

    setStatus(lines) {
        const block = document.createDocumentFragment();
        for (const line of lines) block.appendChild(this.element("div", "", line));
        this.status.textContent = "";
        this.status.appendChild(block);
    }

    setNotice(text, isError) {
        this.notice.textContent = text || "";
        this.notice.classList.toggle("lc_error", isError === true);
    }

    // As text, never as markup (conception, section 6): a log line holding page code shows as it is.
    setLog(text) { this.log.textContent = text; }

    // sections: conflicts_view.js's, each with its title, its help lines and its entries.
    setConflicts(sections) {
        const list = document.createDocumentFragment();
        for (const section of sections) {
            list.appendChild(this.element("div", "lc_section", section.title));
            for (const line of section.help) list.appendChild(this.element("div", "lc_help", line));
            for (const block of section.blocks) {
                list.appendChild(this.element("div", "lc_key", block.key));
                for (const line of block.lines) list.appendChild(this.element("div", "lc_use", line));
            }
        }
        this.conflicts.textContent = "";
        this.conflicts.appendChild(list);
    }

    // The bar is made once the holder has a size: on a hidden holder, OAKScroll's init asks for a frame again and
    // again until it has one (Mod Settings, scroll.js). Returns "game", "absent" or "" (not made yet).
    ensureBar() {
        if (this.bar !== null || !this.holder.offsetHeight) return "";
        if (typeof OAKScroll !== "function") {
            this.bar = false;
            return "absent";
        }
        this.bar = new OAKScroll(this.holder);
        return "game";
    }

    // atEnd: the log opens on its last lines, the conflicts on their first.
    scrollTo(atEnd) {
        this.holder.scrollTop = atEnd ? this.holder.scrollHeight : 0;
        this.refreshBar();
    }

    scrollBy(pixels) {
        this.holder.scrollTop += pixels;
        this.refreshBar();
    }

    // The bar follows the content through the event the game's own scrolling sends (input_manager.js).
    refreshBar() {
        if (!this.bar) return;
        this.stop();
        this.timer = setTimeout(() => {
            this.timer = 0;
            this.holder.dispatchEvent(new CustomEvent("oakscrollupdate", { bubbles: true, cancelable: true }));
        }, this.page.config.page.scrollUpdateDelayMs);
    }

    stop() {
        if (this.timer) clearTimeout(this.timer);
        this.timer = 0;
    }

    remove() {
        this.stop();
        if (this.root && this.root.parentNode) this.root.parentNode.removeChild(this.root);
        this.root = null;
        this.bar = null;
    }
}
