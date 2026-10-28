/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// One row of tabs of the options screen (navigationbar.html: top_nav for the tabs, sub_nav for the sub-tabs), drawn
// in the page with the game's markup and stylesheet. The game's bar is a layer the engine drives for its own menus:
// the page draws its own and switches it itself, on a click on a tab or on a key's glyph, or on the tab actions the
// engine sends to the menu (borrow.js). Its items are plain divs, not the game's gbx-button, which tells the
// native side on each click (pieces.js, button). A bar wider than the screen scrolls sideways to its selected
// tab through the game's own helper, as the game's bar does on a vertically split screen (navigationbar.css).

class MsTabBar {
    // prefix: "top_nav" or "sub_nav"; onSelect(index, fromPad) is told the tab the player chose.
    constructor(page, prefix, onSelect) {
        this.page = page;
        this.prefix = prefix;
        this.onSelect = onSelect;
        this.key = prefix === "top_nav" ? "top" : "sub";
        this.choices = page.config.page.tabs.glyphs[this.key];
        this.actions = this.choices[0].actions;
        this.sounds = page.config.page.tabs.sounds[this.key];
        this.glyphReport = null;
        this.row = null;
        this.container = null;
        this.glyphs = [];
        this.items = [];
        this.tabs = null;
        this.selected = -1;
        this.frame = 0;
        this.press = null;
        this.samePressMs = page.config.page.tabs.samePressMs;
    }

    // The bar's row, built once with the page's frame; its tabs come with show().
    build() {
        this.glyphReport = this.chooseGlyphs();
        const row = this.page.element("div", this.prefix + " menu_screen_boundaries");
        row.appendChild(this.trigger(0));
        this.container = row.appendChild(this.page.element("div", this.prefix + "_cntr"));
        row.appendChild(this.trigger(1));
        this.row = row;
        return row;
    }

    // The key glyph of the game's action on either side, which the game draws with the player's own key.
    trigger(side) {
        const node = this.page.element("div", this.prefix + "_trigger");
        const glyph = node.appendChild(document.createElement("gbx-glyph"));
        glyph.setAttribute("action", this.actions[side]);
        glyph.setAttribute("submap", "");
        node.addEventListener("click", () => this.step(side === 0 ? -1 : 1, null));
        this.glyphs.push(glyph);
        return node;
    }

    // The first pair of glyph actions the game knows in this menu (over the pause menu, its lobby panel's: trial 10),
    // and for the log the keys the game draws for them. A bar without any still works with the mouse.
    chooseGlyphs() {
        const glyphs = typeof GlyphMgr !== "undefined" && GlyphMgr && GlyphMgr.GetGlyphInfo ? GlyphMgr : null;
        const info = (action) => (glyphs ? glyphs.GetGlyphInfo(action) : null);
        const choice = this.choices.find((candidate) => candidate.actions.every(info));
        if (!choice) return { state: this.key, source: "absent" };
        this.actions = choice.actions;
        const infos = choice.actions.map(info);
        return { state: this.key, source: choice.source, keyboard: msKeysCode(infos, "km_keys"),
                 gamepad: msKeysCode(infos, "gamepad_keys") };
    }

    // tabs: [{ label }]. The same tabs again only move the selection (OPTI.md, rule 9).
    show(tabs, selected) {
        if (tabs !== this.tabs) {
            this.tabs = tabs;
            this.selected = -1;
            const strip = document.createDocumentFragment();
            this.items = tabs.map((tab, index) => strip.appendChild(this.item(tab.label, index)).firstChild);
            this.container.textContent = "";
            this.container.scrollLeft = 0;
            this.container.appendChild(strip);
            for (const glyph of this.glyphs) glyph.parentNode.classList.toggle("invisible", tabs.length < 2);
        }
        this.select(selected);
    }

    item(label, index) {
        const page = this.page;
        const wrapper = page.element("div", this.prefix + "_inner_wrapper");
        const item = wrapper.appendChild(page.element("div", this.prefix + "_item_cntr"));
        item.appendChild(page.element("div", this.prefix + "_item_bg"));
        item.appendChild(page.element("div", this.prefix + "_item_txt")).textContent = label;
        item.appendChild(page.element("div", this.prefix + "_item_line"));
        item.addEventListener("mouseenter", () => {
            item.classList.add("hover_effect");
            page.sound(item, this.sounds.enter);
        });
        item.addEventListener("mouseleave", () => {
            item.classList.remove("hover_effect");
            page.sound(item, this.sounds.leave);
        });
        item.addEventListener("click", () => this.onSelect(index, false));
        return wrapper;
    }

    // The tab lit, its forward or backward sound as the game's bar plays it (PlayTabAudio), the glyphs greyed at
    // the ends, and the tab brought into view once its width is laid out (the next frame, OPTI.md, rule 10).
    select(index) {
        const item = this.items[index];
        if (index === this.selected || !item) return;
        const previous = this.items[this.selected];
        if (previous) {
            previous.classList.remove("selected");
            this.page.sound(item, index > this.selected ? this.sounds.forward : this.sounds.backward);
        }
        item.classList.add("selected");
        this.selected = index;
        this.glyphs[0].setAttribute("disabled", String(index === 0));
        this.glyphs[1].setAttribute("disabled", String(index === this.items.length - 1));
        if (this.frame) window.cancelAnimationFrame(this.frame);
        this.frame = window.requestAnimationFrame(() => {
            this.frame = 0;
            this.page.scroll.reveal(item, this.container, true);
        });
    }

    // via: the action's name for a press, null for a click. A move comes under several names (borrow.js): if
    // one press ever sent two of them, the second, a moment later, would step again. The same name again is another
    // press, and two different keys are never pressed that close together.
    step(delta, via) {
        if (via) {
            const now = msNow();
            const last = this.press;
            if (last && last.delta === delta && last.via !== via && now - last.at < this.samePressMs) return;
            this.press = { delta: delta, via: via, at: now };
        }
        const index = this.selected + delta;
        if (this.tabs && index >= 0 && index < this.tabs.length) this.onSelect(index, Boolean(via));
    }

    stop() {
        if (this.frame) window.cancelAnimationFrame(this.frame);
        this.frame = 0;
        this.press = null;
    }
}
