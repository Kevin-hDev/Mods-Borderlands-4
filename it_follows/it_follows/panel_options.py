"""The OPTIONS page (sketch 4 of esquisses_menu, validated by Kevin): the bar shown or not (decision 50), its size among
three (decision 52) with a look at it under the choice, the Lost Loot, the 16:10 resolution, the colour profile on one
line (decision 149, panel_colours.py), the key that opens the window (decision 48), and the key that launches the
companions' team or stops it (team_key.py). The two keys are never the same: one would open the window and start the
team at once.

The look writes the bar's words at the size chosen, in points as the bar itself does (bar.py): the window is drawn for
a 1080p screen and scaled, so the look is the bar's size on such a screen, not on every one. The key's field is the
engine's key selector (panel_pages.selector), as on BL4 Arena's settings, the only widget that captures a key and names
it as the game does: clicked, it waits for a key, and the key it gets is written at once; a key refused (the left
button, a second click on the field) gives the field its key back, and Escape cancels the wait."""

from typing import Any

import unrealsdk

from . import open_key, options, panel_colours, panel_i18n as i18n, panel_pages as p, panel_text as tx, team_key
from . import panel_theme as t
from . import panel_widgets as w, report, texts

# The look's example: a run going well.
EXAMPLE = (152, 1, 64, 1, 767.0)
# Each key's row: its module, which holds it, then its words.
KEYS = {"open_key": (open_key, "key_label", "key_hint"), "team_key": (team_key, "team_key_label", "team_key_hint")}


def page(owner: Any, group: Any, key: str, widgets: dict, template: Any) -> Any:
    scroll, body = p.scrolling_body(owner, template)
    rows = p.card(body, widgets, key)
    # The colour profile's buttons go on its switch's line (panel_colours.merge), not on a row of their own.
    p.setting_rows(rows, [row for row in group.children if row is not options.colour_profile], widgets, template,
                   expose_rows=True)
    panel_colours.merge(rows, widgets, template)
    band = w.border(rows, t.COLOR_INK, w.pad(t.SPACE_2, t.SPACE_4))
    widgets["bar_look"] = tx.text(band, "", "look")
    band.SetContent(widgets["bar_look"])
    w.column(rows, band, padding=w.pad(t.SPACE_2, 0, t.SPACE_3), halign="Left")
    for name in KEYS:
        widgets[f"{name}_label"] = tx.text(rows, "", "label", wrap=True)
        widgets[name] = p.selector(rows, "", template)
        p._row(rows, widgets[f"{name}_label"], p._selector_frame(rows, widgets[name]))
        widgets[f"{name}_hint"] = tx.text(rows, "", "hint", wrap=True)
        w.column(rows, widgets[f"{name}_hint"], padding=w.pad(t.SPACE_2, 0, t.SPACE_3))
    return scroll


def _show_key(selector: Any, held: Any) -> None:
    key = unrealsdk.make_struct("Key", KeyName=held.key())
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
    """Whether a row was clicked since the look, or the colour profile's line, was painted: they follow the click, not
    the write."""
    return _chosen(form) != getattr(form, "look_shown", None) or panel_colours.changed(form)


def paint(form: Any, widgets: dict, language: str) -> None:
    widgets["heading:options"].SetText(i18n.text("options", language))
    widgets["group:options"].SetText("")
    form.look_shown = shown, points = _chosen(form)
    look = widgets["bar_look"]
    look.SetText(texts.bar(language, *EXAMPLE))
    w.cosmetic("bar_look_size", lambda: _size(look, points))
    look.SetRenderOpacity(1.0 if shown else t.OPACITY_DISABLED)
    panel_colours.paint(form, widgets, language)
    for name, (held, label, hint) in KEYS.items():
        widgets[f"{name}_label"].SetText(i18n.text(label, language).upper())
        widgets[f"{name}_hint"].SetText(i18n.text(hint, language))
        selector = widgets[name]
        selector.SetKeySelectionText(i18n.text("press_key", language))
        if not selector.GetIsSelectingKey():
            _show_key(selector, held)


def selecting(widgets: dict) -> bool:
    """Whether a key's field waits for a key: Escape then cancels the wait alone (control_escape)."""
    return any(bool(widgets[name].GetIsSelectingKey()) for name in KEYS)


def poll_key(form: Any, widgets: dict) -> bool:
    """The key each field got, written; refused, the field shows its chosen key again. Whether one changed."""
    return any([_poll_one(form, widgets, name) for name in KEYS])


def _poll_one(form: Any, widgets: dict, name: str) -> bool:
    held = KEYS[name][0]
    other = next(module for module, _label, _hint in KEYS.values() if module is not held)
    selector = widgets[name]
    if selector.GetIsSelectingKey() or form.model.transaction.pending:
        return False
    chosen = str(selector.SelectedKey.Key.KeyName)
    if chosen == held.key():
        return False
    if not open_key.valid(chosen) or chosen == other.key():
        _show_key(selector, held)
        if chosen == other.key():
            form.report(widgets, "key_taken")
        report.note(f"{name}_refused", key=chosen)
        return False
    saved = form.model.save(((held.option, chosen),))
    if saved is False:
        form.report(widgets, form.failure_notice())
        _show_key(selector, held)
    report.note(f"{name}_saved", key=chosen, saved=saved)
    return saved is True
