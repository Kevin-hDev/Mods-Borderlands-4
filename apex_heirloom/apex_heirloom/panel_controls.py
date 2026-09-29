"""Visible saved controls: the key chosen for each device, or none."""

from . import panel_i18n as i18n
from . import panel_glyphs, panel_preferences


def summary(bindings, language):
    family = panel_preferences.controller_icons.value
    def label(key):
        return panel_glyphs.label(key, family, language)
    rows = [i18n.text("current_controls", language)]
    for device in bindings.config.DEVICES:
        try:
            selected = device.selection()
            value = " + ".join(label(key) for key in selected) if selected else i18n.text("no_key", language)
        except (ValueError, ImportError):
            value = i18n.text("invalid_keys", language)
        rows.append(f"{i18n.text(device.name, language)} : {value}")
    return "\n".join(rows)
