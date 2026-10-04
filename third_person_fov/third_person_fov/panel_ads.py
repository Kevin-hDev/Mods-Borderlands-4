"""Read the elected runtime's aiming notice; never create or control a camera."""

from . import camera, panel_i18n as i18n, panel_labels, panel_theme as t


def refresh(form, widgets):
    option = form.model.options["third_person_ads"]
    elsewhere = camera.elected_elsewhere()
    if elsewhere and "third_person_ads" in form.pending:
        form.pending.pop("third_person_ads")
        form.shown["third_person_ads"] = option.value
        panel_labels.value(widgets, option, option.value, form.model.language)
        form.report(widgets, "camera_draft_discarded")
    form.ads_blocked = elsewhere or form.shown["third_person"] is not True
    widgets["setting:third_person_ads"].SetIsEnabled(not form.ads_blocked)
    for part in ("row", "description"):
        widgets[f"{part}:third_person_ads"].SetRenderOpacity(t.OPACITY_DISABLED if form.ads_blocked else 1.0)
    _title, description = i18n.option_text(option, form.model.language)
    status = camera.aim_status() if not elsewhere else None
    if status is not None and (status[0] == "cleanup_pending" or not form.ads_blocked and option.value is True):
        reason, english = status
        message = i18n.text(f"ads_{reason}", "FR") if form.model.language == "FR" else english
        description += "\n" + message
    widgets["description:third_person_ads"].SetText(description)


def refuses(values):
    return type(values) is dict and "third_person_ads" in values and camera.elected_elsewhere()
