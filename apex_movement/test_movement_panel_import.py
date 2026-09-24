"""The complete pack's window components load without Apex Grapple installed."""

from movement_test_result import Reporter

result = Reporter("standalone Movement panel components import and expose their window actions")

import movement_ui_fixture

movement_ui_fixture.install()

from apex_movement import menu, panel_factory, panel_form, panel_labels, panel_pages, panel_view

assert len(menu.MENU) == 10
assert callable(panel_factory.build)
assert callable(panel_form.PanelForm.poll)
assert callable(panel_labels.apply)
assert callable(panel_pages.settings_page)
assert callable(panel_view.build_view)
assert callable(panel_view.viewport_slot)
result.success()
