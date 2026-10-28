/* Copyright (c) 2026 kevin-hDev
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

"use strict";

// How a page of a mod is laid out as the options screen, after Kevin's choice of drawing A (README, 25 October
// 2026: a mod's pages as tabs, its sub-pages as sub-tabs). The rule is the page's own, the same for every mod:
// the page's loose rows go under a General tab, then each page it opens (a NestedOption, found through its groups,
// since the SDK wraps a mod's options in a group by default: Mod.iter_display_options) becomes a tab. Inside a tab
// the same split gives the sub-tabs. A page deeper than a sub-tab stays a row that opens it, as a screen laid out
// the same way. Pure: the node tests drive it.

// [{ label, link (the row that opens it, null for General), rows }]
function msTabs(rows, config) {
    const general = [];
    const tabs = [];
    let title = null;
    for (const row of rows) {
        if (row.kind === "title") {
            title = row;
        } else if (row.kind === "link" && row.target) {
            tabs.push({ label: row.label, link: row, rows: row.target.rows });
        } else {
            // A group's title shows above rows of its own only: one holding nothing but pages, or followed at once
            // by another group's title (Python flattens a group in a group), leaves no title, never two in a row.
            if (title) general.push(title);
            title = null;
            general.push(row);
        }
    }
    if (general.length > 0 || tabs.length === 0) {
        tabs.unshift({ label: config.page.generalLabel, link: null, rows: general });
    }
    return tabs;
}

// A screen: "list" (the mods, one tab whose rows are the mods), "mod" (a mod's page) or "page" (a page opened from
// a sub-tab). page: { title, rows, locked, details } as msParseModel gives it; crumb: the names leading to it.
function msView(kind, page, crumb, config) {
    const tabs = kind === "list" ? [{ label: page.title, link: null, rows: page.rows }] : msTabs(page.rows, config);
    return { kind: kind, crumb: crumb, details: page.details, locked: page.locked, tabs: tabs,
        subtabs: tabs.map(() => undefined) };
}

// A tab's sub-tabs, worked out once: its own pages when it opens any, else null (General never has any).
function msSubtabs(view, index, config) {
    if (view.subtabs[index] === undefined) {
        const tab = view.tabs[index];
        const split = tab.link ? msTabs(tab.rows, config) : [];
        view.subtabs[index] = split.some((sub) => sub.link) ? split : null;
    }
    return view.subtabs[index];
}

// What the screen shows for a tab and a sub-tab: their rows, and the details shown until a row is lit (the
// sub-tab's page, else the tab's, else the screen's own).
function msSelection(view, tab, sub, config) {
    const subtabs = msSubtabs(view, tab, config);
    const shown = subtabs ? subtabs[sub] : view.tabs[tab];
    const owner = (subtabs && shown.link) || view.tabs[tab].link;
    return { rows: shown.rows, subtabs: subtabs, details: owner ? owner.details : view.details };
}

// The screen a row opens: a mod's page from the list, else a page, its crumb the tabs it was reached through.
function msChildView(view, tab, sub, link, config) {
    if (view.kind === "list") return msView("mod", link.target, [config.page.title, link.label], config);
    const crumb = view.crumb.slice();
    if (view.tabs[tab].link) crumb.push(view.tabs[tab].label);
    const subtabs = msSubtabs(view, tab, config);
    if (subtabs && subtabs[sub].link) crumb.push(subtabs[sub].label);
    crumb.push(link.label);
    return msView("page", link.target, crumb, config);
}
