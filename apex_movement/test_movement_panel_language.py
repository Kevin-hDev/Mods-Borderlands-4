"""Every movement and setting in the new window has a French label."""

from movement_test_result import Reporter

result = Reporter("full Movement menu has English and French labels and descriptions")

import movement_ui_fixture

movement_ui_fixture.install()

from apex_movement import camera_settings, menu, panel_i18n, panel_theme

assert len(panel_theme.PAGES) == 11 and panel_theme.PAGES[-1] == "commands"
for group, page in zip(menu.MENU, panel_theme.PAGES[:-1]):
    assert panel_i18n.text(page, "FR")
    assert panel_i18n.group_text(group, page, "FR")
    for option in group.children:
        title, description = panel_i18n.option_text(option, "FR")
        assert title and description
        assert title != option.identifier
assert panel_i18n.text("saved", "FR") != panel_i18n.text("saved", "EN")
assert panel_i18n.text("restore", "unknown") == panel_i18n.text("restore", "EN")
for key in ("options", "options_desc", "camera", "camera_desc", "language", "menu_language",
            "change_key", "press_key", "no_key", "right", "left", "commands", "keyboard", "controller",
            "command_third_person", "command_third_person_desc", "command_shoulder", "command_shoulder_desc",
            "command_orbit", "command_orbit_desc", "command_tools", "command_tools_desc", "commands_reset"):
    assert panel_i18n.text(key, "FR") and panel_i18n.text(key, "EN")
# Camera settings keep their own translations; shortcuts are described on the Commands page.
for option in (camera_settings.third_person, camera_settings.shoulder_left,
               camera_settings.orbit, camera_settings.custom_fov, camera_settings.fov):
    title, description = panel_i18n.option_text(option, "FR")
    assert title and description and title != option.identifier
result.success()
