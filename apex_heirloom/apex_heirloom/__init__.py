"""Apex Heirloom: an Apex Legends style heirloom in Borderlands 4, and a key to put your weapon away. Put your weapon
away and your heirloom, the Jakobs knife or the axe, comes into your right hand, with its own animations.

Two parts, each with its own switch (parts.py): the heirloom, and the holster, which was Tidy Weapons until it joined
the heirloom (Kevin, 2026-09-26, docs/mokup/menu_mods/decisions.md). The heirloom shows on any weapon put away,
whichever key or mod does it. Everything the heirloom's page sets applies from the next weapon change.

The same code builds the full mod and each separate file, Tidy Weapons and Heirloom: pack.py says which parts this one
runs, and only their hooks, keys and settings are given to the mod below.
"""

from mods_base import build_mod

from . import family, frame, heirloom, heirloom_settings, holster_settings, keys, lifecycle, pack, panel_open
from . import heirloom_choices, inspect_keys
from . import panel_preferences, parts, restriction, settings

__version__ = "1.0.3"
__author__ = "kevin-hDev"

# Set here: heirloom_settings is read by heirloom, which it cannot import back.
heirloom_settings.mode.on_change_while_enabled = heirloom_choices.mode_changed
heirloom_settings.model.on_change_while_enabled = heirloom_choices.heirloom_changed
heirloom_settings.glow.on_change_while_enabled = heirloom_choices.glow_changed
for _skin in heirloom_settings.SKINS.values():
    _skin.on_change_while_enabled = heirloom_choices.skin_changed

# What each part brings to the mod, in the full mod's order: its hooks, its keys, and its options besides its settings.
_BROUGHT = {
    parts.HEIRLOOM: ([lifecycle.arms_frame], [inspect_keys.keyboard_bind, inspect_keys.controller_bind],
                     [inspect_keys.keyboard_key, inspect_keys.controller_key]),
    parts.HOLSTER: ([frame.tick, restriction.on_restriction], [keys.keyboard_bind, keys.controller_bind],
                    [keys.keyboard_key, keys.controller_key]),
}
# The mod list's line, by the parts a file runs (pack.PARTS).
DESCRIPTIONS = {
    (): "An Apex Legends style heirloom: the Jakobs knife or the axe in your right hand when your weapon is put away, "
        "and a key to put it away.",
    (heirloom_settings.heirloom.identifier,): "An Apex Legends style heirloom: the Jakobs knife or the axe in your "
                                              "right hand when your weapon is put away.",
    (holster_settings.holster.identifier,): "A key to put your weapon away.",
}

# FamilyMod refuses to switch on while another installed file of this mod already runs one of these parts.
mod = build_mod(
    cls=family.FamilyMod,
    name=pack.NAME,
    description=DESCRIPTIONS[pack.PARTS],
    hooks=[hook for part in parts.PARTS for hook in _BROUGHT[part][0]],
    keybinds=[bind for part in parts.PARTS for bind in _BROUGHT[part][1]],
    # The window's language, icons and page are hidden options: the SDK menu lists the settings and the keys.
    options=[*settings.ALL, *(option for part in parts.PARTS for option in _BROUGHT[part][2]),
             panel_preferences.language, panel_preferences.controller_icons, panel_preferences.last_page],
    on_enable=parts.mod_on,
    on_disable=parts.mod_off,
)
panel_open.install(mod)

# mods_base only enables a mod whose settings file says so; a fresh install has none and would stay off.
if mod.settings_file is not None and not mod.settings_file.exists():
    mod.enable()
