/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// Gamepad navigation inside the page. The game's own navigation stays locked on the hidden menu
// (borrow.js), so up and down move between rows here, left and right step the row's piece, and select
// does what the options screen's OnClickEntry does. A row is lit the way the game lights it: a mouse event on
// the row's CursorHandler, sent while InputMgr says it simulates the mouse (cursorhandler.js, OnEnter refuses
// cursor events otherwise; input_manager.js sends its own the same way). An open dropdown takes up, down and
// select for its items until it closes. The lit row and an opened list are kept in view (scroll.js).

function msSimulate(element, type) {
    const input = typeof InputMgr !== "undefined" && InputMgr ? InputMgr : null;
    const previous = input ? input.SimulatingMouse : undefined;
    if (input) input.SimulatingMouse = true;
    try {
        element.dispatchEvent(new MouseEvent(type, { bubbles: type === "click", cancelable: true, view: window }));
    } finally {
        if (input) input.SimulatingMouse = previous;
    }
}

class MsFocus {
    constructor(page) {
        this.page = page;
        this.index = -1;
        this.hovered = false;
        this.list = null;
        this.item = -1;
    }

    pieces() { return this.page.screens.items(); }

    // A row lit, by the mouse or the gamepad: the details panel tells what it is (menu_options.js, OnEnterEntry).
    entered(index) {
        this.index = index;
        this.hovered = true;
        const piece = this.pieces()[index];
        if (piece) this.page.frame.details.show(piece.row.details);
    }

    left(index) {
        if (index === this.index) this.hovered = false;
    }

    reset() {
        if (this.hovered && this.pieces()[this.index]) this.light(this.index, false);
        this.index = -1;
        this.hovered = false;
        this.list = null;
        this.item = -1;
    }

    // Back on a screen: its row, unlit, so the next press lights it again instead of the first row.
    restore(index) {
        this.index = Number.isInteger(index) && index < this.pieces().length ? index : -1;
        this.hovered = false;
    }

    nav(name) {
        if (this.list) return this.navList(name);
        const pieces = this.pieces();
        if (pieces.length === 0) return;
        if (name === "up" || name === "down") return this.move(name === "up" ? -1 : 1);
        if (!this.hovered) return this.move(0);
        const piece = pieces[this.index];
        if (name === "select") piece.activate();
        else piece.step(name);
    }

    // The first press after the mouse left a row lights that row again, as a menu does, instead of skipping it.
    move(delta) {
        const count = this.pieces().length;
        const from = this.index;
        let to = from;
        if (from < 0) to = 0;
        else if (this.hovered) to = Math.min(count - 1, Math.max(0, from + delta));
        if (from === to && this.hovered) return;
        if (from >= 0 && this.hovered) this.light(from, false);
        this.light(to, true);
    }

    light(index, on) {
        const piece = this.pieces()[index];
        msSimulate(piece.entry, on ? "mouseenter" : "mouseleave");
        if (on) {
            piece.enter();
            this.page.scroll.reveal(piece.entry);
        } else {
            piece.leave();
        }
    }

    // Told by the dropdowns' stand-in widget when a list opens or closes (dropdown.js, UpdateDirectionalNavigation).
    dropdownChanged(open, container) {
        const piece = open ? this.pieces().find((candidate) => candidate.target.contains(container)) : null;
        this.list = piece || null;
        this.item = -1;
        if (!piece) return;
        // A list opened low on the screen would hang past the scrolled area's edge: brought into view.
        this.page.scroll.reveal(container);
        const items = this.items();
        const selected = items.findIndex((item) => item.classList.contains("selected"));
        this.lightItem(selected < 0 ? 0 : selected);
    }

    items() {
        const items = this.list && this.list.target.DropdownItems;
        return Array.isArray(items) ? items.filter((item) => item.dataset.inputDisabled !== "true") : [];
    }

    navList(name) {
        const items = this.items();
        if (items.length === 0) return;
        if (name === "select" && this.item >= 0) return msSimulate(items[this.item], "click");
        if (name === "up" || name === "down") {
            this.lightItem(Math.min(items.length - 1, Math.max(0, this.item + (name === "up" ? -1 : 1))));
        }
    }

    lightItem(index) {
        const items = this.items();
        if (index === this.item || !items[index]) return;
        if (items[this.item]) msSimulate(items[this.item], "mouseleave");
        this.item = index;
        msSimulate(items[index], "mouseenter");
    }
}
