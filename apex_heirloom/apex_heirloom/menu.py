"""The window's pages: HEIRLOOM, then HOLSTER, each led by its part's switch; the COMMANDS page follows, Apex
Movement's, a card per command (control_config.py). Kevin chose it on 2026-09-26 from the sketches in
cosmetics/heirloom/docs/esquisses_menu/ (U1 to U3), the HEIRLOOM page's choice of heirloom, skin and glow on 2026-09-29
(sketch H2), and the COMMANDS page's cards on 2026-09-30 (sketch I1), docs/mokup/menu_mods/decisions.md.
"""

from mods_base import NestedOption

from . import control_config, heirloom_settings, holster_settings, pack

# Left out of the mod's options: saved values stay at the top level of the settings file, as before the window.
heirloom_page = NestedOption(
    "heirloom_menu", list(heirloom_settings.ALL),
    display_name="Heirloom", description="Your heirloom in your right hand when your weapon is put away.",
)
holster_page = NestedOption(
    "holster_menu", [holster_settings.holster],
    display_name="Holster", description="Whether your keys put your weapon away.",
)
ALL = MENU = [heirloom_page, holster_page]

_RUNS_HEIRLOOM = pack.runs(heirloom_settings.heirloom.identifier)
_RUNS_HOLSTER = pack.runs(holster_settings.holster.identifier)
# The pages a player can open, in the window's order (panel_theme.PAGES): a separate file shows its own part's only.
# The other part's pages are still built, never shown, so the window's code finds every widget it reads. COMMANDS is in
# every file since the heirloom has keys of its own (sketch I1, 2026-09-30): Heirloom shows its INSPECT card there.
SHOWN_PAGES = (*(("heirloom",) if _RUNS_HEIRLOOM else ()), *(("holster",) if _RUNS_HOLSTER else ()), "controls")

# A row that changes nothing while its switches are off greys and stays still, as the FOV under Custom FOV in Apex
# Movement: each tuple needs one of its switches on. A part's switch greys its whole page (Kevin, 2026-09-26, U2).
# Only the rows of the parts this file runs: the window reads the switches of those alone (settings.ALL).
_HEIRLOOM, _HOLSTER = (heirloom_settings.heirloom.identifier,), (holster_settings.holster.identifier,)
_A_KEY_HELD = (holster_settings.keyboard_hold.identifier, holster_settings.controller_hold.identifier)
_HEIRLOOM_ROWS = {option.identifier: (_HEIRLOOM,) for option in heirloom_settings.ALL
                  if option is not heirloom_settings.heirloom}
_HOLSTER_ROWS = {
    holster_settings.keyboard_hold.identifier: (_HOLSTER,),
    holster_settings.controller_hold.identifier: (_HOLSTER,),
    holster_settings.hold_time.identifier: (_HOLSTER, _A_KEY_HELD),
}
DEPENDS_ON = {**(_HEIRLOOM_ROWS if _RUNS_HEIRLOOM else {}), **(_HOLSTER_ROWS if _RUNS_HOLSTER else {})}
# Each card of the COMMANDS page greys and stays still with the switch of the part it serves: PUT AWAY with the holster
# (Kevin, 2026-09-26: « oui on grise aussi »), INSPECT with the heirloom (Kevin, 2026-09-30, sketch I1). By command,
# as DEPENDS_ON: one of each tuple's switches on.
COMMANDS_DEPEND_ON = {command.name: ((command.part,),) for command in control_config.COMMANDS}
# The settings of a card's keys, shown on it under its rows and put back with the keys by RESET CONTROLS (Kevin,
# 2026-10-06: the hold is a key setting, « ce sont des réglages de touches assignables »). By command, those this file
# runs only, as COMMANDS_DEPEND_ON.
COMMAND_SETTINGS = {command.name: holster_settings.HOLD_SETTINGS for command in control_config.COMMANDS
                    if command.name == "put_away"}
# Said at the top of a page, always in view: the heirloom's settings wait for the next weapon change (Kevin,
# 2026-09-26, sketch A). By page, the text's key in panel_en.py and panel_fr.py.
NOTICES = {"heirloom": "applies"}


def chosen(shown: dict) -> str:
    """The heirloom the window shows chosen, from its values (the form's `shown`, saved or not)."""
    return heirloom_settings.heirloom_of(shown.get(heirloom_settings.model.identifier))


def _skin(shown: dict) -> str:
    name = chosen(shown)
    return heirloom_settings.skin_of(name, shown.get(heirloom_settings.SKINS[name].identifier))


_SKINS, _SIZES = heirloom_settings.SKINS, heirloom_settings.SIZES
# Sketch H2: a row also greys and stays still while it changes nothing, whatever its switch: the skin of a heirloom
# that has one only (the knife), the glow while the chosen skin has not ours. By row, a test of the window's values.
_ACTIVE_WHEN = {
    **{option.identifier: (lambda _shown, option=option: len(option.choices) > 1) for option in _SKINS.values()},
    heirloom_settings.glow.identifier: lambda shown: heirloom_settings.glows(chosen(shown), _skin(shown)),
}
# Each heirloom keeps its own skin and size, one row each (sketches K1 and H2): the window shows the chosen one's.
_SHOWN_WHEN = {option.identifier: (lambda shown, name=name: chosen(shown) == name)
               for name in heirloom_settings.OFFERED for option in (_SKINS[name], _SIZES[name])}
ACTIVE_WHEN = _ACTIVE_WHEN if _RUNS_HEIRLOOM else {}
SHOWN_WHEN = _SHOWN_WHEN if _RUNS_HEIRLOOM else {}
# Rows whose choices show as two arrows around the chosen name, its place among them in the value box (sketch H2): a
# heirloom may keep many skins, the row stays one line.
ARROWS = frozenset(option.identifier for option in _SKINS.values())
# Shown right of a page's title, description and sentence, so the player sees the heirloom (Kevin, 2026-09-26: « où
# j'ai mis le rectangle jaune à droite de heirloom, on peut rajouter l'image ? pour voir le couteau »). By page: which
# of its pictures the window's values choose, then each picture's file in assets/ and its width and height in the
# window's units, about the height of the three lines beside it.
PICTURES = {"heirloom": (chosen, {"jakobs_knife": ("knife.png", 266, 130), "axe": ("axe.png", 266, 130)})}
