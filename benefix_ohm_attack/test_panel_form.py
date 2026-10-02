"""Benefix Ohm Attack's window in use: the element's arrows, the sliders and the bar's switch shown at once and saved after a
moment, both languages, Restore and Undo, the mod's switch; and the COMMANDS page: a key per device saved at once and
given to its bind, a key refused with its cause, NONE, and the reset."""

import pathlib
import sys
from types import SimpleNamespace as NS

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import panel_fixture as pf  # noqa: E402

from benefix_ohm_attack import bar, keys, mod, panel_en, panel_form, panel_fr, panel_theme, settings  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def click(name: str) -> None:
    w[name].checked = True
    form.poll()


def wait() -> None:
    """The moment after which a change shown is saved."""
    clock[0] += panel_theme.SAVE_DELAY_NS
    form.poll()


def capture(slot: str, key: str) -> None:
    """A key pressed in a row's selector, as the game's widget hands it over."""
    w[f"command:{slot}"].SelectedKey = NS(Key=NS(KeyName=key))
    form.poll()


check("both languages word the same things, every setting and every element included",
      panel_fr.TEXT.keys() == panel_en.TEXT.keys()
      and set(panel_fr.OPTIONS) == {option.identifier for option in settings.ALL}
      and set(panel_fr.CHOICES) == set(panel_en.CHOICES) == set(settings.ELEMENTS)
      and set(panel_fr.GROUPS) == {"beam"})
clock = [0]
panel_form.time.perf_counter_ns = lambda: clock[0]
w, form = pf.create()
saves = pf.state["saves"]
for _ in range(3):
    form.poll()
check("opening and polling never rewrite the settings", pf.state["saves"] == saves)
check("the window opens on BEAM, in English, the element in use between its arrows with its place among them",
      w["pages"].index == 0 and w["heading:beam"].text == "BEAM" and w["heading:energy"].text == "ENERGY"
      and w["label:element"].text == "ELEMENT" and w["choice:element"].text == "FIRE"
      and w["value:element"].text == f"1/{len(settings.ELEMENTS)}"
      and w["setting:element:previous_label"].text == "<" and w["setting:element:next_label"].text == ">")
check("each setting shows its value: the damage, the bar's switch on, the three energy numbers",
      w["value:damage"].text == "75" and w["setting:show_bar_label"].text == "ON" and w["value:drain"].text == "20"
      and w["value:regen"].text == "25" and w["value:regen_delay"].text == "2.0"
      and w["label:damage"].text == "DAMAGE PER SECOND" and w["label:show_bar"].text == "ENERGY BAR")

click("setting:element:next")
check("the next arrow shows the next element at once, saved a moment later only",
      w["choice:element"].text == "SHOCK" and w["value:element"].text.startswith("2/")
      and settings.element.value == "Fire" and pf.state["saves"] == saves)
wait()
check("... then saved, and the window says so", settings.element.value == "Shock" and pf.state["saves"] == saves + 1
      and w["notice"].text == panel_en.TEXT["saved"])
click("setting:element:previous")
click("setting:element:previous")
check("before the first element, the previous arrow comes round to the last",
      w["choice:element"].text == "KINETIC" and w["value:element"].text == "6/6" and len(settings.ELEMENTS) == 6)
click("setting:element:next")
wait()
check("and past the last, the next arrow comes back to the first", settings.element.value == "Fire")

w["setting:damage"].value = 203.0
form.poll()
check("a slider moved shows its value on the setting's step at once", w["value:damage"].text == "205"
      and settings.damage.value == 75)
w["setting:regen_delay"].value = 3.26
form.poll()
wait()
check("... and both are saved together a moment later, the delay on its half seconds",
      settings.damage.value == 205 and type(settings.damage.value) is int and settings.regen_delay.value == 3.5
      and w["value:regen_delay"].text == "3.5")
w["setting:drain"].value = 5000.0
form.poll()
check("a value out of the slider's range is refused, said, and the slider put back",
      w["notice"].text == panel_en.TEXT["failed"] and w["setting:drain"].value == 20.0 and settings.drain.value == 20)

click("setting:show_bar")
check("the bar's switch turns off at once", w["setting:show_bar_label"].text == "OFF" and settings.show_bar.value is True)
wait()
check("... and is saved", settings.show_bar.value is False)

click("FR")
check("in French, the page's names and sentences are those of sketch M1",
      w["heading:beam"].text == "RAYON" and w["heading:energy"].text == "ÉNERGIE"
      and w["group:energy"].text == panel_fr.TEXT["energy_desc"] and w["group:beam"].text == panel_fr.GROUPS["beam"]
      and w["label:element"].text == "ÉLÉMENT" and w["choice:element"].text == "FEU"
      and w["label:damage"].text == "DÉGÂTS PAR SECONDE" and w["label:show_bar"].text == "BARRE D'ÉNERGIE"
      and w["setting:show_bar_label"].text == "NON" and w["label:drain"].text == "ÉNERGIE PAR SECONDE"
      and w["label:regen"].text == "RECHARGE PAR SECONDE" and w["label:regen_delay"].text == "DÉLAI AVANT RECHARGE"
      and w["nav:beam_label"].text == "RAYON" and w["nav:controls_label"].text == "COMMANDES")

pf.state["refuse_saves"] = True
w["setting:regen"].value = 60.0
form.poll()
wait()
check("a save that fails keeps the previous value and says so", settings.regen.value == 25
      and w["notice"].text == panel_fr.TEXT["failed"] and w["setting:regen"].value == 25.0)
pf.state["refuse_saves"] = False

click("nav:controls")
check("the COMMANDS page opens: one card, LANCER LE RAYON, no key on either device",
      w["pages"].index == 1 and w["heading:command_fire"].text == "LANCER LE RAYON"
      and w["group:command_fire"].text == panel_fr.TEXT["command_fire_desc"]
      and w["device:fire:keyboard"].text == "CLAVIER / SOURIS" and w["device:fire:controller"].text == "MANETTE"
      and w["value:fire:keyboard"].text == "AUCUNE" and w["value:fire:controller"].text == "AUCUNE"
      and w["command:fire:keyboard"].placeholder == "CHOISIR UNE TOUCHE"
      and w["command:fire:controller"].placeholder == "CHOISIR UN BOUTON"
      and keys.keyboard_bind.key is None and keys.controller_bind.key is None)
capture("fire:keyboard", "N")
check("a key chosen on the keyboard's row is saved at once, shown, and given to its bind",
      keys.keyboard_key.value == "N" and keys.keyboard_bind.key == "N" and w["value:fire:keyboard"].text == "N"
      and w["commands_status"].text == panel_fr.TEXT["saved"]
      and w["command:fire:keyboard"].SelectedKey.Key.KeyName == "None")
keys.keyboard_bind.callback("IE_Pressed")
check("... and that key held fires", keys.held())
keys.keyboard_bind.callback("IE_Released")
for key, cause in (("Gamepad_FaceButton_Top", "invalid_keyboard"), ("MouseScrollUp", "wheel_key"),
                   ("F10", "reserved_key"), ("Tilde", "reserved_key")):
    capture("fire:keyboard", key)
    check(f"{key} on the keyboard's row is refused with its own words, the previous key kept",
          keys.keyboard_key.value == "N" and keys.keyboard_bind.key == "N"
          and w["commands_status"].text == panel_fr.TEXT[cause])
status = w["commands_status"].text
capture("fire:keyboard", "Escape")
check("Escape cancels the capture: nothing changes", keys.keyboard_key.value == "N" and w["commands_status"].text == status)
capture("fire:controller", "Gamepad_FaceButton_Left")
check("a button chosen on the controller's row is saved, given to its bind and named as the player's controller does",
      keys.controller_key.value == "Gamepad_FaceButton_Left" and keys.controller_bind.key == "Gamepad_FaceButton_Left"
      and w["value:fire:controller"].text == "Carré" and keys.keyboard_key.value == "N")
capture("fire:controller", "N")
check("a keyboard key on the controller's row is refused with its own words",
      keys.controller_key.value == "Gamepad_FaceButton_Left"
      and w["commands_status"].text == panel_fr.TEXT["invalid_controller"])
click("icons:XSX")
check("the icons' choice renames the button", w["value:fire:controller"].text == "X")
click("clear:fire:keyboard")
check("AUCUNE unbinds the keyboard's key, the controller's kept",
      keys.keyboard_key.value is None and keys.keyboard_bind.key is None and w["value:fire:keyboard"].text == "AUCUNE"
      and keys.controller_bind.key == "Gamepad_FaceButton_Left")
capture("fire:keyboard", "N")
click("commands_reset")
check("TOUCHES D'ORIGINE puts both back to none, and says so",
      keys.keyboard_bind.key is None and keys.controller_bind.key is None
      and w["commands_status"].text == panel_fr.TEXT["controls_reset"])

capture("fire:keyboard", "N")
click("nav:beam")
click("restore")
check("RÉGLAGES D'ORIGINE puts every setting and both keys back, and can be undone",
      settings.damage.value == 75 and settings.show_bar.value is True and settings.regen_delay.value == 2.0
      and settings.element.value == "Fire" and keys.keyboard_key.value is None
      and w["notice"].text == panel_fr.TEXT["restored"] and w["undo"].enabled is True and w["value:damage"].text == "75")
click("undo")
check("ANNULER LE RESET brings them all back, the key included",
      settings.damage.value == 205 and settings.show_bar.value is False and settings.regen_delay.value == 3.5
      and keys.keyboard_key.value == "N" and w["notice"].text == panel_fr.TEXT["undone"] and w["undo"].enabled is False)

# A port of its own: the mod's switch starts the energy bar's service, and a test never takes the game's port.
bar.PORT = 0
check("the mod is off in this fake game, and the window says so", w["enabled_label"].text == "DÉSACTIVÉ")
# As mods_base leaves it at a launch: the settings file's own copy of the key, loaded after the option.
keys.keyboard_bind.key = "K"
click("enabled")
check("ACTIVÉ switches the mod on, its keys aligned on their options",
      mod.is_enabled and w["enabled_label"].text == "ACTIVÉ" and keys.keyboard_bind.key == "N")
click("enabled")
check("... and off again", not mod.is_enabled and w["enabled_label"].text == "DÉSACTIVÉ")

w["setting:damage"].value = 300.0
form.poll()
w["close"].checked = True
check("FERMER saves what was still waiting and lets the window close", form.poll() is True and settings.damage.value == 300)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
