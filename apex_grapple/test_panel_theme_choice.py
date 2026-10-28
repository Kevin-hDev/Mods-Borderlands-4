"""The header's THEME button: the following theme, saved with the mod's settings, then a request to draw again."""

import json
import sys
import panel_fixture as pf
from apex_grapple import menu, panel_preferences as preferences, panel_theme_choice as choice

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


check([choice.following(theme) for theme in ("EMBER", "DARK", "LIGHT", "BL4")] == ["DARK", "LIGHT", "BL4", "EMBER"],
      "Each click moves to the next theme, and the last one back to the first")
check(choice.following("no such theme") == "EMBER", "An unknown saved name starts over at EMBER")
check(preferences.theme in menu.MENU and preferences.theme.is_hidden and preferences.theme.mod is pf.f.mod,
      "The theme is one of the mod's hidden SDK options")
check(preferences.theme.default_value == "EMBER", "A first opening draws EMBER")

w, form = pf.create()
saved = pf.f.mod.saved
w["theme"].checked = True
form.poll()
check(preferences.theme.value == "DARK" and form.model.theme == "DARK", "A click saves the following theme")
check(pf.f.mod.saved == saved + 1 and form.redraw is True, "It is written at once and asks for a new window")
stored = json.dumps({option.identifier: option.value for option in menu.MENU if hasattr(option, "value")})
check(json.loads(stored)["menu_theme"] == "DARK", "It travels with the mod's settings file")

w, form = pf.create()
check(form.redraw is False and w["theme_label"].text == "THEME: DARK", "A new window opens in the saved theme")
w["nav:controls"].checked = True
form.poll()
w["first"].selecting = True
w["theme"].checked = True
form.poll()
check(preferences.theme.value == "DARK" and form.redraw is False,
      "During a key capture the click is ignored: a new window would drop the capture")
w["first"].selecting = False

pf.f.mod.fail_save = True
w["theme"].checked = True
form.poll()
check(preferences.theme.value == "DARK" and form.redraw is False, "A theme that could not be saved is not drawn")
check(form.notice == "failed", "The window says the change was not saved")
pf.f.mod.fail_save = False

preferences.theme.value = "LIGHT"
w, form = pf.create()
preferences.theme.value = "nothing we know"
check(form.model.theme == "EMBER", "A hand-edited settings file with an unknown theme reads as EMBER")
preferences.theme.value = "EMBER"

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | theme button: next theme, saved, redraw asked, capture kept")
sys.exit(1 if failures else 0)
