"""A setting chosen among a few names (panel_choices.py): a button per name, the chosen one gold, a click saved through
the model, the words of each row in English, French and Chinese, and two arrows for a row of menu.ARROWS."""

import sys
from types import SimpleNamespace as NS

import panel_render_fixture as fixture
from apex_grapple import look_settings, menu, panel_buttons as b, panel_choices, panel_fonts, panel_form
from apex_grapple import panel_factory, panel_model, panel_theme as t, panel_view, panel_widgets as w

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def inside(node, widget):
    return node is widget or any(inside(child, widget) for child in node.children)


fixture.install()
panel_fonts.build = lambda outer: {"title": object(), "body": object()}
model = panel_model.Model(fixture.pf.f.mod)
root, widgets = panel_view.build_view(NS(), model)
form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()},
                            panel_factory.PanelBindings(), model)
on, off = (w.linear(b.colours(style)[0]) for style in ("on", "off"))

# Sketch A (Kevin, 2026-10-14): the look's names as buttons side by side on its row, the chosen one gold.
look = look_settings.look
buttons = [widgets[f"setting:look:{choice}"] for choice in look.choices]
check(widgets["setting:look"].kind == "HorizontalBox" and all(inside(widgets["setting:look"], item) for item in buttons)
      and inside(widgets["row:look"], widgets["setting:look"]), "The look is a button per name on its row")
check(widgets["setting:look:GRAPPLE_GUN_fill"].brush == on and widgets["setting:look:CLASSIC_fill"].brush == off,
      "The chosen name is the gold one")
check([widgets[f"setting:look:{choice}_label"].text for choice in look.choices] == ["GRAPPLE GUN", "CLASSIC"]
      and widgets["setting:rope_thickness:L_label"].text == "MEDIUM", "English words, in capitals")
check(not any(f"value:{option.identifier}" in widgets for option in look_settings.ALL
              if option.identifier not in menu.ARROWS),
      "A row of buttons has no value box")
# The colours, nine names each, on arrows (Kevin, 2026-10-14, sketch A): the chosen name and its place.
check(menu.ARROWS == {"rope_colour", "game_rope_colour"}
      and {"setting:rope_colour:previous", "setting:rope_colour:next"} <= set(widgets)
      and widgets["choice:rope_colour"].text == "ORANGE" and widgets["value:rope_colour"].text == "1/9"
      and widgets["choice:game_rope_colour"].text == "BLUE" and widgets["value:game_rope_colour"].text == "5/9",
      "The colours show on arrows, ours orange and the game's blue at first")

# A click is shown at once, saved after the delay as a slider's move, through the model's check.
clock = [0]
panel_form.time.perf_counter_ns = lambda: clock[0]
saved = fixture.pf.f.mod.saved
widgets["setting:look:CLASSIC"].checked = True
form.poll()
check(form.shown["look"] == look_settings.CLASSIC and look.value == look_settings.GRAPPLE_GUN
      and widgets["setting:look:CLASSIC_fill"].brush == on and widgets["setting:look:GRAPPLE_GUN_fill"].brush == off
      and not widgets["setting:look:CLASSIC"].checked, "A click shows its choice at once and releases its button")
clock[0] += t.SAVE_DELAY_NS
form.poll()
check(look.value == look_settings.CLASSIC and fixture.pf.f.mod.saved == saved + 1,
      "The choice is saved after the delay")
widgets["setting:look:CLASSIC"].checked = True
form.poll()
check(not form.pending and fixture.pf.f.mod.saved == saved + 1, "A click on the chosen name changes nothing")
check(not model.write({"look": "Classic"}) and not model.write({"rope_light": 3})
      and look.value == look_settings.CLASSIC, "The model refuses a name that is not one of the row's own")

# French agrees each word with its row (sketch A): MOYENNE for the thickness and the light, MOYEN for the others.
widgets["FR"].checked = True
form.poll()
check(widgets["setting:look:GRAPPLE_GUN_label"].text == "PISTOLET GRAPPIN"
      and widgets["setting:rope_thickness:L_label"].text == "MOYENNE"
      and widgets["setting:rope_light:2_label"].text == "MOYENNE"
      and widgets["setting:rope_movement:H_label"].text == "MOYEN"
      and widgets["setting:hook_size:B_label"].text == "MOYEN"
      and widgets["setting:rope_look:B_label"].text == "CŒUR", "French words agree with their row")
check(panel_choices.label("L", "ZH", look_settings.rope_thickness) == "中等"
      and panel_choices.label("A", "ZH", look_settings.hook_size) == "小"
      and panel_choices.label("A", "ZH", look_settings.rope_look) == "光丝", "Chinese words by row")
# A word given for every row (Apex Heirloom's, Vehicle Driving's), then English, then the name itself.
english, french = panel_choices._WORDS["EN"], panel_choices._WORDS["FR"]
english["Far"], french["Far"] = "Far", "Éloignée"
plain = NS(identifier="view")
check(panel_choices.label("Far", "FR", plain) == "ÉLOIGNÉE" and panel_choices.label("Far", "FR") == "ÉLOIGNÉE"
      and panel_choices.label("Far", "ZH", plain) == "FAR" and panel_choices.label("Near", "FR", plain) == "NEAR",
      "A word for every row, then English, then the name")
del english["Far"], french["Far"]

# A row of menu.ARROWS: two arrows around the chosen name, its place in the value box; a menu without the table shows
# buttons.
arrows = {}
owner = fixture.Node("VerticalBox", None)
template = fixture.Struct()
spinner = NS(identifier="rope_light", choices=["1", "2", "3"])
menu.ARROWS = frozenset(("rope_light",))
try:
    parts = panel_choices.controls(owner, arrows, spinner, template)
    panel_choices.paint(arrows, spinner, "3", "EN")
    check(len(parts) == 2 and parts[1] is not arrows["setting:rope_light"]
          and {"setting:rope_light:previous", "setting:rope_light:next", "choice:rope_light",
               "value:rope_light"} <= set(arrows)
          and arrows["choice:rope_light"].text == "HIGH" and arrows["value:rope_light"].text == "3/3",
          "A row of arrows shows the chosen name and its place")
    arrows["setting:rope_light:next"].checked = True
    check(panel_choices.taken(form.take, arrows, spinner, "3") == "1", "Past the last name, the next arrow comes back")
finally:
    menu.ARROWS = frozenset()
del menu.ARROWS
try:
    check(len(panel_choices.controls(owner, {}, spinner, template)) == 1,
          "A window whose menu has no ARROWS shows every choice as buttons")
finally:
    menu.ARROWS = frozenset()

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | choice rows: buttons, chosen in gold, click saved, "
      "words by row, arrows")
sys.exit(1 if failures else 0)
