"""Visible saved controls; defaults come from the same mappings as gameplay, never guessed."""

from . import game, input_list, panel_i18n as i18n, report
from . import panel_glyphs, panel_preferences


def summary(bindings, language):
    family = panel_preferences.controller_icons.value
    def label(key):
        return panel_glyphs.label(key, family, language)
    try:
        defaults = input_list.grapple_keys(game.input_mappings())
    except Exception:
        report.error_once("controls:display", "game controls unavailable for display")
        defaults = set()
    rows = [i18n.text("current_controls", language)]
    for device in bindings.config.DEVICES:
        try:
            selected = device.selection()
            if selected:
                value = " + ".join(label(key) for key in selected)
            else:
                actual = sorted(key for key in defaults if bindings.config.device_of(key) == device.name)
                value = " / ".join(label(key) for key in actual)
                value = (f"{value} ({i18n.text('game_controls', language)})" if value
                         else i18n.text("game_controls_pending", language))
        except (ValueError, ImportError):
            value = i18n.text("invalid_keys", language)
        rows.append(f"{i18n.text(device.name, language)} : {value}")
    return "\n".join(rows)
