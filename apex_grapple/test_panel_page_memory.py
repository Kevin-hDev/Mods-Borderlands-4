"""Reopening restores the last settings tab, without touching gameplay or binding drafts."""

import json
import panel_fixture as pf
from apex_grapple import panel_theme as t, settings

w, form = pf.create()
before = tuple(option.value for option in settings.ALL)
w["nav:release"].checked = True
form.poll()
assert form.page == 2
w["close"].checked = True
assert form.poll()
saved = pf.f.mod.saved
w, form = pf.create()
assert form.page == 2 and w["pages"].index == 2, "Letting go must survive reopening"
assert pf.f.mod.saved == saved, "Reopening must not rewrite settings"

from apex_grapple import panel_preferences as preferences, menu

assert preferences.last_page in menu.MENU and preferences.last_page.is_hidden
assert preferences.last_page.mod is pf.f.mod
for index, page in enumerate(t.PAGES):
    w[f"nav:{page}"].checked = True
    form.poll()
    assert preferences.last_page.value == page
    w["close"].checked = True
    assert form.poll()
    w, form = pf.create()
    assert form.page == index and w["pages"].index == index
assert tuple(option.value for option in settings.ALL) == before

# A stored page is part of the SDK's registered options, not a session-only global.
stored = json.dumps({option.identifier: option.value for option in menu.MENU if hasattr(option, "value")})
preferences.last_page.value = preferences.last_page.default_value
preferences.last_page.value = json.loads(stored)[preferences.last_page.identifier]
w, form = pf.create()
assert form.page == 3 and not form.selecting()
assert form.model.change_language("FR")
assert form.model.restore() and form.model.undo()
assert form.model.page == "controls"

saved = pf.f.mod.saved
for invalid in ("unknown", "Letting go", "", None, 2):
    assert not form.model.change_page(invalid)
assert pf.f.mod.saved == saved
assert form.model.change_page("controls") and pf.f.mod.saved == saved
pf.f.mod.fail_save = True
w["nav:release"].checked = True
form.poll()
assert form.page == 3 and preferences.last_page.value == "controls"
assert w["pages"].index == 3 and "Échec" in w["notice"].text
pf.f.mod.fail_save = False
preferences.last_page.value = "removed_page"
w, form = pf.create()
assert form.page == 0 and w["pages"].index == 0
print("OK | saved tab, reopening, SDK option round-trip, reset preservation and failure rollback")
