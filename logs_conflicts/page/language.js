/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The page's texts in the game's language: English, French and Chinese; any other language stays English. Read once,
// when the menu loads, so the entry is already in the right language. Rewritten from Mod Settings' language.js,
// proven in game: the game says its language through its own translation of its Quit Game entry, first by
// engine.translate, else by the text the engine wrote into that entry.
function lcGameLanguage(config, engineApi, doc) {
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
        const said = lcSampleText(text);
        if (!said) continue;
        if (said === lcSampleText(sample.english)) return { code: languages.default, source: source };
        for (const code of Object.keys(sample.texts)) {
            if (said === lcSampleText(sample.texts[code])) return { code: code, source: source };
        }
        return { code: languages.default, source: source + "_other" };
    }
    return { code: languages.default, source: "none" };
}

function lcSampleText(text) {
    return typeof text === "string" ? text.trim().toLowerCase() : "";
}

// The config with the chosen language's texts in its page part; a text missing in that language is the English one.
function lcLocalized(config, code) {
    const texts = config.texts;
    const fallback = texts[config.languages.default];
    const chosen = texts[code] || fallback;
    const page = Object.assign({}, config.page, fallback, chosen);
    page.states = Object.assign({}, fallback.states, chosen.states);
    page.errors = Object.assign({}, fallback.errors, chosen.errors);
    page.keyNames = Object.assign({}, fallback.keyNames, chosen.keyNames);
    return Object.assign({}, config, { language: texts[code] ? code : config.languages.default, page: page });
}
