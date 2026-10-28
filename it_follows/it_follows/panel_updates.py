"""The update notes (decision 117, docs/RUN/spec-notes-de-mise-a-jour.md): at the first opening of the window after
an update, one page for each version missed that has a note, the newest first, its title the version and « 1 / 3 »,
then its points. NEXT turns the page, on every page but the last; CLOSE, a click beside it or Escape close it on any
page (Kevin: « on ne doit pas le forcer a tout lire »), never the window: the pop-up of our windows' shared kind
(panel_popup.py), as the « ? »'s help.

The version installed is remembered as seen as soon as it shows, as the welcome: a game that crashes later must not
show it again. The notes are in the window's language, English where they have none."""

from typing import Any

from . import panel_buttons as b, panel_i18n as i18n, panel_popup, panel_text as tx, panel_theme as t
from . import panel_widgets as w, report, updates

KEY = "updates"


def build(widgets: dict, template: Any) -> None:
    """The notes' pop-up, closed: its points above NEXT, its CLOSE under them."""
    content = panel_popup.build(widgets, KEY, template)
    widgets["updates_points"] = tx.text(content, "", "body", wrap=True)
    w.column(content, widgets["updates_points"], padding=w.pad(t.SPACE_2, 0, t.SPACE_2))
    widgets["updates_next_box"] = b.button(content, widgets, "updates_next", "action", template, "primary")
    w.column(content, widgets["updates_next_box"], halign="Right")


def open_first(form: Any, widgets: dict, notes: list[tuple[str, dict]]) -> None:
    """The notes shown on their first page, the version installed remembered as seen at once."""
    from . import __version__

    form.update_notes, form.update_page = notes, 0
    paint(form, widgets, form.model.language)
    panel_popup.show(form, widgets, KEY)
    saved = form.model.save(((updates.seen, __version__),))
    report.note("updates_shown", versions=[version for version, _texts in notes], saved=saved)


def poll(form: Any, widgets: dict) -> bool:
    """While the notes show, NEXT, then what closes any pop-up; whether they show."""
    if form.popup != KEY:
        return False
    if form.take(widgets["updates_next"]) and form.update_page + 1 < len(form.update_notes):
        form.update_page += 1
        paint(form, widgets, form.model.language)
        report.note("updates_next", page=form.update_page + 1)
    panel_popup.poll(form, widgets)
    return True


def paint(form: Any, widgets: dict, language: str) -> None:
    """The page shown, in the window's language: its version, its place, its points, NEXT unless it is the last."""
    widgets["updates_next_label"].SetText(i18n.text("updates_next", language))
    if not form.update_notes:
        return
    version, texts = form.update_notes[form.update_page]
    points = texts.get(language.lower()) or texts["en"]
    widgets[f"heading:popup_{KEY}"].SetText(i18n.text("updates_title", language).format(version=version))
    widgets[f"group:popup_{KEY}"].SetText(i18n.text("updates_count", language).format(
        page=form.update_page + 1, pages=len(form.update_notes)))
    widgets["updates_points"].SetText("\n\n".join(f"• {point}" for point in points))
    last = form.update_page + 1 >= len(form.update_notes)
    shown = "Collapsed" if last else "SelfHitTestInvisible"
    widgets["updates_next_box"].SetVisibility(w.enum("ESlateVisibility", shown))
