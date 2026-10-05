"""Read the elected runtime's aiming notice; never create or control a camera."""

from . import camera, panel_i18n as i18n, panel_theme as t, panel_camera_ownership


def refresh(form, widgets):
    from . import panel_framing_form
    panel_camera_ownership.refresh(form, widgets)
    panel_framing_form.refresh(form, widgets)
    option = form.model.options["third_person_ads"]
    elsewhere = camera.elected_elsewhere()
    if camera.framing_status() == "camera_outdated":
        # All three menus disclose the same protocol refusal, including hidden camera rows.
        for name in ("group:camera", "group:command_external"):
            if name in widgets:
                widgets[name].SetText(i18n.text("camera_outdated", form.model.language))
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
