# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The catalog's view of the SDK (catalog.py): the mods in the SDK menu's order, each option's kind, names
as plain text, and which mods the page may change. Game thread only, like everything that reads the mods."""

# Most specific first: a mod may subclass an option type, and is then shown as its base.
KIND_CLASSES = (("NestedOption", "nested"), ("GroupedOption", "title"), ("ButtonOption", "button"),
                ("KeybindOption", "keybind"), ("SliderOption", "slider"), ("BoolOption", "toggle"),
                ("DropdownOption", "dropdown"), ("SpinnerOption", "stepper"))


class SdkSource:
    def __init__(self, mods_base, own_mod):
        # own_mod: a function giving Mod Settings' own Mod. Read when needed: the game's thread may start the service
        # before the load's thread has finished building the mod (__init__.py).
        self.mods_base = mods_base
        self.own_mod = own_mod
        self.kinds = tuple((getattr(mods_base, name), kind) for name, kind in KIND_CLASSES)

    def mods(self):
        return self.mods_base.get_ordered_mod_list()

    def kind_of(self, option):
        for option_class, kind in self.kinds:
            if isinstance(option, option_class):
                return kind
        return None

    def plain(self, text: str) -> str:
        return self.mods_base.html_to_plain_text(text)

    def writable(self, mod) -> bool:
        # Every mod but Mod Settings: turned off from its own page, it would cut the page off mid-way. The SDK's
        # console turns it on and off, and the page says so (texts "lockedLabel").
        return mod is not self.own_mod()
