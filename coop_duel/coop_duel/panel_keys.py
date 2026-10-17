"""The OPTIONS page: the key that opens the window (F9 at first) and the key that starts or stops the duel (N at
first), each in the engine's key selector (panel_pages.selector), as on It Follows' OPTIONS page, the only widget that
captures a key and names it as the game does: clicked, it waits for a key, and the key it gets is written at once; a
key refused (the left button, Escape, the other shortcut's key) gives the field its key back, and Escape cancels the
wait."""

from typing import Any

import unrealsdk

from . import keys, panel_i18n as i18n, panel_pages as p, panel_text as tx, panel_theme as t, panel_widgets as w
from . import report

# Each field's widget name and its texts' keys, by shortcut.
FIELDS = ((keys.OPEN, "open_key"), (keys.DUEL, "duel_key"))


def page(owner: Any, group: Any, key: str, widgets: dict, template: Any) -> Any:
    scroll, body = p.scrolling_body(owner, template)
    rows = p.card(body, widgets, key)
    for _shortcut, name in FIELDS:
        widgets[f"{name}_label"] = tx.text(rows, "", "label", wrap=True)
        widgets[name] = p.selector(rows, "", template)
        p._row(rows, widgets[f"{name}_label"], p._selector_frame(rows, widgets[name]))
        widgets[f"{name}_hint"] = tx.text(rows, "", "hint", wrap=True)
        w.column(rows, widgets[f"{name}_hint"], padding=w.pad(t.SPACE_2, 0, t.SPACE_3))
    return scroll


def _show_key(selector: Any, shortcut: keys.Shortcut) -> None:
    key = unrealsdk.make_struct("Key", KeyName=shortcut.key())
    selector.SetSelectedKey(unrealsdk.make_struct("InputChord", Key=key))


def paint(widgets: dict, language: str) -> None:
    widgets["heading:options"].SetText(i18n.text("options", language))
    widgets["group:options"].SetText("")
    for shortcut, name in FIELDS:
        widgets[f"{name}_label"].SetText(i18n.text(f"{name}_label", language).upper())
        widgets[f"{name}_hint"].SetText(i18n.text(f"{name}_hint", language))
        selector = widgets[name]
        selector.SetKeySelectionText(i18n.text("press_key", language))
        if not selector.GetIsSelectingKey():
            _show_key(selector, shortcut)


def selecting(widgets: dict) -> bool:
    """Whether a key's field waits for a key: Escape then cancels the wait alone (control_escape)."""
    return any(bool(widgets[name].GetIsSelectingKey()) for _shortcut, name in FIELDS)


def poll(form: Any, widgets: dict) -> bool:
    """The key a field got, written; refused, the field shows its key again. Whether one changed."""
    if form.model.transaction.pending:
        return False
    for shortcut, name in FIELDS:
        selector = widgets[name]
        if selector.GetIsSelectingKey():
            continue
        chosen = str(selector.SelectedKey.Key.KeyName)
        if chosen == shortcut.key():
            continue
        if not keys.valid(chosen) or keys.taken_by_other(shortcut, chosen):
            _show_key(selector, shortcut)
            form.notice = "key_taken" if keys.valid(chosen) else form.notice
            report.note("key refused", key=shortcut.identifier, name=chosen)
            return True
        saved = form.model.save(((shortcut.option, chosen),))
        if saved is False:
            form.report(widgets, form.failure_notice())
            _show_key(selector, shortcut)
        if saved is True:
            form.notice = "ready"
        report.note("key saved", key=shortcut.identifier, name=chosen, saved=saved)
        return saved is True
    return False
