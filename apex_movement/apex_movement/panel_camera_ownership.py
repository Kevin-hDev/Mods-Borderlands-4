"""One authority hides dormant camera controls and discards their drafts."""
from . import panel_labels, panel_widgets as w


def refresh(form, widgets):
    elsewhere = form.model.camera_elsewhere
    if getattr(form, "owner_elsewhere", None) == elsewhere:
        return False
    form.owner_elsewhere = elsewhere
    discarded = False
    if elsewhere:
        for key, option in form.model.camera_options.items():
            discarded = form.pending.pop(key, None) is not None or discarded
            form.shown[key] = option.value
            panel_labels.value(widgets, option, option.value, form.model.language)
            if type(option.default_value) is bool:
                widgets[f"setting:{key}"].SetIsChecked(False)
            else:
                widgets[f"setting:{key}"].SetValue(float(option.value))
        framing = getattr(form, "framing_form", None)
        if framing is not None and framing.pending:
            framing.reset(widgets)
            discarded = True
    for name, visible in (("camera:settings", not elsewhere), ("dynamic_camera:settings", not elsewhere),
                          ("shoulder:settings", not elsewhere),
                          ("commands:settings", not elsewhere),
                          ("commands:external", elsewhere)):
        if name in widgets:
            widgets[name].SetVisibility(w.enum("ESlateVisibility", "Visible" if visible else "Collapsed"))
    if form.command_form is not None:
        form.command_form.set_enabled(not elsewhere and not form.model.transaction.pending)
    if discarded:
        form.report(widgets, "camera_draft_discarded")
    return "discarded" if discarded else "changed"
