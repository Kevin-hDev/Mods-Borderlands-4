"""A page's sentence (panel_notice.py): on the LOOK page, under its title and above its rows, why the grapple gun's
look gave way to the classic one, read when the window opens; hidden, frame and all, while there is nothing to say."""

import sys
from types import SimpleNamespace as NS

import panel_render_fixture as fixture
from apex_grapple import look_choice, menu, panel_en, panel_fonts, panel_fr, panel_model, panel_notice
from apex_grapple import panel_preferences, panel_theme as t, panel_view, panel_widgets as w

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def inside(node, widget):
    return node is widget or any(inside(child, widget) for child in node.children)


def walk(node):
    yield node
    for child in node.children:
        yield from walk(child)


fixture.install()
HIDDEN, SHOWN = (w.enum("ESlateVisibility", name) for name in ("Collapsed", "HitTestInvisible"))
panel_fonts.build = lambda outer: {"title": object(), "body": object()}
model = panel_model.Model(fixture.pf.f.mod)
_root, built = panel_view.build_view(NS(), model)
page = list(walk(built["pages"].children[t.PAGES.index("look")]))
check(built["notice_frame:look"] in page and inside(built["notice_frame:look"], built["notice:look"])
      and page.index(built["heading:look"]) < page.index(built["notice_frame:look"])
      < page.index(built["row:show_rope"]),
      "The LOOK page's sentence sits under its title, above its rows, in its frame")
check(not any(name.startswith("notice:") for name in built if name != "notice:look"),
      "Only the LOOK page has a sentence")

# The grapple gun's look can play: nothing to say, the frame is gone.
check(look_choice.notice() is None, "The grapple gun's look plays at first")
widgets, _form = fixture.pf.create()
check(widgets["notice_frame:look"].visibility == HIDDEN, "Nothing to say: the sentence is hidden, frame and all")

# Its files missing: the window says so the next time it opens, in the language chosen.
look_choice.stop(look_choice.MISSING, "test: the container did not load")
widgets, form = fixture.pf.create()
check(widgets["notice_frame:look"].visibility == SHOWN
      and widgets["notice:look"].text == panel_en.TEXT["look_missing"].upper(), "The sentence for missing files shows")
widgets["FR"].checked = True
form.poll()
check(widgets["notice:look"].text == panel_fr.TEXT["look_missing"].upper(), "... in French once FR is chosen")
panel_preferences.language.value = "EN"

# A function's answer is read at each opening; a text key always shows, its frame left as drawn.
notices = dict(menu.NOTICES)
try:
    menu.NOTICES["look"] = lambda: "look_failed"
    widgets, _form = fixture.pf.create()
    check(widgets["notice:look"].text == panel_en.TEXT["look_failed"].upper()
          and widgets["notice_frame:look"].visibility == SHOWN, "Another reason, another sentence")
    menu.NOTICES["look"] = "look_failed"
    widgets, _form = fixture.pf.create()
    check(widgets["notice:look"].text == panel_en.TEXT["look_failed"].upper()
          and widgets["notice_frame:look"].visibility == "Visible", "A text key's sentence always shows")
finally:
    menu.NOTICES.clear()
    menu.NOTICES.update(notices)

# Every generated window ships this module: a menu without NOTICES has no sentence.
del menu.NOTICES
try:
    check(panel_notice.pages() == {}, "A menu without NOTICES: no page has a sentence")
finally:
    menu.NOTICES = notices

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | page sentence: placed, hidden, shown, read at opening, FR")
sys.exit(1 if failures else 0)
