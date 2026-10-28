/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The page's texts in the game's language (Kevin, 26 October 2026: English, French and Chinese; any other language
// stays English). Read once, when the menu loads, so the MODS entry is already in the right language.
//
// The game says its language through its own translation of one of its menu texts (constants "languages.sample",
// the Quit Game entry both menus show): first engine.translate, which the game's pieces call (toggle.js), else the
// text the engine wrote into that entry (data-l10n-id). The UI engine's CSS language feature, read first, matched
// nothing in game (first trial of the mod: event=language source=none in a French game).
function msGameLanguage(config, engineApi, doc) {
    const languages = config.languages;
    const sample = languages.sample;
    const told = [];
    if (engineApi && typeof engineApi.translate === "function") {
        try {
            told.push(["translate", engineApi.translate(sample.key)]);
        } catch (error) {
            told.push(["translate_error", ""]);
        }
    }
    const entry = doc && typeof doc.querySelector === "function"
        ? doc.querySelector('[data-l10n-id="' + sample.key + '"]') : null;
    if (entry) told.push(["element", entry.textContent]);
    for (const [source, text] of told) {
        const said = msSampleText(text);
        if (!said) continue;
        if (said === msSampleText(sample.english)) return { code: languages.default, source: source };
        for (const code of Object.keys(sample.texts)) {
            if (said === msSampleText(sample.texts[code])) return { code: code, source: source };
        }
        return { code: languages.default, source: source + "_other" };
    }
    return { code: languages.default, source: "none" };
}

function msSampleText(text) {
    return typeof text === "string" ? text.trim().toLowerCase() : "";
}

// The config with the chosen language's texts in its page part. A text missing in that language falls back to
// English (CLAUDE.md: English is shown when a translation is missing).
function msLocalized(config, code) {
    const texts = config.texts;
    const fallback = texts[config.languages.default];
    const chosen = texts[code] || fallback;
    const page = Object.assign({}, config.page, fallback, chosen);
    page.statusTexts = Object.assign({}, fallback.statusTexts, chosen.statusTexts);
    return Object.assign({}, config, { language: texts[code] ? code : config.languages.default, page: page });
}
