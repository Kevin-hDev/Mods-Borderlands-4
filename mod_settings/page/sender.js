/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The page's single line to Python: one request at a time. Events and presses wait in a queue bounded by
// maxPending, so a dead service cannot grow memory. A dragged slider fires a value per frame: per row, the latest
// value replaces the waiting one, and values leave at most once per valueIntervalMs (OPTI.md, rule 13); the last one
// always leaves. A change Python refuses (old model, locked row, busy game) is told to onRefused with its status,
// its row's id (null for a press), and whether a newer value of that row still waits to leave.

class MsSender {
    constructor(transport, intervalMs, maxPending, clock, timer, onRefused) {
        this.transport = transport;
        this.intervalMs = intervalMs;
        this.maxPending = maxPending;
        this.clock = clock;
        this.timer = timer;
        this.onRefused = onRefused;
        this.busy = false;
        this.pending = [];
        this.values = new Map();
        this.lastValueAt = -Infinity;
        this.wait = null;
        this.dropped = 0;
    }

    send(body) { this.queue({ change: false, body: body, key: null }); }

    sendPress(body) { this.queue({ change: true, body: body, key: null }); }

    // The values still waiting leave first, then body: the page's last word (page_closed) comes after them.
    sendAfterValues(body) {
        for (const [key, value] of this.values) this.queue({ change: true, body: value, key: key }, true);
        this.values.clear();
        this.send(body);
    }

    queue(item, held) {
        if (item.body === null) return;
        if (this.pending.length < this.maxPending) this.pending.push(item);
        else this.dropped += 1;
        if (!held) this.next();
    }

    // key: the row's id; the map holds one entry per row of the page at most.
    sendValue(key, body) {
        if (body === null) return;
        this.values.set(key, body);
        this.next();
    }

    next() {
        if (this.busy) return;
        let item = this.pending.shift();
        if (item === undefined) item = this.takeValue();
        if (item === undefined) return;
        this.busy = true;
        const done = (status) => {
            this.busy = false;
            if (item.change && status !== 200 && this.onRefused) {
                this.onRefused(status, item.key, this.waiting(item.key));
            }
            this.next();
        };
        if (item.change) this.transport.change(item.body, done);
        else this.transport.post(item.body, () => done(200));
    }

    waiting(key) {
        return key !== null && (this.values.has(key) || this.pending.some((item) => item.key === key));
    }

    takeValue() {
        if (this.values.size === 0 || this.wait !== null) return undefined;
        const early = this.lastValueAt + this.intervalMs - this.clock();
        if (early > 0) {
            this.wait = this.timer(() => {
                this.wait = null;
                this.next();
            }, early);
            return undefined;
        }
        const [key, body] = this.values.entries().next().value;
        this.values.delete(key);
        this.lastValueAt = this.clock();
        return { change: true, body: body, key: key };
    }
}
