/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// The page's life, over the pause menu or the main menu: opened from the MODS entry, its frame
// (frame.js) built once at the first opening, then only shown and hidden (OPTI.md, rules 5 and 8); the
// gamepad, the tab actions and Escape; closed with the menu. It shows at once from what MsData already holds and
// never waits on Python.

const MS_TAB_ACTIONS = { tab_left: ["top", -1], tab_right: ["top", 1], sub_left: ["sub", -1], sub_right: ["sub", 1] };

class MsPage {
    constructor(config, sender, transport) {
        this.config = config;
        this.sender = sender;
        this.transport = transport;
        this.data = new MsData(config, transport, (body) => this.sender.send(body));
        this.settings = new MsSettings(this);
        this.focus = new MsFocus(this);
        this.capture = new MsCapture(this);
        this.parts();
        this.notice = "";
        this.widget = null;
        this.release = null;
        this.isOpen = false;
        this.prefetched = false;
        this.otherActions = new Set();
    }

    // What belongs to one frame, made again when the page moves to another menu's document.
    parts() {
        this.screens = new MsScreens(this);
        this.scroll = new MsScroll(this);
        this.frame = new MsFrame(this);
    }

    report(name, fields) {
        this.sender.send(msEventBody(this.config, name, fields));
    }

    reportTimings(timings) {
        this.sender.send(msTimingsBody(this.config, timings));
    }

    sound(node, id) {
        if (this.widget && typeof this.widget.PlaySoundAtNode === "function") this.widget.PlaySoundAtNode(node, id);
    }

    // Called when a menu with the MODS entry is built: the first opening then waits on nothing.
    prefetch() {
        if (this.prefetched) return;
        this.prefetched = true;
        this.data.withTemplates(() => {});
        this.refresh();
    }

    refresh() {
        this.data.refresh((model) => this.settings.applyModel(model), () => this.showStatus());
    }

    open(widget, host) {
        if (this.isOpen) return;
        const hostConfig = this.config.page.hosts[host];
        if (!hostConfig || !widget || typeof widget.TriggerWidgetEvent !== "function" || !widget.querySelector) {
            this.report("error", { code: "no_widget" });
            return;
        }
        const start = msNow();
        // One page per menu: its pieces were set up in that menu's document.
        if (this.widget !== widget) this.destroy();
        this.widget = widget;
        this.release = msBorrowMenu(this.config, widget, hostConfig, {
            onEscape: () => this.escape(),
            onClose: (reason) => this.close(reason),
            onNav: (name, via) => this.nav(name, via),
            onOther: (name) => this.otherAction(name)
        });
        if (!this.release) {
            this.report("error", { code: "menu_borrow_failed" });
            return;
        }
        this.isOpen = true;
        this.notice = "";
        this.otherActions.clear();
        this.settings.opened();
        this.report("page_opened", { host: host });
        if (this.frame.root) {
            this.frame.root.classList.remove("ms_closed");
            // At the top again, as the options screen at each activation (menu_options.js, Event_Activate).
            this.scroll.shown(0);
            if (this.screens.current) this.showScreen(this.screens.current);
            this.showStatus();
            this.data.timing("shown", start);
        } else {
            this.data.withTemplates(() => this.build(start));
        }
        this.refresh();
    }

    build(start) {
        if (!this.isOpen || this.frame.root) return;
        const begin = msNow();
        const holder = this.frame.build(this.widget);
        this.scroll.attach(holder);
        this.screens.attach(holder);
        if (this.data.model) this.screens.showRoot(this.data.model);
        else this.frame.showEmpty();
        this.showStatus();
        this.report("page_built", { code: this.data.model ? "with_model" : "without_model" });
        this.report("glyph", this.frame.topBar.glyphReport);
        this.report("glyph", this.frame.subBar.glyphReport);
        this.data.timing("build", begin);
        this.data.timing("shown", start);
    }

    // A newer model from Python: the list is built again, once the frame exists.
    showModel(model) {
        if (this.frame.root && this.data.templates) this.screens.showRoot(model);
    }

    openScreen(link) {
        if (this.data.templates) this.screens.open(link);
    }

    // The frame and the locked notice follow the screen shown.
    showScreen(shown) {
        if (!this.frame.root) return;
        this.frame.showScreen(shown, this.screens.depth);
        this.notice = shown.view.locked ? this.config.page.lockedLabel : "";
        this.showStatus();
    }

    // Escape (the gamepad's back button too): a capture is cancelled, an open list closes, a mod's page goes back,
    // the page closes. Over the main menu the list gets no Escape of its own: one press must not also go back.
    escape() {
        if (this.capture.active) this.capture.cancel("escape");
        else if (this.focus.list) this.closeList();
        else if (!this.screens.back()) this.close("escape");
    }

    nav(name, via) {
        if (this.capture.active) return;
        const tab = MS_TAB_ACTIONS[name];
        // A tab action is logged with its name and its device: which key sends which was not known (trial 10).
        this.report("gamepad", tab ? { name: name, code: msActionCode(via), device: this.inputDevice() }
                                   : { name: name });
        if (tab) (tab[0] === "top" ? this.frame.topBar : this.frame.subBar).step(tab[1], via);
        else this.focus.nav(name);
    }

    inputDevice() {
        const input = typeof InputMgr !== "undefined" && InputMgr ? InputMgr : null;
        return (input && this.config.page.input.devices[String(input.InputDeviceType)]) || "unknown";
    }

    otherAction(name) {
        const code = msActionCode(name);
        if (this.otherActions.has(code) || this.otherActions.size >= this.config.page.input.maxOtherActions) return;
        this.otherActions.add(code);
        this.report("input_action", { name: code });
    }

    // A change Python did not take: said on screen, and the model asked again. Its row no longer counts as
    // changed, and the model is taken even at the same revision: the row shows what the mod holds again. While a
    // newer value of the row still waits to leave, the row is left as it is: that value decides.
    changeRefused(status, ident, newerWaiting) {
        this.notify(this.config.page.statusTexts.refused + " (" + status + ")");
        if (ident && newerWaiting) return;
        if (ident) this.settings.changed.delete(ident);
        this.data.forceNext = true;
        this.refresh();
    }

    // An open list holds its own Escape claim: closed first, so the claim goes back with it.
    closeList() {
        if (this.focus.list) this.focus.list.target.OnClick(undefined);
    }

    close(reason) {
        if (!this.isOpen) return;
        this.capture.cancel("page_closed");
        this.closeList();
        this.screens.reset();
        // After the screens: going back gives each screen its row again, and a page opened anew starts from none.
        this.focus.reset();
        const failure = this.release ? this.release() : null;
        this.release = null;
        this.isOpen = false;
        if (this.frame.root) this.frame.root.classList.add("ms_closed");
        this.scroll.stop();
        this.frame.stop();
        // Python saves the sliders' mods on page_closed: the values still waiting leave before it.
        this.sender.sendAfterValues(msEventBody(this.config, "page_closed", { reason: reason }));
        if (failure) this.report("error", { code: failure });
    }

    destroy() {
        this.frame.remove();
        this.scroll.stop();
        this.parts();
    }

    // What the player did that leaves nothing else on screen, shown after Python's state until the next notice.
    notify(text) {
        this.notice = text;
        this.showStatus();
    }

    showStatus() {
        this.frame.showStatus(msStatusText(this.config.page.statusTexts, this.data, this.notice));
    }

    text(content, className) {
        const node = this.element("p", "ms_text " + className);
        node.textContent = content;
        return node;
    }

    element(tag, className) {
        const node = document.createElement(tag);
        node.className = className;
        return node;
    }
}
