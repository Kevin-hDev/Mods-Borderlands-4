"""The window greys a row that changes nothing (panel_form.refresh_dependency): the look's rows while the rope is
hidden (menu.DEPENDS_ON), the grapple gun's while the look is classic (menu.ACTIVE_WHEN), from the values the window
shows, saved or not, and wakes them at the click that makes them count."""

import panel_fixture as pf
from apex_grapple import look_settings, panel_form, panel_theme as t, settings

clock = [0]
panel_form.time.perf_counter_ns = lambda: clock[0]
w, form = pf.create()
LOOK = [option.identifier for option in look_settings.ALL]
OURS = [option.identifier for option in look_settings.OURS_ONLY]
# Rows with a rule of their own: the glow's face counts with the glow only, the game rope's colour with the classic
# look only.
OWN = ("glow_face", "game_rope_colour")
COUNTING = [name for name in LOOK if name not in OWN]


def active(name):
    return w[f"setting:{name}"].enabled and w[f"row:{name}"].opacity == w[f"description:{name}"].opacity == 1.0


def greyed(name):
    return (not w[f"setting:{name}"].enabled
            and w[f"row:{name}"].opacity == w[f"description:{name}"].opacity == t.OPACITY_DISABLED)


def click(name):
    w[name].checked = True
    form.poll()


assert settings.show_rope.value is True and look_settings.look.value == look_settings.GRAPPLE_GUN
assert all(active(name) for name in ["show_rope", *COUNTING]), "With the rope shown and our look, every row counts"
assert greyed("glow_face") and greyed("game_rope_colour"), \
    "... but the glow's face without the glow, and the game's rope"
click("setting:rope_look:C")
assert active("glow_face") and greyed("game_rope_colour"), "The glow chosen: its face counts at once"
click("setting:rope_look:A")
assert greyed("glow_face"), "Another rope: its face greys again"

click("setting:show_rope")
assert settings.show_rope.value is True and form.pending == {"show_rope": False}
assert all(greyed(name) for name in LOOK) and active("show_rope"), "The rope hidden, unsaved yet: the look's rows grey"
click("setting:show_rope")
assert not form.pending and all(active(name) for name in COUNTING), "The rope shown again: they wake at once"

click("setting:look:CLASSIC")
assert all(greyed(name) for name in OURS) and active("look") and active("show_rope"), "Classic: the gun's rows grey"
assert active("game_rope_colour"), "Classic: the game rope's colour counts"
clock[0] += t.SAVE_DELAY_NS
form.poll()
assert look_settings.look.value == look_settings.CLASSIC and all(greyed(name) for name in OURS), "... saved, still grey"
click("setting:look:GRAPPLE_GUN")
assert all(active(name) for name in OURS if name not in OWN), "Our look chosen again: they wake at once"

# Opening the window reads the saved values: a classic look opens with the gun's rows grey.
look_settings.look.value = look_settings.CLASSIC
w, form = pf.create()
assert all(greyed(name) for name in OURS) and active("look")
# RESTORE DEFAULTS puts back our look, and its rows count again.
click("restore")
assert look_settings.look.value == look_settings.look.default_value and all(active(name) for name in COUNTING)
click("undo")
assert look_settings.look.value == look_settings.CLASSIC and all(greyed(name) for name in OURS)
print("OK | greyed rows: rope hidden, classic look, unsaved values, woken at once, opening, restore and undo")
