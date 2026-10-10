"""The gear page from mockup V2, in tabs since 2026-10-06: camera, shoulder, aiming, dynamic camera, sensitivity,
commands and the menu language.

Kevin found the single page too long (docs/mokup/menu_mods/decisions.md, sketch A of options_onglets): each tab is a
page of the window's switcher with the same head, the tilted OPTIONS title and the three tab buttons, then its own
sentence. "options" stays the camera tab's page key, the one a saved page already names.
"""

from . import panel_buttons as b, panel_dynamic, panel_pages as p, panel_shortcut as sc
from . import panel_text as tx, panel_theme as t, panel_widgets as w

# The page each tab shows, in the order of its buttons. Without the camera, Apex Movement's separate files keep one
# page, the language under the OPTIONS title, and no tab.
# The dynamic camera is a camera setting, so its tab follows the camera's (Kevin, 2026-10-06: a fourth button in
# OPTIONS rather than a sidebar page, the sidebar being full).
# The camera tab splits in two, CAMERA VIEW and SHOULDER VIEW, on the same row (Kevin, 2026-10-07: the tab grew too
# long; sketch A, two tabs rather than a second row of buttons). "options" stays the CAMERA VIEW tab's page key.
# AIMING and SENSITIVITY came on 2026-10-08 (Kevin: sensitivity is « des réglages différents », and Apex Movement gets
# the AIMING page the two other camera mods have). Seven tabs no longer fit one row: two rows right of the title, the
# camera first, then what is not the view (Kevin: « si on met les boutons sur deux lignes [...] ça passe facilement »).
# OMNI DIRECTION, the eighth, last on the second row (Kevin, 2026-10-09).
TAB_ROWS = (("options", "shoulder", "aiming", "dynamic_camera"),
            ("sensitivity", "commands", "language", "omni_direction"))
TABS = tuple(tab for row in TAB_ROWS for tab in row)
# Each tab's button and the sentence under the title.
NAMES = {"options": "camera_view", "shoulder": "shoulder_view", "aiming": "aiming", "dynamic_camera": "dynamic_camera",
         "sensitivity": "sensitivity", "commands": "commands", "language": "languages",
         "omni_direction": "omni_direction"}
SENTENCES = {"options": "camera_tab_desc", "shoulder": "shoulder_tab_desc", "aiming": "aiming_tab_desc",
             "dynamic_camera": "dynamic_camera_tab_desc", "sensitivity": "sensitivity_tab_desc",
             "commands": "commands_tab_desc", "language": "options_desc_menu",
             "omni_direction": "omni_direction_tab_desc"}
# The camera settings of the tabs other than CAMERA VIEW, by identifier.
CARD_PAGES = ("shoulder", "aiming", "sensitivity", "omni_direction")


def _language_card(body, widgets, template):
    rows = p.card(body, widgets, "language")
    # The mockup's language card has no sentence under its plate: collapsed, the empty text takes no room.
    widgets["group:language"].SetVisibility(w.enum("ESlateVisibility", "Collapsed"))
    w.column(rows, w.line(rows, t.COLOR_HOVER, height=t.STROKE_THIN), padding=w.pad(t.SPACE_2, 0, 0))
    line = w.new("HorizontalBox", rows)
    widgets["menu_language"] = tx.text(line, "", "label", wrap=True)
    w.row(line, w.sized(line, widgets["menu_language"], width=t.ROW_LABEL_WIDTH), valign="Center")
    choices = w.new("HorizontalBox", line)
    for language, gap in (("EN", t.SPACE_3), ("FR", 0)):
        w.row(choices, b.button(choices, widgets, f"language:{language}", "switch", template, "off"),
              padding=w.pad(0, gap, 0, 0), valign="Center")
    w.row(line, choices, padding=w.pad(0, t.SPACE_6), valign="Center")
    w.column(rows, line, padding=w.pad(t.SPACE_3, 0, t.SPACE_3))


def head(body, widgets, template, page, tabs):
    """The mockup's page head: the tilted inked title and its tabs on one line, then a plain sentence."""
    line = w.new("HorizontalBox", body)
    title = tx.text(line, "", "hero")
    title.SetRenderTransformPivot(w.vector(0.0, 0.5))
    title.SetRenderTransformAngle(float(t.TILT_TITLE))
    w.row(line, title, valign="Center")
    rows = w.new("VerticalBox", line)
    for number, row in enumerate(TAB_ROWS):
        shown = [tab for tab in row if tab in tabs]
        if not shown:
            continue
        buttons = w.new("HorizontalBox", rows)
        for index, tab in enumerate(shown):
            w.row(buttons, b.button(buttons, widgets, f"tab:{page}:{tab}", "tab", template, "off"),
                  padding=w.pad(0, 0, 0, 0 if index == 0 else t.SPACE_3), valign="Center")
        w.column(rows, buttons, padding=w.pad(t.SPACE_2 if number else 0, 0, 0))
    w.row(line, rows, padding=w.pad(0, 0, 0, t.SPACE_7), valign="Center")
    description = tx.text(body, "", "body", wrap=True)
    widgets[f"options_title:{page}"], widgets[f"options_description:{page}"] = title, description
    w.column(body, line)
    w.column(body, w.sized(body, description, width=t.DESC_MAX_WIDTH),
             padding=w.pad(t.SPACE_1, 0, t.SPACE_6), halign="Left")


def tab_page(owner, widgets, template, page, tabs=TABS):
    """A tab's page: its head stays at the top, always in reach, while the cards scroll under it (Kevin,
    2026-10-06)."""
    frame = w.new("VerticalBox", owner)
    top = w.new("VerticalBox", frame)
    head(top, widgets, template, page, tabs)
    w.column(frame, top, padding=w.pad(t.SPACE_7, t.SPACE_8, 0))
    scroll, body = p.scrolling_body(frame, template, top=0)
    w.column(frame, scroll, fill=True)
    return frame, body


def options_page(owner, model, widgets, template):
    if not model.camera_options:
        page, body = tab_page(owner, widgets, template, "options", ())
        _language_card(body, widgets, template)
        return page
    page, body = tab_page(owner, widgets, template, "options")
    rows = p.card(body, widgets, "camera")
    controls = w.new("VerticalBox", rows)
    widgets["camera:settings"] = controls
    w.column(rows, controls)
    from .camera_settings import CARD_SETTINGS
    elsewhere = ({name for _key, names in panel_dynamic.SECTIONS for name in names}
                 | {name for page in CARD_PAGES for name in CARD_SETTINGS[page]})
    sc.rows(controls, [option for key, option in model.camera_options.items() if key not in elsewhere], widgets,
            template)
    from . import panel_framing
    panel_framing.build(controls, widgets, template, ("horizontal", "height"))
    return page


def card_page(owner, model, widgets, template, page):
    """A tab of one card holding its own camera settings (CARD_PAGES), hidden with the camera's while another camera
    mod is in charge. AIMING also holds the aim zoom's framing card."""
    from .camera_settings import CARD_SETTINGS
    frame, body = tab_page(owner, widgets, template, page)
    rows = p.card(body, widgets, page)
    controls = w.new("VerticalBox", rows)
    widgets[f"{page}:settings"] = controls
    w.column(rows, controls)
    options = [model.camera_options[key] for key in CARD_SETTINGS[page]]
    if page == "sensitivity":
        from . import panel_weapon_sensitivity as weapons
        options, weapon_rows = weapons.split(options)
    if page == "aiming":
        from . import panel_optics
        options, optics = panel_optics.split(options)
    if page == "omni_direction":
        from . import panel_omni_direction
        panel_omni_direction.build(controls, options, widgets, template)
        return frame
    sc.rows(controls, options, widgets, template)
    if page == "aiming" and optics:
        panel_optics.build(controls, optics, widgets, template)
    if page == "sensitivity":
        weapons.build(controls, weapon_rows, widgets, template)
    if page == "aiming":
        from . import panel_framing
        panel_framing.build(controls, widgets, template, ("zoom",))
    return frame


def dynamic_page(owner, model, widgets, template):
    """The DYNAMIC CAMERA tab: one card, hidden with the camera's while another camera mod is in charge."""
    page, body = tab_page(owner, widgets, template, panel_dynamic.PAGE)
    rows = p.card(body, widgets, panel_dynamic.PAGE)
    controls = w.new("VerticalBox", rows)
    widgets[f"{panel_dynamic.PAGE}:settings"] = controls
    w.column(rows, controls)
    panel_dynamic.build(controls, model.camera_options.values(), widgets, template)
    return page


def language_page(owner, widgets, template):
    page, body = tab_page(owner, widgets, template, "language")
    _language_card(body, widgets, template)
    return page


def commands_frame(widgets, template):
    """How the commands page is built here: as an Options tab (panel_camera_commands.page)."""
    return lambda owner: tab_page(owner, widgets, template, "commands")
