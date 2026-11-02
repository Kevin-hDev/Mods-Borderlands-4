/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The shared menu file's own script, loaded last, after each mod's script. Every entry of the shared file starts
// hidden: a mod whose script is missing (not installed) keeps its entry hidden. Mod Settings' MODS entry carries this
// file's hook, which shows the entry from its Init, once the menu is built, when Mod Settings' script set
// window.ModSettings, as its 1.0.0 script does. Looked up when this script loads, the entry was not there yet and MODS
// stayed hidden (Logs & Conflicts, trial 1, 1 November 2026). Without that script, the entry never shows: it leaves
// the menu, as the game's own entries do through data-bind-if. Hidden only, the gamepad still stopped on it unseen:
// the game's lists skip an input element marked data-input-disabled, never a hidden one (input_behaviors.js,
// GetNextNode; audit of 1 November 2026). Logs & Conflicts shows its own entry once its service answers
// (docs/tools/journaux-et-conflits/conception.md, section 3).
(function () {
    if (window.MenuEntriesHook) return;
    // The global each mod's script sets: the entries this file may show.
    const globals = { mod_settings: "ModSettings" };

    class MenuEntriesHook extends GbxCustomElement {
        Init() {
            super.Init();
            const entry = this.parentElement;
            if (!entry) return;
            const name = globals[this.getAttribute("mod")];
            if (name && window[name]) entry.style.display = "";
            else if (entry.parentNode) entry.parentNode.removeChild(entry);
        }
    }

    window.MenuEntriesHook = MenuEntriesHook;
    window.customElements.define("menu-entries-hook", MenuEntriesHook);
})();
