"""Every movement and setting in the new window has a French label."""

from movement_test_result import Reporter

result = Reporter("full Movement menu has English and French labels and descriptions")

import movement_ui_fixture

movement_ui_fixture.install()

from apex_movement import camera_settings, menu, panel_i18n, panel_theme

# Three Options tabs close the list: their pages have no sidebar button (2026-10-06).
assert len(panel_theme.PAGES) == 17 and panel_theme.PAGES[-7:] == ("commands", "language", "dynamic_camera", "shoulder",
                                                                   "aiming", "sensitivity", "omni_direction")
for group, page in zip(menu.MENU, panel_theme.PAGES[:-3]):
    assert panel_i18n.text(page, "FR")
    assert panel_i18n.group_text(group, page, "FR")
    for option in group.children:
        title, description = panel_i18n.option_text(option, "FR")
        assert title and description
        assert title != option.identifier
assert panel_i18n.text("saved", "FR") != panel_i18n.text("saved", "EN")
assert panel_i18n.text("restore", "unknown") == panel_i18n.text("restore", "EN")
for key in ("options", "options_desc_menu", "camera_tab_desc", "commands_tab_desc", "languages",
            "camera", "camera_desc", "language", "menu_language",
            "change_key", "press_key", "no_key", "right", "left", "commands", "keyboard", "controller",
            "command_third_person", "command_third_person_desc", "command_shoulder", "command_shoulder_desc",
            "command_orbit", "command_orbit_desc", "command_tools", "command_tools_desc", "commands_reset",
            "dynamic_camera", "dynamic_camera_tab_desc", "dynamic_camera_page", "dynamic_fov", "dynamic_fov_desc",
            "dynamic_framing", "dynamic_framing_desc", "dynamic_motion", "dynamic_motion_desc",
            "omni_direction", "omni_direction_tab_desc", "omni_direction_page", "omni_full_turn", "omni_half_turn",
            "omni_dash", "omni_slide", *(f"{part}omni_{row}{end}" for row in ("body", "angle", "crouch")
                                         for part, end in (("popup_", ""), ("popup_", "_desc"), ("", "_help_text")))):
    assert panel_i18n.text(key, "FR") and panel_i18n.text(key, "EN")
assert panel_i18n.text("omni_slide", "FR") == "GLISSADE" and panel_i18n.text("omni_slide", "EN") == "SLIDE"
# Camera settings keep their own translations; shortcuts are described on the Commands page.
for option in (camera_settings.third_person, camera_settings.shoulder_left, camera_settings.orbit,
               camera_settings.custom_fov, camera_settings.fov, *camera_settings.DYNAMIC,
               *camera_settings.omni.options):
    title, description = panel_i18n.option_text(option, "FR")
    assert title and description and title != option.identifier
result.success()
