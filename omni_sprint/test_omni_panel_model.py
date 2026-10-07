"""Omni Sprint's window: its settings in both languages, hidden while a higher-priority camera mod owns them."""

import pathlib
import sys
import weakref

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

from apex_camera_runtime import constants, shared as runtime  # noqa: E402

from omni_sprint import camera, menu, mod, panel_i18n, panel_open, panel_preferences as prefs, settings  # noqa: E402
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
check("the camera declaration contains no command row",
      not ({option.identifier for group in menu.CAMERA for option in group.children}
           & {option.identifier for option in settings.commands.options}))
PAGES = ("omni_sprint", "camera", "aiming", "orbit_camera", "loot", "dynamic_camera", "commands", "shoulder")
check("the sprint's page then the five camera pages (Kevin, 2026-10-06), the recovery values left out",
      model.pages == PAGES and model.page == "omni_sprint" and not model.camera_elsewhere
      and list(model.options) == ["omni_sprint", "third_person", "custom_fov", "fov", "camera_distance_close",
                                  "camera_distance_far", "orbit_smooth", "shoulder_seconds",
                                  "free_look_keyboard_hold", "free_look_controller_hold", "free_look_hold_time",
                                  "shoulder_left", "shoulder_auto", "shoulder_auto_swap", "shoulder_auto_return",
                                  "shoulder_smooth",
                                  "third_person_ads", "orbit", "orbit_distance", "extended_loot", "loot_reach",
                                  "speed_fov", "speed_fov_gain", "speed_fov_seconds", "action_framing",
                                  "action_framing_strength", "camera_motion", "camera_motion_strength"]
      and set(model.camera_options) == set(model.options) - {"omni_sprint"}
      and list(model.command_options) == ["third_person_key", "third_person_controller", "shoulder_key",
                                          "shoulder_controller", "orbit_key", "orbit_controller",
                                          "zoom_in_key", "zoom_in_controller", "zoom_out_key", "zoom_out_controller",
                                          "free_look_key", "free_look_controller", "camera_distance_key",
                                          "camera_distance_controller"])
check("choosing the mod in the SDK's menu opens the window", getattr(mod, panel_open.MARKER, False) is True)
# mods_base refuses a slider whose step is wider than its range (options.py, SliderOption.__post_init__).
check("the saved page is a slider the SDK accepts",
      prefs.PAGE_KEYS == PAGES
      and prefs.last_page.kwargs["step"] <= prefs.last_page.max_value - prefs.last_page.min_value)
check("pages named OMNI SPRINT in both languages (Kevin), then CAMERA and CAMÉRA, each with its description",
      panel_i18n.text("omni_sprint", "EN") == panel_i18n.text("omni_sprint", "FR") == "OMNI SPRINT"
      and panel_i18n.group_text(menu.sprint, "omni_sprint", "EN") == "The game's sprint, in every direction."
      and panel_i18n.group_text(menu.sprint, "omni_sprint", "FR") == "Le sprint du jeu, dans toutes les directions."
      and panel_i18n.text("camera", "EN") == "CAMERA" and panel_i18n.text("camera", "FR") == "CAMÉRA")
camera_pages = dict(zip(PAGES[1:6], menu.CAMERA))
check("each camera page has its name and its one-line description in both languages",
      [(panel_i18n.text(key, "EN"), panel_i18n.text(key, "FR")) for key in camera_pages]
      == [("CAMERA", "CAMÉRA"), ("AIMING", "VISÉE"), ("ORBIT CAMERA", "CAMÉRA ORBITALE"), ("LOOT", "LOOT"),
          ("DYNAMIC CAMERA", "CAMÉRA DYNAMIQUE")]
      and [panel_i18n.group_text(group, key, "FR") for key, group in camera_pages.items()]
      == ["Vue à pied, champ de vision et vue libre.", "Visée en troisième personne et zoom.",
          "Tourne autour du personnage, à la distance de ton choix.", "Ramasse le loot de plus loin.",
          "La caméra suit l'action : vitesse, sauts, accroupi et conduite."]
      and [panel_i18n.group_text(group, key, "EN") for key, group in camera_pages.items()]
      == ["View on foot, field of view and Free Look.", "Third-person aiming and zoom.",
          "Circles the character at the distance you choose.", "Pick up loot from farther away.",
          "The camera follows the action: speed, jumps, crouching and driving."])
check("one name for the orbit camera: its page is named as its command (review, 2026-09-26)",
      all(panel_i18n.text("orbit_camera", language) == panel_i18n.text("command_orbit", language)
          for language in ("EN", "FR")))
check("pages greyed by third person say where its switch is",
      panel_i18n.text("third_person_needed", "EN") == "Turn on third person in the CAMERA tab."
      and panel_i18n.text("third_person_needed", "FR") == "Active la troisième personne dans l'onglet CAMÉRA.")
shown = (settings.omni_sprint, settings.third_person, settings.shoulder_left,
         settings.orbit, settings.zoom.option, settings.custom_fov, settings.fov, *settings.loot.options)
check("each setting has one short sentence in both languages, the French one translated",
      all(one_sentence(panel_i18n.option_text(option, language)[1])
          for option in shown for language in ("EN", "FR"))
      and all(panel_i18n.option_text(option, "FR") != panel_i18n.option_text(option, "EN") for option in shown))
check("the other camera mod notice says where to adjust it in both languages",
      panel_i18n.text("camera_elsewhere", "EN") == "Another camera mod controls the camera. Use its menu to adjust it."
      and panel_i18n.text("camera_elsewhere", "FR") == "Un autre mod contrôle la caméra. Règle-la dans son menu.")

check("the saved language and page are read back", model.change_language("FR") and model.change_page("camera")
      and Model(mod).language == "FR" and Model(mod).page == "camera")
check("an FOV past the slider's bounds is refused", not model.write({"fov": 200})
      and settings.fov.value == settings.fov.default_value)
check("a valid FOV is saved", model.write({"fov": 120}) and settings.fov.value == 120)
check("a refused key keeps the saved one", not model.write_commands({"third_person_key": "Tilde"})
      and settings.third_person_key.value == "P")
check("a keyboard key is saved and moves the shortcut", model.write_commands({"third_person_key": "K"})
      and settings.third_person_bind.key == "K")
check("Restore puts the defaults back and Undo the previous values",
      model.restore() and settings.fov.value == settings.fov.default_value and settings.third_person_key.value == "P"
      and model.undo() and settings.fov.value == 120 and settings.third_person_key.value == "K")

mod.is_enabled = True
camera_calls = []
orbit_deferred = [False]


def set_shoulder(left):
    camera_calls.append(("shoulder", left))
    settings.set_shoulder_left(left)
    return True


def set_orbit(enabled):
    camera_calls.append(("orbit", enabled))
    if not orbit_deferred[0]:
        settings.set_orbit(enabled)
    return True


camera.set_shoulder, camera.set_orbit = set_shoulder, set_orbit
camera.ready = lambda: True
orbit_deferred[0] = True
check("camera rows route through the runtime and Orbit waits for confirmation",
      model.write({"shoulder_left": True}) and settings.shoulder_left.value is True
      and model.write({"orbit": True}) is None
      and settings.orbit.value is False
      and camera_calls[-2:] == [("shoulder", True), ("orbit", True)])
settings.set_orbit(True)
saved = model.advance()
settings.third_person.value = True
first_restore = model.restore()
settings.set_orbit(False)
restored = model.advance()
undone_started = model.undo()
settings.set_orbit(True)
undone = model.advance()
check("Restore and Undo use the same camera transactions",
      saved == "saved" and first_restore is None and restored == "restored"
      and undone_started is None and undone == "undone" and settings.orbit.value is True
      and settings.shoulder_left.value is True and settings.third_person.value is True)

check("asking which mod drives the camera never creates the runtime",
      runtime.elected() is None and runtime.STATE not in sys.modules)
shared = runtime.shared(weak_ref=weakref.ref, address_of=id)
shared.register("omni_sprint", 100, object(), constants.PROTOCOL)
check("while Omni Sprint drives the camera, its pages show all their settings",
      not Model(mod).camera_elsewhere and len(Model(mod).options) == 28 and len(Model(mod).command_options) == 14)
shared.register("apex_movement", 200, object(), constants.PROTOCOL)
elsewhere = Model(mod)
check("while Apex Movement is on, stable camera controls refuse writes but the sprint remains writable",
      elsewhere.camera_elsewhere and len(elsewhere.options) == 28 and len(elsewhere.command_options) == 14
      and not elsewhere.write({"orbit_distance": 400})
      and not elsewhere.write({"fov": 130}) and elsewhere.write({"omni_sprint": False})
      and elsewhere.command_actions is not None and elsewhere.restore() and settings.omni_sprint.value is True
      and settings.fov.value == 120)
check("a malformed dormant camera write is refused without an exception",
      not elsewhere.write(None))
shared.unregister("apex_movement")
check("Apex Movement switched off gives the page its settings back", not Model(mod).camera_elsewhere)
runtime.reset_for_tests()

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
