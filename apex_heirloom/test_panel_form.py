"""Apex Heirloom's window, as Apex Grapple's: delayed saves, the HEIRLOOM page's sentence and mode buttons, rows
greyed with their switches; its heirloom's buttons and skin's arrows (sketch H2), the chosen heirloom's rows shown,
a row greyed while it changes nothing, by the values shown before the save; and Apex Movement's COMMANDS page (sketch
I1): a card per command saving a key per device at once, the controller's shown as the game's icon, a key another
command holds, the wheel or the console's refused with its cause, each card greyed and blocked with its part."""

import pathlib
import sys
import types
from types import SimpleNamespace as NS

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import panel_fixture as pf  # noqa: E402

from apex_heirloom import heirloom_settings, holster_settings, inspect_keys, keys, panel_en, panel_form  # noqa: E402
from apex_heirloom import panel_fr  # noqa: E402
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
check("... and so does the COMMANDS page's INSPECT card, its keys blocked; PUT AWAY stays live (Kevin, 2026-09-30)",
      not w["card:command_inspect"].enabled and w["card:command_inspect"].opacity < 1
      and not w["command:inspect:keyboard"].enabled and not w["clear:inspect:controller"].enabled
      and w["card:command_put_away"].opacity == 1.0 and w["command:put_away:keyboard"].enabled)
w["setting:heirloom"].checked = True
form.poll()
check("on again, they are live", w["setting:mode"].enabled and w["row:draw_speed"].opacity == 1.0
      and w["card:command_inspect"].opacity == 1.0 and w["command:inspect:keyboard"].enabled)
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
check("the holster off: its rows grey and still, and so does the PUT AWAY card, its keys blocked, the switch live",
      all(not w[f"setting:{name}"].enabled and w[f"row:{name}"].opacity < 1
          for name in ("keyboard_hold", "controller_hold", "hold_time"))
      and not w["card:command_put_away"].enabled and w["card:command_put_away"].opacity < 1
      and all(not w[f"{kind}:put_away:{device}"].enabled for kind in ("command", "clear")
              for device in ("keyboard", "controller"))
      and w["setting:holster"].enabled)
check("... the INSPECT card stays live: it serves the heirloom",
      w["card:command_inspect"].enabled and w["card:command_inspect"].opacity == 1.0
      and w["command:inspect:keyboard"].enabled and w["clear:inspect:controller"].enabled)
w["setting:holster"].checked = True
form.poll()
check("on again, the card is live, the hold time still grey while no key is held",
      w["card:command_put_away"].enabled and w["card:command_put_away"].opacity == 1.0
      and w["command:put_away:keyboard"].enabled and w["clear:put_away:controller"].enabled
      and w["setting:keyboard_hold"].enabled and not w["setting:hold_time"].enabled)

w["nav:controls"].checked = True
form.poll()
check("COMMANDS is the third page: PUT AWAY then ANIMATION, each a keyboard/mouse row and a controller row",
      w["pages"].index == 2 and w["heading:command_put_away"].text == "PUT AWAY"
      and w["heading:command_inspect"].text == "ANIMATION"
      and w["group:command_put_away"].text == "The key that puts your weapon away. Greyed out while Holster is OFF."
      and w["device:inspect:keyboard"].text == "KEYBOARD / MOUSE"
      and w["device:inspect:controller"].text == "CONTROLLER")
check("each row asks for its own device's key, and NONE clears it",
      w["command:put_away:keyboard"].placeholder == "CHOOSE A KEY"
      and w["command:put_away:controller"].placeholder == "CHOOSE A BUTTON"
      and w["command:inspect:keyboard"].listening == "PRESS A KEY"
      and w["command:inspect:controller"].listening == "PRESS A BUTTON"
      and w["clear:inspect:keyboard_label"].text == "NONE")
check("no inspection key yet, the put-away button shown by its name while no icon matches (Kevin, 2026-09-30)",
      w["value:inspect:keyboard"].text == "NONE" and w["value:inspect:controller"].text == "NONE"
      and w["value:put_away:controller"].text == "Square" and w["value:put_away:controller"].visibility != "Collapsed")
check("then the icons, the reset and the Esc hint, as sketch I1",
      w["icons_label"].text == "CONTROLLER ICONS" and w["icons:PS5_label"].text == "PLAYSTATION"
      and w["icons:XSX_label"].text == "XBOX" and w["commands_reset_label"].text == "RESET CONTROLS"
      and w["escape_hint"].text == "Esc cancels key capture. The console key is reserved.")
w["command:inspect:controller"].SelectedKey.Key.KeyName = "Gamepad_FaceButton_Top"
form.poll()
check("a controller button chosen for INSPECT is saved at once", inspect_keys.controller_bind.key
      == "Gamepad_FaceButton_Top" and w["commands_status"].text == "Saved."
      and w["command:inspect:controller"].SelectedKey.Key.KeyName == "None")
check("it shows as the game's icon", w["value:inspect:controller:icon"].icon_brush.ResourceObject is resource
      and w["value:inspect:controller:icon"].visibility == "HitTestInvisible"
      and w["value:inspect:controller"].visibility == "Collapsed")
w["command:put_away:keyboard"].SelectedKey.Key.KeyName = "Q"
form.poll()
w["command:inspect:keyboard"].SelectedKey.Key.KeyName = "F"
form.poll()
check("a keyboard key for each command, the controller's kept", keys.keyboard_bind.key == "Q"
      and inspect_keys.keyboard_bind.key == "F" and inspect_keys.controller_bind.key == "Gamepad_FaceButton_Top"
      and w["value:inspect:keyboard"].text == "F")
w["command:inspect:keyboard"].SelectedKey.Key.KeyName = "Q"
form.poll()
check("the key that puts the weapon away is refused for INSPECT, which keeps its own, and says why",
      inspect_keys.keyboard_bind.key == "F" and keys.keyboard_bind.key == "Q"
      and w["commands_status"].text == "Not saved: this key already puts your weapon away. Previous key kept.")
w["command:put_away:controller"].SelectedKey.Key.KeyName = "Gamepad_FaceButton_Top"
form.poll()
check("the inspection's button is refused for PUT AWAY, which keeps Square",
      keys.controller_bind.key == "Gamepad_FaceButton_Left"
      and w["commands_status"].text == "Not saved: this key already plays your heirloom's animation. Previous key "
                                       "kept.")
for command, owner, kept in (("inspect", inspect_keys, "F"), ("put_away", keys, "Q")):
    w[f"command:{command}:keyboard"].SelectedKey.Key.KeyName = "MouseScrollDown"
    form.poll()
    check(f"the wheel is refused on {command}'s keyboard row, which keeps its key", owner.keyboard_bind.key == kept
          and w["commands_status"].text == "Not saved: the mouse wheel changes weapons in the game. Previous key kept.")
w["command:inspect:keyboard"].SelectedKey.Key.KeyName = "F10"
form.poll()
check("the console's key is refused, and the choice cleared", inspect_keys.keyboard_bind.key == "F"
      and "reserved" in w["commands_status"].text and w["command:inspect:keyboard"].SelectedKey.Key.KeyName == "None")
w["command:inspect:controller"].SelectedKey.Key.KeyName = "Gamepad_LeftX"
form.poll()
check("a stick as an axis is refused", inspect_keys.controller_bind.key == "Gamepad_FaceButton_Top"
      and w["commands_status"].text == "Not saved: choose a controller button. Previous button kept.")
w["command:inspect:keyboard"].selecting = True
w["command:inspect:keyboard"].SelectedKey.Key.KeyName = "J"
form.poll()
check("nothing is saved while a row still waits for a key, the other rows waiting too",
      inspect_keys.keyboard_bind.key == "F" and not w["command:put_away:keyboard"].enabled and form.selecting())
w["command:inspect:keyboard"].selecting = False
w["command:inspect:keyboard"].SelectedKey.Key.KeyName = "None"
form.poll()
w["clear:inspect:keyboard"].checked = True
form.poll()
check("NONE clears the inspection's keyboard key", inspect_keys.keyboard_bind.key is None
      and w["value:inspect:keyboard"].text == "NONE")

w["icons:XSX"].checked = True
form.poll()
check("the controller's icons follow the chosen family", panel_preferences.controller_icons.value == "XSX")
w["commands_reset"].checked = True
form.poll()
check("RESET CONTROLS gives the put-away keys back, A (the key right of Tab) and Square, and no inspection key",
      keys.keyboard_bind.key == keys.keyboard_bind.default_key and keys.controller_bind.key == "Gamepad_FaceButton_Left"
      and inspect_keys.keyboard_bind.key is None and inspect_keys.controller_bind.key is None
      and w["commands_status"].text == "Default controls restored.")

w["FR"].checked = True
form.poll()
check("in French, the pages speak French", panel_preferences.language.value == "FR"
      and w["nav:holster_label"].text == "RANGEMENT" and w["nav:controls_label"].text == "COMMANDES"
      and w["notice:heirloom"].text == "QUITTE LE MENU ET CHANGE D'ARME POUR APPLIQUER LE CHANGEMENT."
      and w["setting:model:axe_label"].text == "HACHE" and w["label:glow"].text == "LUMIÈRE"
      and w["choice:skin_axe"].text == "COUTEAU JAKOBS")
check("... and the COMMANDS page speaks the sketch's words",
      w["heading:command_put_away"].text == "RANGER L'ARME" and w["heading:command_inspect"].text == "ANIMATION"
      and w["group:command_put_away"].text == "La touche qui range ton arme. Grisée quand le Rangement est sur NON."
      and w["group:command_inspect"].text == "Fais tourner ton heirloom dans ta main quand ton arme est rangée. "
                                             "Grisée quand le Heirloom est sur NON."
      and w["device:inspect:keyboard"].text == "CLAVIER / SOURIS" and w["device:inspect:controller"].text == "MANETTE"
      and w["command:inspect:keyboard"].placeholder == "CHOISIR UNE TOUCHE"
      and w["command:inspect:controller"].placeholder == "CHOISIR UN BOUTON"
      and w["command:inspect:controller"].listening == "APPUIE SUR UN BOUTON"
      and w["clear:inspect:keyboard_label"].text == "AUCUNE" and w["value:inspect:keyboard"].text == "AUCUNE"
      and w["icons_label"].text == "ICÔNES MANETTE" and w["commands_reset_label"].text == "TOUCHES D’ORIGINE"
      and w["escape_hint"].text == "Échap annule la saisie. La touche console est réservée.")
w["command:inspect:controller"].SelectedKey.Key.KeyName = "Gamepad_FaceButton_Left"
form.poll()
check("a refusal in French says its cause too", inspect_keys.controller_bind.key is None
      and w["commands_status"].text == "Non enregistrée : cette touche range déjà ton arme. Touche précédente gardée.")

w["command:put_away:keyboard"].SelectedKey.Key.KeyName = "G"
form.poll()
w["command:inspect:controller"].SelectedKey.Key.KeyName = "Gamepad_DPad_Up"
form.poll()
w["restore"].checked = True
form.poll()
check("Restore puts the settings and the four keys back, the inspection's to none, undoable",
      holster_settings.keyboard_hold.value is True
      and holster_settings.hold_time.value == 0.4 and keys.keyboard_bind.key == keys.keyboard_bind.default_key
      and keys.controller_bind.key == "Gamepad_FaceButton_Left" and inspect_keys.controller_bind.key is None
      and w["undo"].enabled and heirloom_settings.model.value == "jakobs_knife" and heirloom_settings.glow.value == 3
      and heirloom_settings.SKINS["axe"].value == "own" and w["value:inspect:controller"].text == "AUCUNE")
w["undo"].checked = True
form.poll()
check("Undo gives the settings and the keys back", holster_settings.keyboard_hold.value is False
      and holster_settings.hold_time.value == 0.6 and keys.keyboard_bind.key == "G"
      and inspect_keys.controller_bind.key == "Gamepad_DPad_Up"
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
w["restore"].checked = True
form.poll()
w["nav:controls"].checked = True
form.poll()
w["command:inspect:keyboard"].SelectedKey.Key.KeyName = "F"
form.poll()
check("a key chosen after a Restore ends its Undo, which would take that key back, as in Apex Movement's window",
      inspect_keys.keyboard_bind.key == "F" and not w["undo"].enabled)

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
# The mod off, as ENABLED leaves it: marked so, the fake game having no hands for the heirloom to switch off from.
pf.mod.is_enabled = False
w, form = pf.create()
check("the mod switched off greys no card: the keys stay settable, as the switches' rows",
      w["card:command_put_away"].opacity == 1.0 and w["card:command_inspect"].opacity == 1.0
      and w["command:inspect:keyboard"].enabled and w["command:put_away:controller"].enabled)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
