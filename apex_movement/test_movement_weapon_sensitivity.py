"""SENSITIVITY's weapon-type rows: the same bars as the rest of the window, folded under their switch, faded outside
third person and while another camera mod is in charge; the sniper rifle's optic zooms fold under their own switch,
inside the weapon rows; the names match the runtime's options."""

from movement_test_result import Reporter

result = Reporter("Weapon-type sensitivity rows are bars, fold under their switch and fade outside third person")

from types import SimpleNamespace as NS

import movement_ui_fixture

movement_ui_fixture.install()

from movement_ui_fixture import Widget

from apex_movement import camera_settings, panel_shortcut, panel_widgets
from apex_movement import panel_weapon_sensitivity as weapons

panel_widgets.enum = lambda name, member: member

sensitivity = camera_settings.sensitivity
assert sensitivity.per_weapon.identifier == weapons.SWITCH and sensitivity.per_optic.identifier == weapons.OPTICS
assert all(option.identifier.startswith(weapons.PREFIX) for option in sensitivity.weapons)
assert all(option.identifier.startswith(weapons.OPTIC_PREFIX) for option in sensitivity.optics)
assert not any(option.identifier.startswith(weapons.OPTIC_PREFIX) for option in sensitivity.weapons)
plain, rows = weapons.split(sensitivity.options)
assert plain == [sensitivity.look, sensitivity.aim, sensitivity.per_weapon]
assert rows == [*sensitivity.weapons, sensitivity.per_optic, *sensitivity.optics]

# Built with the window's own setting rows, so each type is a bar; its description stays hidden.
built = []
real_rows = panel_shortcut.rows
panel_shortcut.rows = lambda card, options, widgets, template: (
    built.append(list(options)),
    widgets.update({f"description:{option.identifier}": Widget() for option in options}))
widgets = {}
weapons.w.new = lambda kind, owner: Widget()
weapons.w.column = lambda *_args, **_kwargs: None
weapons.build(Widget(), rows, widgets, None)
panel_shortcut.rows = real_rows
# The weapon types in their box, then the per-optic switch outside it, then the zooms in their own box: the two
# switches are independent (Kevin, 2026-10-10).
assert built == [list(sensitivity.weapons), [sensitivity.per_optic], list(sensitivity.optics)]
assert widgets["weapons:rows"].visibility == "Collapsed" and widgets["weapons:optics"].visibility == "Collapsed"
assert all(widgets[f"description:{option.identifier}"].visibility == "Collapsed" for option in rows
           if option is not sensitivity.per_optic)
assert not hasattr(widgets[f"description:{weapons.OPTICS}"], "visibility")

form = NS(shown={"third_person": True, weapons.SWITCH: False, weapons.OPTICS: False}, model=NS(camera_elsewhere=False))
weapons.poll(form, widgets, 0)
assert widgets["weapons:rows"].visibility == "Collapsed"
form.shown[weapons.SWITCH] = True
weapons.poll(form, widgets, 0)
assert widgets["weapons:rows"].visibility == "Visible" and widgets["weapons:rows"].enabled is True
assert widgets["weapons:rows"].opacity == 1.0
# One sniper value until the per-optic switch unfolds the zooms (Kevin, 2026-10-09).
assert widgets["weapons:optics"].visibility == "Collapsed"
form.shown[weapons.OPTICS] = True
weapons.poll(form, widgets, 0)
assert widgets["weapons:optics"].visibility == "Visible"
# The zooms stay open with the weapon types folded.
form.shown[weapons.SWITCH] = False
weapons.poll(form, widgets, 0)
assert widgets["weapons:rows"].visibility == "Collapsed" and widgets["weapons:optics"].visibility == "Visible"
form.shown["third_person"] = False
weapons.poll(form, widgets, 0)
assert all(widgets[name].enabled is False and widgets[name].opacity < 1.0
           for name in ("weapons:rows", "weapons:optics"))
form.shown["third_person"], form.model.camera_elsewhere = True, True
weapons.poll(form, widgets, 0)
assert widgets["weapons:rows"].enabled is False
result.success()
