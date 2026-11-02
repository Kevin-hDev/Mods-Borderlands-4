/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// Where the gamepad stands on the page: one of the buttons shown, or the panel where up and down scroll. Up and down
// move along the buttons, right goes to the panel, left comes back to the button it left (conception, section 4,
// proposed, checked at the trial). The first move only shows the focus, so the player sees it before it moves. The
// pointer moves it too, and leaving the button under it hides it. byPointer says the pointer put it there: a mouse
// click sends the game's select action as well (trial 1), and that action must not press the button a second time.

class LcFocus {
    constructor(frame, scrollStepPx) {
        this.frame = frame;
        this.scrollStepPx = scrollStepPx;
        this.index = 0;
        this.lastButton = 0;
        this.shown = false;
        this.byPointer = false;
    }

    set(index, byPointer) {
        this.index = index;
        this.shown = true;
        this.byPointer = byPointer === true;
        this.frame.highlight(index);
    }

    hide() {
        this.shown = false;
        this.frame.highlight(-1);
    }

    pointAway(index) {
        if (this.index === index && this.byPointer) this.hide();
    }

    // The button the gamepad or the keys put the focus on, or null: on the panel, hidden, or under the pointer.
    pressable() {
        return this.shown && !this.byPointer && this.index < LC_PANEL ? LC_BUTTONS[this.index] : null;
    }

    // The nearest button shown at index or above it: LOGS is always shown.
    shownFrom(index) {
        let at = index;
        while (at > 0 && !this.frame.isShown(at)) at -= 1;
        return at;
    }

    // After a view change: a focus left on a button the view hides goes up to one it shows.
    settle() {
        this.lastButton = this.shownFrom(this.lastButton);
        if (this.index < LC_PANEL && !this.frame.isShown(this.index)) {
            this.index = this.shownFrom(this.index);
            if (this.shown) this.frame.highlight(this.index);
        }
    }

    step(delta) {
        let at = this.index + delta;
        while (at >= 0 && at < LC_PANEL && !this.frame.isShown(at)) at += delta;
        if (at >= 0 && at < LC_PANEL) this.set(at);
        else this.set(this.index);
    }

    move(move) {
        // Taken from the pointer, the focus stays where the pointer left it before moving.
        if (!this.shown || this.byPointer) {
            this.set(this.index);
            return;
        }
        if (this.index === LC_PANEL) {
            if (move === "up" || move === "down") this.frame.scrollBy((move === "up" ? -1 : 1) * this.scrollStepPx);
            else if (move === "left") this.set(this.shownFrom(this.lastButton));
            return;
        }
        if (move === "up" || move === "down") this.step(move === "up" ? -1 : 1);
        else if (move === "right") {
            this.lastButton = this.index;
            this.set(LC_PANEL);
        }
    }
}
