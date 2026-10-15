"""The OPTIONS page (sketch 4 of esquisses_menu, validated by Kevin): the bar shown or not (decision 50), its size among
three (decision 52) with a look at it under the choice, and the key that opens the window (decision 48).

The look writes the bar's words at the size chosen, in points as the bar itself does (bar.py): the window is drawn for
a 1080p screen and scaled, so the look is the bar's size on such a screen, not on every one. The key's field is the
engine's key selector (panel_pages.selector), as on BL4 Arena's settings, the only widget that captures a key and names
it as the game does: clicked, it waits for a key, and the key it gets is written at once; a key refused (the left
button, a second click on the field) gives the field its key back, and Escape cancels the wait."""

from typing import Any

import unrealsdk

from . import open_key, options, panel_i18n as i18n, panel_pages as p, panel_text as tx, panel_theme as t
from . import panel_widgets as w, report, texts

# The look's example: a run going well.
EXAMPLE = (152, 1, 64, 767.0)


def page(owner: Any, group: Any, key: str, widgets: dict, template: Any) -> Any:
    scroll, body = p.scrolling_body(owner, template)
    rows = p.card(body, widgets, key)
    p.setting_rows(rows, group.children, widgets, template, expose_rows=True)
    band = w.border(rows, t.COLOR_INK, w.pad(t.SPACE_2, t.SPACE_4))
    widgets["bar_look"] = tx.text(band, "", "look")
    band.SetContent(widgets["bar_look"])
    w.column(rows, band, padding=w.pad(t.SPACE_2, 0, t.SPACE_3), halign="Left")
    widgets["open_key_label"] = tx.text(rows, "", "label", wrap=True)
    widgets["open_key"] = p.selector(rows, "", template)
    p._row(rows, widgets["open_key_label"], p._selector_frame(rows, widgets["open_key"]))
    widgets["open_key_hint"] = tx.text(rows, "", "hint", wrap=True)
    w.column(rows, widgets["open_key_hint"], padding=w.pad(t.SPACE_2, 0, t.SPACE_3))
    return scroll


def _show_key(selector: Any) -> None:
    key = unrealsdk.make_struct("Key", KeyName=open_key.key())
    selector.SetSelectedKey(unrealsdk.make_struct("InputChord", Key=key))


def _size(widget: Any, points: float) -> None:
    font = widget.Font
    try:
        font.Size = points
    except TypeError:
        font.Size = round(points)  # Engines before 5.1 size fonts in whole points.
    widget.SetFont(font)


def _chosen(form: Any) -> tuple[bool, float]:
    """The bar shown or not and its size, as the rows show them, before they are written."""
    shown = form.shown.get(options.bar.identifier) is not False
    return shown, options.BAR_SIZES.get(form.shown.get(options.bar_size.identifier),
                                        options.BAR_SIZES[options.DEFAULT_BAR_SIZE])


def look_changed(form: Any) -> bool:
    """Whether a row was clicked since the look was painted: the look follows the click, not the write."""
    return _chosen(form) != getattr(form, "look_shown", None)


def paint(form: Any, widgets: dict, language: str) -> None:
    widgets["heading:options"].SetText(i18n.text("options", language))
    widgets["group:options"].SetText("")
    form.look_shown = shown, points = _chosen(form)
    look = widgets["bar_look"]
    look.SetText(texts.bar(language, *EXAMPLE))
    w.cosmetic("bar_look_size", lambda: _size(look, points))
    look.SetRenderOpacity(1.0 if shown else t.OPACITY_DISABLED)
    widgets["open_key_label"].SetText(i18n.text("key_label", language).upper())
    widgets["open_key_hint"].SetText(i18n.text("key_hint", language))
    selector = widgets["open_key"]
    selector.SetKeySelectionText(i18n.text("press_key", language))
    if not selector.GetIsSelectingKey():
        _show_key(selector)


def selecting(widgets: dict) -> bool:
    """Whether the key's field waits for a key: Escape then cancels the wait alone (control_escape)."""
    return bool(widgets["open_key"].GetIsSelectingKey())


def poll_key(form: Any, widgets: dict) -> bool:
    """The key the field got, written; refused, the field shows the chosen key again. Whether it changed."""
    selector = widgets["open_key"]
    if selector.GetIsSelectingKey() or form.model.transaction.pending:
        return False
    name = str(selector.SelectedKey.Key.KeyName)
    if name == open_key.key():
        return False
    if not open_key.valid(name):
        _show_key(selector)
        report.note("open_key_refused", key=name)
        return False
    saved = form.model.save(((open_key.option, name),))
    if saved is False:
        form.report(widgets, form.failure_notice())
        _show_key(selector)
    report.note("open_key_saved", key=name, saved=saved)
    return saved is True
