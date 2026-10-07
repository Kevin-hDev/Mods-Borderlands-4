"""The gear page from mockup V2, in tabs since 2026-10-06: camera, dynamic camera, commands and the menu language.

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
TABS = ("options", "shoulder", "dynamic_camera", "commands", "language")
# Each tab's button and the sentence under the title.
NAMES = {"options": "camera_view", "shoulder": "shoulder_view", "dynamic_camera": "dynamic_camera",
         "commands": "commands", "language": "languages"}
SENTENCES = {"options": "camera_tab_desc", "shoulder": "shoulder_tab_desc", "dynamic_camera": "dynamic_camera_tab_desc",
             "commands": "commands_tab_desc", "language": "options_desc_menu"}


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
    for index, tab in enumerate(tabs):
        w.row(line, b.button(line, widgets, f"tab:{page}:{tab}", "tab", template, "off"),
              padding=w.pad(0, 0, 0, t.SPACE_7 if index == 0 else t.SPACE_3), valign="Center")
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
    from .camera_settings import SHOULDER_PAGE
    elsewhere = {name for _key, names in panel_dynamic.SECTIONS for name in names} | set(SHOULDER_PAGE)
    sc.rows(controls, [option for key, option in model.camera_options.items() if key not in elsewhere], widgets,
            template)
    from . import panel_framing
    panel_framing.build(controls, widgets, template)
    return page


def shoulder_page(owner, model, widgets, template):
    """The SHOULDER VIEW tab: one card, hidden with the camera's while another camera mod is in charge."""
    from .camera_settings import SHOULDER_PAGE
    page, body = tab_page(owner, widgets, template, "shoulder")
    rows = p.card(body, widgets, "shoulder")
    controls = w.new("VerticalBox", rows)
    widgets["shoulder:settings"] = controls
    w.column(rows, controls)
    sc.rows(controls, [model.camera_options[key] for key in SHOULDER_PAGE], widgets, template)
    return page


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
