"""Navigation and language changes preserve pending edits and completed bindings."""

import panel_fixture as pf
from apex_grapple import panel_form, panel_theme, settings, panel_preferences, panel_fr, panel_en

assert panel_fr.TEXT.keys() == panel_en.TEXT.keys()
assert set(panel_fr.OPTIONS) == {option.identifier for option in settings.ALL}
clock = [0]
panel_form.time.perf_counter_ns = lambda: clock[0]
w, form = pf.create()
count = pf.f.mod.saved
for _ in range(5):
    form.poll()
assert pf.f.mod.saved == count  # Opening/polling never rewrites existing settings.
w["setting:pull_strength"].value = 2.2
form.poll()
assert settings.pull_strength.value == 1.7 and pf.f.mod.saved == count
clock[0] += panel_theme.SAVE_DELAY_NS
form.poll()
assert settings.pull_strength.value == 2.2 and pf.f.mod.saved == count + 1
w["setting:ground_grace"].value = 0.349999994
for _ in range(10):
    clock[0] += panel_theme.SAVE_DELAY_NS
    form.poll()
assert pf.f.mod.saved == count + 1  # No float32 noise write loop.
w["setting:pull_strength"].value = 2.6
w["FR"].checked = True
form.poll()
assert settings.pull_strength.value == 2.6 and panel_preferences.language.value == "FR"
assert w["close_label"].text == "FERMER"
assert w["label:grapple_range"].text == "PORTÉE"
w["nav:controls"].checked = True
form.poll()
assert w["pages"].index == 3
w["two"].checked = True
form.poll()
assert w["second"].enabled and "deux touches" in w["status"].text
w["first"].SelectedKey.Key.KeyName = "V"
form.poll()
assert pf.f.config.DEVICES[0].selection() is None
w["second"].SelectedKey.Key.KeyName = "G"
form.poll()
assert pf.f.config.DEVICES[0].selection() == ("V", "G")
assert w["status"].text == "Commandes enregistrées."
w["enabled"].checked = True
form.poll()
assert pf.f.mod.is_enabled and form.bindings.ready()
w["enabled"].checked = True
form.poll()
assert not pf.f.mod.is_enabled and form.bindings.ready()
w["setting:pull_strength"].value = 3.0
pf.f.mod.fail_save = True
w["close"].checked = True
assert not form.poll()
assert settings.pull_strength.value == 2.6 and w["setting:pull_strength"].value == 2.6
assert "Échec" in w["notice"].text
pf.f.mod.fail_save = False
w["restore"].checked = True
form.poll()
assert settings.pull_strength.value == 1.7 and w["undo"].enabled
assert panel_preferences.language.value == "FR"
w["undo"].checked = True
form.poll()
assert settings.pull_strength.value == 2.6 and not w["undo"].enabled
w["close"].checked = True
assert form.poll()
print("OK | full menu: no opening writes, delayed save, navigation, FR, chords, failures, reset undo")
