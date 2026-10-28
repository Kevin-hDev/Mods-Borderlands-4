# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The page in headless Chrome, on the game's own pieces (scripts and markup copied from its paks by
game_ui_copies.py) and wired to the real Python service on a temporary port. The engine, the input manager and the
component store are played by tests_browser/fake_game.js; the SDK and the game thread by fixture_world.py, with the
SDK's own option classes and save. Proves the page's code with the game's pieces, not the game itself: Kevin's trial
alone proves the game.
python test_page_browser.py [--refresh]   (--refresh reads the game's files again, after a game update)"""

import copy
import html
import json
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

import package_path  # noqa: F401  (before the package's modules)
import fixture_world
import game_ui_copies
import pak_recipe
import capture
import protocol
import server

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "tests_browser"
CHROME = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
# The component store's ids (menu_options.js, menu_pause.html, menu_main.html) and their files.
COMPONENTS = {"slider_alt": "slider_alt.html", "toggle": "toggle.html", "stepper_alt": "stepper_alt.html",
              "dropdown_options_alt": "dropdown_options_alt.html", "rebind_entry": "rebind_entry.html",
              "oak_option_button": "oak_option_button.html", "list_button": "list_button.html",
              "main_menu_button": "main_menu_button.html"}
SMALL_LIST = "small_list.css"
# What the game sends the glyph manager for its lobby panel's tab actions (glyph_manager.js, Event_UpdateGlyphMap).
# The keys are the test's: which ones the game gives is read in game (the page logs them).
LOBBY_GLYPHS = [{"action_name": "action_ui_lobby_tab_left", "km_keys": ["q"], "gamepad_keys": ["gamepad_left_shoulder"]},
                {"action_name": "action_ui_lobby_tab_right", "km_keys": ["e"],
                 "gamepad_keys": ["gamepad_right_shoulder"]}]
FAILURES = []


def check(name, condition):
    if not condition:
        FAILURES.append(name)
        print(f"ECHEC: {name}")


class AlternatingKeys:
    """Python's keyboard as the test plays it: F9 down every other pair of readings, the game's window in front.
    Counted in readings, not in time: Chrome's virtual time runs the page faster than the clock."""

    def __init__(self, code):
        self.code = code
        self.readings = 0

    def pressed(self, code):
        if code != self.code:
            return False
        self.readings += 1
        return self.readings % 4 in (2, 3)

    def focused(self):
        return True


def gameface_markup(text: str) -> str:
    """The component markup without the blank text between tags. Chrome keeps it, and stepper.js then reads a
    text node as the indicator (UpdateStepperIndicatorVisuals: item.firstChild.classList) and throws; the same
    code runs in game on the same store copy without error (the options screen's arrows work), so the game's
    engine has no such node there."""
    return re.sub(r">\s+<", "><", text)


def harness(config: dict, game: dict, driver: str) -> str:
    sources = {name: (pak_recipe.PAGE / name).read_text(encoding="utf-8") for name in pak_recipe.SOURCES}
    templates = "".join(f'<template id="component-{ident}">{gameface_markup(game[name].read_text(encoding="utf-8"))}'
                        '</template>'
                        for ident, name in COMPONENTS.items())
    pause = (pak_recipe.PAGE / "entry_pause.html.inc").read_text(encoding="utf-8")
    main = (pak_recipe.PAGE / "entry_main.html.inc").read_text(encoding="utf-8")
    # As gbxmain.js: the glyph manager exists before the key tables, and is ready once the game has sent them. As the
    # pause menu, the game knows its lobby panel's tab actions, not the options screen's (trial 10).
    glyph_manager = ("<script>window.GlyphMgr = new GlyphManager(); GlyphMgr.Event_GlyphManager_Ready();"
                     f"GlyphMgr.Event_UpdateGlyphMap({json.dumps(LOBBY_GLYPHS)});</script>")
    scripts = "".join((glyph_manager if name == game_ui_copies.GLYPH_TABLE else "") + f'<script src="{name}"></script>'
                      for name in ("fake_game.js",) + game_ui_copies.SCRIPTS)
    # The stylesheets every menu has loaded before the page adds its own (gbx.css sets the rem, as in game).
    styles = "".join(f'<link rel="stylesheet" href="{name}">'
                     for name in game_ui_copies.MENU_STYLESHEETS + (SMALL_LIST,))
    # The menus' root classes as in the game's files (menu_pause.html, menu_main.html): oakgame.css reads them.
    return ('<!doctype html><html><head><meta charset="utf-8">' + styles + scripts + '</head><body>' + templates +
            '<widget-menu-pause class="widget list_menu_widget"><div class="temp_bg_color"></div>'
            '<div class="menu_pause"><div class="list">' + pause + '</div></div></widget-menu-pause>'
            '<widget-menu-main class="widget list_menu_widget menu_main"><div class="menu_screen_boundaries">'
            '<div class="mm_entry_list">' + main +
            '</div></div><div class="mm_campaign_progress_cntr"></div><div class="mm_tooltip_cntr"></div>'
            '</widget-menu-main>'
            # The main menu's group panel and news card, widgets of their own (lobby_info.html, menu_news.html).
            '<widget-lobby-info style="display: flex"></widget-lobby-info><widget-news></widget-news>'
            '<pre id="result"></pre>'
            f'<script>{pak_recipe.page_script(None, sources, config)}</script>'
            f'<script src="{driver}"></script></body></html>')


def run_page(config: dict, game: dict, driver: str) -> dict:
    with tempfile.TemporaryDirectory() as name:
        folder = Path(name)
        for path in [FIXTURES / "fake_game.js", FIXTURES / driver, FIXTURES / SMALL_LIST,
                     pak_recipe.PAGE / pak_recipe.STYLESHEET]:
            shutil.copy(path, folder / path.name)
        for path in game.values():
            shutil.copy(path, folder / path.name)
        page = folder / "harness.html"
        page.write_text(harness(config, game, driver), encoding="utf-8")
        output = subprocess.run(
            [str(CHROME), "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
             f"--user-data-dir={folder / 'profile'}", "--allow-file-access-from-files",
             # Small, so the test mod's page is longer than the scrolled area (driver.js, trial 8).
             "--window-size=900,420", "--virtual-time-budget=30000", "--dump-dom", page.as_uri()],
            capture_output=True, timeout=120, check=False).stdout.decode("utf-8", "replace")
    match = re.search(r'<pre id="result">(.*?)</pre>', output, re.S)
    return json.loads(html.unescape(match.group(1))) if match and match.group(1) else {}


def page_config(base: dict, port: int) -> dict:
    config = pak_recipe.page_config(base)
    config["http"] = dict(config["http"], port=port)
    # The game's copies, under their own names (game_ui_copies.py).
    stylesheets = [url.rsplit("/", 1)[1] for url in config["page"]["stylesheets"]]
    config["page"] = dict(config["page"], optionsHtml="menu_options.html", stylesheets=stylesheets,
                          ownStylesheet=pak_recipe.STYLESHEET)
    return config


class NoKeys:
    """Python's keyboard pressing nothing: a capture waits until the page ends it."""

    def pressed(self, code):
        return False

    def focused(self):
        return True


def start_service(base: dict, logs: list, keys=None, prebuilt=True, **http):
    # Chrome names a local page's origin file://; the game's UI uses its own (constants), refused here otherwise.
    served = copy.deepcopy(base)
    served["http"]["nativeOrigins"] = base["http"]["nativeOrigins"] + ["file://"]
    served["http"].update(http)
    keys = keys or AlternatingKeys(base["capture"]["keys"]["F9"])
    worlds = []

    def make_routes(log):
        world = fixture_world.World(served, log, lambda on_end: capture.KeyCapture(served, keys, on_end),
                                    locked="real")
        # Built ahead, as when the page asks after the mod's start; left out, the first read is the page's.
        if prebuilt:
            world.bridge.rebuild()
        worlds.append(world)
        return world.routes

    service = server.Service(served, make_routes, logs.append, port=0)
    service.start()
    return service, worlds[0]


def check_trial(result: dict, logs: list, world) -> None:
    # The page of an English game (language.js): Chrome knows no "language" media feature.
    page = {**world.constants["page"], **world.constants["texts"]["en"]}
    general, crumb_sep, meta_sep = page["generalLabel"], page["crumbSeparator"], page["metaSeparator"]
    check("page finished", result and "error" not in result and len(result.get("steps", [])) == 7)
    check("pause entry labelled MODS", result.get("pauseLabel") == "MODS")
    check("main entry labelled MODS", result.get("mainLabel") == "MODS")
    check("shown at once", result.get("shownAtOnce") is True)
    check("list of the mods, from Python", result.get("listRows") == "Sample Mod|Real|Wide|Mod Settings")
    check("the list is one MODS tab, no path, no sub-tabs", result.get("listHeader") == [page["title"], "", False])
    check("a mod's details: name, description lines, version and author", result.get("modDetails") == [
        "Sample Mod", "A sample mod: each kind of setting, and pages laid out as tabs.|Every row can change.",
        page["versionPrefix"] + "1.0" + meta_sep + "Sample author"])
    check("a mod's words shown as text, never as markup", result.get("markupAsText") == [fixture_world.WIDE_SHOWN, 0])
    check("pause menu hidden by display", result.get("pauseHidden") is True)
    check("escape claimed", result.get("escapeClaimed") is True)
    check("menu navigation locked", result.get("navLocked") is True)
    # Drawing A: the mod's pages as tabs, its loose rows under General, its own details until a row is lit.
    check("mod page: path, tabs, General chosen, the mod's details", result.get("modHeader") == [
        f"MODS{crumb_sep}SAMPLE MOD", f"{general}|More settings|Pages", 0, False, "Sample Mod"])
    check("BACK shown", result.get("backShown") is True)
    check("General holds the loose rows", result.get("modRows") ==
          "Enabled|Whole number|Fraction|Switch|Arrows|List|Key|Button" and result.get("groupTitles") == ["Sample group"])
    check("a lit row's details", result.get("rowDetails") == ["Whole number", "A whole number from 0 to 100, in steps "
                                                              "of 5.", ""] and result.get("ownTitle") == "Switch title")
    check("values from Python", result.get("wholeText") == "50" and result.get("fractionText") == "1.0")
    check("rebind draws its key", "Key_F7.png" in str(result.get("rebindKey")))
    check("mouse slider", result.get("mouseSlider") == "55")
    check("mouse stepper", result.get("mouseStepper") == "High")
    check("mouse list", result.get("dropdownOpened") is True and result.get("dropdownPicked") == "Blue")
    check("mouse button says pressed", result.get("buttonNotice") is True)
    check("a tab clicked shows its page", result.get("mouseTab") == [1, "Inner switch|Inner number", False,
                                                                       "A page with no page of its own: a tab without "
                                                                       "sub-tabs."])
    check("the key's glyph clicked moves a tab, sub-tabs shown", result.get("glyphTab") == [
        2, True, f"{general}|Page A|Page B", 0, "Pages switch"])
    check("General again keeps the values", result.get("mouseGeneral") == [0, False, "55"])
    check("gamepad lights the first row", result.get("padFirstRow") is True)
    check("gamepad steps the sliders", result.get("padSlider") == "60" and result.get("padFraction") == "1.1")
    check("gamepad reaches the key", result.get("padRebindRow") is True and result.get("captureLabel") == page["captureLabel"])
    check("captured key drawn", "Key_F9.png" in str(result.get("capturedKey")))
    check("gamepad presses the button", result.get("padButton") is True)
    check("tab action: next tab, its first row lit", result.get("padTab") == [1, "Inner switch|Inner number", True])
    check("gamepad flips the tab's switch", result.get("nestedToggle") is False)
    check("tab action reaches the sub-tabs", result.get("padSubtabs") == [True, f"{general}|Page A|Page B", 0,
                                                                         "Pages switch"])
    check("sub-tab action: its page, first row lit", result.get("padPageB") == [2, "Page B switch|Deep page", True])
    # OPTI.md, rule 7: a tab's rows are removed when another is chosen; the list stays, hidden.
    check("only the shown tab's rows exist", result.get("rowsAfterTabs") == 2)
    check("no tab past the last", result.get("padEnds") == [2, 2])
    check("a deeper page opens as its own screen", result.get("deepLinkLit") is True and result.get("deep") == [
        f"MODS{crumb_sep}SAMPLE MOD{crumb_sep}PAGES{crumb_sep}PAGE B{crumb_sep}DEEP PAGE", general, False,
        "Deep switch", 0, 2])
    check("gamepad flips the deep switch", result.get("deepToggle") is True)
    check("escape goes back to the tab and sub-tab", result.get("backToPageB") == [2, True, 2,
                                                                                  "Page B switch|Deep page"])
    check("back keeps the gamepad's row", result.get("rowKept") is True)
    check("tabs sound as the game's bar", result.get("tabSounds") == [])
    # OPTI.md, rule 7: the list stays, hidden; only the shown tab's rows exist.
    check("escape back to the list, only its rows left", result.get("backToList") == ["", 4, page["closeLabel"],
                                                                                     page["title"], 1]
          and result.get("screensWithMod") == 2)
    # Enabled, restore, speed and the long page's sliders, all locked.
    check("real mod page locked", result.get("realCrumb") == f"MODS{crumb_sep}REAL" and result.get("lockedNotice") is True
          and result.get("lockedRows") == 3 + fixture_world.REAL_LONG_PAGE)
    check("locked slider kept", result.get("realSliderKept") is True)
    check("a single page inside a tab is its sub-tab", result.get("realSub") == [1, True, "Real sub", True])
    check("gamepad keeps its row in view", result.get("realScrolled") is True)
    check("a locked mod's deeper page opens at its top, its rows locked", result.get("realDeep") == [
        f"MODS{crumb_sep}REAL{crumb_sep}REAL MORE{crumb_sep}REAL SUB{crumb_sep}REAL DEEP", 0, 1])
    check("back keeps the place and the row", result.get("realBack") == [1, True] and result.get("realRowKept") is True)
    # Its pages, and General first: its Enabled row.
    check("a bar wider than the screen", result.get("wideTabs") == fixture_world.WIDE_TABS + 1
          and result.get("wideOverflows") is True)
    check("the bar scrolls to the chosen tab and back", result.get("wideLast") is True and result.get("wideFirst") is True)
    check("one press under two names is one step", result.get("twoNamesOneStep") == 1)
    check("each name moves the tabs in its own frame", result.get("namesNextFrames") == 3)
    check("the glyphs drawn are the ones the menu knows", result.get("glyphActions") == [
        "action_ui_lobby_tab_left", "action_ui_lobby_tab_right",
        "action_ui_menu_sub_tab_left", "action_ui_menu_sub_tab_right"])
    check("the keys' glyphs keep their width", result.get("triggersKept") is True)
    check("another handler's escape ignored", result.get("otherEscapeIgnored") is True)
    check("escape closes the page", result.get("closedByEscape") is True and result.get("pauseBack") is True)
    check("navigation and escape given back", result.get("navGivenBack") is True and result.get("escapeReleased") is True)
    check("reopening reuses the page, on the list", result.get("sameRootReused") is True and result.get("reopenedOnList") is True)
    check("values kept on reopening", result.get("valuesKept") == "60")
    check("page leaves with the menu", result.get("closedWithMenu") is True)
    check("main menu opens its own page", result.get("mainOpen") is True and result.get("mainHidden") is True)
    check("over the main menu, its group panel and news hidden", result.get("mainOthersHidden") is True)
    check("given back as they were", result.get("mainOthersBack") is True)
    check("over the pause menu, the group panel left alone", result.get("pauseLobbyKept") is True)
    check("pause menu: the Escape action alone goes nowhere", result.get("pauseEscapeActionIgnored") is True)
    check("main menu page has the values", result.get("mainValues") == "60" and result.get("mainBack") is True)
    check("close button", result.get("mainClosed") is True)
    check("nothing else reaches the native side", result.get("otherNative") == [])

    option = world.option
    check("test mod changed by the page", option("sample_whole").value == 60 and option("sample_fraction").value == 1.1
          and option("sample_switch").value is True and option("sample_arrows").value == "High"
          and option("sample_list").value == "Blue" and option("sample_key").value == "F9"
          and option("sample_more_switch").value is False and option("sample_deep_switch").value is True
          and world.test_mod.is_enabled)
    real_options = list(world.real.walk(world.real.options))
    long_page = [option for option in real_options if option.identifier.startswith(("extra_", "inner_"))]
    deep_flag = next(option for option in real_options if option.identifier == "deep_flag")
    check("real mod untouched", world.real.options[1].value == 2.0 and world.real_pressed == []
          and world.real.is_enabled is False and len(long_page) == 2 * fixture_world.REAL_LONG_PAGE
          and all(option.value == 1.0 for option in long_page) and deep_flag.value is True)
    check("wide mod untouched", world.wide.is_enabled is False
          and all(option.value is True for option in world.wide.walk(world.wide.options) if hasattr(option, "value")))
    joined = "\n".join(logs)
    callbacks = [line for line in logs if "TEST_MOD_CALLBACK" in line or "TEST_MOD_BUTTON" in line]
    check("every mod callback ran on the game thread", len(callbacks) >= 9
          and all(line.endswith("thread=game") for line in callbacks))
    check("enabled on the game thread", "TEST_MOD_ENABLED thread=game" in joined)
    check("each change applied with its wait", joined.count("APPLIED id=") >= 10)
    check("locked rows never reached the game thread", "CHANGE_REFUSED" not in joined)
    # A click saves at once, as the SDK's console does; a slider's steps wait for the next save (bridge.py).
    check("saved at each click, by the game thread", "SAVED reason=change mods=1" in joined
          and all(line.endswith("thread=game") for line in logs if "SAVED reason=" in line))
    saved = json.loads(world.test_mod.settings_file.read_text(encoding="utf-8"))
    check("saved by the SDK's own save", saved["options"]["sample_group"]["sample_whole"] == 60
          and saved["options"]["sample_more"]["sample_more_switch"] is False
          and saved["options"]["sample_pages"]["sample_page_b"]["sample_deep"]["sample_deep_switch"] is True
          and saved["enabled"] is True)
    expected = ["event=script_loaded", "event=entry_clicked host=pause", "event=page_opened host=pause",
                "event=template source=game", "event=model source=python", "event=language code=en source=translate", "event=screen_opened screen=list code=rows_4",
                "event=screen_opened screen=mod code=rows_8", "event=screen_opened screen=tab code=rows_2",
                "event=screen_opened screen=back code=rows_2", "event=tab state=top code=i1",
                "event=tab state=sub code=i2",
                "event=glyph state=top source=lobby keyboard=q_e gamepad=gamepad_left_shoulder_gamepad_right_shoulder",
                "event=glyph state=sub source=absent",
                "event=gamepad name=tab_right code=input_action_ui_lobby_tabright device=gamepad",
                "event=gamepad name=tab_right code=input_action_menu_tabright device=gamepad",
                "event=gamepad name=sub_right code=input_action_menu_subtabright device=gamepad",
                "event=gamepad name=sub_right", "event=gamepad name=tab_left",
                "event=dropdown state=open", "event=dropdown state=closed", "event=scroll source=game",
                "CAPTURE_START id=", "state=done key=F9",
                "event=capture state=done", "event=gamepad name=down",
                "event=input_action name=input_action_menu_openoptionsmenu", "event=timings",
                "event=page_closed reason=escape", "event=page_closed reason=menu_closed",
                "event=entry_clicked host=main", "event=page_opened host=main", "MODEL_SENT revision="]
    for line in expected:
        check(f"log has {line}", line in joined)
    check("page frame built once per menu", joined.count("event=page_built") == 2)
    # Rule 5: the list is built again only for a newer model: first opening, after the changes, main menu.
    check("list built once per model and menu", joined.count("event=screen_opened screen=list") == 3)
    timings = [line for line in logs if "event=timings" in line]
    check("timings carry each step", any(all(f"{name}=" in line for name in ("template", "model", "build", "shown"))
                                         for line in timings) and any("screen=" in line for line in timings))
    check("no rejected event", "EVENT_REJECTED" not in joined)
    check("no page error", "event=error" not in joined)


def check_key_table(game: dict, base: dict) -> None:
    """Every key Python may capture has a glyph in the game's keyboard table, under its lowercase name."""
    table = game[game_ui_copies.GLYPH_TABLE].read_text(encoding="utf-8")
    defaults = table.split("const defaults", 1)[1].split("}", 1)[0]
    drawn = set(re.findall(r'"([a-z0-9_]+)"\s*:', defaults))
    missing = [name for name in base["capture"]["keys"] if name.lower() not in drawn]
    check(f"each capturable key has a glyph (missing: {missing})", len(drawn) > 50 and not missing)


def main() -> None:
    # Both exist in the workshop; elsewhere (the public copy) the test says it did not run, and why.
    if not CHROME.is_file():
        print(f"SKIP  | the page in Chrome: Chrome not found at {CHROME}")
        print("RESULTAT: SKIP")
        sys.exit(0)
    if not game_ui_copies.available():
        print("SKIP  | the page in Chrome: it runs on the game's own UI files, read by game_files, which is not here")
        print("RESULTAT: SKIP")
        sys.exit(0)
    game = game_ui_copies.copies(refresh="--refresh" in sys.argv)
    base = protocol.load_constants()
    # Chrome names the site of this local test page (Sec-Fetch-Site: cross-site); the game's UI engine sends no such
    # header (the HUD Editor's same guard, in game since 23 October 2026). Allowed here only.
    base["http"]["fetchSites"] = base["http"]["fetchSites"] + ["cross-site"]
    check_key_table(game, base)
    logs = []
    service, world = start_service(base, logs)
    result = run_page(page_config(base, service.port), game, "driver.js")
    world.game.settle()
    service.stop()
    print("page:", json.dumps(result))
    check_trial(result, logs, world)
    check("no task raised on the game thread", world.game.errors == [])

    # Python absent: a port just released, so the requests are refused (trial 4, where the page waited ~2 s).
    with socket.socket() as spare:
        spare.bind(("127.0.0.1", 0))
        free = spare.getsockname()[1]
    alone = run_page(page_config(base, free), game, "driver_absent.js")
    print("page without python:", json.dumps(alone))
    check("no python: page open at once", alone.get("openAtOnce") is True)
    check("no python: says absent, no mod list", alone.get("absentShown") is True and alone.get("rows") == 0)
    check("no python: the MODS tab alone", alone.get("tabs") == [base["texts"]["en"]["title"]])
    check("no python: escape still closes", alone.get("closed") is True)

    # The review's fixes (26 October 2026). No wait for the game thread and nothing built ahead: the page's first
    # read gets Python's 503 "not ready", as in game where the first read took 321 to 350 ms.
    fix_logs = []
    service, world = start_service(base, fix_logs, keys=NoKeys(), prebuilt=False, modelWaitMs=0)
    fixes = run_page(page_config(base, service.port), game, "driver_fixes.js")
    world.game.settle()
    service.stop()
    print("page fixes:", json.dumps(fixes))
    check("fixes: page finished, no task raised on the game thread", fixes and "error" not in fixes
          and world.game.errors == [])
    # The page says what it took Python's answer for: before the frame shows its state, the log alone tells.
    check("not ready yet: taken for loading, never for absent, then the list", fixes.get("listAfterNotReady") is True
          and fixes.get("neverSaidAbsent") is True and "event=model source=not_ready" in "\n".join(fix_logs)
          and "event=model source=absent" not in "\n".join(fix_logs))
    check("the key row's second slot hidden", fixes.get("secondHidden") is True)
    check("the gamepad steps over it both ways", fixes.get("padRight") == 2 and fixes.get("padLeft") == 0)
    check("a tab clicked ends a capture, Python's too", fixes.get("captureStarted") is True
          and fixes.get("captureEndedByTab") is True and "CAPTURE_START" in "\n".join(fix_logs)
          and "state=cancelled key=None" in "\n".join(fix_logs))
    check("a refused change shown back as the mod holds it", fixes.get("changedOnScreen") is True
          and fixes.get("refusedShownBack") is True and fixes.get("refusedSaid") is True
          and fixes.get("revisionKept") is True and "reason=old_model" in "\n".join(fix_logs))
    check("also when the player has gone to another tab meanwhile", fixes.get("refusedOffTabShownBack") is True)
    check("over the main menu, one Escape closes an open list only", fixes.get("mainListOpened") is True
          and fixes.get("mainEscapeClosedListOnly") is True and fixes.get("mainSecondEscapeBack") is True
          and fixes.get("mainClosed") is True)
    if FAILURES:
        logs.extend(fix_logs)

    if FAILURES:
        print("\n".join(logs))
    print("RESULTAT: OK" if not FAILURES else f"RESULTAT: ECHEC {len(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


main()
