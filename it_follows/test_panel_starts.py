"""Tests the Horde's starting points in It Follows' window (panel_starts.py and its wiring), every module of the window
as it is but the session's start and the pictures' import: the Starting point row first, off, its place hidden, its
« ? » opening the starting point's help; switched on, the seven tabs on the title's line before anything is saved,
each name on two lines, the place chosen in gold; a tab opens its place's page instead of the settings, its name, its
region, its two pictures as wide as each other and as tall as each wants, loaded then and not before; the tab clicked
again or BACK coming back; CHOOSE writing the place, then CHOSEN; switched off, the tabs gone, the place kept and shown
again once on; a picture that does not load hidden; START with a place closing the window, the trip asked with the
window's call to open it again; a refusal and a run that raises said in the footer; during a trip the rows and tabs
locked, START away; opened again after a trip that failed, the Horde's page saying why; in French and Chinese, the
places' names in English (decision 141)."""

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
from it_follows import game_pause, options, panel_assets, panel_fonts, panel_form, panel_model, panel_run  # noqa: E402
from it_follows import panel_theme as t, panel_view, panel_widgets as w, session, start_point, updates  # noqa: E402
from it_follows import control_window, panel_starts, welcome  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


loaded: list[str] = []
missing: set[str] = set()


def texture(_world: object, name: str = panel_assets.AVATAR) -> object:
    loaded.append(name)
    return None if name in missing else SimpleNamespace(name=name)


panel_assets.texture = texture
panel_fonts.build = lambda _root: {"title": object(), "body": object()}
game_pause.watch = lambda: None
welcome.seen.value = welcome.EDITION
updates.seen.value = it_follows.__version__
state["pc"] = SimpleNamespace(OakCharacter=None)
mod = it_follows.mod
model = panel_model.Model(mod)
GOLD = w.slate(t.COLOR_GOLD)


def window():
    _root, made = panel_view.build_view(object(), model)
    return made, panel_form.PanelForm({name: (lambda item=item: item) for name, item in made.items()}, model)


def press(name: str):
    widgets[name].SetIsChecked(True)
    return form.poll()


def text(name: str) -> str:
    return panel_fixture.text(widgets, name)


def shown(name: str) -> bool:
    return panel_fixture.visible(widgets, name)


def enabled(name: str) -> bool:
    return widgets[name].calls.get("SetIsEnabled", (True,)) == (True,)


asked: list = []
answer = SimpleNamespace(outcome="travelling")


def start(settings: object, on_failed: object = None) -> str:
    asked.append((settings, on_failed))
    return answer.outcome


try:
    widgets, form = window()
    loaded.clear()
    check("the Starting point row first on the Horde's page, off, no place shown, its « ? » beside",
          options.RUN[0] is options.start_point and text("setting:start_point_label") == "OFF"
          and text("start_place_name") == "" and text("start_help_label") == "?")
    check("off: no tab, the settings shown, no place's page", not shown("start_tabs") and shown("run_settings_box")
          and not shown("start_page_box"))
    check("its « ? » opens the starting point's help", press("start_help") is False and form.popup == "help_start"
          and text("heading:popup_help_start") == "STARTING POINT"
          and text("help:help_start").startswith("Choose where your Horde run starts."))
    form.escape()

    press("setting:start_point")
    check("switched on: the seven tabs on the title's line before anything is saved",
          shown("start_tabs") and options.start_point.value is False and text("setting:start_point_label") == "ON"
          and widgets["start_tabs"] in widgets["heading_line:run"].children)
    check("each name on two lines, as the game names it in English",
          [text(f"start_tab:{number}_label") for number in (3, 5, 8, 9, 11, 12, 15)]
          == ["PURGE\nGUARD", "CHECKPOINT\nVERMILLION", "THE VESTAL\nGARRISON", "THE DECKLED\nSPRAWL", "PAIN\nSTREET",
              "THE\nGUNKWORKS", "LOCUST PRODUCTION\nFACILITY"])
    check("the place chosen at first, Kevin's first, named on the row and in gold on its tab",
          text("start_place_name") == "PURGE GUARD"
          and widgets["start_tab:3_label"].calls["SetColorAndOpacity"] == (GOLD,)
          and widgets["start_tab:5_label"].calls["SetColorAndOpacity"] != (GOLD,))
    check("no picture loaded before a tab opens", not loaded)

    press("start_tab:11")
    check("a tab opens its place's page instead of the settings", shown("start_page_box")
          and not shown("run_settings_box") and text("start_page_name") == "PAIN STREET"
          and text("start_page_region") == "CARCADIA BURN" and text("start_caption:place") == "THE PLACE"
          and text("start_caption:map") == "ON THE MAP")
    check("the window drawn LARGE", model.window_size == "LARGE")
    check("its two pictures loaded then, as wide as each other, each as tall as it wants",
          loaded == ["start_11_place.png", "start_11_map.png"]
          and widgets["start_picture:place"].calls["SetBrushFromTexture"][0].name == "start_11_place.png"
          and widgets["start_picture:map"].calls["SetBrushFromTexture"][0].name == "start_11_map.png"
          and widgets["start_picture_box:place"].calls["SetWidthOverride"]
          == widgets["start_picture_box:map"].calls["SetWidthOverride"] == (585.0,)
          and widgets["start_picture_box:place"].calls["SetHeightOverride"] == (585 * 231 / 440,)
          and widgets["start_picture_box:map"].calls["SetHeightOverride"] == (585 * 359 / 800,)
          and shown("start_picture_box:place") and shown("start_picture_box:map"))
    check("the open tab in orange, CHOOSE offered", widgets["start_tab:11_fill"].calls["SetBrushColor"]
          == (w.linear(t.COLOR_SPARK),) and text("start_choose_label") == "CHOOSE" and enabled("start_choose")
          and text("start_back_label") == "BACK")
    press("start_tab:11")
    check("the open tab clicked again: back to the settings", shown("run_settings_box") and not shown("start_page_box"))
    press("start_tab:11")
    check("its pictures loaded again at each opening: no texture kept in Python, which the game may free",
          loaded == ["start_11_place.png", "start_11_map.png"] * 2)
    check("BACK: back to the settings", press("start_back") is False and shown("run_settings_box")
          and not shown("start_page_box"))

    press("start_tab:11")
    press("start_choose")
    check("CHOOSE writes the place, with the row switched on, then CHOSEN, which does nothing",
          options.start_place.value == "11" and options.start_point.value is True and text("notice") == "Saved."
          and text("start_choose_label") == "CHOSEN" and not enabled("start_choose")
          and text("start_place_name") == "PAIN STREET"
          and widgets["start_tab:11_label"].calls["SetColorAndOpacity"] != (GOLD,))
    press("start_tab:11")
    check("its tab, closed, in gold", widgets["start_tab:11_label"].calls["SetColorAndOpacity"] == (GOLD,))

    missing.add("start_12_map.png")
    press("start_tab:12")
    check("a picture that does not load hidden with its caption, never an empty frame",
          shown("start_picture_column:place") and not shown("start_picture_column:map"))
    missing.clear()
    press("start_tab:12")
    press("start_tab:12")
    check("loaded the next time: shown again with its caption", shown("start_picture_column:map"))
    press("setting:start_point")
    check("switched off: the tabs gone, the page closed, no place on the row, the place chosen kept",
          not shown("start_tabs") and shown("run_settings_box") and not shown("start_page_box")
          and text("start_place_name") == "" and options.start_place.value == "11")
    press("setting:start_point")
    check("on again: the place kept shown again", text("start_place_name") == "PAIN STREET")
    form.flush(widgets)

    session.start = start
    check("START with a place: the window closes, the trip asked with START's settings and the call to open it "
          "again", press("run_start") == "leave" and asked[-1][0].start_place == 11
          and asked[-1][1] is panel_run._reopen)
    answer.outcome = "not_open_world"
    check("START refused outside the open world: said, the window kept", press("run_start") is False
          and text("notice") == "No starting point from here: go back to the open world, then press START.")
    answer.outcome = "start_failed"
    check("a run that raises at START: its own words in the footer",
          press("run_start") is False and text("notice").startswith("The run could not start. The reason is in"))
    answer.outcome = "no_camp"
    check("any other refusal: the run's general words", press("run_start") is False
          and text("notice").startswith("The run could not start here."))

    start_point.travelling = lambda: True
    widgets, form = window()
    check("during a trip: the rows and the tabs locked, START away, the line saying the run starts on arrival",
          not enabled("setting:level") and not enabled("start_tab:3") and not shown("run_start_box")
          and shown("run_locked") and text("run_locked") == "On your way to the starting point: the run starts on "
                                                            "arrival.")
    press("start_tab:3")
    check("a tab clicked during a trip opens nothing", not shown("start_page_box"))
    model.start_open = 5
    press("start_choose")
    check("CHOOSE during a trip writes nothing", options.start_place.value == "11")
    start_point.travelling = lambda: False
    model.start_open = None
    form.poll()
    check("the trip over: the tabs free again", enabled("start_tab:3") and shown("run_start_box"))
    press("start_tab:5")
    start_point.travelling = lambda: True
    form.poll()
    check("a trip that begins while a tab is open closes it", not shown("start_page_box")
          and panel_starts.opened(form) is None)
    start_point.travelling = lambda: False
    form.poll()
    running = session.running
    session.running = lambda: True
    form.poll()
    press("start_tab:5")
    check("during a run: the tabs locked, a click opens nothing", not enabled("start_tab:5")
          and not shown("start_page_box"))
    session.running = running
    form.poll()
    start_point._state["outcome"] = "no_floor"
    check("a trip that fails while the window is open: said at once in its footer, once", form.poll() is False
          and text("notice").startswith("The starting point did not load in time")
          and start_point.take_outcome() is None)
    start_point._state["outcome"] = "arrival_coop"
    form.poll()
    check("a run refused on arrival: its own words, the player moved", text("notice").startswith(
        "Someone joined your game on the way") and "not changed" not in text("notice"))
    reopened = []
    opening = control_window.start
    control_window.start = lambda: reopened.append(True)
    panel_run._reopen()
    control_window.start = opening
    check("a trip that failed opens the window again", reopened == [True])

    start_point._state["outcome"] = "no_floor"
    model.change_page("history")
    widgets, form = window()
    check("opened again after a trip that failed: on the Horde's page, saying why",
          form.model.pages[form.page] == "run" and text("notice").startswith("The starting point did not load in time")
          and start_point.take_outcome() is None)

    check("the window NORMAL", model.change_window_size("NORMAL"))
    press("start_tab:11")
    loaded.clear()
    widgets, form = window()
    check("drawn again (size, theme) with a tab open: the tab still open, its pictures loaded",
          shown("start_page_box") and text("start_page_name") == "PAIN STREET"
          and [name for name in loaded if name.startswith("start_")] == ["start_11_place.png", "start_11_map.png"])
    check("a new opening of the window: a model of its own, no tab open",
          panel_starts.opened(SimpleNamespace(model=panel_model.Model(mod))) is None)
    check("in the smallest window the pictures narrower: they grow with the window",
          widgets["start_picture_box:place"].calls["SetWidthOverride"] == (440.0,)
          and widgets["start_picture_box:map"].calls["SetHeightOverride"] == (440 * 359 / 800,))
    press("start_back")
    check("French chosen", press("FR") is False and model.language == "FR")
    press("start_tab:9")
    check("in French: the row, the help, CHOOSE and BACK in French, the places in English",
          text("label:start_point").lower().startswith("point de départ") and text("start_choose_label") == "CHOISIR"
          and text("start_back_label") == "RETOUR" and text("start_tab:9_label") == "THE DECKLED\nSPRAWL"
          and text("start_page_name") == "THE DECKLED SPRAWL" and text("start_caption:map") == "SUR LA CARTE")
    check("Chinese chosen", press("ZH") is False and model.language == "ZH")
    check("in Chinese: CHOOSE in Chinese, the places in English", text("start_choose_label") == "选择"
          and text("start_page_name") == "THE DECKLED SPRAWL" and text("start_tab:15_label") == "LOCUST PRODUCTION\n"
                                                                                               "FACILITY")
    press("EN")
except Exception as error:
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")
    raise

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
