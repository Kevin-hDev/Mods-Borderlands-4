"""The DYNAMIC CAMERA page's three cards, FIELD OF VIEW, FRAMING and MOTION (Kevin, 2026-10-06).

The same page in the three camera mods: Apex Movement shows it as an Options tab, Omni Sprint and Third Person & FOV
as a sidebar page (outils/sync_menu_camera_pages.py); this module is copied into both by outils/sync_menu_ui.py.
"""

from . import panel_i18n as i18n, panel_pages as p

PAGE = "dynamic_camera"
# Each card's key and its settings, by identifier, in their order on the page.
SECTIONS = (
    ("fov", ("speed_fov", "speed_fov_gain", "speed_fov_seconds")),
    ("framing", ("action_framing", "action_framing_strength")),
    ("motion", ("camera_motion", "camera_motion_strength")),
)


def build(parent, options, widgets, template):
    by_name = {option.identifier: option for option in options}
    for key, names in SECTIONS:
        rows = p.card(parent, widgets, f"dynamic:{key}")
        p.setting_rows(rows, [by_name[name] for name in names], widgets, template, expose_rows=True)


def refresh(widgets, language):
    for key, _names in SECTIONS:
        widgets[f"heading:dynamic:{key}"].SetText(i18n.text(f"dynamic_{key}", language))
        widgets[f"group:dynamic:{key}"].SetText(i18n.text(f"dynamic_{key}_desc", language))
