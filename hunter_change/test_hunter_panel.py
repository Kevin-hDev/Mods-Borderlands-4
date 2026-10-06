"""The Hunter Change window: built whole in the plain frame, its APPEARANCE page of six hunter cards in three columns,
each with its picture, name and class; no UNDO nor RESTORE in the footer; the sentence above the cards in the heirloom's
orange frame, in capitals; the look worn framed in gold and tagged CHOSEN, the hunter played tagged YOUR HUNTER, the
tags in the card's top right corner as sketch B2 drew them, CHOSEN in gold and YOUR HUNTER outlined in orange; the
class in its colour, the sentence naming both; the own look shown without CHOSEN; outside a game no card, no frame and
a sentence asking for one; the texts in French; a card without its picture keeps its name; a card clicked read
once."""

import sys
from types import SimpleNamespace

import sdk_stubs

state = sdk_stubs.install()

import panel_fixture  # noqa: E402
from hunter_change import hunters, panel_assets, panel_fonts, panel_hunters, panel_hunters_theme as ht  # noqa: E402
from hunter_change import panel_model, panel_preferences, panel_theme as theme, panel_view  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


panel_fixture.install()
loaded: list[str] = []


def texture(_world, name=panel_assets.AVATAR):
    loaded.append(name)
    return None if name == "hunter_RoboDealer.png" else object()


panel_assets.texture = texture
panel_fonts.build = lambda _root: {"title": object(), "body": object()}

model = panel_model.Model(SimpleNamespace(is_enabled=True))
root, widgets = panel_view.build_view(SimpleNamespace(), model)
check("built whole in the plain frame, under the mod's name",
      root.WidgetTree.RootWidget.kind == "CanvasPanel"
      and [child.kind for child in root.WidgetTree.RootWidget.children] == ["BackgroundBlur", "ScaleBox"]
      and theme.BRAND == "HUNTER CHANGE"
      and model.pages[0] == "appearance" and len(widgets["pages"].children) == len(model.pages))
grid = widgets["hunter_grid"]
check("six hunter cards in three columns", [len(line.children) for line in grid.children] == [3, 3]
      and all(f"hunter:{hunter.code}" in widgets for hunter in hunters.HUNTERS))
check("each card with its picture, name and class", all(
    f"hunter:{hunter.code}_picture" in widgets for hunter in hunters.HUNTERS if hunter.code != "RoboDealer")
      # One picture per card: each page of the window, APPEARANCE and HUNTER, has its six cards.
      and loaded.count("hunter_Paladin.png") == len(model.pages))
check("a card without its picture keeps its name", "hunter:RoboDealer_picture" not in widgets
      and "hunter:RoboDealer_name" in widgets)
check("no UNDO nor RESTORE in the footer", "undo" not in widgets and "restore" not in widgets)

attached = set()


def visit(node):
    attached.add(id(node))
    for child in node.children:
        visit(child)


visit(root.WidgetTree.RootWidget)
check("every registered widget in the tree", all(id(widget) in attached for widget in widgets.values()))

harlowe, loveless = hunters.by_code("Gravitar"), hunters.by_code("CorpoHacker")


def text(name):
    return panel_fixture.text(widgets, name)


def brush(name):
    return widgets[name].calls["SetBrushColor"][0]


def colour(struct):
    named = {"gold": theme.COLOR_GOLD, "spark": theme.COLOR_SPARK, "ink": theme.COLOR_INK}
    return next((name for name, value in named.items() if (struct.R, struct.G, struct.B) == theme.rgba(value)[:3]),
                None)


def shown(name):
    return widgets[name].calls["SetVisibility"][0] == "ESlateVisibility.Visible"


def slot_of(widget):
    return widget.owner.slots[widget.owner.children.index(widget)]


panel_hunters.paint(widgets, (harlowe, loveless), "EN")
check("the sentence above the cards in the heirloom's orange frame, in capitals",
      text("notice:applies") == "APPLIES AT ONCE, FOR THIS GAME." and shown("hunter_applies")
      and colour(widgets["notice:applies"].owner.owner.calls["SetBrushColor"][0]) == "spark")
check("the look worn framed in gold and tagged CHOSEN", text("hunter:CorpoHacker_chosen") == "CHOSEN"
      and shown("hunter:CorpoHacker_chosen_tag") and not shown("hunter:Gravitar_chosen_tag")
      and brush("hunter:CorpoHacker_frame").R == theme.rgba(theme.COLOR_GOLD)[0]
      and brush("hunter:Gravitar_frame").R == theme.rgba(theme.COLOR_TEXT_DIM)[0])
check("the hunter played tagged YOUR HUNTER", text("hunter:Gravitar_own") == "YOUR HUNTER"
      and shown("hunter:Gravitar_own_tag") and not shown("hunter:CorpoHacker_own_tag"))
tags = widgets["hunter:Gravitar_tags"]
check("the tags in the card's top right corner as sketch B2 drew them",
      slot_of(tags).calls["SetHorizontalAlignment"][0] == "EHorizontalAlignment.HAlign_Right"
      and slot_of(tags).calls["SetVerticalAlignment"][0] == "EVerticalAlignment.VAlign_Top"
      and widgets["hunter:Gravitar_own_tag"] in tags.children
      and widgets["hunter:Gravitar_chosen_tag"] in tags.children)
check("CHOSEN in gold, YOUR HUNTER outlined in orange",
      colour(brush("hunter:CorpoHacker_chosen_tag")) == "gold"
      and colour(widgets["hunter:CorpoHacker_chosen"].calls["SetColorAndOpacity"][0].SpecifiedColor) == "ink"
      and colour(brush("hunter:Gravitar_own_tag")) == "spark"
      and colour(widgets["hunter:Gravitar_own"].calls["SetColorAndOpacity"][0].SpecifiedColor) == "spark")
check("the class in its colour", text("hunter:Paladin_class") == "FORGEKNIGHT"
      and widgets["hunter:Paladin_class"].calls["SetColorAndOpacity"][0].SpecifiedColor.R
      == theme.rgba(ht.CLASS_COLOURS["Paladin"])[0])
check("the sentence naming both", text("hunter_state") == "You play Harlowe with Loveless's look. "
                                                         "Choose HARLOWE to get yours back."
      and widgets["hunter_grid"].calls["SetVisibility"][0] == "ESlateVisibility.Visible")

panel_hunters.paint(widgets, (harlowe, harlowe), "EN")
check("the own look shown without CHOSEN", not shown("hunter:Gravitar_chosen_tag") and shown("hunter:Gravitar_own_tag")
      and brush("hunter:Gravitar_frame").R == theme.rgba(theme.COLOR_GOLD)[0]
      and text("hunter_state").startswith("You play Harlowe."))

panel_hunters.paint(widgets, None, "EN")
check("outside a game no card, no frame and a sentence asking for one",
      not shown("hunter_grid") and not shown("hunter_applies")
      and text("hunter_state") == "Load a game to choose a look.")

panel_hunters.paint(widgets, (harlowe, loveless), "FR")
check("the texts in French", text("hunter:Gravitar_own") == "TON CHASSEUR"
      and text("notice:applies") == "S'APPLIQUE TOUT DE SUITE, POUR CETTE PARTIE."
      and text("hunter:Paladin_class") == "CHEVALIER-\nFORGERON"
      and text("hunter_state") == "Tu joues Harlowe. Apparence portée : Loveless. "
                                  "Choisis HARLOWE pour retrouver la tienne.")
amon = hunters.by_code("Paladin")
panel_hunters.paint(widgets, (harlowe, amon), "FR")
check("the French look sentence never puts de before a hunter's name, as de Amon would read",
      " de A" not in text("hunter_state") and "Amon" in text("hunter_state"))

checked = {"hunter:Paladin"}


def take(widget):
    name = next(key for key, value in widgets.items() if value is widget)
    if name in checked:
        checked.discard(name)
        return True
    return False


check("a card clicked read once", panel_hunters.taken(take, widgets) == "Paladin"
      and panel_hunters.taken(take, widgets) is None)


# Each theme changes colours only, read when the window is drawn: no colour of another theme stays (2026-10-06).
veils = {tuple(theme.HOVER_OVERLAY), tuple(theme.PRESS_OVERLAY)}
original_rgba = theme.rgba
for theme_name in theme.THEMES:
    panel_preferences.theme.value = theme_name
    used = []
    theme.rgba = lambda colour, alpha=1.0: used.append((colour, alpha)) or original_rgba(colour, alpha)
    try:
        panel_view.build_view(SimpleNamespace(), model)
    finally:
        theme.rgba = original_rgba
    allowed = {*{**theme._EMBER, **theme.PALETTES[theme_name]}.values(), *map(theme.on_card, ht.CLASS_COLOURS.values())}
    stray = {(colour, alpha) for colour, alpha in used if colour not in allowed and (colour, alpha) not in veils}
    check(f"{theme_name}: no colour kept from another theme, hunter tags included {sorted(stray)}", not stray)
panel_preferences.theme.value = "EMBER"

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
