/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";
// Trial 4 again: the mod's Python side is not running. The page must open at once, say LOADING then PYTHON ABSENT with
// no mod list when the request fails, instead of waiting for it, and stay usable: Escape closes it.
(async function () {
    const result = {};
    const config = window.ModSettings.config.page;
    const pause = document.querySelector("widget-menu-pause");
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const status = () => document.querySelector(".ms_status");
    const texts = config.statusTexts;
    try {
        const entry = pause.querySelector('[name="Mod Settings Button"]');
        // Leave time for the prefetch of the row markup, as the pause menu gives it before any click.
        await sleep(400);
        entry.querySelector(".list_btn").dispatchEvent(new MouseEvent("click", { bubbles: true, view: window }));
        const root = pause.querySelector(".ms_root");
        result.openAtOnce = root !== null && !root.classList.contains("ms_closed");
        for (let i = 0; i < 80 && !(status() && status().textContent.indexOf(texts.pythonAbsent) === 0); i += 1) await sleep(50);
        result.absentShown = status() !== null && status().textContent === texts.pythonAbsent + " | " + texts.noMods;
        result.rows = document.querySelectorAll(".ms_root .menu_options_entry").length;
        result.tabs = Array.from(document.querySelectorAll(".ms_root .top_nav_item_txt")).map((node) => node.textContent);
        document.dispatchEvent(new CustomEvent(config.escape.event, { detail: { ident: config.escape.ident } }));
        result.closed = root.classList.contains("ms_closed");
    } catch (error) {
        result.error = String(error && error.stack || error);
    }
    document.getElementById("result").textContent = JSON.stringify(result);
})();
