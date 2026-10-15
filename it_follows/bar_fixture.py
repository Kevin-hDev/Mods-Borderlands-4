"""Fake widgets and screen for the tests of the bar (it_follows/bar.py): what the bar is made of and the screen it is
put on, recorded for the tests to read. Fixture(state) puts them in the fake SDK sdk_stubs.install made. Taken from
the fixture of trial 9 (docs/RUN/sondes/bar_fixture.py)."""

import types
from typing import Any


class Font:
    """A font description; with whole points it refuses a float size, as engines before 5.1 do."""

    def __init__(self, fixture: "Fixture") -> None:
        object.__setattr__(self, "fixture", fixture)
        object.__setattr__(self, "Size", 24)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "Size" and self.fixture.whole_points and type(value) is not int:
            raise TypeError("whole points only")
        object.__setattr__(self, name, value)


class Slot:
    def __init__(self, child: Any) -> None:
        self.child, self.padding, self.across, self.down = child, None, None, None

    def SetPadding(self, margin: Any) -> None:
        self.padding = margin

    def SetHorizontalAlignment(self, value: Any) -> None:
        self.across = value

    def SetVerticalAlignment(self, value: Any) -> None:
        self.down = value


class Widget:
    """Any widget the bar makes; a UserWidget's WidgetTree and a WidgetTree's RootWidget are plain fields here."""

    def __init__(self, fixture: "Fixture", kind: str, outer: Any) -> None:
        self.fixture, self.kind, self.outer, self.freed = fixture, kind, outer, False
        self.text = self.font = self.colour = self.brush = self.padding = self.content = self.visibility = None
        self.WidgetTree = self.RootWidget = self.bIsFocusable = None
        self.slots: list[Slot] = []
        self.Font = Font(fixture)
        self.text_fails = self.removal_fails = False

    def SetText(self, text: str) -> None:
        if self.text_fails:
            raise RuntimeError("no text")
        self.text = text

    def SetFont(self, font: Any) -> None:
        self.font = font

    def SetColorAndOpacity(self, colour: Any) -> None:
        self.colour = colour

    def SetBrushColor(self, colour: Any) -> None:
        self.brush = colour

    def SetPadding(self, margin: Any) -> None:
        self.padding = margin

    def SetContent(self, child: Any) -> None:
        self.content = child

    def AddChildToOverlay(self, child: Any) -> Slot:
        self.slots.append(Slot(child))
        return self.slots[-1]

    def SetVisibility(self, value: Any) -> None:
        self.visibility = value

    def RemoveFromParent(self) -> None:
        self.fixture.journal.append(("RemoveFromParent", self.kind))
        if self.removal_fails:
            raise RuntimeError("stuck")
        self.fixture.screen.on.discard(id(self))


class Screen:
    """The screen's widget subsystem: what it was given, what it says is on it, and how it answers."""

    def __init__(self, fixture: "Fixture", name: str) -> None:
        self.fixture, self.Name, self.added, self.on, self.answer = fixture, name, [], set(), True
        self.freed = self.add_fails = False
        self.says = None

    def AddWidget(self, widget: Widget, slot: Any) -> Any:
        self.fixture.journal.append(("AddWidget", widget.kind))
        if self.add_fails:
            raise RuntimeError("no screen")
        self.added.append((widget, slot))
        if self.answer:
            self.on.add(id(widget))
        return self.answer

    def IsWidgetAdded(self, widget: Widget) -> Any:
        if self.says is not None:
            return self.says()
        return id(widget) in self.on


class Fixture:
    def __init__(self, state: dict) -> None:
        self.journal: list[tuple] = []
        self.built: list[Widget] = []
        self.whole_points = self.construct_fails = False
        self.default_screen = Screen(self, "Default__GameViewportSubsystem")
        self.screen = Screen(self, "GameViewportSubsystem_2147482000")
        state["all"]["GameViewportSubsystem"] = [self.default_screen, self.screen]
        for name, members in {"ESlateVisibility": ("HitTestInvisible", "Visible", "Collapsed"),
                              "EHorizontalAlignment": ("HAlign_Left", "HAlign_Fill"),
                              "EVerticalAlignment": ("VAlign_Top", "VAlign_Fill")}.items():
            state["enums"][name] = types.SimpleNamespace(**{member: f"{name}.{member}" for member in members})
        state["construct"] = self.construct

    def construct(self, kind: str, outer: Any) -> Widget:
        if self.construct_fails:
            raise RuntimeError("no such class")
        self.journal.append(("construct", kind))
        self.built.append(Widget(self, kind, outer))
        return self.built[-1]

    def shown(self) -> list[Widget]:
        """The holders the screen holds now, oldest first; a freed one is no longer drawn."""
        return [widget for widget, _ in self.screen.added if id(widget) in self.screen.on and not widget.freed]
