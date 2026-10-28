/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";
// Stand-ins for what surrounds the game's pieces, never the pieces themselves: the test loads the game's own
// custom_elements.js, cursorhandler.js, oakscroll.js, input_manager.js and the pieces' scripts and markup, copied
// from the game's paks at test time (game_ui_copies.py). Only the engine, the input manager's state (its file
// defines the class, not the game's instance) and the component store are played here.

window.TestRecord = { triggers: [], engine: [], sounds: [] };

window.engine = {
    trigger(name) { TestRecord.engine.push(name); },
    // An English game: the one text the page reads its language from (language.js) comes back in English.
    translate(key) { return key === "QuitGameEntry" ? "Quit Game" : key; },
    updateWholeModel() {},
    synchronizeModels() {},
    registerBindingAttribute() {},
    on() {}
};

window.RegisterGlobalEvent = () => {};

// The input manager's state the pieces and the page read. Cursor mode by default; the driver switches it off
// to play the gamepad, as the game does on a gamepad action (input_manager.js, OnNavigationTypeChanged).
window.InputMgr = {
    bIsUsingCursorNavigation: true,
    SimulatingMouse: false,
    CurrWidget: null,
    functionOnDirectionalNavigationItemFocus: () => {},
    GamepadModel: null,
    IsUsingCursor() { return this.bIsUsingCursorNavigation; },
    IsUsingGamepad() { return false; },
    ShouldBlockCursorInput() { return !this.IsUsingCursor() && !this.SimulatingMouse; },
    FindContainer() { return null; },
    // The game's own code, from its input_manager.js loaded after this file: only the state around it is played.
    DirectionalNavigationItemFocusHelper(element, container, horizontal) {
        return InputManager.prototype.DirectionalNavigationItemFocusHelper.call(this, element, container, horizontal);
    }
};

window.InteractorManager = { isScrolling: false, currentInteractionType: "mouse", types: { mouse: "mouse", keyboard: "keyboard" } };

window.Animator = class {
    constructor() {}
    StopAllAnimations() {}
    StopAllAnimationsOnNode() {}
};

// The game finds a node's widget through its data-widget-ident (triggers.js); the test's widgets are the
// menu elements themselves.
window.getParentWidget = (node) => {
    let current = node;
    while (current) {
        if (current.tagName && current.tagName.toLowerCase().indexOf("widget-") === 0) return current;
        current = current.parentNode;
    }
    return null;
};

// The game fills its store with each component's whole file (component_loader.js, LoadComponentComplete).
window.CompStore = {
    GetComponent(id) {
        const source = document.getElementById("component-" + id);
        if (!source) return undefined;
        const holder = document.createElement("div");
        holder.innerHTML = source.innerHTML;
        return holder;
    }
};

// The two menus' widgets, as the page sees them: their native calls are recorded, sounds remembered. Defined
// before the menus are parsed, since the game's gbx-component calls its widget during its own Init.
class FakeWidget extends HTMLElement {
    TriggerWidgetEvent(name, ident) { TestRecord.triggers.push(name + ":" + ident); }
    PlaySoundAtNode(node, id) {
        this.dataset.sound = id;
        TestRecord.sounds.push(id);
    }
    OnComponentNodeUpdated() {}
}
customElements.define("widget-menu-pause", class extends FakeWidget {});
customElements.define("widget-menu-main", class extends FakeWidget {});
