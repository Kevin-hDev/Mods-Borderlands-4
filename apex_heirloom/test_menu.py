"""Tests the window's pages: HEIRLOOM, its switch then the heirloom, each one's skin, the glow, the mode, each one's
size and the draw (sketch H2); HOLSTER, its switch then the two hold switches and the hold time; then Movement's
COMMANDS (sketch I1). Each page's rows grey with its part's switch, the hold time also while no key is held, the
COMMANDS page's PUT AWAY card with the holster, its INSPECT card with the heirloom; a skin row greys when its
heirloom has one skin only, the glow when the skin shown has none of ours; the chosen heirloom's skin, size and
picture show, the other's hide, by the values the window shows; the skins are chosen with arrows; the HEIRLOOM page
says the next weapon change applies its settings; every heirloom and skin has a name in English, the heirlooms in
French too, and every setting its French words."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import heirloom_stubs  # noqa: E402

heirloom_stubs.install()

from apex_heirloom import heirloom_settings, holster_settings, inspect_keys, keys, menu, panel_en  # noqa: E402
from apex_heirloom import panel_fr  # noqa: E402
from apex_heirloom import panel_theme  # noqa: E402
from apex_heirloom.heirloom_catalog import HEIRLOOMS, OFFERED  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


h, k = heirloom_settings, holster_settings
check("two settings pages, HEIRLOOM then HOLSTER", menu.MENU == menu.ALL == [menu.heirloom_page, menu.holster_page]
      and [page.identifier for page in menu.MENU] == ["heirloom_menu", "holster_menu"])
check("HEIRLOOM holds its switch, the heirloom, each one's skin, the glow, the mode, each one's size and the draw",
      menu.heirloom_page.children == list(h.ALL) and h.ALL[:2] == (h.heirloom, h.model))
check("HOLSTER holds its switch alone: the hold is a key setting (Kevin, 2026-10-06)",
      menu.holster_page.children == [k.holster])
check("... shown on the PUT AWAY card of the COMMANDS page, and on no other card",
      menu.COMMAND_SETTINGS == {"put_away": (k.keyboard_hold, k.controller_hold, k.hold_time)})
check("the keys, the inspection's too, are chosen on the COMMANDS page that follows, on neither page",
      panel_theme.PAGES == ("heirloom", "holster", "controls")
      and not {keys.keyboard_key, keys.controller_key, inspect_keys.keyboard_key, inspect_keys.controller_key}
      & {*menu.heirloom_page.children, *menu.holster_page.children})
check("each row but the switches greys with its part's switch, the hold time also while no key is held",
      menu.DEPENDS_ON == {**{option.identifier: (("heirloom",),) for option in h.ALL[1:]},
                          "keyboard_hold": (("holster",),), "controller_hold": (("holster",),),
                          "hold_time": (("holster",), ("keyboard_hold", "controller_hold"))})
check("the PUT AWAY card greys with the holster, the INSPECT card with the heirloom (Kevin, 2026-09-30)",
      menu.COMMANDS_DEPEND_ON == {"put_away": (("holster",),), "inspect": (("heirloom",),)})
check("the full mod offers every page (a separate file, its own part's: test_build_heirloom_files.py)",
      menu.SHOWN_PAGES == panel_theme.PAGES)
check("the HEIRLOOM page, and it alone, says the next weapon change applies its settings, in both languages",
      menu.NOTICES == {"heirloom": "applies"}
      and panel_fr.TEXT["applies"] == "Quitte le menu et change d'arme pour appliquer le changement."
      and panel_en.TEXT["applies"] == "Leave the menu and change weapons to apply the change.")


def shown(heirloom, skin="own"):
    """The window's values with `heirloom` chosen, wearing `skin`."""
    return {h.model.identifier: heirloom, **{option.identifier: "own" for option in h.SKINS.values()},
            h.SKINS.get(heirloom, h.SKINS["axe"]).identifier: skin}


knife_skin, axe_skin = h.SKINS["jakobs_knife"].identifier, h.SKINS["axe"].identifier
check("a skin row greys when its heirloom has one skin only: the knife's, not the axe's",
      set(menu.ACTIVE_WHEN) == {knife_skin, axe_skin, h.glow.identifier}
      and not menu.ACTIVE_WHEN[knife_skin](shown("axe")) and menu.ACTIVE_WHEN[axe_skin](shown("jakobs_knife")))
glow = menu.ACTIVE_WHEN[h.glow.identifier]
check("the glow greys while the skin shown has none of ours: the axe's own look glows, a game skin and the knife not",
      glow(shown("axe")) and not glow(shown("axe", "hacker")) and not glow(shown("jakobs_knife"))
      and glow(shown("axe", "rust")) and not glow(shown("sword")))
rows = {name: (h.SKINS[name].identifier, h.SIZES[name].identifier) for name in OFFERED}


def visible(values):
    return {name for name, test in menu.SHOWN_WHEN.items() if test(values)}


check("the chosen heirloom's skin and size show, the other's hide; a heirloom no longer offered shows the knife's",
      set(menu.SHOWN_WHEN) == {row for pair in rows.values() for row in pair}
      and visible(shown("jakobs_knife")) == set(rows["jakobs_knife"]) and visible(shown("axe")) == set(rows["axe"])
      and visible(shown("sword")) == set(rows["jakobs_knife"]) and menu.chosen({}) == "jakobs_knife")
check("the skins are chosen with arrows, the other choices with a button each", menu.ARROWS == {knife_skin, axe_skin})
choose, pictures = menu.PICTURES["heirloom"]
check("the HEIRLOOM page shows the chosen heirloom's picture, one for each, at the knife's size",
      list(menu.PICTURES) == ["heirloom"] and list(pictures) == list(OFFERED)
      and pictures["jakobs_knife"] == ("knife.png", 266, 130) and pictures["axe"] == ("axe.png", 266, 130)
      and choose(shown("axe")) == "axe" and choose(shown("sword")) == "jakobs_knife")
names = {*OFFERED, *(skin["name"] for name in OFFERED for skin in HEIRLOOMS[name]["skins"])}
check("every heirloom and every skin has its name in English, each heirloom in French too, the axe's own look named",
      names <= set(panel_en.CHOICES) and set(OFFERED) <= set(panel_fr.CHOICES)
      and panel_fr.CHOICES["axe"] == "Hache" and panel_fr.CHOICES["own"] == "D'origine")
check("every setting of both pages has its French words, the page's description too",
      {option.identifier for option in (*h.ALL, *k.ALL)} <= set(panel_fr.OPTIONS)
      and panel_fr.GROUPS["heirloom"] == "Ton heirloom dans ta main droite quand ton arme est rangée."
      and menu.heirloom_page.description == "Your heirloom in your right hand when your weapon is put away.")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
