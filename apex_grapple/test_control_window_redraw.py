"""A theme change draws the open window again: new window first, old one out, never two left, old kept on failure."""

import sys
from types import ModuleType, SimpleNamespace as NS

from ui_test_loader import PACKAGE, load

events = []
sdk = ModuleType("unrealsdk")
sdk.logging = NS(info=events.append)
sdk.find_enum = lambda name: NS(Default=0, DoNotLock=0)
sdk.unreal = NS(WeakPointer=lambda item: (lambda: item))
sdk.hooks = NS(remove_hook=lambda *args: None, has_hook=lambda *args: False, Type=NS(POST=1))
sdk.commands = NS(remove_command=lambda *args: None, has_command=lambda *args: False)
sys.modules["unrealsdk"] = sdk
base = ModuleType("mods_base")
base.get_pc = lambda **kwargs: None
sys.modules["mods_base"] = base
import ui_clock_fixture
ui_clock_fixture.install(sdk)
theme = load("panel_theme")
factory = ModuleType(f"{PACKAGE}.panel_factory")
sys.modules[f"{PACKAGE}.panel_factory"] = factory
modal = ModuleType(f"{PACKAGE}.panel_modal")
sys.modules[f"{PACKAGE}.panel_modal"] = modal
modal.viewport_slot = lambda: "slot"
redraw_module = load("control_window_redraw")
window = load("control_window")
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


class Root:
    def __init__(self, name, fail=False):
        self.name, self.fail = name, fail

    def RemoveFromParent(self):
        events.append(f"remove:{self.name}")
        if self.fail:
            raise RuntimeError("refused")


def setup(build_fails=False, accept=True, old_fails=False):
    """A session whose old window was drawn in DARK; the click saved LIGHT, which the factory draws."""
    events.clear()
    theme.use("DARK")
    old_root, new_root = Root("old", fail=old_fails), Root("new")
    reports = []
    old_form = NS(model="the model", redraw=True, report=lambda widgets, key: reports.append(key),
                  resolve=lambda: {}, focus=lambda: "old focus")
    new_form = NS(model="the model", redraw=False, focus=lambda: "new focus")

    def build(pc, bindings, return_to_menu, model):
        events.append(("build", model, return_to_menu))
        theme.use("LIGHT")
        if build_fails:
            raise ValueError("broken")
        return new_root, new_form

    factory.build = build
    viewport = NS(AddWidget=lambda root, slot: events.append(f"add:{root.name}") or accept)
    library = NS(SetInputMode_UIOnlyEx=lambda *args: events.append("ui_input"))
    pc = NS(bShowMouseCursor=False, CurrentMouseCursor=None)
    session = NS(form=old_form, root=lambda: old_root, pc=lambda: pc, bindings="bindings", return_to_menu=True,
                 viewport=lambda: viewport, selector=old_form.focus,
                 focus=lambda: events.append("focus"))
    return session, old_form, new_form, new_root, reports


session, old_form, new_form, new_root, reports = setup()
check(redraw_module.redraw(session) is True, "A drawn window takes the old one's place")
check(events[:3] == [("build", "the model", True), "add:new", "remove:old"],
      "Built around the same model, shown, and only then the old one removed")
check(session.root() is new_root and session.form is new_form and session.selector is new_form.focus,
      "The session now closes, polls and focuses the new window")
check("focus" in events and old_form.redraw is False and not reports, "Focus returns to the new window")
check(theme.current() == "LIGHT" and any("redrawn=true theme=LIGHT" in str(line) for line in events),
      "The log says which theme the window was drawn again in")

for case, arguments, removed in (("build", {"build_fails": True}, []), ("viewport", {"accept": False}, []),
                                 ("swap", {"old_fails": True}, ["remove:old", "remove:new"])):
    session, old_form, new_form, new_root, reports = setup(**arguments)
    check(redraw_module.redraw(session) is False, f"{case}: a window that cannot be drawn reports it")
    check([event for event in events if str(event).startswith("remove:")] == removed,
          f"{case}: the old window stays, and a new one shown must not stay beside it")
    check(session.form is old_form and session.root().name == "old", f"{case}: the session keeps the old window")
    check(theme.current() == "DARK", f"{case}: the old window repaints in the colours it was drawn in")
    check(reports == ["theme_later"], f"{case}: it says the theme will show at the next opening")
    check(any("redraw_error=" in str(line) for line in events), f"{case}: the cause is in the log")

# The session asks for the drawing after the form's poll, and never instead of a close.
calls, closed = [], []
window.redraw = lambda item: calls.append(item)
player = NS(CurrentMouseCursor=0, bShowMouseCursor=True, OakCharacter=None)
for closes, redraw, expected in ((False, True, 1), (False, False, 0), (True, True, 0)):
    calls.clear()
    form = NS(poll=lambda closes=closes: closes, redraw=redraw, selecting=lambda: False,
              widgets={"first": lambda: NS()}, focus=lambda: NS())
    item = window.Session(lambda: player, lambda: NS(), lambda: NS(), False, form, NS(ready=lambda: True),
                          lambda: None)
    item.same_context = lambda pc: True
    item.close = closed.append
    item.poll(10**12)
    check(len(calls) == expected, f"poll with close={closes} redraw={redraw}: {expected} redrawing expected")
check(closed == ["button"], "Close still closes, without drawing a window first")

for message in failures:
    print("FAILED |", message)
print(f"RESULTAT: {'OK' if not failures else 'ECHEC'} | redraw: same model, new before old, rollback on each failure")
sys.exit(1 if failures else 0)
