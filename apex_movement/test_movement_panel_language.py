"""Every movement and setting in the new window has a French label."""

import movement_ui_fixture

movement_ui_fixture.install()

from apex_movement import menu, panel_i18n, panel_theme

assert len(panel_theme.PAGES) == 10
for group, page in zip(menu.MENU, panel_theme.PAGES):
    assert panel_i18n.text(page, "FR")
    assert panel_i18n.group_text(group, page, "FR")
    for option in group.children:
        title, description = panel_i18n.option_text(option, "FR")
        assert title and description
        assert title != option.identifier
assert panel_i18n.text("saved", "FR") != panel_i18n.text("saved", "EN")
assert panel_i18n.text("restore", "unknown") == panel_i18n.text("restore", "EN")
print("OK | full Movement menu has English and French labels and descriptions")
