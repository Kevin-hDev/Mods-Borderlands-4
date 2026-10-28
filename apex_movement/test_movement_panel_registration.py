"""Menu preferences are saved with the same SDK settings file as movement options."""

from movement_test_result import Reporter

result = Reporter("Movement menu language and last page share its SDK settings authority")

import movement_ui_fixture

movement_ui_fixture.install()

from apex_movement import menu, mod, panel_preferences

options = mod.kwargs["options"]
assert options[:len(menu.MENU)] == menu.MENU
assert options[-len(panel_preferences.ALL):] == list(panel_preferences.ALL)
assert {option.identifier for option in panel_preferences.ALL}.isdisjoint(
    {option.identifier for group in menu.MENU for option in group.children})
result.success()
