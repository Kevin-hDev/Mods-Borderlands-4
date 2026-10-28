/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// What the page keeps between openings: the options screen's row markup, read once from the game's file, and
// Python's last model of the mods. Nothing here makes the page wait (OPTI.md, rules 2, 5, 14).

function msNow() {
    return typeof performance !== "undefined" && performance.now ? performance.now() : Date.now();
}

class MsData {
    constructor(config, transport, report) {
        this.config = config;
        this.transport = transport;
        this.report = report;
        this.model = null;
        this.revision = -1;
        // Set after a refused change: the next model is taken even at the revision kept.
        this.forceNext = false;
        this.python = null;
        // Python answers but has sent no model after every retry: the page says what to do instead of "wait".
        this.notReady = false;
        this.templates = null;
        this.waiters = null;
        this.timings = {};
    }

    // One opening's durations, sent together once the page is shown and Python has answered or failed.
    timing(name, since) {
        this.timings[name] = Math.max(0, msNow() - since);
        if ("shown" in this.timings && "model" in this.timings) this.flushTimings();
    }

    flushTimings() {
        const body = msTimingsBody(this.config, this.timings);
        this.timings = {};
        this.report(body);
    }

    // Empty strings mean the game's file had no such row: the page then uses its fallback. Read once either way.
    withTemplates(done) {
        if (this.templates !== null) return done(this.templates);
        if (this.waiters) return this.waiters.push(done);
        this.waiters = [done];
        const start = msNow();
        const page = this.config.page;
        this.transport.getGameFile(page.optionsHtml, (html) => {
            const regular = msExtractTemplate(html, page.regularMarker);
            const title = msExtractTemplate(html, page.titleMarker);
            this.templates = { regular: regular || "", title: title || "" };
            this.report(msEventBody(this.config, "template", { source: regular && title ? "game" : "fallback" }));
            this.timings.template = Math.max(0, msNow() - start);
            const waiters = this.waiters;
            this.waiters = null;
            for (const waiter of waiters) waiter(this.templates);
        });
    }

    // onModel(model) runs only when Python's revision differs from the one kept, or when forceNext asks; the page
    // decides what of it may replace what the player has just changed. A 503 is Python answering that its first
    // read of the mods is not done yet (routes.py): still loading, asked again after retryMs, at most retries times;
    // the next opening asks again anyway.
    refresh(onModel, onStatus, attempt) {
        const start = msNow();
        const tries = attempt || 0;
        this.transport.getModel((text, status) => {
            const model = msParseModel(text, this.config);
            const retry = this.config.page.model;
            if (!model && status === 503) {
                this.report(msEventBody(this.config, "model", { source: "not_ready" }));
                if (this.python !== true) this.python = null;
                this.notReady = tries >= retry.retries;
                onStatus();
                if (tries < retry.retries) setTimeout(() => this.refresh(onModel, onStatus, tries + 1), retry.retryMs);
                return;
            }
            this.notReady = false;
            this.python = model !== null;
            this.report(msEventBody(this.config, "model", { source: model ? "python" : "absent" }));
            this.timing("model", start);
            if (model && (model.revision !== this.revision || this.forceNext)) {
                this.forceNext = false;
                this.revision = model.revision;
                this.model = model;
                onModel(model);
            }
            onStatus();
        });
    }
}
