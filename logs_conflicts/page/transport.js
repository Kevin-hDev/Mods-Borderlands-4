/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// Loopback requests to the mod's service, rewritten from Mod Settings' transport.js. done(text): text is null unless
// the service answered 200. The engine seemed not to apply xhr.timeout (Mod Settings, trial 7): a timer of the page
// ends the request too, or one that never answers would keep the page waiting.
function lcRequest(method, url, body, timeoutMs, done) {
    let finished = false;
    let request = null;
    let guard = null;
    const finish = (text) => {
        if (finished) return;
        finished = true;
        if (guard !== null) clearTimeout(guard);
        done(text);
    };
    try {
        request = new XMLHttpRequest();
        request.open(method, url, true);
        guard = setTimeout(() => {
            guard = null;
            finish(null);
            request.abort();
        }, timeoutMs);
        request.onload = () => finish(request.status === 200 && typeof request.responseText === "string"
            ? request.responseText : null);
        request.onerror = () => finish(null);
        request.send(body);
    } catch (error) {
        finish(null);
    }
}

// The answer's JSON object, or null when nothing came back, or an answer over its route's bound or without this
// mod's marker: a program unrelated to this mod that holds the port is not taken for the service (audit, 1 November
// 2026). The marker is public: a program made to fake it gets in, yet the page shows any text as text only. The
// bounds are the service's own (OPTI.md, rule 16, checked on both sides).
function lcAnswer(text, limit, marker) {
    if (text === null || text.length > limit) return null;
    let answer = null;
    try {
        answer = JSON.parse(text);
    } catch (error) {
        return null;
    }
    return answer && typeof answer === "object" && answer.marker === marker ? answer : null;
}

// One request at a time, as Mod Settings' sender: the service has one thread, and the page asked five things at once
// when it opened (audit, 1 November 2026). The queue is bounded: past it, a request is answered null at once and an
// event is dropped. onError: an answer's handler threw; the game shows no script error, so it would be lost.
function lcTransport(config, onError) {
    const http = config.http;
    const base = "http://" + http.host + ":" + http.port + http.basePath;
    const queue = [];
    let busy = false;
    const next = () => {
        if (busy || queue.length === 0) return;
        busy = true;
        const job = queue.shift();
        lcRequest(job.method, base + job.route, job.body, http.timeoutMs, (text) => {
            busy = false;
            try {
                job.done(lcAnswer(text, job.limit, config.marker));
            } catch (error) {
                onError();
            }
            next();
        });
    };
    const call = (method, route, body, limit, done) => {
        if (queue.length >= http.maxQueued) {
            done(null);
            return;
        }
        queue.push({ method: method, route: route, body: body, limit: limit, done: done });
        next();
    };
    const small = http.maxResponseBytes;
    return {
        hello(done) { call("GET", http.routes.hello, null, small, done); },
        log(revision, done) {
            call("GET", http.routes.log + (revision ? "?rev=" + revision : ""), null, http.maxLogResponseBytes, done);
        },
        conflicts(done) { call("GET", http.routes.conflicts, null, http.maxConflictsResponseBytes, done); },
        copy(done) { call("POST", http.routes.copy, null, small, done); },
        copyConflicts(done) { call("POST", http.routes.copyConflicts, null, small, done); },
        openFolder(done) { call("POST", http.routes.openFolder, null, small, done); },
        event(body) { call("POST", http.routes.event, JSON.stringify(body), small, () => {}); }
    };
}
