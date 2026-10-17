"""Co-op Duel's pages wired into our windows' form (docs/duel/outils/menu_window.py writes the calls): DUEL
(panel_duel.py) and OPTIONS (panel_keys.py), the footer's sentence, and the key that opens the window closing it too,
as It Follows' panel_follows.py does with its own key."""

from typing import Any

from . import keys, menu, panel_duel, panel_i18n as i18n, panel_keys, report

DUEL, OPTIONS = (group.identifier.removesuffix("_menu") for group in (menu.duel, menu.options))
PAGES = {DUEL: panel_duel.page, OPTIONS: panel_keys.page}
# What poll answers when the window must close without the mods list (a duel that starts), and when it closes as its
# CLOSE button does (panel_form.py, control_window.py).
LEAVE, CLOSE = panel_duel.LEAVE, "close"


def page(owner: Any, group: Any, key: str, widgets: dict, template: Any) -> Any:
    return PAGES[key](owner, group, key, widgets, template)


def start(form: Any) -> None:
    """When the window's form is made: the keys given to the SDK, and the watch of the key that opened it."""
    keys.align()
    form.closer = keys.closer()


def _follow_keys(form: Any) -> None:
    """The SDK's keybinds and the closing watch given the keys just chosen."""
    if keys.align():
        form.closer = keys.closer()


def poll(form: Any, widgets: dict) -> str | bool:
    """The pages' own buttons and the keys' fields; LEAVE or CLOSE when the window must close, else whether something
    was handled."""
    _follow_keys(form)
    if form.closer is not None and form.closer.released(panel_keys.selecting(widgets)):
        report.note("open key closes", name=keys.OPEN.key())
        return CLOSE if form.flush(widgets) else True
    polled = panel_duel.poll(form, widgets)
    if polled:
        return polled
    if panel_keys.poll(form, widgets):
        _follow_keys(form)
        form.refresh_labels(widgets)
        return True
    return False


def selecting(form: Any) -> bool:
    return panel_keys.selecting(form.resolve())


def paint(form: Any, widgets: dict, language: str) -> None:
    panel_duel.paint(form, widgets, language)
    panel_keys.paint(widgets, language)


def notice(form: Any, language: str) -> str:
    """The footer's sentence: the page's own while the window has nothing else to say."""
    options = form.model.pages[form.page] == OPTIONS
    # A start refused belongs to the DUEL page: on OPTIONS it would speak of a button not shown there.
    if form.notice != "ready" and not (options and form.notice.startswith("start_")):
        return i18n.text(form.notice, language)
    if options:
        return i18n.text("ready_options", language)
    return panel_duel.notice(form, language)
