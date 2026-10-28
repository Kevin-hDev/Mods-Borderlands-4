/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// What the page borrows from the menu it opens over (pause or main), all given back on close:
// - the menu's layers, hidden: shown, they kept every click drawn under the page (trial 1, 25 October 2026).
//   Over the main menu, its group panel and its news card too (host "otherWidgets"): they are widgets of their
//   own beside the menu, and were drawn over the page (second trial of the mod, 26 October 2026);
//   display: none, not visibility: hidden, which keeps their layout computed each frame (OPTI.md, rule 8);
// - Escape, claimed through the route the game's dropdowns use: the game never sends it to the page as a key.
//   The main menu ignores that claim and sends Escape only as an input action (first trial of the mod, 26
//   October 2026): there, that action is the page's Escape (host "escapeAction"). Over the pause menu the same
//   action comes too, with the claim, and is left alone so that one press goes back once;
// - the menu's own closing, watched: the page must leave with the menu at once;
// - the gamepad: the game keeps moving the hidden menu's selection, and its select button would then press a
//   hidden entry (Quit). Locked through the widget flags InputMgr.TryNavigation reads, while every menu action
//   reaches the page from Event_OnInputAction, the event InputMgr sends for each one. Any other action is told to
//   onOther (gate 3: does Start, which opens the Options screen over the page, reach the page at all?).
// The HUD Editor learned the first three in game (docs/candidats/HUD/ERREURS.md, section 25; its pause_cover.js).

function msBorrowMenu(config, widget, host, handlers) {
    const page = config.page;
    const input = page.input;
    const layers = host.layers;
    const actions = { [input.up]: "up", [input.down]: "down", [input.left]: "left", [input.right]: "right",
                      [input.select]: "select" };
    // A move may come under several names: over the pause menu the tabs' keys send its lobby panel's actions, never
    // the options screen's (trial 10, README).
    for (const bar of ["top", "sub"]) {
        for (const side of ["left", "right"]) {
            for (const name of input.tabs[bar][side]) actions[name] = (bar === "top" ? "tab_" : "sub_") + side;
        }
    }
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
        const name = actions[detail.inputActionName];
        if (name) handlers.onNav(name, detail.inputActionName);
        else handlers.onOther(detail.inputActionName);
    };
    // The game closes a menu by adding the inactive class (widget_class.js, Deactivate).
    const observer = new MutationObserver(() => {
        if (watched.classList.contains(page.inactiveClass)) handlers.onClose("menu_closed");
    });

    // Returns null, or the code of what could not be given back.
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
        for (const selector of layers) {
            const layer = widget.querySelector(selector);
            if (layer) hidden.push({ style: layer.style, previous: layer.style.display || "" });
        }
        for (const selector of host.otherWidgets || []) {
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
