"""Apex Heirloom's window model, as Apex Grapple's: both parts' settings in both languages, the mode among its
choices only, its pages and preferences saved."""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import panel_fixture as pf  # noqa: E402

from apex_heirloom import heirloom_settings, holster_settings, keys, menu, mod, panel_i18n, panel_open  # noqa: E402
from apex_heirloom import panel_preferences as prefs, settings  # noqa: E402
from apex_heirloom.panel_model import Model  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def one_sentence(text: str) -> bool:
    # Kevin, 2026-09-23: a description says what the player gets in one plain sentence.
    return 0 < len(text) <= 60 and text.count(".") == 1 and text.endswith(".")


model = Model(mod)
check("the HEIRLOOM page then the HOLSTER page, with both parts' settings, HEIRLOOM opened first",
      model.groups == (menu.heirloom_page, menu.holster_page) and list(model.options) == [
          "heirloom", "model", "skin_jakobs_knife", "skin_axe", "glow", "mode", "size", "size_axe", "draw_start",
          "draw_speed", "holster", "keyboard_hold", "controller_hold", "hold_time"] and model.page == "heirloom")
check("choosing the mod in the SDK's menu opens the window", getattr(mod, panel_open.MARKER, False) is True)
check("the pages are named in both languages, each with its description",
      panel_i18n.text("holster", "EN") == "HOLSTER" and panel_i18n.text("holster", "FR") == "RANGEMENT"
      and panel_i18n.text("controls", "EN") == "CONTROLS" and panel_i18n.text("controls", "FR") == "COMMANDES"
      and panel_i18n.text("heirloom", "EN") == panel_i18n.text("heirloom", "FR") == "HEIRLOOM"
      and panel_i18n.group_text(menu.holster_page, "holster", "EN") == "How each key puts your weapon away."
      and panel_i18n.group_text(menu.holster_page, "holster", "FR") == "Comment chaque touche range ton arme."
      and panel_i18n.group_text(menu.heirloom_page, "heirloom", "FR")
      == "Ton heirloom dans ta main droite quand ton arme est rangée.")
check("every setting of both parts has its French words",
      all(panel_i18n.option_text(option, "FR") != panel_i18n.option_text(option, "EN") for option in settings.ALL))
check("each holster setting has one short sentence in both languages, the French one translated",
      all(one_sentence(panel_i18n.option_text(option, language)[1]) for option in holster_settings.ALL
          for language in ("EN", "FR"))
      and all(panel_i18n.option_text(option, "FR") != panel_i18n.option_text(option, "EN")
              for option in holster_settings.ALL))
check("the CONTROLS page keeps Grapple's words where one key changes nothing",
      panel_i18n.text("listening", "FR") == "APPUIE SUR TA TOUCHE" and panel_i18n.text("gamepad", "FR") == "Manette"
      and panel_i18n.text("reset_controls", "FR") == "TOUCHES D’ORIGINE")
check("and its own where Grapple speaks of two slots or of the game's controls",
      panel_i18n.text("first", "FR") == "CHOISIR UNE TOUCHE" and "grappin" not in panel_i18n.text("controls_reset", "FR")
      and "ensemble" not in panel_i18n.text("escape_hint", "FR"))

check("a hold time past the slider's bounds is refused", not model.write({"hold_time": 0.1})
      and holster_settings.hold_time.value == 0.4)
check("the mode takes only one of its choices", not model.write({"mode": "Halo"}) and not model.write({"mode": 1})
      and model.write({"mode": "Borderlands"}) and heirloom_settings.mode.value == "Borderlands")
check("the switches take only On or Off", not model.write({"keyboard_hold": "yes"})
      and model.write({"keyboard_hold": False}) and holster_settings.mode(holster_settings.KEYBOARD) == "Press")
keys.controller_key.value = "Gamepad_FaceButton_Top"
heirloom_settings.heirloom.value = False
check("Restore puts both parts' settings and both keys back", model.restore()
      and heirloom_settings.heirloom.value is True and heirloom_settings.mode.value == "Apex"
      and holster_settings.keyboard_hold.value is True
      and keys.controller_bind.key == "Gamepad_FaceButton_Left" and model.can_undo)
check("Undo gives them back", model.undo() and holster_settings.keyboard_hold.value is False
      and keys.controller_bind.key == "Gamepad_FaceButton_Top")
check("the language, the controller's icons and the page are saved",
      model.change_language("FR") and model.change_controller_icons("XSX") and model.change_page("controls")
      and Model(mod).language == "FR" and Model(mod).controller_icons == "XSX" and Model(mod).page == "controls")
check("an unknown page or icon family is refused", not model.change_page("options")
      and not model.change_controller_icons("Switch"))
check("the window's preferences stay out of the SDK's list", all(option.is_hidden for option in (
    prefs.language, prefs.controller_icons, prefs.last_page)))

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
