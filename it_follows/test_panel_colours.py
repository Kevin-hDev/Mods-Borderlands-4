"""Tests the colour profile's line and its preview card in It Follows' window (panel_colours.py and its wiring), every
module of the window as it is but the session's start: one line on the OPTIONS page, COLOR PROFILE and one help
sentence, off, the profiles and PREVIEW hidden, no row of the profile's own; switched on, the three profiles and
PREVIEW on the switch's line before anything is saved, Profile 2 lit; PREVIEW saving what was clicked, then hiding the
window and showing the card alone, the keyboard in it; a profile of the card written at once and lit; BACK showing the
window again on the OPTIONS page, the keyboard back on it; the card hidden at a new opening; in French and Chinese."""

import pathlib
import sys
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import panel_fixture  # noqa: E402

panel_fixture.install()

import it_follows  # noqa: E402
from it_follows import game_pause, options, panel_assets, panel_colours as colours_panel, panel_fonts  # noqa: E402
from it_follows import panel_follows, panel_form, panel_model, panel_theme as t, panel_view, panel_widgets as w  # noqa
from it_follows import updates, welcome  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


panel_assets.texture = lambda _world, name=panel_assets.AVATAR: SimpleNamespace(name=name)
panel_fonts.build = lambda _root: {"title": object(), "body": object()}
game_pause.watch = lambda: None
welcome.seen.value = welcome.EDITION
updates.seen.value = it_follows.__version__
state["pc"] = SimpleNamespace(OakCharacter=None)
mod = it_follows.mod
model = panel_model.Model(mod)
ON, OFF = w.linear(t.COLOR_GOLD), w.linear(t.COLOR_OFF)


def window():
    _root, made = panel_view.build_view(object(), model)
    made["colour_corner"].HasFocusedDescendants = lambda: False
    return made, panel_form.PanelForm({name: (lambda item=item: item) for name, item in made.items()}, model)


def press(name: str):
    widgets[name].SetIsChecked(True)
    return form.poll()


def text(name: str) -> str:
    return panel_fixture.text(widgets, name)


def shown(name: str) -> bool:
    return panel_fixture.visible(widgets, name)


def lit(name: str) -> bool:
    return widgets[f"{name}_fill"].calls["SetBrushColor"] == (ON,)


def focused(name: str) -> bool:
    return "SetKeyboardFocus" in widgets[name].calls


def inside(child: object, parent: object) -> bool:
    """Whether child is drawn somewhere under parent."""
    return child is parent or any(inside(child, item) for item in getattr(parent, "children", ()))


try:
    widgets, form = window()
    # The game holds the window's widgets by weak pointers: one placed nowhere is collected, and the window then
    # closes on its next turn (trial 120).
    check("every widget the window names is placed, in the window or in the card",
          [name for name, item in widgets.items() if not inside(item, widgets[colours_panel.MENU])
           and not inside(item, widgets[colours_panel.CORNER])] == [])
    press(f"nav:{panel_follows.OPTIONS}")
    line = widgets["row:saturated_colours"]
    check("one line on the OPTIONS page: COLOR PROFILE, one help sentence, off",
          text("label:saturated_colours") == "COLOR PROFILE"
          and text("description:saturated_colours") == "Brighter colors over the whole game."
          and text("setting:saturated_colours_label") == "OFF")
    check("the profiles and PREVIEW on the switch's line, hidden while off",
          inside(widgets["setting:colour_profile"], line) and inside(widgets[colours_panel.PREVIEW], line)
          and not shown(colours_panel.EXTRAS))
    check("no row of the profile's own; its label and help on the line, collapsed, so the engine keeps them",
          "row:colour_profile" not in widgets
          and all(inside(widgets[name], line) and not shown(name)
                  for name in ("label:colour_profile", "description:colour_profile")))
    press("setting:saturated_colours")
    check("switched on: the three profiles and PREVIEW shown before anything is saved, Profile 2 lit",
          shown(colours_panel.EXTRAS) and options.colours.value is False
          and [text(f"setting:colour_profile:{p}_label") for p in options.COLOUR_PROFILES]
          == ["PROFILE 1", "PROFILE 2", "PROFILE 3"] and text(f"{colours_panel.PREVIEW}_label") == "PREVIEW")
    press("setting:colour_profile:Profile 3")
    check("PREVIEW hidden, the card hidden, until asked", not shown(colours_panel.CORNER)
          and not colours_panel.previewing(form))
    press(colours_panel.PREVIEW)
    check("PREVIEW: what was clicked saved, the window hidden, the card alone, the keyboard in it",
          options.colours.value is True and options.colour_profile.value == "Profile 3"
          and widgets[colours_panel.MENU].calls["SetVisibility"] == ("ESlateVisibility.Collapsed",)
          and shown(colours_panel.CORNER) and focused("colour_card:Profile 3"))
    check("the card: the row's name, the three profiles, the one chosen lit, BACK",
          text(f"heading:{colours_panel.CARD}") == "COLOR PROFILE"
          and [text(f"colour_card:{p}_label") for p in options.COLOUR_PROFILES] == ["PROFILE 1", "PROFILE 2",
                                                                                     "PROFILE 3"]
          and lit("colour_card:Profile 3") and not lit("colour_card:Profile 1")
          and text(f"{colours_panel.BACK}_label") == "BACK")
    press("colour_card:Profile 1")
    check("a profile of the card written at once and lit", options.colour_profile.value == "Profile 1"
          and lit("colour_card:Profile 1") and not lit("colour_card:Profile 3") and colours_panel.previewing(form))
    widgets["colour_card:Profile 1"].calls.pop("SetKeyboardFocus", None)
    form.poll()
    check("the keyboard kept in the card", focused("colour_card:Profile 1"))
    widgets["focus"].calls.pop("SetKeyboardFocus", None)
    press(colours_panel.BACK)
    check("BACK: the window again on the OPTIONS page, the card hidden, the keyboard back on the window",
          widgets[colours_panel.MENU].calls["SetVisibility"] == ("ESlateVisibility.Visible",)
          and not shown(colours_panel.CORNER) and not colours_panel.previewing(form) and focused("focus")
          and form.page == model.pages.index(panel_follows.OPTIONS)
          and text("setting:colour_profile:Profile 1_label") == "PROFILE 1")
    press(colours_panel.PREVIEW)
    widgets, form = window()
    check("a new opening: the card hidden, the window shown", not shown(colours_panel.CORNER)
          and not colours_panel.previewing(form) and shown(colours_panel.EXTRAS))

    press("setting:saturated_colours")
    form.flush(widgets)
    press(colours_panel.PREVIEW)
    check("switched off: PREVIEW opens no card", not shown(colours_panel.CORNER) and options.colours.value is False)

    press("setting:saturated_colours")
    check("French chosen", press("FR") is False and model.language == "FR")
    press(colours_panel.PREVIEW)
    check("in French: the line, PREVIEW, the profiles and BACK in French",
          text("label:saturated_colours") == "PROFIL DE COULEURS"
          and text("description:saturated_colours") == "Des couleurs plus vives dans tout le jeu."
          and text(f"{colours_panel.PREVIEW}_label") == "APERÇU" and text("colour_card:Profile 2_label") == "PROFIL 2"
          and text(f"heading:{colours_panel.CARD}") == "PROFIL DE COULEURS"
          and text(f"{colours_panel.BACK}_label") == "RETOUR")
    press(colours_panel.BACK)
    check("Chinese chosen", press("ZH") is False and model.language == "ZH")
    check("in Chinese: the game's words", text("label:saturated_colours") == "颜色预设"
          and text(f"{colours_panel.PREVIEW}_label") == "预览" and text("colour_card:Profile 3_label") == "预设 3"
          and text(f"{colours_panel.BACK}_label") == "返回")
    press("EN")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")
    raise

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
