# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A sample mod for the tests: one option of each kind the SDK has, descriptions, pages laid out as tabs (one
plain, one with pages of its own, one of which opens a deeper page), and callbacks that write in the log on which
thread they run. Its settings file is in the test's temporary folder."""

import threading

DESCRIPTION = "A sample mod: each kind of setting, and pages laid out as tabs.<br>Every row can change."
NAME, AUTHOR, VERSION = "Sample Mod", "Sample author", "1.0"
SETTINGS_FILE = "sample_mod.json"


def build(mods_base, constants: dict, here, log, game_thread_id):
    prefix = constants["logPrefix"]
    budget = {"left": constants["http"]["maxChangeLogs"]}

    def thread_name() -> str:
        return "game" if threading.get_native_id() == game_thread_id else "other"

    def changed(option, value) -> None:
        if budget["left"] <= 0:
            return
        budget["left"] -= 1
        log(f"{prefix} TEST_MOD_CALLBACK option={option.identifier} value={value!r} thread={thread_name()}")

    def pressed(option) -> None:
        log(f"{prefix} TEST_MOD_BUTTON option={option.identifier} thread={thread_name()}")

    def value_options():
        return [
            mods_base.SliderOption("sample_whole", 50, 0, 100, step=5, is_integer=True, display_name="Whole number",
                                   description="A whole number from 0 to 100, in steps of 5.",
                                   on_change_anytime=changed),
            mods_base.SliderOption("sample_fraction", 1.0, 0.5, 5.0, step=0.1, is_integer=False,
                                   display_name="Fraction", on_change_anytime=changed),
            mods_base.BoolOption("sample_switch", False, display_name="Switch", description_title="Switch title",
                                 description="On or off.", on_change_anytime=changed),
            mods_base.SpinnerOption("sample_arrows", "Medium", ["Low", "Medium", "High", "Ultra"],
                                    display_name="Arrows", on_change_anytime=changed),
            mods_base.DropdownOption("sample_list", "Red", ["Red", "Green", "Blue", "Yellow"], display_name="List",
                                     on_change_anytime=changed),
            mods_base.KeybindOption("sample_key", "F7", display_name="Key", on_change_anytime=changed),
            mods_base.ButtonOption("sample_button", display_name="Button", on_press=pressed),
        ]

    more = mods_base.NestedOption("sample_more", [
        mods_base.BoolOption("sample_more_switch", True, display_name="Inner switch", on_change_anytime=changed),
        mods_base.SliderOption("sample_more_slider", 3, 1, 10, display_name="Inner number", on_change_anytime=changed),
    ], display_name="More settings", description="A page with no page of its own: a tab without sub-tabs.")
    deep = mods_base.NestedOption("sample_deep", [
        mods_base.BoolOption("sample_deep_switch", False, display_name="Deep switch", on_change_anytime=changed),
    ], display_name="Deep page", description="A page inside a sub-tab: it opens as a screen of its own.")
    pages = mods_base.NestedOption("sample_pages", [
        mods_base.BoolOption("sample_pages_switch", False, display_name="Pages switch", on_change_anytime=changed),
        mods_base.NestedOption("sample_page_a", [
            mods_base.SliderOption("sample_page_a_slider", 2, 0, 4, display_name="Page A number",
                                   on_change_anytime=changed),
        ], display_name="Page A"),
        mods_base.NestedOption("sample_page_b", [
            mods_base.BoolOption("sample_page_b_switch", True, display_name="Page B switch", on_change_anytime=changed),
            deep,
        ], display_name="Page B", description="A sub-tab whose page opens a deeper one."),
    ], display_name="Pages", description="A page with pages of its own: a tab with sub-tabs.")
    settings = here / SETTINGS_FILE
    return mods_base.Mod(
        name=NAME, author=AUTHOR, version=VERSION, description=DESCRIPTION,
        settings_file=settings, keybinds=[], hooks=[], commands=[],
        options=[mods_base.GroupedOption("sample_group", value_options(), display_name="Sample group"), more, pages],
        on_enable=lambda: log(f"{prefix} TEST_MOD_ENABLED thread={thread_name()}"),
        on_disable=lambda: log(f"{prefix} TEST_MOD_DISABLED thread={thread_name()}"),
    )
