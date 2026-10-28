/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";
// Plays the trial the way Kevin does in game, on the game's own pieces: MODS in the pause menu, the list of mods
// and a mod's details, the test mod's page with the mouse then the gamepad, its tabs, sub-tabs and deeper page, a
// real mod's locked page, a mod with more tabs than the screen is wide, Escape back and out, reopening, the menu
// closing under the page, then MODS in the main menu. Python's capture is played by the test: it sees F9 pressed.
(async function () {
    const result = { steps: [] };
    const config = window.ModSettings.config.page;
    const input = config.input;
    const pause = document.querySelector("widget-menu-pause");
    const main = document.querySelector("widget-menu-main");
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const waitFor = async (test, tries = 100) => {
        for (let i = 0; i < tries; i += 1) {
            if (test()) return true;
            await sleep(50);
        }
        return false;
    };
    // As InputMgr.OnInputAction: on select it first clicks the element the hidden menu still has selected (the
    // MODS entry, Event_Input_Select), then sends the action to the page.
    let selected = null;
    const action = (name) => document.dispatchEvent(new CustomEvent(input.event,
        { detail: { inputActionName: name, inputActionType: input.pressed } }));
    const pad = (name) => {
        if (name === "select" && selected) selected.dispatchEvent(new MouseEvent("click", { bubbles: true, view: window }));
        action(input[name]);
    };
    // The tab actions as the pause menu sends them: its lobby panel's for the tabs (trial 10).
    const tabs = { right: input.tabs.top.right[1], left: input.tabs.top.left[1], subRight: input.tabs.sub.right[0] };
    const escape = (ident) => document.dispatchEvent(new CustomEvent(config.escape.event, { detail: { ident: ident } }));
    const click = (node) => node.dispatchEvent(new MouseEvent("click", { bubbles: true, view: window }));
    const mouse = (node, type) => node.dispatchEvent(new MouseEvent(type, { bubbles: false, cancelable: true, view: window }));
    const all = (selector) => Array.from(document.querySelectorAll(".ms_root " + selector));
    const text = (selector) => document.querySelector(".ms_root " + selector).textContent;
    const root = (widget) => widget.querySelector(".ms_root");
    const isOpen = (widget) => root(widget) !== null && !root(widget).classList.contains("ms_closed");
    const screen = () => document.querySelector(".ms_root .ms_rows:not(.ms_hidden)");
    const rows = () => (screen() ? Array.from(screen().querySelectorAll(".menu_options_entry")) : []);
    const labels = () => rows().map((row) => row.querySelector(".menu_options_entry_text").textContent).join("|");
    const inScreen = (selector) => Array.from(screen().querySelectorAll(selector));
    const lit = (index) => rows()[index].classList.contains("hover_effect");
    const crumb = () => text(".ms_crumb");
    const status = () => text(".ms_status");
    const closeText = () => text(".ms_close");
    const topTabs = () => all(".top_nav_item_txt").map((node) => node.textContent);
    const topSelected = () => all(".top_nav_item_cntr").findIndex((node) => node.classList.contains("selected"));
    const subShown = () => !document.querySelector(".ms_root .sub_nav_wrapper").classList.contains("ms_hidden");
    const subTabs = () => all(".sub_nav_item_txt").map((node) => node.textContent).join("|");
    const subSelected = () => all(".sub_nav_item_cntr").findIndex((node) => node.classList.contains("selected"));
    const details = () => [text(".menu_options_details_title"), all(".ms_line").map((node) => node.textContent).join("|"),
        text(".ms_meta")];
    const openLink = (index) => click(rows()[index].querySelector(".oak_option_button"));
    const sliderText = (index) => inScreen("gbx-slider-alt")[index].querySelector(".slider_value").textContent;
    const triggered = (name) => TestRecord.triggers.indexOf(name) >= 0;
    const navLocked = () => input.lockedNavigation.every((flag) => pause.dataset[flag] === "true");
    const step = (name) => result.steps.push(name);
    const holder = () => document.querySelector(".ms_root .ms_screens");
    const within = (node, box, vertical) => {
        const outer = box.getBoundingClientRect();
        const inner = node.getBoundingClientRect();
        return vertical ? inner.top >= outer.top - 1 && inner.bottom <= outer.bottom + 1
            : inner.left >= outer.left - 1 && inner.right <= outer.right + 1;
    };
    const inView = (node) => within(node, holder(), true);
    InputMgr.CurrWidget = pause;
    pause.dataset[input.lockedNavigation[0]] = "false";

    try {
        const pauseEntry = pause.querySelector('[name="Mod Settings Button"]');
        const mainEntry = main.querySelector('[name="Mod Settings Button"]');
        await waitFor(() => pauseEntry.querySelector(".button_txt").textContent === config.entryLabel);
        result.pauseLabel = pauseEntry.querySelector(".button_txt").textContent;
        result.mainLabel = mainEntry.querySelector(".mm_button_txt").textContent;
        await sleep(300);

        step("list");
        click(pauseEntry.querySelector(".list_btn"));
        result.shownAtOnce = isOpen(pause);
        // Python answering shows no status (texts "pythonOk" is empty): its four mods are the sign.
        await waitFor(() => status() === "" && rows().length === 4);
        result.listRows = labels();
        result.listHeader = [topTabs().join("|"), crumb(), subShown()];
        mouse(rows()[0], "mouseenter");
        result.modDetails = details();
        mouse(rows()[0], "mouseleave");
        mouse(rows()[2], "mouseenter");
        result.markupAsText = [details()[1], document.querySelectorAll(".ms_root .menu_options_details b, " +
            ".ms_root .menu_options_details img").length];
        mouse(rows()[2], "mouseleave");
        result.glyphActions = all(".top_nav_trigger gbx-glyph").map((node) => node.getAttribute("action")).concat(
            all(".sub_nav_trigger gbx-glyph").map((node) => node.getAttribute("action")));
        result.pauseHidden = pause.querySelector(".menu_pause").style.display === "none";
        result.pauseLobbyKept = document.querySelector("widget-lobby-info").style.display === "flex";
        result.escapeClaimed = triggered(config.escape.added + ":" + config.escape.ident);
        result.navLocked = navLocked();

        step("test_mod_mouse");
        openLink(0);
        result.modHeader = [crumb(), topTabs().join("|"), topSelected(), subShown(), details()[0]];
        result.backShown = closeText() === config.backLabel;
        // Over the pause menu Escape comes as the claim and as an action: the action alone goes nowhere.
        action("Input.Action.Menu.Escape");
        result.pauseEscapeActionIgnored = crumb() !== "";
        result.modRows = labels();
        result.screensWithMod = all(".ms_rows").length;
        result.groupTitles = inScreen(".cat_divider_title").map((node) => node.textContent);
        mouse(rows()[1], "mouseenter");
        result.rowDetails = details();
        mouse(rows()[1], "mouseleave");
        mouse(rows()[3], "mouseenter");
        result.ownTitle = details()[0];
        mouse(rows()[3], "mouseleave");
        const toggles = inScreen("gbx-toggle");
        const sliders = inScreen("gbx-slider-alt");
        const stepper = inScreen("gbx-stepper-alt")[0];
        const dropdown = inScreen("gbx-dropdown-options-alt")[0];
        result.rebindKey = String(inScreen("oak-rebind-entry")[0].primaryRebindGlyph.querySelector(".glyph-key")
            .style.backgroundImage);
        result.wholeText = sliderText(0);
        result.fractionText = sliderText(1);
        click(toggles[0].querySelector(".toggle_button_right"));
        sliders[0].WhileRightMouseDown();
        result.mouseSlider = sliderText(0);
        click(toggles[1].querySelector(".toggle_button_right"));
        stepper.buttonRightElement.dispatchEvent(new MouseEvent("mousedown"));
        stepper.buttonRightElement.dispatchEvent(new MouseEvent("mouseup"));
        result.mouseStepper = stepper.querySelector(".stepper_value").textContent;
        // Trial 8: a long page ran off the screen. This page is longer than the scrolled area (small_list.css): it
        // scrolls, with the game's bar, and an opened list is brought into view.
        await sleep(300);
        result.scrollStyle = getComputedStyle(holder()).overflowY;
        result.pageOverflows = holder().scrollHeight > holder().clientHeight;
        result.barActive = document.querySelector(".ms_root .menu_options_entry_content > .oakscroll-v.is-active") !== null;
        holder().scrollTop = 0;
        click(dropdown.querySelector(".dropdown_opt_header"));
        result.dropdownOpened = dropdown.classList.contains("expanded");
        result.listInView = inView(dropdown.DropdownList) && holder().scrollTop > 0;
        click(dropdown.DropdownItems[2]);
        result.dropdownPicked = dropdown.querySelector(".dropdown_opt_label_text").textContent;
        click(rows()[7].querySelector(".oak_option_button"));
        result.buttonNotice = status().indexOf(config.statusTexts.buttonPressed + " (1)") >= 0;
        // Tabs with the mouse: a tab, the right key's glyph, then General again, its values kept.
        click(all(".top_nav_item_cntr")[1]);
        result.mouseTab = [topSelected(), labels(), subShown(), details()[1]];
        click(all(".top_nav_trigger")[1]);
        result.glyphTab = [topSelected(), subShown(), subTabs(), subSelected(), labels()];
        click(all(".top_nav_item_cntr")[0]);
        result.mouseGeneral = [topSelected(), subShown(), sliderText(0)];
        await sleep(1000);

        step("test_mod_gamepad");
        InputMgr.bIsUsingCursorNavigation = false;
        InputMgr.InputDeviceType = 1;
        selected = pauseEntry.querySelector(".list_btn");
        pad("down");
        result.padFirstRow = lit(0);
        pad("down");
        pad("right");
        result.padSlider = sliderText(0);
        pad("down");
        pad("right");
        result.padFraction = sliderText(1);
        for (let i = 0; i < 4; i += 1) pad("down");
        result.padRebindRow = lit(6);
        const rebind = inScreen("oak-rebind-entry")[0];
        const drawnKey = () => {
            const image = rebind.primaryRebindGlyph.querySelector(".glyph-key");
            return image ? image.style.backgroundImage : null;
        };
        pad("select");
        result.captureLabel = rows()[6].querySelector(".menu_options_entry_text").textContent;
        await waitFor(() => String(drawnKey()).indexOf("Key_F9.png") >= 0, 60);
        result.capturedKey = drawnKey();
        pad("down");
        pad("select");
        result.padButton = status().indexOf(config.statusTexts.buttonPressed + " (2)") >= 0;
        // The game's tab actions: a tab starts at its first row, lit.
        action(tabs.right);
        result.padTab = [topSelected(), labels(), lit(0)];
        pad("select");
        result.nestedToggle = inScreen("gbx-toggle")[0].CurrentValue;
        action(tabs.right);
        result.padSubtabs = [subShown(), subTabs(), subSelected(), labels()];
        action(tabs.subRight);
        action(tabs.subRight);
        result.padPageB = [subSelected(), labels(), lit(0)];
        result.rowsAfterTabs = all(".ms_rows").length;
        action(tabs.subRight);
        action(tabs.right);
        result.padEnds = [subSelected(), topSelected()];
        pad("down");
        result.deepLinkLit = lit(1);
        pad("select");
        result.deep = [crumb(), topTabs().join("|"), subShown(), labels(), holder().scrollTop, all(".ms_rows").length];
        pad("down");
        pad("select");
        result.deepToggle = inScreen("gbx-toggle")[0].CurrentValue;
        escape(config.escape.ident);
        result.backToPageB = [topSelected(), subShown(), subSelected(), labels()];
        pad("down");
        result.rowKept = lit(1) && !lit(0);
        result.tabSounds = ["NavForward", "NavBackward", "SubNavForward"].filter((id) => TestRecord.sounds.indexOf(id) < 0);
        await sleep(600);

        step("real_mod_locked");
        escape(config.escape.ident);
        result.backToList = [crumb(), rows().length, closeText(), topTabs().join("|"), all(".ms_rows").length];
        InputMgr.bIsUsingCursorNavigation = true;
        openLink(1);
        result.realCrumb = crumb();
        result.lockedNotice = status().indexOf(config.lockedLabel) >= 0;
        result.lockedRows = inScreen(".ms_locked").length;
        const realSlider = inScreen("gbx-slider-alt")[0];
        const before = realSlider.querySelector(".slider_value").textContent;
        realSlider.WhileRightMouseDown();
        InputMgr.bIsUsingCursorNavigation = false;
        pad("down");
        pad("down");
        pad("select");
        pad("down");
        pad("right");
        result.realSliderKept = realSlider.querySelector(".slider_value").textContent === before;
        // Its page holds one page: a single sub-tab, its long rows ending with a deeper page.
        action(tabs.right);
        result.realSub = [topSelected(), subShown(), subTabs(), lit(0)];
        holder().scrollTop = 0;
        const last = rows().length - 1;
        for (let i = 0; i < last; i += 1) pad("down");
        result.realScrolled = lit(last) && holder().scrollTop > 0 && inView(rows()[last]);
        const realTop = holder().scrollTop;
        pad("select");
        result.realDeep = [crumb(), holder().scrollTop, inScreen(".ms_locked").length];
        escape(config.escape.ident);
        result.realBack = [topSelected(), holder().scrollTop === realTop];
        pad("down");
        result.realRowKept = lit(last);
        action("Input.Action.Menu.OpenOptionsMenu");
        await sleep(600);

        step("wide_tabs");
        escape(config.escape.ident);
        InputMgr.bIsUsingCursorNavigation = true;
        openLink(2);
        result.wideTabs = topTabs().length;
        const bar = document.querySelector(".ms_root .top_nav_cntr");
        result.wideOverflows = bar.scrollWidth > bar.clientWidth;
        // The keys' glyphs keep their width (navigationbar.css: 5rem) when the tabs overflow.
        const rem = parseFloat(getComputedStyle(document.documentElement).fontSize);
        result.triggersKept = all(".top_nav_trigger").every((node) =>
            Math.abs(node.getBoundingClientRect().width - 5 * rem) < 1);
        InputMgr.bIsUsingCursorNavigation = false;
        const lastTab = result.wideTabs - 1;
        for (let i = 0; i < lastTab; i += 1) action(tabs.right);
        await sleep(300);
        result.wideLast = topSelected() === lastTab && bar.scrollLeft > 0 &&
            within(all(".top_nav_item_cntr")[lastTab], bar, false);
        for (let i = 0; i < lastTab; i += 1) action(tabs.left);
        await sleep(300);
        result.wideFirst = topSelected() === 0 && within(all(".top_nav_item_cntr")[0], bar, false);
        // The options screen's name moves the tabs too; with the lobby's in the same frame, it is one press.
        action(input.tabs.top.right[0]);
        action(tabs.right);
        result.twoNamesOneStep = topSelected();
        await sleep(100);
        action(input.tabs.top.right[0]);
        await sleep(100);
        action(tabs.right);
        result.namesNextFrames = topSelected();
        await sleep(300);
        escape(config.escape.ident);
        await sleep(300);

        step("close_and_reopen");
        escape("SomeoneElse");
        result.otherEscapeIgnored = isOpen(pause) && crumb() === "";
        escape(config.escape.ident);
        result.closedByEscape = !isOpen(pause);
        result.pauseBack = pause.querySelector(".menu_pause").style.display === "";
        result.navGivenBack = pause.dataset[input.lockedNavigation[0]] === "false" &&
            input.lockedNavigation.slice(1).every((flag) => pause.dataset[flag] === undefined);
        result.escapeReleased = triggered(config.escape.removed + ":" + config.escape.ident);
        const firstRoot = root(pause);
        await sleep(600);
        InputMgr.bIsUsingCursorNavigation = true;
        click(pauseEntry.querySelector(".list_btn"));
        result.sameRootReused = root(pause) === firstRoot && isOpen(pause);
        result.reopenedOnList = crumb() === "" && topTabs().join("|") === config.title;
        await sleep(600);
        openLink(0);
        result.valuesKept = sliderText(0);
        pause.classList.add(config.inactiveClass);
        await waitFor(() => !isOpen(pause));
        result.closedWithMenu = !isOpen(pause);
        pause.classList.remove(config.inactiveClass);
        await sleep(300);

        step("main_menu");
        click(mainEntry.querySelector(".menu_button_wrapper"));
        await waitFor(() => root(main) !== null && rows().length === 4);
        result.mainOpen = isOpen(main) && root(pause) === null;
        result.mainHidden = main.querySelector(".menu_screen_boundaries").style.display === "none";
        result.mainOthersHidden = ["widget-lobby-info", "widget-news"].every((name) =>
            document.querySelector(name).style.display === "none");
        openLink(0);
        result.mainValues = sliderText(0);
        // The main menu sends Escape only as an action (first trial of the mod): it goes back.
        action("Input.Action.Menu.Escape");
        result.mainBack = crumb() === "";
        click(document.querySelector(".ms_close"));
        result.mainClosed = !isOpen(main) && main.querySelector(".menu_screen_boundaries").style.display === "";
        result.mainOthersBack = document.querySelector("widget-lobby-info").style.display === "flex"
            && document.querySelector("widget-news").style.display === "";
        await sleep(600);
        // Nothing but the Escape claims may reach the menus' native side (the rebind entry and gbx-button would).
        const escapes = [config.escape.added, config.escape.removed];
        result.otherNative = TestRecord.triggers.filter((entry) => escapes.indexOf(entry.split(":")[0]) < 0);
    } catch (error) {
        result.error = String(error && error.stack || error);
    }
    document.getElementById("result").textContent = JSON.stringify(result);
})();
