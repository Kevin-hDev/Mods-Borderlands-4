"""Omni Sprint's window: its sprint and four camera pages, or one accurate notice while another camera mod owns them."""

import pathlib
import sys
import weakref
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

sdk_stubs.install()

import unrealsdk  # noqa: E402
from apex_camera_runtime import constants, shared as runtime  # noqa: E402

from omni_sprint import panel_assets, panel_fonts, panel_form, panel_model, panel_preferences  # noqa: E402
from omni_sprint import panel_theme as theme, panel_view  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


from omni_panel_view_test_fixtures import Enum, Widget


def walk(node):
    yield node
    for child in node.children:
        yield from walk(child)


def attached_once(root, widgets):
    seen = set()
    for node in walk(root.WidgetTree.RootWidget):
        if id(node) in seen:
            return False
        seen.add(id(node))
    return all(id(widget) in seen for widget in widgets.values())


def build():
    Widget.created.clear()
    model = panel_model.Model(SimpleNamespace(is_enabled=True))
    root, widgets = panel_view.build_view(SimpleNamespace(), model)
    form = panel_form.PanelForm({name: (lambda item=item: item) for name, item in widgets.items()}, model)
    return model, root, widgets, form


unrealsdk.construct_object = Widget
unrealsdk.find_enum = Enum
panel_assets.texture = lambda _world: None
panel_fonts.build = lambda _root: {"title": object(), "body": object()}

model, root, widgets, form = build()
CAMERA_PAGES = ("camera", "aiming", "orbit_camera", "loot")
check("six pages, opened on OMNI SPRINT, under the mod's name",
      len(widgets["pages"].children) == len(model.pages) == 6 and widgets["focus"] is widgets["nav:omni_sprint"]
      and theme.BRAND == "OMNI SPRINT")
check("EN and FR sit in the header, with no gear nor Options page",
      "EN" in widgets and "FR" in widgets and "options" not in widgets and "language:EN" not in widgets)
check("the page's rows are the camera settings, the FOV row registered to be greyed",
      all(f"row:{key}" in widgets for key in
          ("third_person", "shoulder_left", "orbit", "custom_fov", "fov"))
      and all(f"setting:{key}" in widgets for key in model.options))
camera_actions = ("third_person", "shoulder", "orbit", "zoom_in", "zoom_out")
check("camera shortcuts have five cards and one row per device",
      all(f"heading:command_{action}" in widgets for action in camera_actions)
      and all(f"command:{action}:{device}" in widgets
              for action in camera_actions for device in ("keyboard", "controller"))
      and all(f"setting:{key}" not in widgets for key in
              ("third_person_key", "third_person_controller", "shoulder_key", "shoulder_controller",
               "orbit_key", "orbit_controller", "zoom_in_key", "zoom_in_controller",
               "zoom_out_key", "zoom_out_controller")))
change = widgets["command:third_person:keyboard"]
check("the command selector and current value speak the menu's language",
      change.calls["SetNoKeySpecifiedText"] == ("CHANGE",)
      and change.calls["SetKeySelectionText"] == ("PRESS A KEY",)
      and widgets["value:third_person:keyboard"].calls["SetText"] == ("P",))
form.page = model.pages.index("commands")
duplicate = widgets["command:orbit:keyboard"]
duplicate.SelectedKey = SimpleNamespace(Key=SimpleNamespace(KeyName="P"))
form.poll()
check("the real Omni form keeps the key after a refused duplicate",
      model.command_options["orbit_key"].value == "Seven")
check("the real Omni form classifies a refused duplicate",
      form.command_form.notice == "refused")
check("the real Omni form explains a refused duplicate",
      widgets["commands_status"].calls["SetText"] ==
      ("Assignment refused. This input is reserved or already used.",))
check("the sprint's page holds its switch, and each card says what its page sets",
      "row:omni_sprint" in widgets and widgets["label:omni_sprint"].calls["SetText"] == ("SPRINT IN ALL DIRECTIONS",)
      and widgets["group:omni_sprint"].calls["SetText"] == ("The game's sprint, in every direction.",)
      and widgets["group:camera"].calls["SetText"] == ("View on foot, shoulder and field of view.",))


def page_of(widget):
    return next(key for key, page in zip(model.pages, widgets["pages"].children)
                if any(node is widget for node in walk(page)))


placement = {"camera": ("setting:third_person", "setting:shoulder_left", "setting:custom_fov", "setting:fov",
                        "heading:framing:horizontal", "heading:framing:height"),
             "aiming": ("setting:third_person_ads", "heading:framing:zoom"),
             "orbit_camera": ("setting:orbit", "setting:orbit_distance"),
             "loot": ("setting:extended_loot", "setting:loot_reach")}
check("each camera setting sits on its page (Kevin, 2026-10-06), spacing and height with the view on foot",
      all(page_of(widgets[name]) == key for key, names in placement.items() for name in names))
hint = "Turn on third person in the CAMERA tab."
check("only AIMING requires third person; Orbit is also available from first person",
      widgets['group:aiming'].calls['SetText'][0].endswith('\n' + hint)
      and all(hint not in widgets[f"group:{key}"].calls["SetText"][0] for key in ("camera", "orbit_camera", "loot")))
form.shown["third_person"] = True
form.refresh_labels(form.resolve())
check("with third person on, the line goes away",
      widgets["group:aiming"].calls["SetText"] == ("Third-person aiming and zoom.",)
      and widgets["group:orbit_camera"].calls["SetText"] == ("Circles the character at the distance you choose.",))
form.shown["third_person"] = model.options["third_person"].value
check("the Orbit distance reads in metres, its bounds too",
      [widgets[f"{part}:orbit_distance"].calls["SetText"] for part in ("value", "low", "high")]
      == [("3 m",), ("0.75 m",), ("6 m",)])
check("the shoulder uses side labels instead of generic on/off",
      widgets["setting:shoulder_left_label"].calls["SetText"] == ("RIGHT",))
panel_preferences.french.value = True
form.refresh_labels(form.resolve())
check("in French, the fields say MODIFIER, APPUIE SUR UNE TOUCHE and AUCUNE",
      change.calls["SetNoKeySpecifiedText"] == ("MODIFIER",)
      and change.calls["SetKeySelectionText"] == ("APPUIE SUR UNE TOUCHE",)
      and widgets["clear:third_person:keyboard_label"].calls["SetText"] == ("AUCUNE",))
check("the French shoulder side is explicit",
      widgets["setting:shoulder_left_label"].calls["SetText"] == ("DROITE",))
check("in French, the Orbit distance has a decimal comma",
      widgets["low:orbit_distance"].calls["SetText"] == ("0,75 m",)
      and widgets["group:aiming"].calls["SetText"][0].endswith("\nActive la troisième personne dans l'onglet CAMÉRA."))
check("every widget is attached once", attached_once(root, widgets))
check("one scroll area per page, one for the sidebar",
      sum(node.kind == "ScrollBox" for node in Widget.created) == len(model.pages) + 1)

shared = runtime.shared(weak_ref=weakref.ref, address_of=id)
shared.register("apex_movement", 200, object(), constants.PROTOCOL)
shared.register("third_person_fov", 150, object(), constants.PROTOCOL)
model, root, widgets, form = build()
check("while another camera mod is on, stable camera controls are hidden and the sprint's switch stays",
      all(name in widgets for name in
          ("setting:third_person", "setting:shoulder_left", "setting:orbit", "setting:fov",
           "label:omni_sprint", "setting:omni_sprint", "row:omni_sprint", "heading:command_external",
           "command:third_person:keyboard"))
      and all(widgets[f"{key}:settings"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
              for key in CAMERA_PAGES)
      and widgets["commands:settings"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",))
check("every camera card identifies an external owner when Apex Movement wins",
      all(widgets[f"group:{key}"].calls["SetText"] ==
          ("Un autre mod contrôle la caméra. Règle-la dans son menu.",) for key in CAMERA_PAGES)
      and widgets["group:omni_sprint"].calls["SetText"] == ("Le sprint du jeu, dans toutes les directions.",)
      and attached_once(root, widgets))
runtime.reset_for_tests()

shared = runtime.shared(weak_ref=weakref.ref, address_of=id)
shared.register("omni_sprint", 100, object(), constants.PROTOCOL)
model, root, widgets, form = build()
pending_sprint = not model.options["omni_sprint"].value
form.pending["omni_sprint"] = pending_sprint
form.shown["omni_sprint"] = pending_sprint
form.pending["fov"] = 120
form.shown["fov"] = 120
form.changed_at = 10**30  # Keep this draft pending while ownership changes in this poll.
shared.register("apex_movement", 200, object(), constants.PROTOCOL)
form.poll()
check("an open Omni window hides the dormant camera and keeps sprint restoration available",
      model.camera_elsewhere
      and all(widgets[f"{key}:settings"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
              for key in CAMERA_PAGES)
      and widgets["commands:settings"].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
      and widgets["commands:external"].calls["SetVisibility"] == ("ESlateVisibility.Visible",)
      and widgets["restore"].calls.get("SetIsEnabled") == (True,))
check("a live camera ownership change keeps an unsaved Omni Sprint choice",
      form.pending.get("omni_sprint") is pending_sprint and form.shown["omni_sprint"] is pending_sprint)
check("discarded camera drafts are explained in the open window",
      "fov" not in form.pending and form.notice == "camera_draft_discarded"
      and widgets["notice"].calls["SetText"] ==
      ("Mod caméra changé : les réglages caméra non enregistrés ont été annulés.",))
shared.unregister("apex_movement")
form.poll()
check("the same Omni window restores camera controls when ownership returns",
      not model.camera_elsewhere
      and all(widgets[f"{key}:settings"].calls["SetVisibility"] == ("ESlateVisibility.Visible",)
              for key in CAMERA_PAGES)
      and widgets["restore"].calls["SetIsEnabled"] == (True,))
runtime.reset_for_tests()

# Each theme changes colours only, read when the window is drawn: no colour of another theme stays (2026-10-06).
veils = {tuple(theme.HOVER_OVERLAY), tuple(theme.PRESS_OVERLAY)}
original_rgba = theme.rgba
for theme_name in theme.THEMES:
    panel_preferences.theme.value = theme_name
    used = []
    theme.rgba = lambda colour, alpha=1.0: used.append((colour, alpha)) or original_rgba(colour, alpha)
    try:
        build()
    finally:
        theme.rgba = original_rgba
    allowed = {*{**theme._EMBER, **theme.PALETTES[theme_name]}.values()}
    stray = {(colour, alpha) for colour, alpha in used if colour not in allowed and (colour, alpha) not in veils}
    check(f"{theme_name}: no colour kept from another theme, camera pages included {sorted(stray)}", not stray)
panel_preferences.theme.value = "EMBER"

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
