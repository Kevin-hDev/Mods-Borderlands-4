/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// Loopback requests to the mod's Python side, and reads of the game's own UI files. The HUD Editor proved
// XMLHttpRequest to 127.0.0.1 from the pause menu in game (docs/candidats/HUD/README.md).

// done(text, status): text is null unless the request succeeded; status is 0 when nothing answered.
// onError runs when the page's own answer handler throws: the game shows no script error, so it would else be
// lost without a trace (a capture once ended this way, in the browser test).
// The game's own files never set xhr.timeout, and the engine seemed not to apply it (trial 7, not verified): a timer
// of the page ends the request too, or a request that never answers would hold the single line to Python for good.
function msRequest(method, url, body, timeoutMs, done, onError) {
    let finished = false;
    let request = null;
    let guard = null;
    const finish = (text, status) => {
        if (finished) return;
        finished = true;
        if (guard !== null) clearTimeout(guard);
        try {
            done(text, status);
        } catch (error) {
            if (onError) onError();
        }
    };
    try {
        request = new XMLHttpRequest();
        request.open(method, url, true);
        if (timeoutMs > 0) {
            request.timeout = timeoutMs;
            guard = setTimeout(() => {
                guard = null;
                finish(null, 0);
                request.abort();
            }, timeoutMs);
        }
        request.onload = () => {
            // A local file (coui:// in game) may answer with status 0 instead of 200.
            const ok = request.status === 200 || (request.status === 0 && url.indexOf("http") !== 0);
            finish(ok && typeof request.responseText === "string" ? request.responseText : null, request.status);
        };
        request.onerror = () => finish(null, 0);
        request.ontimeout = () => finish(null, 0);
        request.send(body);
    } catch (error) {
        finish(null, 0);
    }
}

function msTransport(config, onError) {
    const http = config.http;
    const base = "http://" + http.host + ":" + http.port;
    const request = (method, url, body, done) => msRequest(method, url, body, http.timeoutMs, done, onError);
    return {
        post(body, done) { request("POST", base + http.eventPath, body, () => done()); },
        change(body, done) { request("POST", base + http.changePath, body, (_text, status) => done(status)); },
        getModel(done) { request("GET", base + http.modelPath, null, done); },
        capture(body, done) { request("POST", base + http.capturePath, body, done); },
        captureState(done) { request("GET", base + http.capturePath, null, done); },
        getGameFile(url, done) { request("GET", url, null, done); }
    };
}
