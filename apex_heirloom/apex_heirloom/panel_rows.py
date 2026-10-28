"""Which rows of a page the window shows, which grey besides their switches, and which of its pictures it shows
(menu.SHOWN_WHEN, menu.ACTIVE_WHEN, menu.PICTURES). Each follows the values the window shows, saved or not, so the page
answers a click at once: the chosen heirloom's skin and size, its picture, a row greyed while it changes nothing
(Kevin, 2026-09-29, sketch H2, docs/mokup/menu_mods/decisions.md).
"""

from . import menu, panel_picture, panel_widgets as w

# A shown row's box lets its buttons take the clicks, as the engine's own boxes do.
SHOWN, HIDDEN = "SelfHitTestInvisible", "Collapsed"


def active(name, shown):
    """Whether row `name` changes something with the window's values, its switches aside."""
    test = menu.ACTIVE_WHEN.get(name)
    return test is None or bool(test(shown))


def show(widgets, shown):
    """Each row of menu.SHOWN_WHEN shown or collapsed, its rule and description with it, and each page's picture."""
    for name, test in menu.SHOWN_WHEN.items():
        widgets[f"block:{name}"].SetVisibility(w.enum("ESlateVisibility", SHOWN if test(shown) else HIDDEN))
    panel_picture.show(widgets, shown)
