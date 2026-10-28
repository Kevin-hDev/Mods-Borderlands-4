/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The MODS entry of the pause menu and of the main menu. The hook element sits inside the entry written in each
// menu's HTML, names its menu (host attribute) and acts in Init(), after super.Init(): the HUD Editor learned not
// to touch the page from connectedCallback nor after an arbitrary delay (docs/candidats/HUD/ERREURS.md, section 1).

function msLabelEntry(app, entry) {
    const apply = () => {
        for (const selector of app.config.page.entryTextSelectors) {
            const text = entry.querySelector(selector);
            if (text) {
                text.textContent = app.config.page.entryLabel;
                return true;
            }
        }
        return false;
    };
    if (apply()) {
        app.page.report("entry_ready", { label: "immediate" });
        return;
    }
    // The menu's button may be filled after the hook: wait for it once, then stop observing.
    const observer = new MutationObserver(() => {
        if (!apply()) return;
        observer.disconnect();
        app.page.report("entry_ready", { label: "observed" });
    });
    observer.observe(entry, { childList: true, subtree: true });
}

function msInstall(shared) {
    const language = msGameLanguage(shared, typeof engine !== "undefined" ? engine : null, document);
    const config = msLocalized(shared, language.code);
    const app = { config: config, page: null };
    const transport = msTransport(config, () => app.page.report("error", { code: "answer_handler_failed" }));
    const sender = new MsSender(transport, config.http.valueIntervalMs, config.page.limits.maxPendingMessages, msNow,
        (callback, ms) => setTimeout(callback, ms),
        (status, ident, newerWaiting) => app.page.changeRefused(status, ident, newerWaiting));
    app.page = new MsPage(config, sender, transport);

    class ModSettingsHook extends GbxCustomElement {
        Init() {
            super.Init();
            const entry = this.parentElement;
            const host = this.getAttribute("host");
            if (!entry || entry.modSettingsReady) return;
            entry.modSettingsReady = true;
            // The gamepad confirms an entry by dispatching a bubbling click (input_manager.js), so one listener
            // serves mouse and gamepad. While the page is open the game still clicks this hidden entry on the
            // select button: stopped here, the click cannot reach the window and close an open list of the page.
            entry.addEventListener("click", (event) => {
                if (app.page.isOpen) {
                    event.stopPropagation();
                    return;
                }
                app.page.report("entry_clicked", { host: host });
                app.page.open(this.parentWidget, host);
            });
            msLabelEntry(app, entry);
            app.page.prefetch();
        }
    }

    window.customElements.define("mod-settings-hook", ModSettingsHook);
    app.page.report("script_loaded");
    app.page.report("language", { code: config.language, source: language.source });
    return app;
}

if (!window.ModSettings && window.ModSettingsConfig) {
    window.ModSettings = msInstall(window.ModSettingsConfig);
}
