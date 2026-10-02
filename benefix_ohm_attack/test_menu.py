"""Tests the window's pages as the mod declares them (sketch M1): every setting on a card, once, in the order the
sketch drew; the words each card and each choice need, in both languages; and what the heirloom's window can do that
this one leaves empty."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()
from benefix_ohm_attack import menu, mod, panel_en, panel_fr, panel_preferences, panel_theme, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


check("one page of settings, BEAM, then the COMMANDS page",
      [group.identifier for group in menu.MENU] == ["beam_menu"] and menu.SHOWN_PAGES == ("beam", "controls")
      and panel_theme.PAGES == menu.SHOWN_PAGES and set(menu.CARDS) == {"beam"})
cards = menu.CARDS["beam"]
check("the page's cards are BEAM, under the page's own name, then ENERGY (sketch M1)",
      [name for name, _ in cards] == ["beam", "energy"])
check("BEAM holds the element then the damage; ENERGY the bar's switch, then what is spent, given back and waited",
      cards[0][1] == (settings.element, settings.damage)
      and cards[1][1] == (settings.show_bar, settings.drain, settings.regen, settings.regen_delay))
on_cards = [option for _, options in cards for option in options]
check("every setting of the window is on a card, once, in the window's order",
      on_cards == list(settings.ALL) == list(menu.MENU[0].children))
check("the element shows between two arrows, and is the only row that does", menu.ARROWS == {"element"}
      and settings.element.choices == list(settings.ELEMENTS))
check("nothing is greyed, hidden, pictured or said in an orange frame",
      not any((menu.DEPENDS_ON, menu.COMMANDS_DEPEND_ON, menu.NOTICES, menu.ACTIVE_WHEN, menu.SHOWN_WHEN, menu.PICTURES)))
check("each card after the first has its name and its sentence in both languages",
      all(f"{name}{suffix}" in words for name, _ in cards[1:] for suffix in ("", "_desc")
          for words in (panel_en.TEXT, panel_fr.TEXT)))
check("each page has its name in both languages, and its sentence in French (the English one is the page's own)",
      all(page in panel_en.TEXT and page in panel_fr.TEXT for page in menu.SHOWN_PAGES)
      and set(panel_fr.GROUPS) == {"beam"} and menu.MENU[0].description)
check("each setting has its French name and sentence, and its English ones on the option",
      set(panel_fr.OPTIONS) == {option.identifier for option in settings.ALL}
      and all(option.display_name != option.identifier and option.description for option in settings.ALL))
check("a setting's name fits the label's column: short, as the sketch wrote it",
      all(len(option.display_name) <= 22 for option in settings.ALL)
      and all(len(name) <= 22 for name, _ in panel_fr.OPTIONS.values()))
check("each element has its name in both languages", set(panel_en.CHOICES) == set(panel_fr.CHOICES) == set(settings.ELEMENTS))
check("the bar shows by default", settings.show_bar.default_value is True)
check("the mod saves the window's language, icons and page with its settings",
      mod.options[-3:] == [panel_preferences.language, panel_preferences.controller_icons, panel_preferences.last_page]
      and all(option.is_hidden for option in mod.options[-3:]))
check("the mod's settings page is the one that opens the window (test_panel_entry.py opens it)",
      mod.iter_display_options.__name__ == "display")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
