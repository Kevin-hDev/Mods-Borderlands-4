/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// How the page drives each game piece, as menu_options.js does: setup() before the page enters the document (the
// pieces' Init then applies the model, as in the options screen), connected() once Init has run, then set() for a
// value from Python, step() for gamepad left/right and activate() for the gamepad's select button. A locked row
// (a mod the page may not change) shows its value and ignores the gamepad; mod_settings.css takes the mouse from it.

function msStep(target, direction) {
    if (direction === "left") target.WhileLeftMouseDown();
    else target.WhileRightMouseDown();
}

const MS_PIECES = {
    slider: {
        setup(piece, model) {
            piece.target.bShowChangedIndicator = true;
            piece.target.SetListener(piece.listener);
            piece.target.SetDataModel(model);
        },
        set(piece, model) { piece.target.SetDataModel(model); },
        step(piece, direction) { msStep(piece.target, direction); }
    },
    toggle: {
        setup(piece, model) {
            piece.target.bShowChangedIndicator = true;
            piece.target.SetListener(piece.listener);
            piece.target.SetDataModel(model);
        },
        // A mod's own words for off and on (BoolOption false_text, true_text) replace the game's, whose
        // translation id is removed so the game's localisation cannot write them back.
        connected(piece) {
            const texts = piece.target.querySelectorAll(".toggle_button_text");
            const own = [piece.row.falseText, piece.row.trueText];
            for (let index = 0; index < texts.length && index < 2; index += 1) {
                if (!own[index]) continue;
                texts[index].removeAttribute("data-l10n-id");
                texts[index].textContent = own[index];
            }
        },
        set(piece, model) { piece.target.UpdateCurrentValue(model.initialvalue, false); },
        step(piece, direction) { msStep(piece.target, direction); },
        activate(piece) { piece.target.WhileLeftMouseDown(); }
    },
    stepper: {
        setup(piece, model) {
            piece.target.bShowChangedIndicator = true;
            piece.target.SetListener(piece.listener);
            piece.target.SetDataModel(model);
        },
        set(piece, model) { piece.target.UpdateCurrentValue(model.initialvalue, false); },
        step(piece, direction) { msStep(piece.target, direction); }
    },
    // The dropdown talks to a widget: it gets the page's stand-in, so nothing reaches the menu's native side
    // except the Escape claim it needs (page.js, dropdownWidget).
    dropdown: {
        setup(piece, model) {
            piece.target.SetListener(piece.listener);
            piece.target.SetWidget(piece.widget);
            piece.target.SetDataModel(model);
            piece.target.SetNameAlt(model.ident);
        },
        set(piece, model) {
            piece.target.SetDataModel(model);
            piece.target.UpdateDropdownItems();
            piece.target.RefreshHeaderText();
        },
        activate(piece) { piece.target.OnClick(undefined); }
    },
    // The rebind entry's own clicks ask the menu's native side to rebind a game action (rebind_entry.js,
    // OnClickRebindEntry): replaced once Init has set them, by the page's capture and clear.
    keybind: {
        setup(piece, model) { piece.target.SetDataModel(model); },
        connected(piece) {
            const target = piece.target;
            target.primaryRebindEntry.onclick = (event) => piece.settings.startCapture(piece, event);
            target.secondaryRebindEntry.onclick = (event) => event.stopPropagation();
            target.clearBindingEntry.onclick = (event) => piece.settings.clearKey(piece, event);
            target.resetBindingEntry.onclick = (event) => event.stopPropagation();
        },
        set(piece, model) { piece.target.UpdateData(model.primarybind, "", false); },
        // The second slot is hidden (mod_settings.css): left or right goes one step further past it.
        step(piece, direction) {
            msStep(piece.target, direction);
            if (piece.target.currentTargetEntryIdx === RebindEntryType.SECONDARY) msStep(piece.target, direction);
        },
        activate(piece) {
            if (piece.target.currentTargetEntryIdx === RebindEntryType.CLEAR) piece.settings.clearKey(piece, null);
            else piece.settings.startCapture(piece, null);
        },
        enter(piece) { piece.target.OnSpecialEnter(); },
        leave(piece) { piece.target.OnSpecialLeave(); }
    },
    // gbx-button tells the native side on each click (gbx_button.js, OnClick: InputMgr.SelectElement), which in
    // the pause menu could select a hidden entry: its markup is kept in a plain div, for its look only.
    button: {
        prepare(element) {
            const plain = document.createElement("div");
            plain.className = element.className;
            while (element.firstChild) plain.appendChild(element.firstChild);
            return plain;
        },
        setup(piece) {
            const text = piece.target.querySelector(".oak_option_button_txt");
            if (text) text.textContent = piece.row.text;
            piece.target.addEventListener("click", (event) => {
                event.stopPropagation();
                piece.settings.pressButton(piece);
            });
        },
        activate(piece) { piece.settings.pressButton(piece); }
    }
};
// A row that opens a page (a mod in the list, a nested page): the button's look, the page's own action.
MS_PIECES.link = MS_PIECES.button;

class MsPiece {
    constructor(settings, row, target) {
        this.settings = settings;
        this.row = row;
        this.target = target;
        this.handler = MS_PIECES[row.kind];
        this.listener = settings.listener;
        this.widget = settings.dropdownWidget;
        this.entry = null;
    }

    model(value) {
        const build = MS_MODELS[this.row.kind];
        return build ? build(this.row, value) : null;
    }

    setup(value) { this.handler.setup(this, this.model(value)); }

    connected() { if (this.handler.connected) this.handler.connected(this); }

    set(value) { if (this.handler.set) this.handler.set(this, this.model(value)); }

    step(direction) { if (this.handler.step && !this.row.locked) this.handler.step(this, direction); }

    activate() { if (this.handler.activate && !this.row.locked) this.handler.activate(this); }

    enter() { if (this.handler.enter) this.handler.enter(this); }

    leave() { if (this.handler.leave) this.handler.leave(this); }
}
