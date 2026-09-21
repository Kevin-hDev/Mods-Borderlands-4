"""Transactional menu changes, using the option objects as the authority on defaults."""

from . import control_config as config, report, settings


def save_values(mod, values: tuple) -> bool:
    from . import frame, keys, session
    old = tuple((option, option.value) for option, _ in values)
    # An active rope must not survive a reset or a change of its release keys.
    if not session.reset(frame.rope):
        report.warning(config.FAILED)
        return False
    try:
        for option, value in values:
            option.value = value
        mod.save_settings()
    except Exception:
        for option, value in old:
            option.value = value
        try:
            mod.save_settings()
        except Exception:
            report.error_once("controls:save", "settings could not be saved; retry before leaving the game")
        report.warning(config.FAILED)
        return False
    keys.unbind()
    frame._next_keys_ns = 0
    return True


def assign(mod, device, chosen: tuple[str, ...]) -> bool:
    mode = config.SINGLE if len(chosen) == 1 else config.DOUBLE
    return save_values(mod, ((device.mode, mode), (device.first, chosen[0]),
                             (device.second, chosen[1] if len(chosen) == 2 else None)))


def restore(button) -> None:
    from . import control_window
    control_window.cancel()
    if save_values(button.mod, tuple((option, option.default_value) for option in (*settings.ALL, *config.ALL))):
        report.note(config.RESTORED)
