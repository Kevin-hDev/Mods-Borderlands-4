"""The window reopens scrolled where it was left: the shown page's scroll box is found, set again while the page is
laid out, read back once, saved at closing only once placed, and a failure never takes the window down."""

import sys
from types import ModuleType, SimpleNamespace as NS

from ui_test_loader import load

events = []
sdk = ModuleType("unrealsdk")
sdk.logging = NS(info=events.append)
sys.modules["unrealsdk"] = sdk
base = ModuleType("mods_base")


class Slider:
    def __init__(self, identifier, value, *args, **kwargs):
        self.identifier, self.value, self.is_hidden = identifier, value, kwargs.get("is_hidden")


base.SliderOption = Slider
sys.modules["mods_base"] = base
scroll_module = load("panel_scroll")
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


class Widget:
    def __init__(self, kind, *children):
        self.Class = NS(Name=kind)
        self.children = list(children)

    def GetChildrenCount(self):
        return len(self.children)

    def GetChildAt(self, index):
        return self.children[index]


class Scroll(Widget):
    def __init__(self, clamp=10_000.0):
        super().__init__("ScrollBox")
        self.offset, self.clamp, self.sets = 0.0, clamp, 0

    def SetScrollOffset(self, value):
        self.sets += 1
        self.offset = min(value, self.clamp)

    def GetScrollOffset(self):
        return self.offset


class Text:
    Class = NS(Name="TextBlock")


def window(scroll):
    """Apex Movement's Options page: a head with its tab buttons, then the scrolling body."""
    page = Widget("VerticalBox", Widget("HorizontalBox", Text(), Text()), Widget("Border", scroll))
    return {"pages": NS(GetActiveWidget=lambda: page)}


class Model:
    def __init__(self, answer=True):
        self.answer, self.saves = answer, []

    def save(self, changes):
        self.saves.append(tuple((option.identifier, value) for option, value in changes))
        for option, value in changes:
            option.value = value
        return self.answer


option = scroll_module.last_scroll
check(option.identifier == "menu_last_scroll" and option.value == 0 and option.is_hidden,
      "A hidden preference, at the top by default")
scroll = Scroll()
check(scroll_module.page_scroll(window(scroll)) is scroll, "The scroll box under a kept head is found")
check(scroll_module.page_scroll({"pages": NS(GetActiveWidget=lambda: Text())}) is None, "No scroll box, none")

option.value = 640
scroll, model = Scroll(), Model()
memory = scroll_module.Memory(model)
widgets = window(scroll)
for _ in range(scroll_module.SETTLE_POLLS):
    memory.restore(widgets)
check(scroll.offset == 640 and scroll.sets == scroll_module.SETTLE_POLLS and not memory.done,
      "The saved place is set again while the page is laid out")
memory.restore(widgets)
check(memory.done and events[-1].endswith("scroll_restored wanted=640 shown=640"), "Then read back once, in the log")
memory.restore(widgets)
check(scroll.sets == scroll_module.SETTLE_POLLS, "Nothing more once placed: the player's own scrolling is left alone")
scroll.offset = 1210.4
memory.remember(widgets)
check(model.saves == [(("menu_last_scroll", 1210),)], "At closing, the page's place is saved in whole pixels")
memory.remember(widgets)
check(len(model.saves) == 1, "An unchanged place is not saved again")

option.value = 640
model = Model()
memory = scroll_module.Memory(model)
memory.restore(widgets)
memory.remember(widgets)
check(not model.saves, "A window closed before its place was set keeps the saved one")

option.value = 0
memory = scroll_module.Memory(Model())
check(memory.done, "At the top, nothing to place")

option.value = float("nan")
check(scroll_module.saved() == 0, "A value edited by hand that is not a number reads as the top")
option.value = 10 ** 9
check(scroll_module.saved() == 0, "A value past the limit reads as the top")

option.value = 900
short = Scroll(clamp=300.0)
memory = scroll_module.Memory(Model())
for _ in range(scroll_module.SETTLE_POLLS + 1):
    memory.restore(window(short))
check(short.offset == 300 and events[-1].endswith("wanted=900 shown=300"), "A shorter page shows its end")

broken = {"pages": NS(GetActiveWidget=lambda: (_ for _ in ()).throw(RuntimeError("gone")))}
memory = scroll_module.Memory(Model())
memory.restore(broken)
check(memory.done and events[-1].endswith("scroll_restore_error=RuntimeError"), "A failure ends the restore, logged")
memory.remember(broken)
check(events[-1].endswith("scroll_save_error=RuntimeError"), "A failure at closing is logged, never raised")

option.value = 0
model = Model(answer=False)
memory = scroll_module.Memory(model)
scroll = Scroll()
scroll.offset = 50.0
memory.remember(window(scroll))
check(events[-1].endswith("scroll_save=failed"), "A refused save is logged")
model = Model(answer=None)
memory = scroll_module.Memory(model)
scroll.offset = 70.0
count = len(events)
memory.remember(window(scroll))
check(len(events) == count, "A save still under way (Apex Movement answers None) is not a failure")
carried = scroll_module.Memory(Model(), wanted=scroll_module.offset(window(scroll)))
check(carried.wanted == 70 and not carried.done, "A redrawn window starts from where the old one is")

for failure in failures:
    print("ECHEC |", failure)
print("RESULTAT:", "OK | scroll memory" if not failures else f"{len(failures)} ECHEC(S)")
raise SystemExit(1 if failures else 0)
