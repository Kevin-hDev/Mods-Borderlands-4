"""Tests the window's pages as the mod declares them (sketch M1, then the LOCK page of 2026-10-02): every setting on a
card, once, in the window's order; the words each card and each choice need, in both languages; the rows a switch
greys; and what the heirloom's window can do that this one leaves empty."""

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


check("two pages of settings, BEAM and LOCK, then the COMMANDS page",
      [group.identifier for group in menu.MENU] == ["beam_menu", "lock_menu"]
      and menu.SHOWN_PAGES == ("beam", "lock", "controls")
      and panel_theme.PAGES == menu.SHOWN_PAGES and set(menu.CARDS) == {"beam", "lock"})
cards = menu.CARDS["beam"]
check("the BEAM page's cards are BEAM, under the page's own name, then ENERGY (sketch M1)",
      [name for name, _ in cards] == ["beam", "energy"])
check("BEAM holds the element, the damage, then the catch distance; ENERGY the bar's switch, then what is spent, given "
      "back and waited",
      cards[0][1] == (settings.element, settings.damage, settings.width)
      and cards[1][1] == (settings.show_bar, settings.drain, settings.regen, settings.regen_delay))
lock_cards = menu.CARDS["lock"]
check("the LOCK page's cards are LOCK, under the page's own name, then BOUNCE",
      [name for name, _ in lock_cards] == ["lock", "bounce"])
check("LOCK holds its switch, then the time before the lock and the angle that breaks it; BOUNCE its switch",
      lock_cards[0][1] == (settings.lock, settings.lock_delay, settings.lock_angle)
      and lock_cards[1][1] == (settings.bounce,))
every_card = [card for page in ("beam", "lock") for card in menu.CARDS[page]]
on_cards = [option for _, options in every_card for option in options]
check("every setting of the window is on a card, once, in the window's order",
      on_cards == list(settings.ALL) == [option for group in menu.MENU for option in group.children])
check("each page's settings are its group's", list(menu.MENU[0].children) == list(settings.BEAM_PAGE)
      and list(menu.MENU[1].children) == list(settings.LOCK_PAGE))
check("the element shows between two arrows, and is the only row that does", menu.ARROWS == {"element"}
      and settings.element.choices == list(settings.ELEMENTS))
check("the lock's two numbers grey and stay still while the lock is off: they would change nothing",
      menu.DEPENDS_ON == {"lock_delay": (("lock",),), "lock_angle": (("lock",),)})
check("the catch and the bounce act with the lock off: they are never greyed",
      "width" not in menu.DEPENDS_ON and "bounce" not in menu.DEPENDS_ON)
check("nothing else is greyed, hidden, pictured or said in an orange frame",
      not any((menu.COMMANDS_DEPEND_ON, menu.NOTICES, menu.ACTIVE_WHEN, menu.SHOWN_WHEN, menu.PICTURES)))
other_cards = [name for page in ("beam", "lock") for name, _ in menu.CARDS[page][1:]]
check("each card after a page's first has its name and its sentence in both languages",
      other_cards == ["energy", "bounce"]
      and all(f"{name}{suffix}" in words for name in other_cards for suffix in ("", "_desc")
              for words in (panel_en.TEXT, panel_fr.TEXT)))
check("each page has its name in both languages, and its sentence in French (the English one is the page's own)",
      all(page in panel_en.TEXT and page in panel_fr.TEXT for page in menu.SHOWN_PAGES)
      and set(panel_fr.GROUPS) == {"beam", "lock"} and all(group.description for group in menu.MENU))
check("each setting has its French name and sentence, and its English ones on the option",
      set(panel_fr.OPTIONS) == {option.identifier for option in settings.ALL}
      and all(option.display_name != option.identifier and option.description for option in settings.ALL))
check("a setting's name fits the label's column: short, as the sketch wrote it",
      all(len(option.display_name) <= 22 for option in settings.ALL)
      and all(len(name) <= 22 for name, _ in panel_fr.OPTIONS.values()))
check("each element has its name in both languages", set(panel_en.CHOICES) == set(panel_fr.CHOICES) == set(settings.ELEMENTS))
check("the bar shows by default", settings.show_bar.default_value is True)
check("the mod saves the window's language, icons, page and theme with its settings",
      mod.options[-4:] == [panel_preferences.language, panel_preferences.controller_icons, panel_preferences.last_page,
                           panel_preferences.theme]
      and all(option.is_hidden for option in mod.options[-4:]))
check("the mod's settings page is the one that opens the window (test_panel_entry.py opens it)",
      mod.iter_display_options.__name__ == "display")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
