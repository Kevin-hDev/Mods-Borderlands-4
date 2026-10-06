"""Operate real camera controls: duration survives close, smoothing-off and restoration."""
import panel_fixture as f
from third_person_fov import settings

_, widgets, form = f.build()
assert widgets['setting:shoulder_seconds'].calls['SetIsEnabled'] == (True,)
f.click(form, widgets, 'setting:third_person')
assert widgets['setting:shoulder_seconds'].calls['SetIsEnabled'] == (True,)
widgets['setting:shoulder_seconds'].value = 0.75
assert f.click(form, widgets, 'close')
_, widgets, form = f.build()
assert widgets['setting:shoulder_seconds'].value == 0.75
f.click(form, widgets, 'setting:shoulder_smooth')
assert widgets['setting:shoulder_seconds'].calls['SetIsEnabled'] == (True,)
f.click(form, widgets, 'setting:orbit_smooth')
assert widgets['setting:shoulder_seconds'].calls['SetIsEnabled'] == (False,)
assert f.click(form, widgets, 'close')
_, widgets, form = f.build()
assert not settings.shoulder_transition.smooth.value
assert not settings.shoulder_transition.orbit_smooth.value
assert settings.shoulder_transition.duration.value == 0.75
assert settings.shoulder_transition.seconds() == 0
assert settings.shoulder_transition.orbit_seconds() == 0
f.click(form, widgets, 'setting:shoulder_smooth')
assert widgets['setting:shoulder_seconds'].calls['SetIsEnabled'] == (True,)
assert f.click(form, widgets, 'close')
assert settings.shoulder_transition.seconds() == 0.75
_, widgets, form = f.build()
f.click(form, widgets, 'restore')
assert settings.shoulder_transition.smooth.value
assert settings.shoulder_transition.orbit_smooth.value
assert settings.shoulder_transition.seconds() == 0.2
f.click(form, widgets, 'undo')
assert settings.shoulder_transition.seconds() == 0.75
print('RESULTAT: OK - saved shoulder duration, greyed controls and Restore/Undo')
