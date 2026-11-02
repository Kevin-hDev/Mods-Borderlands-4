/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// What the page borrows from the menu it opens over, all given back on close. Rewritten from Mod Settings'
// page/borrow.js; the feasibility gate of 1 November 2026 used the same recipe in game. Each part answers a failure
// Mod Settings met:
// - the menu's layers, hidden: shown, they kept every click drawn under the page; over the main menu, its group panel
//   and news card too, widgets of their own drawn over the page;
// - Escape, claimed through the route the game's dropdowns use: the game never sends it to the page as a key. The
//   main menu ignores that claim and sends Escape only as an input action (host "escapeAction");
// - the menu's own closing, watched: the page must leave with the menu at once;
// - the gamepad, locked on the hidden menu (its select button would press a hidden entry, Quit), while each menu
//   action reaches the page from Event_OnInputAction.
// Returns the function that gives everything back (it returns null, or the code of what could not be given back),
// or null if the menu could not be borrowed.
function lcBorrowMenu(config, widget, host, handlers) {
    const page = config.page;
    const input = page.input;
    const moves = { [input.up]: "up", [input.down]: "down", [input.left]: "left", [input.right]: "right",
                    [input.select]: "select" };
    for (const name of input.views) moves[name] = "view";
    const hidden = [];
    const locked = [];
    const watched = widget.WidgetDiv || widget;
    // InputMgr reads the flags on the widget it focused; the menu widget when that one is unknown.
    const navigated = (typeof InputMgr !== "undefined" && InputMgr && InputMgr.CurrWidget) || widget;
    let claimed = false;
    let released = false;
    const onEscape = (event) => {
        if (event && event.detail && event.detail.ident === page.escape.ident) handlers.onEscape();
    };
    const onInput = (event) => {
        const detail = event && event.detail;
        if (!detail || detail.inputActionType !== input.pressed) return;
        if (host.escapeAction && detail.inputActionName === host.escapeAction) {
            handlers.onEscape();
            return;
        }
        // An action without a move still goes on, as null: the log then names a button that did nothing.
        handlers.onNav(moves[detail.inputActionName] || null, detail.inputActionName);
    };
    const observer = new MutationObserver(() => {
        if (lcMenuClosed(widget, page)) handlers.onClose("menu_closed");
    });

    const release = () => {
        if (released) return null;
        released = true;
        let failure = null;
        observer.disconnect();
        document.removeEventListener(page.escape.event, onEscape);
        document.removeEventListener(input.event, onInput);
        if (claimed) {
            try {
                widget.TriggerWidgetEvent(page.escape.removed, page.escape.ident);
            } catch (error) {
                failure = "escape_release_failed";
            }
        }
        for (const record of locked) {
            if (record.previous === undefined) delete navigated.dataset[record.flag];
            else navigated.dataset[record.flag] = record.previous;
        }
        for (const record of hidden) record.style.display = record.previous;
        return failure;
    };

    try {
        for (const selector of host.layers) {
            const layer = widget.querySelector(selector);
            if (layer) hidden.push({ style: layer.style, previous: layer.style.display || "" });
        }
        for (const selector of host.otherWidgets) {
            for (const other of document.querySelectorAll(selector)) {
                hidden.push({ style: other.style, previous: other.style.display || "" });
            }
        }
        for (const flag of input.lockedNavigation) locked.push({ flag: flag, previous: navigated.dataset[flag] });
        for (const record of hidden) record.style.display = "none";
        for (const record of locked) navigated.dataset[record.flag] = "true";
        document.addEventListener(page.escape.event, onEscape);
        document.addEventListener(input.event, onInput);
        widget.TriggerWidgetEvent(page.escape.added, page.escape.ident);
        claimed = true;
        observer.observe(watched, { attributes: true, attributeFilter: ["class"] });
    } catch (error) {
        release();
        return null;
    }
    return release;
}

// The game closes a menu by adding the inactive class to its widget (widget_class.js, Deactivate).
function lcMenuClosed(widget, page) {
    const watched = widget.WidgetDiv || widget;
    return Boolean(watched.classList && watched.classList.contains(page.inactiveClass));
}
