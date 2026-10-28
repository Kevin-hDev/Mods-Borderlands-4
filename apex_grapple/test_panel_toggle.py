"""An ENABLED switch that did not take says so in the window, and its cause goes to the log."""

import panel_fixture as pf
from apex_grapple import panel_i18n, panel_toggle, report

w, form = pf.create()
mod, errors = pf.f.mod, pf.f.state["errors"]


def refuse():
    raise RuntimeError("camera start refused")


class Named(RuntimeError):
    notice = "saved"


class Stranger(RuntimeError):
    notice = "no_such_line"


report.reset()
mod.is_enabled = False
mod.enable = refuse
w["enabled"].checked = True
form.poll()
assert not mod.is_enabled
assert form.notice == "toggle_failed"
assert w["notice"].text == panel_i18n.text("toggle_failed", form.model.language)
assert errors[-1] == "[Apex Grapple] could not switch the mod on: RuntimeError: camera start refused"
count = len(errors)
w["enabled"].checked = True
form.poll()
assert form.notice == "toggle_failed" and len(errors) == count  # One line per kind of error, however many clicks.

assert panel_toggle.notice(True, Named("known line")) == "saved"
assert panel_toggle.notice(True, Stranger("unknown line")) == panel_toggle.FAILED
assert panel_toggle.notice(False, OSError("x" * 1000)) == panel_toggle.FAILED
assert errors[-1].startswith("[Apex Grapple] could not switch the mod off: OSError: xxx") and len(errors[-1]) < 300
assert panel_i18n.text("toggle_failed", "EN") != panel_i18n.text("toggle_failed", "FR")

del mod.enable
w["enabled"].checked = True
form.poll()
assert mod.is_enabled and form.notice == "saved"
print("OK | a switch that did not take: its own line in the window, its cause once in the log")
