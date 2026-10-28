"""Tests the bar: the screen subsystem in play found past the class default; the bar built under the player's
controller, rooted in a UserWidget's WidgetTree, which takes no focus, styled, put in the top left corner of a layer
over the whole screen that takes no click, added with each call written down before it is made; a font in whole
points; what keeps it off the screen; where it is, the screen's silence never taken for "off"; kept each second,
built again once taken off or freed; its words written again; and its removal."""

import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402
import bar_fixture  # noqa: E402

state = sdk_stubs.install()
fixture = bar_fixture.Fixture(state)
journal, built, screen = fixture.journal, fixture.built, fixture.screen

from it_follows import bar as bar_module  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def announce(call: str, log: bool = True, **fields: object) -> None:
    journal.append(("announce", call, fields))


pc = types.SimpleNamespace(Name="OakPlayerController_0")


def rgba(colour: object) -> tuple:
    return (colour.R, colour.G, colour.B, colour.A)


def margin(value: object) -> tuple:
    return (value.Left, value.Top, value.Right, value.Bottom)


try:
    check("the screen in play is found past the class default", bar_module.viewport() is screen)
    state["all"]["GameViewportSubsystem"] = [fixture.default_screen]
    check("no screen but the class default: none", bar_module.viewport() is None)
    BARLOW = object()
    asked_under: list = []


    def window_fonts(outer: object) -> dict:
        asked_under.append(outer)
        return {"title": object(), "body": BARLOW}


    bar = bar_module.Bar(announce, fonts=window_fonts)
    check("with no screen, the bar is kept off and nothing is built",
          bar.show(pc, "x") == "no_viewport" and not built and not journal)
    state["all"]["GameViewportSubsystem"] = [fixture.default_screen, screen]

    check("before any show, the bar is gone", bar.where() == "gone")
    outcome = bar.show(pc, "KILLS 0   DEATHS 0   00:00")
    holder, tree, layer, band, words = built
    check("the bar is shown", outcome == "shown")
    check("each call to the game is written down before it is made",
          [entry[:2] for entry in journal] == [("announce", "construct_object"), ("construct", "UserWidget"),
                                              ("construct", "WidgetTree"), ("construct", "Overlay"),
                                              ("construct", "Border"), ("construct", "TextBlock"),
                                              ("announce", "construct_object"), ("announce", "AddWidget"),
                                              ("AddWidget", "UserWidget")])
    check("a UserWidget under the controller holds the tree, the layer and its root",
          holder.outer is pc and tree.outer is holder and layer.outer is holder and holder.WidgetTree is tree
          and tree.RootWidget is layer and holder.bIsFocusable is False)
    check("the band under the layer, the words under the band", band.outer is layer and words.outer is band)
    check("the words, white, in 19 points", words.text == "KILLS 0   DEATHS 0   00:00" and words.font is words.Font
          and words.Font.Size == 19.0 and type(words.Font.Size) is float
          and rgba(words.colour.SpecifiedColor) == (1.0, 1.0, 1.0, 1.0))
    check("the window's Barlow, bold, built under the bar's holder, in place of the engine's font (trial 202)",
          words.Font.FontObject is BARLOW and words.Font.TypefaceFontName == "ExtraBold"
          and asked_under == [holder])
    check("the band, dark and see-through, holds the words with 6 px above and 12 px aside",
          rgba(band.brush) == (0.0, 0.0, 0.0, 0.55) and margin(band.padding) == (12.0, 6.0, 12.0, 6.0)
          and band.content is words)
    corner = layer.slots[0] if len(layer.slots) == 1 else None
    check("the band sits in the top left corner, 16 px from the edges, at its own size",
          corner is not None and corner.child is band and margin(corner.padding) == (16.0, 16.0, 0.0, 0.0)
          and corner.across == "EHorizontalAlignment.HAlign_Left" and corner.down == "EVerticalAlignment.VAlign_Top")
    check("neither the holder nor the layer takes a click", layer.visibility == "ESlateVisibility.HitTestInvisible"
          and holder.visibility == "ESlateVisibility.HitTestInvisible")
    given, slot = screen.added[0]
    check("the holder goes over the whole screen, under a mod's window, off with its world",
          given is holder and slot.ZOrder == 5000 and slot.bAutoRemoveOnWorldRemoved is True
          and (slot.Anchors.Minimum.X, slot.Anchors.Minimum.Y, slot.Anchors.Maximum.X, slot.Anchors.Maximum.Y)
          == (0.0, 0.0, 1.0, 1.0) and (slot.Alignment.X, slot.Alignment.Y) == (0.0, 0.0)
          and margin(slot.Offsets) == (0.0, 0.0, 0.0, 0.0))
    check("the holder's order is written down with its call", journal[7][2] == {"zorder": 5000}
          and journal[6][2] == {"widgets": "Font"})

    check("on the screen, the bar is on", bar.where() == "on")
    check("kept while on, its words are written again", bar.keep(pc, "KILLS 0   DEATHS 1   00:09") == "written"
          and words.text.endswith("00:09") and len(built) == 5)
    screen.on.clear()
    check("taken off by the game, the bar is off", bar.where() == "off")
    screen.says = lambda: (True,)
    check("an answer that is no bool is unknown, never off", bar.where() == "unknown")
    check("kept while unknown, it is written, never built twice", bar.keep(pc, "x") == "written" and len(built) == 5)
    screen.says = lambda: (_ for _ in ()).throw(RuntimeError("unreadable"))
    check("an answer that raises is unknown", bar.where() == "unknown")
    screen.says = None
    screen.freed = True
    check("a screen freed is unknown", bar.where() == "unknown")
    screen.freed = False
    check("kept while off, it is built again under the controller", bar.keep(pc, "y") == "shown"
          and len(built) == 10 and built[5].outer is pc and fixture.shown() == [built[5]] and built[9].text == "y")
    built[5].freed = True
    check("kept once freed, it is built again", bar.where() == "gone" and bar.keep(pc, "z") == "shown"
          and fixture.shown() == [built[10]])
    built[14].text_fails = True
    check("words that refuse their text say so", bar.keep(pc, "w") == "write_failed")
    built[14].freed = True
    check("words freed are not written", bar.write("x") is False)

    journal.clear()
    current = built[10]
    check("the bar is taken off the screen, announced first",
          bar.remove() == "removed" and journal == [("announce", "RemoveFromParent", {}),
                                                     ("RemoveFromParent", "UserWidget")])
    check("once removed it is off the screen and gone, and removing it again touches nothing",
          id(current) not in screen.on and bar.where() == "gone" and bar.remove() == "gone" and len(journal) == 2)

    fixture.whole_points = True
    built.clear()
    other = bar_module.Bar(announce, fonts=lambda _outer: {})
    check("an engine counting whole points gets 19", other.show(pc, "x") == "shown"
          and built[4].Font.Size == 19 and type(built[4].Font.Size) is int)
    fixture.whole_points = False
    check("no font of the window: the engine's left", getattr(built[4].Font, "FontObject", None) is not BARLOW)
    built[0].removal_fails = True
    check("a removal that raises says why", other.remove() == "failed:RuntimeError")

    screen.answer = (True,)
    odd = bar_module.Bar(announce, fonts=lambda _outer: {})
    check("an answer of another shape that says yes is taken for shown", odd.show(pc, "x") == "shown")
    screen.answer = False
    refused = bar_module.Bar(announce, fonts=lambda _outer: {})
    check("a screen refusing the bar keeps it off, and nothing is kept", refused.show(pc, "x") == "refused"
          and refused.where() == "gone")
    screen.answer, screen.add_fails = True, True
    check("a screen raising keeps it off, and says at which step", refused.show(pc, "x") == "add_failed:RuntimeError")
    screen.add_fails, fixture.construct_fails = False, True
    check("a widget that cannot be made keeps it off", refused.show(pc, "x") == "build_failed:RuntimeError")
    fixture.construct_fails = False
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
