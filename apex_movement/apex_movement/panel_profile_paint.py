"""The camera profile window's words and values (panel_profile_window.py), from the draft, its refusal and the menu's
language and controller icons."""

from . import panel_buttons as b, panel_camera_commands as commands, panel_framing as framing
from . import panel_framing_text as framing_text, panel_i18n as i18n, panel_profile_text as words
from . import panel_slider as s

# The window's own short names for the distances, so they fit beside its narrower sliders (mockup profils/6_coin.png).
SHORT = {"close": "profile_close", "far": "profile_far"}
TEXTS = (("group:profile_window", "profile_desc"), ("profile:name_caption", "profile_name"),
         ("profile:key_caption", "profile_key"), ("profile:cancel_label", "profile_cancel"),
         ("profile:save_label", "profile_save"))


def paint(widgets, form, draft, notice):
    """form is the profile form, for its settings' sources and sliders and the menu it belongs to."""
    model, language = form.form.model, form.form.model.language
    widgets["heading:profile_window"].SetText(words.text("profile_edit" if draft.editing else "profile_new",
                                                         language))
    for name, key in TEXTS:
        widgets[name].SetText(words.text(key, language))
    widgets["profile:status"].SetText(words.text(notice, language) if notice else "")
    for field, (option, group) in form.sources.items():
        _setting(widgets, field, form.fields[field], option, group, getattr(draft.values, field), language)
    for device, key in (("keyboard", draft.keyboard), ("controller", draft.controller)):
        name = f"profile:{device}"
        widgets[f"device:{name}"].SetText(i18n.text(device, language))
        widgets[f"clear:{name}_label"].SetText(i18n.text("no_key", language))
        widgets[f"command:{name}"].SetNoKeySpecifiedText(i18n.text("change_key", language))
        widgets[f"command:{name}"].SetKeySelectionText(i18n.text("press_key", language))
        commands._show_value(widgets, name, key, model.controller_icons, language, form.form.command_catalogue)


def _setting(widgets, field, slider, option, group, value, language):
    key = f"profile:{field}"
    s.show(widgets, slider, value)
    if group is None:
        title = words.text(SHORT[field], language) if field in SHORT else i18n.option_text(option, language)[0]
        widgets[f"label:{key}"].SetText(title.upper())
        return
    custom = all(number != value for _label, number in group.presets)
    widgets[f"label:{key}"].SetText(framing_text.text(group.key, language)[0])
    widgets[f"value:{key}"].SetText(framing.percent(value, language))
    for index, (label, number) in enumerate(group.presets):
        widgets[f"{key}:preset:{index}_label"].SetText(framing_text.text(label, language))
        b.paint(widgets, f"{key}:preset:{index}", "on" if not custom and number == value else "off")
