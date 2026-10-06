"""The Options page's tabs: the gear and the tab buttons open a tab, and every head says which one it is.

The camera tab is the "options" page the gear has always opened; the commands and language tabs are pages of
model.pages whose sidebar buttons are collapsed (panel_view). The gear reopens the last tab seen while the menu is
open, the camera tab otherwise, and the menu reopens on the tab it was closed on, as on any page (announced to Kevin,
2026-10-06).
"""

from . import panel_buttons as b, panel_i18n as i18n
from .panel_options import NAMES, SENTENCES, TABS


def current(form):
    """The open tab's page, or None on a sidebar page."""
    if form.options_open:
        return "options"
    key = form.model.pages[form.page]
    return key if key in TABS else None


def poll(form, widgets):
    """Opens the tab the gear or a tab button asks for; True when one of them was clicked."""
    if form.take(widgets["options"]):
        show(form, widgets, getattr(form, "options_tab", TABS[0]))
        return True
    for page in TABS:
        for tab in TABS:
            name = f"tab:{page}:{tab}"
            if name in widgets and form.take(widgets[name]):
                show(form, widgets, tab)
                return True
    return False


def show(form, widgets, tab):
    if not (form.flush(widgets) and form.model.change_page(tab)):
        form.report(widgets, "failed")
        return
    form.options_open = tab == "options"
    if not form.options_open:
        form.page = form.model.pages.index(tab)
    widgets["pages"].SetActiveWidgetIndex(len(form.model.pages) if form.options_open else form.page)
    form.refresh_labels(widgets)


def refresh(form, widgets, language):
    """The gear, lit on any tab; each head's title, its tabs with its own lit, and its sentence; the cards only the
    Options pages have."""
    shown = current(form)
    if shown is not None:
        form.options_tab = shown
    b.paint_gear(widgets, shown is not None)
    for page in TABS:
        if f"options_title:{page}" not in widgets:
            continue
        widgets[f"options_title:{page}"].SetText(i18n.text("options", language))
        sentence = SENTENCES[page] if form.model.camera_options else "options_desc_menu"
        widgets[f"options_description:{page}"].SetText(i18n.text(sentence, language))
        for tab in TABS:
            name = f"tab:{page}:{tab}"
            if name in widgets:
                widgets[f"{name}_label"].SetText(i18n.text(NAMES[tab], language))
                b.paint(widgets, name, "on" if tab == page else "off")
    widgets["heading:language"].SetText(i18n.text("language", language))
    widgets["menu_language"].SetText(i18n.text("menu_language", language))
    if form.model.camera_options:
        widgets["heading:camera"].SetText(i18n.text("camera", language))
        widgets["group:camera"].SetText(i18n.text("camera_desc", language))
