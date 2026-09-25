"""Omni Sprint's window: its settings in both languages, hidden while a higher-priority camera mod owns them."""

import pathlib
import sys
import weakref

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_camera_runtime import constants, shared as runtime  # noqa: E402

from omni_sprint import menu, mod, panel_i18n, panel_open, panel_preferences as prefs, settings  # noqa: E402
from omni_sprint.panel_model import Model  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def one_sentence(text: str) -> bool:
    # Kevin, 2026-09-23: a description says what the player gets in one plain sentence.
    return 0 < len(text) <= 60 and text.count(".") == 1 and text.endswith(".")


model = Model(mod)
check("the sprint's page then the camera's, holding their five settings, the FOV recovery values left out",
      model.pages == ("omni_sprint", "camera") and model.page == "omni_sprint" and not model.camera_elsewhere
      and list(model.options) == ["omni_sprint", "third_person", "third_person_key", "custom_fov", "fov"])
check("choosing the mod in the SDK's menu opens the window", getattr(mod, panel_open.MARKER, False) is True)
# mods_base refuses a slider whose step is wider than its range (options.py, SliderOption.__post_init__).
check("the saved page is a slider the SDK accepts",
      prefs.PAGE_KEYS == ("omni_sprint", "camera")
      and prefs.last_page.kwargs["step"] <= prefs.last_page.max_value - prefs.last_page.min_value)
check("pages named OMNI SPRINT in both languages (Kevin), then CAMERA and CAMÉRA, each with its description",
      panel_i18n.text("omni_sprint", "EN") == panel_i18n.text("omni_sprint", "FR") == "OMNI SPRINT"
      and panel_i18n.group_text(menu.sprint, "omni_sprint", "EN") == "The game's sprint, in every direction."
      and panel_i18n.group_text(menu.sprint, "omni_sprint", "FR") == "Le sprint du jeu, dans toutes les directions."
      and panel_i18n.text("camera", "EN") == "CAMERA" and panel_i18n.text("camera", "FR") == "CAMÉRA"
      and panel_i18n.group_text(menu.camera, "camera", "EN") == "View and field of view."
      and panel_i18n.group_text(menu.camera, "camera", "FR") == "Vue et champ de vision.")
shown = (settings.omni_sprint, settings.third_person, settings.custom_fov, settings.fov)
check("each setting has one short sentence in both languages, the French one translated",
      all(one_sentence(panel_i18n.option_text(option, language)[1])
          for option in shown for language in ("EN", "FR"))
      and all(panel_i18n.option_text(option, "FR") != panel_i18n.option_text(option, "EN") for option in shown))
check("the other camera mod notice is one short sentence in both languages",
      all(one_sentence(panel_i18n.text("camera_elsewhere", language)) for language in ("EN", "FR")))

check("the saved language and page are read back", model.change_language("FR") and model.change_page("camera")
      and Model(mod).language == "FR" and Model(mod).page == "camera")
check("an FOV past the slider's bounds is refused", not model.write({"fov": 200})
      and settings.fov.value == settings.fov.default_value)
check("a valid FOV is saved", model.write({"fov": 120}) and settings.fov.value == 120)
check("a refused key keeps the saved one", not model.write({"third_person_key": "Tilde"})
      and settings.third_person_key.value == "P")
check("a keyboard key is saved and moves the shortcut", model.write({"third_person_key": "K"})
      and settings.third_person_bind.key == "K")
check("Restore puts the defaults back and Undo the previous values",
      model.restore() and settings.fov.value == settings.fov.default_value and settings.third_person_key.value == "P"
      and model.undo() and settings.fov.value == 120 and settings.third_person_key.value == "K")

check("asking which mod drives the camera never creates the runtime",
      runtime.elected() is None and runtime.STATE not in sys.modules)
shared = runtime.shared(weak_ref=weakref.ref, address_of=id)
shared.register("omni_sprint", 100, object(), constants.PROTOCOL)
check("while Omni Sprint drives the camera, its pages show all their settings",
      not Model(mod).camera_elsewhere and len(Model(mod).options) == 5)
shared.register("apex_movement", 200, object(), constants.PROTOCOL)
elsewhere = Model(mod)
check("while Apex Movement is on, only the sprint's switch is shown, and no camera setting can be written",
      elsewhere.camera_elsewhere and list(elsewhere.options) == ["omni_sprint"] and not elsewhere.write({"fov": 130})
      and settings.fov.value == 120)
shared.unregister("apex_movement")
check("Apex Movement switched off gives the page its settings back", not Model(mod).camera_elsewhere)
runtime.reset_for_tests()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
