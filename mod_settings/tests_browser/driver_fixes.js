/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";
// The page's fixes of the review of 26 October 2026, on the game's own pieces: Python's first read not done in
// time (503) waited for instead of shown as absent; the key row's second slot hidden and stepped over by the
// gamepad; a capture ended by a tab clicked with the mouse; a change Python refuses shown back as the mod holds it;
// over the main menu, one Escape with a list open closing the list only. Python's keyboard presses no key here.
(async function () {
    const result = {};
    const config = window.ModSettings.config.page;
    const input = config.input;
    const page = window.ModSettings.page;
    const pause = document.querySelector("widget-menu-pause");
    const main = document.querySelector("widget-menu-main");
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const waitFor = async (test, tries = 100) => {
        for (let i = 0; i < tries; i += 1) {
            if (test()) return true;
            await sleep(50);
        }
        return false;
    };
    const action = (name) => document.dispatchEvent(new CustomEvent(input.event,
        { detail: { inputActionName: name, inputActionType: input.pressed } }));
    const escape = () => document.dispatchEvent(new CustomEvent(config.escape.event,
        { detail: { ident: config.escape.ident } }));
    const click = (node) => node.dispatchEvent(new MouseEvent("click", { bubbles: true, view: window }));
    const all = (selector) => Array.from(document.querySelectorAll(".ms_root " + selector));
    // Empty until the page's frame is built (it waits for the game's row markup, data.js).
    const text = (selector) => {
        const node = document.querySelector(".ms_root " + selector);
        return node ? node.textContent : "";
    };
    const root = (widget) => widget.querySelector(".ms_root");
    const isOpen = (widget) => root(widget) !== null && !root(widget).classList.contains("ms_closed");
    const screen = () => document.querySelector(".ms_root .ms_rows:not(.ms_hidden)");
    const rows = () => (screen() ? Array.from(screen().querySelectorAll(".menu_options_entry")) : []);
    const inScreen = (selector) => Array.from(screen().querySelectorAll(selector));
    const crumb = () => text(".ms_crumb");
    const status = () => text(".ms_status");
    InputMgr.CurrWidget = pause;
    pause.dataset[input.lockedNavigation[0]] = "false";

    try {
        const pauseEntry = pause.querySelector('[name="Mod Settings Button"]');
        const mainEntry = main.querySelector('[name="Mod Settings Button"]');
        await waitFor(() => pauseEntry.querySelector(".button_txt").textContent === config.entryLabel);

        // Python's first read of the mods takes longer than it waits (the test gives it no wait): 503, then the list.
        click(pauseEntry.querySelector(".list_btn"));
        let sawAbsent = false;
        for (let i = 0; i < 100 && rows().length !== 4; i += 1) {
            if (status().indexOf(config.statusTexts.pythonAbsent) >= 0) sawAbsent = true;
            await sleep(50);
        }
        result.listAfterNotReady = rows().length === 4;
        result.neverSaidAbsent = !sawAbsent;

        // The key row: its second slot hidden; left and right step over it.
        click(rows()[0].querySelector(".oak_option_button"));
        await sleep(200);
        const keyRow = rows().findIndex((row) => row.querySelector("oak-rebind-entry"));
        const rebind = rows()[keyRow].querySelector("oak-rebind-entry");
        result.secondHidden = getComputedStyle(rebind.querySelector(".rebind_entry_glyph_secondary")).display === "none";
        InputMgr.bIsUsingCursorNavigation = false;
        InputMgr.InputDeviceType = 1;
        for (let i = 0; i <= keyRow; i += 1) action(input.down);
        action(input.right);
        result.padRight = rebind.currentTargetEntryIdx;
        action(input.left);
        result.padLeft = rebind.currentTargetEntryIdx;

        // A capture started with the mouse, then another tab clicked: the capture ends with its row.
        InputMgr.bIsUsingCursorNavigation = true;
        click(rebind.primaryRebindEntry);
        result.captureStarted = page.capture.active;
        click(all(".top_nav_item_cntr")[1]);
        result.captureEndedByTab = !page.capture.active;
        click(all(".top_nav_item_cntr")[0]);
        await sleep(300);

        // A change Python refuses (409) while the page already holds Python's model: the model comes back at the
        // same revision, and the row must still show the mod's value again. The change leaves with an older
        // revision, written for this test only, and the page's own is put back at once.
        const toggle = () => inScreen("gbx-toggle")[0];
        const before = toggle().CurrentValue;
        const held = page.data.revision;
        page.data.revision = held + 100;
        click(toggle().querySelector(before ? ".toggle_button_left" : ".toggle_button_right"));
        page.data.revision = held;
        result.changedOnScreen = toggle().CurrentValue !== before;
        await waitFor(() => toggle().CurrentValue === before, 60);
        result.refusedShownBack = toggle().CurrentValue === before;
        result.refusedSaid = status().indexOf(config.statusTexts.refused) >= 0;
        result.revisionKept = page.data.revision === held;

        // The same refusal while the player has gone to another tab: back on it, the row shows the mod's value.
        const offTab = toggle().CurrentValue;
        page.data.revision = held + 100;
        click(toggle().querySelector(offTab ? ".toggle_button_left" : ".toggle_button_right"));
        page.data.revision = held;
        click(all(".top_nav_item_cntr")[1]);
        await sleep(800);
        click(all(".top_nav_item_cntr")[0]);
        result.refusedOffTabShownBack = toggle().CurrentValue === offTab;

        escape();
        escape();
        result.pauseClosed = await waitFor(() => !isOpen(pause), 20);
        await sleep(300);

        // Over the main menu Escape comes as an action only: with a list open, one press closes the list only.
        click(mainEntry.querySelector(".menu_button_wrapper"));
        await waitFor(() => root(main) !== null && rows().length === 4);
        click(rows()[0].querySelector(".oak_option_button"));
        await sleep(200);
        const dropdown = inScreen("gbx-dropdown-options-alt")[0];
        click(dropdown.querySelector(".dropdown_opt_header"));
        result.mainListOpened = dropdown.classList.contains("expanded");
        const onModPage = crumb();
        action("Input.Action.Menu.Escape");
        result.mainEscapeClosedListOnly = !dropdown.classList.contains("expanded") && crumb() === onModPage
            && onModPage !== "";
        action("Input.Action.Menu.Escape");
        result.mainSecondEscapeBack = crumb() === "";
        click(document.querySelector(".ms_close"));
        result.mainClosed = !isOpen(main);
    } catch (error) {
        result.error = String(error && error.stack || error);
    }
    document.getElementById("result").textContent = JSON.stringify(result);
})();
