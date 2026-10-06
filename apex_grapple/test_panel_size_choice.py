"""The header's WINDOW button: the following size, saved with the mod's settings, then a request to draw again."""

import json
import sys
import panel_fixture as pf
from apex_grapple import menu, panel_preferences as preferences, panel_size_choice as choice

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


check([choice.following(size) for size in ("LARGE", "FULL", "NORMAL")] == ["FULL", "NORMAL", "LARGE"],
      "Each click moves to the next size, and the last one back to the first")
check(choice.following("no such size") == "LARGE", "An unknown saved name starts over at LARGE")
check(preferences.window_size in menu.MENU and preferences.window_size.is_hidden
      and preferences.window_size.mod is pf.f.mod, "The size is one of the mod's hidden SDK options")
check(preferences.window_size.default_value == "LARGE", "A first opening draws LARGE, Kevin's new default")

w, form = pf.create()
check(w["window_size_label"].text == "WINDOW: LARGE", "The button says the size the window has")
saved = pf.f.mod.saved
w["window_size"].checked = True
form.poll()
check(preferences.window_size.value == "FULL" and form.model.window_size == "FULL", "A click saves the following size")
check(pf.f.mod.saved == saved + 1 and form.redraw is True and form.redraw_notice == "window_size_later",
      "It is written at once and asks for a new window, which says the size if it cannot be drawn")
stored = json.dumps({option.identifier: option.value for option in menu.MENU if hasattr(option, "value")})
check(json.loads(stored)["menu_window_size"] == "FULL", "It travels with the mod's settings file")
check(preferences.theme.value == "EMBER", "The theme stays as it was")

w, form = pf.create()
check(form.redraw is False and w["window_size_label"].text == "WINDOW: FULL SCREEN",
      "A new window opens at the saved size")
w["FR"].checked = True
form.poll()
check(w["window_size_label"].text == "FENÊTRE : PLEIN ÉCRAN", "The button speaks French with the window")
w["EN"].checked = True
form.poll()
w["nav:controls"].checked = True
form.poll()
w["first"].selecting = True
w["window_size"].checked = True
form.poll()
check(preferences.window_size.value == "FULL" and form.redraw is False,
      "During a key capture the click is ignored: a new window would drop the capture")
w["first"].selecting = False

pf.f.mod.fail_save = True
w["window_size"].checked = True
form.poll()
check(preferences.window_size.value == "FULL" and form.redraw is False, "A size that could not be saved is not drawn")
check(form.notice == "failed", "The window says the change was not saved")
pf.f.mod.fail_save = False

w, form = pf.create()
preferences.window_size.value = "nothing we know"
check(form.model.window_size == "LARGE", "A hand-edited settings file with an unknown size reads as LARGE")
preferences.window_size.value = "LARGE"

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | window button: next size, saved, redraw asked, capture kept")
sys.exit(1 if failures else 0)
