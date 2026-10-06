"""Why the ENABLED switch did not take: the cause goes to the log, the window says what the player can do."""

from . import panel_en, report

# The line for a cause the window cannot name.
FAILED = "toggle_failed"
MAX_REASON = 200


def notice(turning_on, error):
    """Write the cause in the log, once per kind of error, and return the key of the line to show.

    An error may name its own line with a `notice` attribute, as the shared camera does for two camera mods of
    different versions; a key this window does not carry falls back to FAILED.
    """
    report.error_once(f"panel:toggle:{type(error).__name__}",
                      f"could not switch the mod {'on' if turning_on else 'off'}: "
                      f"{type(error).__name__}: {str(error)[:MAX_REASON]}")
    key = getattr(error, "notice", None)
    return key if type(key) is str and key in panel_en.TEXT else FAILED
