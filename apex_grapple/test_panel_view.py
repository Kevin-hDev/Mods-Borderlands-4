"""The window tree follows the approved mockup: every control attached, mockup sizes, states and figures only."""

import sys
from types import SimpleNamespace as NS
import panel_render_fixture as fixture
from apex_grapple import (panel_buttons as b, panel_model, panel_view, panel_form, panel_factory, panel_theme as t,
                          panel_fonts, panel_text as tx, panel_widgets as w)

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


fixture.install()
model = panel_model.Model(fixture.pf.f.mod)
title_font, body_font = object(), object()
panel_fonts.build = lambda outer: {"title": title_font, "body": body_font}
root, widgets = panel_view.build_view(NS(), model)
attached = set()


def visit(node):
    check(id(node) not in attached, "A widget belongs to two parents")
    attached.add(id(node))
    for child in node.children:
        visit(child)


# The garbage collector removed a bare ScaleBox 35 to 50 s after opening: a UserWidget must hold the window.
check(root.kind == "UserWidget" and root.WidgetTree.RootWidget.kind == "ScaleBox", "A UserWidget holds the window")
visit(root.WidgetTree.RootWidget)
icon_overlays = [node for node in fixture.created if node.kind == "Overlay" and node.children
                and node.children[0].kind == "InputKeySelector"]
check(len(icon_overlays) == 2, "One controller icon overlay per native selector")
overlay_slots = [slot for node in fixture.created if node.kind == "Overlay" and node not in icon_overlays
                 for slot in node.slots]
check(overlay_slots and all(slot.attributes.get("SetHorizontalAlignment") == ("EHorizontalAlignment.HAlign_Fill",)
                            for slot in overlay_slots),
      "Every overlay layer fills its width: sliders, shadows and the header row shrank without it")
scrolls = [node for node in fixture.created if node.kind == "ScrollBox"]
check(all(node.slots[0].attributes["SetPadding"][0] == w.pad(t.SPACE_7, t.SPACE_8, t.SPACE_9) for node in scrolls),
      "The page padding sits inside the scroll area, as in the mockup")
check(all(id(widget) in attached for widget in widgets.values()), "A registered widget is not in the tree")
check(set(widgets) == fixture.pf.names(model), "Registered names differ from the form fixture's")
check(len(widgets["pages"].children) == 4, "Four pages expected")
check(all(f"setting:{key}" in widgets for key in model.options), "Every setting has a control")
check(len(widgets) < 300, "Widget count stays bounded: all of them are resolved at every poll")
# Mockup sizes: CSS pixels times 0.75, because Unreal draws font points at 96 DPI.
check(widgets["label:grapple_range"].Font.Size == t.TEXT_MD * 0.75, "Setting labels are 20 px as in the mockup")
check(widgets["label:grapple_range"].Font.FontObject is body_font, "Labels use Barlow Condensed")
check(widgets["label:grapple_range"].Font.TypefaceFontName == "SemiBold", "Labels use the 600 weight")
check(widgets["heading:shot"].Font.FontObject is title_font, "Plates use Anton")
texts = [node for node in fixture.created if node.kind == "TextBlock"]
shadowed = [node for node in texts if "SetShadowOffset" in node.attributes]
check(len(shadowed) == 1 and shadowed[0].Font.OutlineSettings.OutlineSize == 4,
      "Only the logo title carries the ink outline and shadow; plain texts stay sharp")
check(not any(node.attributes.get("SetAutoWrapText") == (True,) for node in
              (widgets["value:grapple_range"], widgets["close_label"], widgets["EN_label"])),
      "Values and button labels never wrap")
heights = [node.attributes["SetHeightOverride"][0] for node in fixture.created if "SetHeightOverride" in node.attributes]
check(t.HEADER_HEIGHT in heights and 78.0 not in heights and 48.0 not in heights,
      "No fixed height smaller than its buttons (footer and header clipped them)")
check(any(node.kind == "ProgressBar" for node in fixture.created), "Sliders are filled by a progress bar")
check(sum(node.kind == "Image" for node in fixture.created) == 4,
      "Four controller images; no avatar without its file")
count = fixture.pf.f.mod.saved
refs = {name: lambda widget=widget: widget for name, widget in widgets.items()}
form = panel_form.PanelForm(refs, panel_factory.PanelBindings(), model)
check(fixture.pf.f.mod.saved == count, "Opening writes nothing")
check(widgets["value:grapple_range"].text == "3000", "Values are figures only, without units")
check(widgets["value:pull_strength"].text == "1.7", "Decimal values keep their step's precision")
check(widgets["fill:grapple_range"].percent == (3000 - 500) / (10000 - 500), "Gold fill follows the value")
check(widgets["nav:shot_label"].text == "THE SHOT" and widgets["EN_label"].text == "EN", "No '> ' or '[EN]' marks")
gold, clear = w.linear(t.COLOR_GOLD), w.linear(t.COLOR_INK, 0.0)
check(widgets["nav:shot_fill"].brush == gold, "The open page is a gold plate")
check(widgets["nav:pull_fill"].brush == clear, "Other pages stay transparent")
check(widgets["setting:show_rope_label"].text == "ON", "Switches read ON / OFF")
widgets["FR"].checked = True
form.poll()
check(widgets["close_label"].text == "FERMER" and widgets["setting:show_rope_label"].text == "OUI", "French texts")
check(widgets["FR_fill"].brush == gold, "The active language is the gold one")
check(widgets["first"].placeholder == "1. CHOISIR UNE TOUCHE" and not widgets["second"].enabled, "Key capture")
slot = panel_view.viewport_slot()
width = (t.WINDOW_WIDTH + t.SHADOW_XL) / t.STAGE_WIDTH
check(abs(slot.Anchors.Minimum.X - (1 - width) / 2) < 1e-9 and abs(slot.Anchors.Maximum.X - (1 + width) / 2) < 1e-9,
      "The window keeps the mockup's share of the screen")
check(t.rgba("000000") == (0.0, 0.0, 0.0, 1.0) and t.rgba("ffffff") == (1.0, 1.0, 1.0, 1.0), "sRGB conversion")
check("settings window: fonts=body+title, avatar=hidden" in " ".join(fixture.pf.f.state["misc"]), "Load report line")
w.cosmetic("probe", lambda: (_ for _ in ()).throw(AttributeError("missing")))
w.cosmetic("probe", lambda: (_ for _ in ()).throw(AttributeError("missing")))
check(sum("'probe'" in line for line in fixture.pf.f.state["errors"]) == 1, "A missing style is reported once")
try:
    w.cosmetic("fault", lambda: 1 / 0)
    failures.append("A real fault must not be hidden as a style problem")
except ZeroDivisionError:
    pass

check(model.change_page("release"), "The last page can be saved")
reopened, next_widgets = panel_view.build_view(NS(), model)
next_refs = {name: lambda widget=widget: widget for name, widget in next_widgets.items()}
next_form = panel_form.PanelForm(next_refs, panel_factory.PanelBindings(), model)
check(next_widgets["pages"].index == 2 and next_form.page == 2, "The saved tab's content is reopened")
check(next_widgets["focus"] is next_widgets["nav:release"], "Controller focus follows the saved tab")
check(next_widgets["nav:release_fill"].brush == gold, "The saved tab is visibly selected")

# Grapple owns these visual primitives for generated Movement even though its own pages do not display them.
shared = {}
template = w.new("InputKeySelector", root.WidgetTree.RootWidget).WidgetStyle.Normal
tx.use({"title": title_font, "body": body_font})
shared_gear = b.gear(root.WidgetTree.RootWidget, shared, template)
shared_hero = tx.text(root.WidgetTree.RootWidget, "OPTIONS", "hero")
tx.use({})
check(shared_gear is not None and shared_hero.Font.FontObject is title_font,
      "Movement-only shared visual primitives construct from Grapple's authority")
round_parts = [shared[f"options_icon:{index}"].icon_brush for index in (4, 5)]
check(all(brush is not None and brush.DrawAs == "ESlateBrushDrawType.RoundedBox"
          and brush.OutlineSettings.RoundingType == "ESlateBrushRoundingType.HalfHeightRadius"
          for brush in round_parts), "The gear's ring and hole are discs, as in the mockup")
check("choice" not in b.KINDS, "Language choices reuse the ON/OFF switch, as in the mockup")

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | mockup window tree, sizes, states, figures only, FR")
sys.exit(1 if failures else 0)
