"""Tests the COMPANIONS page of It Follows' window (panel_companions.py, panel_companions_poll.py and their wiring),
every module of the window as it is but the session's team: after NORMAL MODE in the column; VAULT HUNTERS open at
first, ALLIES on its tab, the open tab in orange; the team empty at first, said; a card's name adding one, its count
and its « − » shown, its frame gold, the team said, written at once and kept; « − » taking one away; its shield
switched, a speed chosen, for that companion only; the outfit offered on the card of the hunter played alone,
written when chosen; a ninth refused, said, nothing written; the bars' row hidden
without their package, shown with it; LAUNCH THE TEAM refused when empty or with the mod off, else the team started
with the choices kept and the window closed; while the team is on, the cards locked under a line, a click said and
nothing written, STOP THE TEAM ending it, the column's RUNNING tag; the footer's own words; in French and Chinese, the
allies named as the game names them, the hunters by their own names. Each card's picture in its square, loaded each
time its tab opens, never again while it stays open, one that does not load hidden."""

import pathlib
import sys
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# Its labels name the − button: a Windows console's cp1252 cannot print it, and the print raising hid the checks after.
sys.stdout.reconfigure(encoding="utf-8")

import sdk_stubs  # noqa: E402

state = sdk_stubs.install()

import panel_fixture  # noqa: E402

panel_fixture.install()

import it_follows  # noqa: E402
from it_follows import companion_pictures_data, game_pause, panel_assets, panel_companions, panel_fonts  # noqa: E402
from it_follows import panel_companion_pictures, panel_form, panel_model, panel_window_size  # noqa: E402
from it_follows import panel_theme as t, panel_view, panel_widgets as w, session, updates, welcome  # noqa: E402
from it_follows import companion_choices as choices  # noqa: E402
from it_follows.characters.companions import bars, owners, player_paint  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


loaded: list[str] = []
missing: set[str] = set()


def texture(_world: object, name: str = panel_assets.AVATAR) -> object:
    if name == panel_assets.AVATAR:
        return None
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


def framed(name: str) -> object:
    return widgets[f"mate:{name}"].calls["SetBrushColor"][0]


team: dict = {"started": [], "stopped": 0, "answer": "started"}


def start_team(names: list, picks: dict) -> str:
    """The session's, its team faked: on once started, as session.team_on reads it."""
    team["started"].append((names, picks))
    if team["answer"] == "started":
        session._state["team"] = SimpleNamespace()
    return team["answer"]


def stop_team() -> str:
    team["stopped"] += 1
    session._state["team"] = None
    return "stopped"


session.start_team, session.stop_team = start_team, stop_team

try:
    check("after NORMAL MODE in the column", model.pages == ("run", "normal", "companions", "history", "options"))
    widgets, form = window()
    press("nav:companions")
    check("its page shown, its title, its footer's own words", form.model.pages[form.page] == "companions"
          and text("heading:companions") == "COMPANIONS"
          and text("notice") == "Choose a companion to add it to the team, then launch the team.")
    check("two tabs on the title's line, VAULT HUNTERS open in orange", text("companions_tab:hunters_label")
          == "VAULT HUNTERS" and text("companions_tab:allies_label") == "ALLIES"
          and widgets["companions_tab:hunters_fill"].calls["SetBrushColor"] == (w.linear(t.COLOR_SPARK),)
          and shown("companions_grid:hunters") and not shown("companions_grid:allies")
          and widgets["companions_tab:allies"].owner is not None)
    check("the team empty, said; the hunters' line", text("companions_count") == "TEAM 0 / 8"
          and text("companions_who") == "No companion yet: choose one to add it to the team."
          and text("companions_lead") == "The Vault Hunters fight with their weapons only, not their skills.")
    check("a card: its name, no count, no « − », its shield on, +20 %, its frame ink", text("mate_add:Vex_label")
          == "VEX" and not shown("mate_times:Vex") and not shown("mate_minus:Vex")
          and text("mate_shield:Vex_label") == "ON" and text("mate_shield_word:Vex") == "SHIELD"
          and text("mate_speed:Vex:+20%_label") == "+20%" and text("mate_speed:Vex:Off_label") == "OFF"
          and widgets["mate_speed:Vex:+20%_fill"].calls["SetBrushColor"] == (w.linear(t.COLOR_GOLD),)
          and framed("Vex") == w.linear(t.COLOR_INK))
    check("the bars' row hidden without their package", not shown("companions_bars_box"))
    check("LAUNCH THE TEAM", text("companions_launch_label") == "LAUNCH THE TEAM")

    press("companions_launch")
    check("launched empty: refused, said, nothing started", text("notice") == "Add at least one companion first."
          and team["started"] == [])
    press("mate_add:Vex")
    check("its name clicked: one added, written at once, said", choices.team.value == ["Vex"]
          and text("notice") == "Saved." and not model.transaction.pending)
    check("its count and its « − » shown, its frame gold, the team said", text("mate_times_text:Vex") == "×1"
          and shown("mate_times:Vex") and shown("mate_minus:Vex") and framed("Vex") == w.linear(t.COLOR_GOLD)
          and text("companions_count") == "TEAM 1 / 8" and text("companions_who") == "VEX")
    press("mate_add:Vex")
    press("mate_add:Rafa")
    check("the same one again, another one: counted", choices.team.value == ["Vex", "Vex", "Rafa"]
          and text("mate_times_text:Vex") == "×2" and text("companions_who") == "VEX ×2 · RAFA")
    press("mate_minus:Vex")
    check("« − »: one taken away", choices.team.value == ["Vex", "Rafa"] and text("mate_times_text:Vex") == "×1")
    press("mate_shield:Rafa")
    press("mate_speed:Rafa:+30%")
    check("its shield switched off, +30 % chosen, for that companion only", choices.choice("Rafa")
          == choices.Choice(False, "+30%") and choices.choice("Vex") == choices.Choice()
          and text("mate_shield:Rafa_label") == "OFF" and text("mate_shield:Vex_label") == "ON"
          and widgets["mate_speed:Rafa:+30%_fill"].calls["SetBrushColor"] == (w.linear(t.COLOR_GOLD),))
    press("mate_shield:Vex")
    press("mate_shield:Vex")
    check("its shield switched twice: on again", choices.choice("Vex").shielded is True
          and text("mate_shield:Vex_label") == "ON")
    check("the hunter played unread: no outfit on any card", not any(shown(f"mate_outfit_line:{one}")
                                                                      for one in panel_companions.HUNTERS))
    check("an ally has no outfit", "mate_outfit:Crankus:own" not in widgets
          and "mate_outfit:Crankus:own" not in panel_companions.buttons("Crankus"))
    played_by = player_paint.played_by
    player_paint.played_by = lambda pc: "Vex"
    widgets, form = window()
    press("nav:companions")
    check("the hunter played: his outfit offered, BASE at first; on no other card", shown("mate_outfit_line:Vex")
          and not shown("mate_outfit_line:Rafa") and text("mate_outfit_word:Vex") == "OUTFIT"
          and text("mate_outfit:Vex:own_label") == "BASE" and text("mate_outfit:Vex:player_label") == "YOUR COLOURS"
          and widgets["mate_outfit:Vex:own_fill"].calls["SetBrushColor"] == (w.linear(t.COLOR_GOLD),))
    press("mate_outfit:Vex:player")
    check("his colours chosen: written at once, shown, the rest of his choice kept", choices.choice("Vex")
          == choices.Choice(True, "+20%", "player") and text("notice") == "Saved."
          and widgets["mate_outfit:Vex:player_fill"].calls["SetBrushColor"] == (w.linear(t.COLOR_GOLD),))
    press("mate_outfit:Vex:own")
    check("his own outfit chosen again", choices.choice("Vex").outfit == "own")
    player_paint.played_by = played_by

    press("companions_tab:allies")
    check("ALLIES: its cards, named as the game names them in English", shown("companions_grid:allies")
          and not shown("companions_grid:hunters") and text("mate_add:Decrepit Frame_label") == "DECREPIT FRAME"
          and text("mate_add:Brine Type M_label") == "BRINE TYPE M")
    for _ in range(6):
        press("mate_add:Crankus")
    check("eight in the team", len(choices.team.value) == 8 and text("companions_count") == "TEAM 8 / 8")
    press("mate_add:Abomination")
    check("a ninth refused, said, nothing written", len(choices.team.value) == 8
          and text("notice") == "The team is full: 8 companions at most." and "Abomination" not in choices.team.value)

    mod.disable()
    press("companions_launch")
    check("the mod off: the team not launched, said", team["started"] == []
          and text("notice") == "It Follows is off: switch it on, then launch the team.")
    mod.enable()
    check("launched: the window closes, the team started with the choices kept", press("companions_launch") == "leave"
          and team["started"][-1] == (choices.team.value, choices.team_choices())
          and team["started"][-1][1]["Rafa"] == choices.Choice(False, "+30%"))

    widgets, form = window()
    check("opened again while the team is on: its cards locked under a line, STOP THE TEAM, the RUNNING tag",
          not enabled("mate_add:Crankus") and not enabled("mate_minus:Crankus") and not enabled("mate_shield:Crankus")
          and not enabled("mate_speed:Crankus:Off") and shown("companions_locked")
          and text("companions_locked") == "Stop the team to change it."
          and text("companions_launch_label") == "STOP THE TEAM" and text("nav_companions_running") == "RUNNING"
          and shown("nav_companions_running_tag") and text("notice") == "Your team follows you. Stop it here to "
                                                                        "change it.")
    check("the tab open kept in a window drawn again", shown("companions_grid:allies"))
    before = list(choices.team.value)
    press("mate_minus:Crankus")
    check("a card clicked while the team is on: said, nothing written", choices.team.value == before
          and text("notice") == "Stop the team to change it.")
    press("companions_launch")
    check("STOP THE TEAM: the team stopped, said, the window kept, the cards free", team["stopped"] == 1
          and text("notice") == "The team stopped: they no longer follow you." and enabled("mate_add:Crankus")
          and text("companions_launch_label") == "LAUNCH THE TEAM" and not shown("nav_companions_running_tag"))
    team["answer"] = "already_on"
    press("companions_launch")
    check("a team already on: said", text("notice") == "The team is already on.")
    team["answer"] = "main_menu"
    press("companions_launch")
    check("at the main menu: said, the window kept (decision 61 of the companions)",
          text("notice") == "Load a game first, then launch the team.")
    MISMATCH = ("It Follows and Companions are at versions that do not work together, so no team starts: update both, "
                "then restart the game.")
    foreign = SimpleNamespace(protocol=owners.PROTOCOL + 1, owners={})
    sys.modules[owners.STATE] = foreign
    check("two versions meeting while the page is open: the page told to paint again",
          panel_companions.changed(form))
    form.notice = "ready"
    form.refresh_labels(widgets)
    check("two versions of the companions' code: the page says so before any click, its cards and LAUNCH THE "
          "TEAM greyed, the footer too", text("companions_locked") == MISMATCH and shown("companions_locked")
          and widgets["companions_launch"].calls["SetIsEnabled"][0] is False
          and widgets["mate_add:Crankus"].calls["SetIsEnabled"][0] is False
          and text("notice") == MISMATCH)
    owners.reset_for_tests()
    form.refresh_labels(widgets)
    check("the versions apart no more: LAUNCH THE TEAM back", widgets["companions_launch"].calls["SetIsEnabled"][0]
          is True and not shown("companions_locked"))
    team["answer"] = "elsewhere"
    press("companions_launch")
    check("no mod can be known to lead (two versions of the companions' code): said, update both (review of "
          "23 October 2026)", text("notice") == MISMATCH)
    team["answer"] = "started"

    installed = bars.installed
    bars.installed = lambda: True
    widgets, form = window()
    check("the bars' package installed: their row shown, off at first", shown("companions_bars_box")
          and text("label:companion_bars") == "HEALTH BARS ON SCREEN" and text("setting:companion_bars_label") == "OFF")
    bars.installed = installed

    pictures = companion_pictures_data.PICTURES
    hunters_files = [pictures[name] for name in panel_companions.HUNTERS]
    allies_files = [pictures[kind.name] for kind in panel_companions.TABS["allies"]]
    loaded.clear()
    widgets, form = window()
    press("nav:companions")
    check("a new window: the open tab's pictures loaded, ALLIES kept, each in its square, 187 in the LARGE window",
          loaded == allies_files and shown("mate_picture_box:Crankus") and not shown("mate_picture_box:Vex")
          and widgets["mate_picture_box:Crankus"].calls["SetWidthOverride"] == (187.0,)
          and widgets["mate_picture_box:Crankus"].calls["SetHeightOverride"] == (187.0,)
          and widgets["mate_picture:Crankus"].calls["SetBrushFromTexture"][0].name == "companion_crankus.png")
    square = widgets["mate_picture_box:Vex"]
    check("the square on the card's left, its settings beside it", square.owner.children[0] is square
          and len(square.owner.children) == 2)
    press("companions_tab:hunters")
    check("the hunters' tab: theirs loaded", loaded[len(allies_files):] == hunters_files
          and shown("mate_picture_box:Vex"))
    press("companions_tab:hunters")
    check("painted again on the same tab: not loaded again", loaded[len(allies_files):] == hunters_files)
    missing.add("companion_crankus.png")
    press("companions_tab:allies")
    check("each opening loads them again; one that does not load hidden, the others shown",
          loaded[len(allies_files) + len(hunters_files):] == allies_files and not shown("mate_picture_box:Crankus")
          and shown("mate_picture_box:Abomination"))
    missing.clear()
    width = panel_window_size.WIDTH
    sides = []
    for panel_window_size.WIDTH in (t.WINDOW_WIDTH, 1690, 4000):
        sides.append(panel_companion_pictures.side())
    panel_window_size.WIDTH = width
    check("the square: 64 in the smallest window, 187 in the LARGE one, never past 240",
          sides == [64.0, 187.0, 240.0])

    check("French chosen", press("FR") is False and model.language == "FR")
    check("in French: the tabs, the words, the allies as the game names them, the hunters their own",
          text("companions_tab:hunters_label") == "CHASSEURS DE L'ARCHE" and text("mate_shield_word:Vex") == "BOUCLIER"
          and text("mate_speed:Vex:Off_label") == "COUPÉE" and text("mate_add:Decrepit Frame_label")
          == "CHÂSSIS VÉTUSTE" and text("mate_add:Vex_label") == "VEX"
          and text("companions_count") == "ÉQUIPE 8 / 8" and text("companions_launch_label") == "LANCER L'ÉQUIPE")
    check("Chinese chosen", press("ZH") is False and model.language == "ZH")
    check("in Chinese: the allies as the game's zh-Hans names them", text("mate_add:Crankus_label") == "克兰库斯"
          and text("companions_tab:allies_label") == "盟友" and text("mate_add:Vex_label") == "VEX")
    press("EN")
    check("the page's names read once per language", {"EN", "FR", "ZH"} <= set(
          panel_companions.bars_names._in_window))
except Exception as error:  # noqa: BLE001 - a test file says what broke and goes on to its verdict
    import traceback
    traceback.print_exc()
    check(f"exception {type(error).__name__}: {error}", False)

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
