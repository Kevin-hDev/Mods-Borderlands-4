"""Keep one widget tree while camera ownership changes; inactive controls stay hidden."""

from . import panel_widgets as w


def section(parent, widgets, name):
    body = w.new("VerticalBox", parent)
    widgets[name] = body
    w.column(parent, body)
    return body


def refresh(form, widgets):
    elsewhere = form.model.camera_elsewhere
    if getattr(form, "owner_elsewhere", None) == elsewhere:
        return False
    form.owner_elsewhere = elsewhere
    # Ownership is live. Keep unrelated drafts, but never save a dormant camera draft.
    discarded = False
    for key in tuple(form.pending):
        if key in form.model.camera_options:
            form.pending.pop(key, None)
            discarded = True
    for name, visible in (("camera:settings", not elsewhere), ("commands:settings", not elsewhere),
                          ("commands:external", elsewhere)):
        widgets[name].SetVisibility(w.enum("ESlateVisibility", "Visible" if visible else "Collapsed"))
    if form.command_form is not None:
        form.command_form.set_enabled(not elsewhere and not form.model.transaction.pending)
    return "discarded" if discarded else "changed"
