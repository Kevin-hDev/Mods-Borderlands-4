/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The screens' scrolling, done as the options screen scrolls its entries (menu_options.js, trial 8: without it a
// long mod page ran off the screen). The holder scrolls by itself (overflow-y: scroll, as menu_options.css gives
// its list), so the mouse wheel moves it; the game's OAKScroll draws the bar beside it (oakscroll.js, already
// created inside this page by the game's dropdowns, trial 7); a row or an open list is brought into view by the
// game's InputMgr.DirectionalNavigationItemFocusHelper, the options screen's own (input_manager.js).

class MsScroll {
    constructor(page) {
        this.page = page;
        this.holder = null;
        // null: not tried yet; false: the game has no OAKScroll here (told once); otherwise the game's instance.
        this.bar = null;
        this.timer = 0;
        this.helperMissing = false;
    }

    attach(holder) { this.holder = holder; }

    // A screen was shown, its list placed at top (0 for a page just opened, where it was left for the list).
    shown(top) {
        if (!this.holder) return;
        this.holder.scrollTop = top;
        this.ensureBar();
        this.refresh();
    }

    top() { return this.holder ? this.holder.scrollTop : 0; }

    // Created once the holder has a size: on an empty or hidden holder, OAKScroll's init asks for a frame again
    // and again until it has one (oakscroll.js, init), work for nothing (OPTI.md, rule 1).
    ensureBar() {
        if (this.bar !== null || !this.page.isOpen || !this.holder.offsetHeight || !this.holder.offsetWidth) return;
        if (typeof OAKScroll !== "function") {
            this.bar = false;
            this.page.report("scroll", { source: "absent" });
            return;
        }
        this.bar = OAKScroll(this.holder);
        this.page.report("scroll", { source: "game" });
    }

    // The bar follows the new content after the delay the options screen gives it (menu_options.js,
    // OnEntriesListUpdated), through the event the game's own scrolling sends (input_manager.js).
    refresh() {
        if (!this.bar) return;
        this.stop();
        this.timer = window.setTimeout(() => {
            this.timer = 0;
            if (this.holder) this.holder.dispatchEvent(new CustomEvent("oakscrollupdate", { bubbles: true, cancelable: true }));
        }, this.page.config.page.scroll.updateDelayMs);
    }

    stop() {
        if (this.timer) window.clearTimeout(this.timer);
        this.timer = 0;
    }

    // node brought into view inside container, the screens' holder unless told (a tab bar scrolls sideways).
    reveal(node, container, horizontal) {
        const scrolled = container || this.holder;
        if (!scrolled || !node) return;
        const input = typeof InputMgr !== "undefined" && InputMgr ? InputMgr : null;
        if (input && typeof input.DirectionalNavigationItemFocusHelper === "function") {
            input.DirectionalNavigationItemFocusHelper(node, scrolled, horizontal === true);
        } else if (!this.helperMissing) {
            this.helperMissing = true;
            this.page.report("error", { code: "no_focus_scroll" });
        }
    }
}
