"""Apex Heirloom's window, as Apex Grapple's: delayed saves, the HEIRLOOM page's sentence and mode buttons, rows
greyed with their switches; its heirloom's buttons and skin's arrows (sketch H2), the chosen heirloom's rows shown,
a row greyed while it changes nothing, by the values shown before the save; and the CONTROLS page saving one key
per device, with the controller's button shown as the game's icon, greyed with the holster."""

import pathlib
import sys
import types
from types import SimpleNamespace as NS

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import panel_fixture as pf  # noqa: E402

from apex_heirloom import heirloom_settings, holster_settings, keys, panel_en, panel_form, panel_fr  # noqa: E402
from apex_heirloom import panel_i18n, panel_preferences, panel_theme, panel_widgets, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def gold(widgets, name):
    return widgets[f"{name}_fill"].brush == panel_widgets.linear(panel_theme.COLOR_GOLD)


class ControllerTable:
    """The game's controller icon table: held through a weak pointer, which a SimpleNamespace refuses."""

    def __init__(self, **fields):
        self.__dict__.update(fields)


resource = object()
pf.state["all"]["CommonInputBaseControllerData"] = [ControllerTable(GamepadName="PS5", InputBrushDataMap=[
    NS(Key=NS(KeyName="Gamepad_FaceButton_Top"), KeyBrush=NS(ResourceObject=resource))])]
check("both languages word the same things", panel_fr.TEXT.keys() == panel_en.TEXT.keys()
      and set(panel_fr.OPTIONS) == {option.identifier for option in settings.ALL})
clock = [0]
panel_form.time.perf_counter_ns = lambda: clock[0]
w, form = pf.create()
saves = pf.state["settings_saves"]
for _ in range(3):
    form.poll()
check("opening and polling never rewrite the settings", pf.state["settings_saves"] == saves)
check("the window opens on HEIRLOOM, its sentence at the top in capitals, the mode in use in gold",
      w["pages"].index == 0 and w["notice:heirloom"].text == "LEAVE THE MENU AND CHANGE WEAPONS TO APPLY THE CHANGE."
      and w["setting:mode:Apex_label"].text == "APEX" and w["setting:mode:Borderlands_label"].text == "BORDERLANDS"
      and gold(w, "setting:mode:Apex") and not gold(w, "setting:mode:Borderlands"))
w["setting:mode:Borderlands"].checked = True
form.poll()
check("a mode clicked turns gold at once, the other not", gold(w, "setting:mode:Borderlands")
      and not gold(w, "setting:mode:Apex") and heirloom_settings.mode.value == "Apex")
clock[0] += panel_theme.SAVE_DELAY_NS
form.poll()
check("and is saved after the delay", heirloom_settings.mode.value == "Borderlands")

shown, hidden = "SelfHitTestInvisible", "Collapsed"
check("the knife chosen: its skin and size show, the axe's hide; its skin greyed, it has one; the glow greyed, it "
      "has none",
      w["block:skin_jakobs_knife"].visibility == shown and w["block:skin_axe"].visibility == hidden
      and w["block:size"].visibility == shown and w["block:size_axe"].visibility == hidden
      and not w["setting:skin_jakobs_knife"].enabled and w["row:skin_jakobs_knife"].opacity < 1
      and w["choice:skin_jakobs_knife"].text == "ORIGINAL" and w["value:skin_jakobs_knife"].text == "1/1"
      and not w["setting:glow"].enabled and w["row:glow"].opacity < 1
      and gold(w, "setting:model:jakobs_knife") and w["setting:model:jakobs_knife_label"].text == "JAKOBS KNIFE")
w["setting:model:axe"].checked = True
form.poll()
check("the axe clicked: gold at once, its skin and size shown, the knife's hidden, its skin and the glow live, unsaved",
      gold(w, "setting:model:axe") and not gold(w, "setting:model:jakobs_knife")
      and w["block:skin_axe"].visibility == shown and w["block:skin_jakobs_knife"].visibility == hidden
      and w["block:size_axe"].visibility == shown and w["block:size"].visibility == hidden
      and w["setting:skin_axe"].enabled and w["setting:glow"].enabled and w["value:skin_axe"].text == "1/8"
      and heirloom_settings.model.value == "jakobs_knife")
w["setting:skin_axe:next"].checked = True
form.poll()
check("the next arrow: the axe's second skin, 2/8, and the glow greys: a game's skin keeps its own",
      w["choice:skin_axe"].text == "JAKOBS KNIFE" and w["value:skin_axe"].text == "2/8"
      and not w["setting:glow"].enabled and not w["setting:skin_axe:next"].checked)
for _ in range(2):
    w["setting:skin_axe:previous"].checked = True
    form.poll()
check("back twice from the second, past the first: the last, 8/8",
      w["value:skin_axe"].text == "8/8" and w["choice:skin_axe"].text == "LEGENDARY 04")
w["setting:skin_axe:next"].checked = True
form.poll()
check("on past the last: the first again, the glow live", w["value:skin_axe"].text == "1/8"
      and w["choice:skin_axe"].text == "ORIGINAL" and w["setting:glow"].enabled)
w["setting:skin_axe:next"].checked = w["setting:skin_axe:previous"].checked = True
form.poll()
check("both arrows at once: the skin stays", w["value:skin_axe"].text == "1/8")
w["setting:skin_axe:next"].checked = True
form.poll()
w["setting:glow"].value = 5
form.poll()
clock[0] += panel_theme.SAVE_DELAY_NS
form.poll()
check("saved after the delay: the axe, its skin, the glow at 5", heirloom_settings.model.value == "axe"
      and heirloom_settings.SKINS["axe"].value == "jakobs_knife" and heirloom_settings.glow.value == 5)
w["setting:heirloom"].checked = True
form.poll()
check("the heirloom off: every row below its switch greys and stills, the switch itself live",
      all(not w[f"setting:{name}"].enabled and w[f"row:{name}"].opacity < 1 and w[f"description:{name}"].opacity < 1
          for name in ("mode", "size", "draw_start", "draw_speed"))
      and w["setting:heirloom"].enabled and w["row:heirloom"].opacity == 1.0)
w["setting:heirloom"].checked = True
form.poll()
check("on again, they are live", w["setting:mode"].enabled and w["row:draw_speed"].opacity == 1.0)
w["nav:holster"].checked = True
form.poll()
check("HOLSTER is the second page, the hold time live while a key is held",
      w["pages"].index == 1 and w["setting:hold_time"].enabled and w["row:hold_time"].opacity == 1.0)

w["setting:hold_time"].value = 0.6
form.poll()
clock[0] += panel_theme.SAVE_DELAY_NS
form.poll()
check("a moved slider is saved after the delay", holster_settings.hold_time.value == 0.6)
w["setting:keyboard_hold"].checked = True
form.poll()
w["setting:controller_hold"].checked = True
form.poll()
check("both keys pressed once: the hold time greys, label and description included",
      not w["setting:hold_time"].enabled and w["row:hold_time"].opacity < 1 and w["description:hold_time"].opacity < 1)
clock[0] += panel_theme.SAVE_DELAY_NS
form.poll()
check("both switches saved Off",
      holster_settings.keyboard_hold.value is False and holster_settings.controller_hold.value is False)
w["setting:holster"].checked = True
form.poll()
check("the holster off: its rows grey and still, and so do the CONTROLS page's keys, the switch itself live",
      all(not w[f"setting:{name}"].enabled and w[f"row:{name}"].opacity < 1
          for name in ("keyboard_hold", "controller_hold", "hold_time"))
      and not w["controls_keys"].enabled and w["controls_keys"].opacity < 1 and not w["first"].enabled
      and w["setting:holster"].enabled)
w["setting:holster"].checked = True
form.poll()
check("on again, the keys are live, the hold time still grey while no key is held",
      w["first"].enabled and w["controls_keys"].enabled and w["controls_keys"].opacity == 1.0
      and w["setting:keyboard_hold"].enabled and not w["setting:hold_time"].enabled)

w["nav:controls"].checked = True
form.poll()
check("CONTROLS is the third page", w["pages"].index == 2)
check("the current keys are listed, the controller's by its name while no icon matches",
      "Keyboard / mouse : " in w["current"].text and "Square" in w["current"].text)
w["first"].SelectedKey.Key.KeyName = "Gamepad_FaceButton_Top"
form.poll()
check("a controller button chosen is saved on the controller's key",
      keys.controller_bind.key == "Gamepad_FaceButton_Top" and w["status"].text == "Controls saved.")
check("it shows as the game's icon, on the selector and in the current keys",
      w["first:icon"].icon_brush.ResourceObject is resource and w["first:icon"].visibility == "HitTestInvisible"
      and w["pad_summary"].visibility == "HitTestInvisible" and "Controller :" not in w["current"].text)
w["first"].SelectedKey.Key.KeyName = "None"
form.poll()
w["first"].SelectedKey.Key.KeyName = "Q"
form.poll()
check("a keyboard key chosen is saved on the keyboard's key, the controller's kept",
      keys.keyboard_bind.key == "Q" and keys.controller_bind.key == "Gamepad_FaceButton_Top")
w["first"].SelectedKey.Key.KeyName = "F10"
form.poll()
check("the console's key is refused, and the choice cleared", keys.keyboard_bind.key == "Q"
      and "reserved" in w["status"].text and w["first"].SelectedKey.Key.KeyName == "None")
w["first"].SelectedKey.Key.KeyName = "Gamepad_LeftX"
form.poll()
check("a stick as an axis is refused", keys.controller_bind.key == "Gamepad_FaceButton_Top"
      and w["status"].text.startswith("Not saved"))
w["first"].selecting = True
w["first"].SelectedKey.Key.KeyName = "J"
form.poll()
check("nothing is saved while the selector still waits for a key", keys.keyboard_bind.key == "Q")
w["first"].selecting = False

w["icons:XSX"].checked = True
form.poll()
check("the controller's icons follow the chosen family", panel_preferences.controller_icons.value == "XSX")
w["reset"].checked = True
form.poll()
check("RESET CONTROLS gives A (the key right of Tab) and Square back",
      keys.keyboard_bind.key == keys.keyboard_bind.default_key and keys.controller_bind.key == "Gamepad_FaceButton_Left"
      and w["status"].text == "Default controls restored.")

w["FR"].checked = True
form.poll()
check("in French, the pages and the controls speak French", panel_preferences.language.value == "FR"
      and w["nav:holster_label"].text == "RANGEMENT" and w["nav:controls_label"].text == "COMMANDES"
      and w["first"].placeholder == "CHOISIR UNE TOUCHE" and "Manette" in w["current"].text + w["pad_label"].text
      and w["notice:heirloom"].text == "QUITTE LE MENU ET CHANGE D'ARME POUR APPLIQUER LE CHANGEMENT."
      and w["setting:model:axe_label"].text == "HACHE" and w["label:glow"].text == "LUMIÈRE"
      and w["choice:skin_axe"].text == "COUTEAU JAKOBS")

w["first"].SelectedKey.Key.KeyName = "None"
form.poll()
w["first"].SelectedKey.Key.KeyName = "G"
form.poll()
w["restore"].checked = True
form.poll()
check("Restore puts the settings and both keys back, undoable", holster_settings.keyboard_hold.value is True
      and holster_settings.hold_time.value == 0.4 and keys.keyboard_bind.key == keys.keyboard_bind.default_key
      and keys.controller_bind.key == "Gamepad_FaceButton_Left" and w["undo"].enabled
      and heirloom_settings.model.value == "jakobs_knife" and heirloom_settings.glow.value == 3
      and heirloom_settings.SKINS["axe"].value == "own")
w["undo"].checked = True
form.poll()
check("Undo gives the settings and the key back", holster_settings.keyboard_hold.value is False
      and holster_settings.hold_time.value == 0.6 and keys.keyboard_bind.key == "G"
      and heirloom_settings.model.value == "axe" and heirloom_settings.SKINS["axe"].value == "jakobs_knife")

pf.state["refuse_saves"] = True
w["nav:holster"].checked = True
form.poll()
w["setting:hold_time"].value = 0.8
form.poll()
w["close"].checked = True
check("a failed save keeps the window open and the value", not form.poll() and holster_settings.hold_time.value == 0.6)
pf.state["refuse_saves"] = False
w["close"].checked = True
check("Close saves and closes", form.poll())

# A slider edited by hand in the settings file: the mod reads it within its bounds (slider_values.bounded), and so
# does the window, or it refused every click (audit of 2026-09-26).
holster_settings.hold_time.value = float("nan")
w, form = pf.create()
before = holster_settings.keyboard_hold.value
w["setting:keyboard_hold"].checked = True
form.poll()
clock[0] += panel_theme.SAVE_DELAY_NS
form.poll()
check("a slider edited to no number shows as the mod uses it, and the other settings still change",
      w["setting:hold_time"].value == 0.4 and holster_settings.keyboard_hold.value is (not before)
      and form.notice != "failed")
holster_settings.hold_time.value = float("inf")
w, form = pf.create()
check("... and past every bound, at its nearest", w["setting:hold_time"].value == 1.0)

# ENABLED refused by the guard (family.py): another installed file, switched on, runs a part of this one. Stand-in
# for Tidy Weapons next to the full mod, with the names every file of the family carries.
sibling = types.ModuleType("tidy_weapons")
sibling.pack = NS(NAME="Tidy Weapons", PARTS=("holster",), runs=lambda part: part == "holster")
sibling.mod = NS(is_enabled=True)
sys.modules["tidy_weapons"] = sibling
pf.mod.disable()
w, form = pf.create()
w["enabled"].checked = True
form.poll()
check("switching on refused because another file runs the same part says so, not a failed save",
      not pf.mod.is_enabled and form.notice == "refused_part"
      and w["notice"].text == panel_i18n.text("refused_part", form.model.language))
del sys.modules["tidy_weapons"]
w["enabled"].checked = True
form.poll()
check("that file gone, it switches on", pf.mod.is_enabled and form.notice == "saved")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
