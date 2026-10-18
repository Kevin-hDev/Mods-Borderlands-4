"""The COMMANDS page's MENU SHORTCUT card, first on the page: the key that opens this window in game (open_key.py),
chosen or cleared as a camera command's key is, on the same row; and the closing of the window by that key.

Third Person & FOV's own, called from its copies of Apex Movement's window files, where
outils/sync_menu_third_person.py puts the calls. When Apex Movement gets its key too (F10, Kevin, 2026-10-18), this
file and those calls move into Apex Movement's own files, the camera windows' source (docs/mokup/menu_mods/
decisions.md, 2026-10-18)."""

from . import open_key, panel_i18n as i18n, report
from .camera_control_form import Form as CommandForm

CARD = "command_open_window"
# The row's widgets are named as a camera command's (panel_camera_commands._device_row).
ACTION, DEVICE = "open_window", "keyboard"
NAME = f"{ACTION}:{DEVICE}"


def refresh(widgets, language, show):
    """The card's words, and its key through show(name, key), the page's way of showing a key."""
    widgets[f"heading:{CARD}"].SetText(i18n.text(CARD, language))
    widgets[f"group:{CARD}"].SetText(i18n.text(f"{CARD}_desc", language))
    widgets[f"device:{NAME}"].SetText(i18n.text(DEVICE, language))
    widgets[f"clear:{NAME}_label"].SetText(i18n.text("no_key", language))
    widgets[f"command:{NAME}"].SetNoKeySpecifiedText(i18n.text("change_key", language))
    widgets[f"command:{NAME}"].SetKeySelectionText(i18n.text("press_key", language))
    show(NAME, open_key.key())


def selecting(widgets):
    """Whether the card's field waits for a key: Escape then cancels the wait alone (control_escape.py)."""
    return bool(widgets[f"command:{NAME}"].GetIsSelectingKey())


def closing(form, widgets):
    """Whether the key that opens the window was just let go, to close it as Close does. Deaf while a key is being
    chosen, a pop-up or a profile's window is open: as Escape, it then never closes the whole window."""
    if open_key.align() or not hasattr(form, "open_closer"):
        form.open_closer = open_key.closer()
    if form.open_closer is None:
        return False
    busy = form.selecting() or form.popup is not None or bool(form.profile_form and form.profile_form.open)
    if not form.open_closer.released(busy):
        return False
    report.note(f"open key closes the window: {open_key.key()}")
    return True


def poll(form, widgets):
    """The card's NONE button and key field; whether either was handled. The answer shows on the page's status
    line, as a camera command's."""
    if form.model.transaction.pending or selecting(widgets):
        return False
    if CommandForm.take(widgets[f"clear:{NAME}"]):
        return _choose(form, widgets, None)
    selector = widgets[f"command:{NAME}"]
    name = str(selector.SelectedKey.Key.KeyName)
    if name in ("", "None"):
        return False
    CommandForm.clear_selector(selector)
    # Imported here: that module's imports load the COMMANDS page, whose file loads this one.
    from .panel_profile_form import CANCELLING
    return name in CANCELLING or _choose(form, widgets, name)


def refusal(model, name):
    """Why name cannot open the window, as a notice of the page, or None. One press never does two things: a camera
    command's key, now or by default (its reset must not take this one), or a camera profile's, is refused."""
    if name is None:
        return None
    try:
        open_key.normalize(name)
    except ValueError:
        return "refused"
    commands = model.command_actions.commands
    if name in {item.value for item in commands.options} | set(commands.defaults().values()):
        return "open_key_command"
    return "command_held" if model._held_by_profile((name,)) else None


def _choose(form, widgets, name):
    notice = refusal(form.model, name)
    if notice is None and name != open_key.chosen():
        saved = form.model.save(((open_key.option, name),))
        notice = "saved" if saved else "ready" if saved is None else form.failure_notice()
        report.note(f"open key chosen: {name}, saved={saved}")
    form.command_form.notice = notice or "ready"
    form.refresh_labels(widgets)
    return True
