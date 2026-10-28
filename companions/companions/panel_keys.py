"""The two keys under OPTIONS on the SETTINGS page (sketch A2): the one that opens Companions' window, none at first
(decision 71 of docs/renforts), and the one that launches the team or stops it, F8 at first (team_key.py). The two
are never the same: one press would open the window and launch the team at once.

Each field is the engine's key selector (panel_pages.selector), as on It Follows' OPTIONS page, the only widget that
captures a key and names it as the game does: clicked, it waits for a key, and the key it gets is written at once; a
key refused (the left button, a second click on the field, the other key) gives the field its key back, and Escape
cancels the wait. With no key, the field says NONE, as Third Person & FOV's key fields do (SetNoKeySpecifiedText,
the key named None)."""

from typing import Any

import unrealsdk

from . import open_key, panel_i18n as i18n, panel_pages as p, panel_text as tx, panel_theme as t
from . import panel_widgets as w, report, team_key

# Each key's row: its module, which holds it, then its words.
KEYS = {"open_key": (open_key, "key_label", "key_hint"), "team_key": (team_key, "team_key_label", "team_key_hint")}
# How an Unreal key that is none is named.
NONE = "None"
MAX_NAME = 64


def draw(rows: Any, widgets: dict, template: Any) -> None:
    for name in KEYS:
        widgets[f"{name}_label"] = tx.text(rows, "", "label", wrap=True)
        widgets[name] = p.selector(rows, "", template)
        p._row(rows, widgets[f"{name}_label"], p._selector_frame(rows, widgets[name]))
        widgets[f"{name}_hint"] = tx.text(rows, "", "hint", wrap=True)
        w.column(rows, widgets[f"{name}_hint"], padding=w.pad(t.SPACE_2, 0, t.SPACE_3))


def _held(held: Any) -> str:
    return held.key() or NONE


def _show_key(selector: Any, held: Any) -> None:
    key = unrealsdk.make_struct("Key", KeyName=_held(held))
    selector.SetSelectedKey(unrealsdk.make_struct("InputChord", Key=key))


def paint(widgets: dict, language: str, blocked: bool = False) -> None:
    """The two keys' rows; the team's greyed while no team may start (blocked): it would launch nothing. The
    window's key stays: it opens this window."""
    for name, (held, label, hint) in KEYS.items():
        greyed = blocked and name == "team_key"
        widgets[name].SetIsEnabled(not greyed)
        for part in (f"{name}_label", f"{name}_hint"):
            widgets[part].SetRenderOpacity(t.OPACITY_DISABLED if greyed else 1.0)
        widgets[f"{name}_label"].SetText(i18n.text(label, language).upper())
        widgets[f"{name}_hint"].SetText(i18n.text(hint, language))
        selector = widgets[name]
        selector.SetKeySelectionText(i18n.text("press_key", language))
        selector.SetNoKeySpecifiedText(i18n.text("no_key", language))
        if not selector.GetIsSelectingKey():
            _show_key(selector, held)


def selecting(widgets: dict) -> bool:
    """Whether a key's field waits for a key: Escape then cancels the wait alone (control_escape)."""
    return any(bool(widgets[name].GetIsSelectingKey()) for name in KEYS)


def poll(form: Any, widgets: dict) -> bool:
    """The key each field got, written; refused, the field shows its chosen key again. Whether one changed."""
    return any([_poll_one(form, widgets, name) for name in KEYS])


def _poll_one(form: Any, widgets: dict, name: str) -> bool:
    held = KEYS[name][0]
    other = next(module for module, _label, _hint in KEYS.values() if module is not held)
    selector = widgets[name]
    if selector.GetIsSelectingKey() or form.model.transaction.pending:
        return False
    chosen = str(selector.SelectedKey.Key.KeyName)
    if chosen == _held(held):
        return False
    if not open_key.valid(chosen) or chosen == other.key():
        _show_key(selector, held)
        if chosen == other.key():
            form.report(widgets, "key_taken")
        report.note(f"{name}_refused", key=chosen[:MAX_NAME])
        return False
    saved = form.model.save(((held.option, chosen),))
    if saved is False:
        form.report(widgets, form.failure_notice())
        _show_key(selector, held)
    report.note(f"{name}_saved", key=chosen, saved=saved)
    return saved is True
