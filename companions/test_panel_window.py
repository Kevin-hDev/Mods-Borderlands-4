"""Companions' window as built and polled, every module of it as it is, the game faked (companion_fixture.py,
panel_fixture.py): the pages VAULT HUNTERS, ALLIES and SETTINGS (sketch A, decision 68 of docs/renforts), no UNDO nor
RESTORE; on a card page, the team's count and who is in it, the page's cards only, a card's name adding one more,
written at once, its count and « − » shown, a ninth refused and said, « − » taking the last one away; the outfit only
on the card of the hunter the player plays, chosen and written; LAUNCH THE TEAM refused with no companion, starting
the team with the settings and closing the window without the mods list; reopened, the cards locked under a line,
STOP THE TEAM stopping it and the window kept; a greyed button takes no click, as in the game; It Follows leading
the team, copies of the companions' code of two versions, or an It Follows too old in the game: the cards and the
settings greyed under the line that says why, LAUNCH THE TEAM greyed, the footer saying why; Companions disabled:
LAUNCH THE TEAM greyed, the footer saying where to enable it; the main menu and a saving under way said. The
SETTINGS page: its title, the five sliders with their values and ends in words (×4, 30 %, NEVER, +20 %, 45 s), in
French too, greyed while the team is on; OPTIONS under them, the bars' row only with their package in the game; the
menu's key NONE at first, chosen and written, the team's F8, the other key refused and given back; the key that opens
the window closing it. The footer's sentence on each page. The pause looked at by every poll. The menu's key NONE in
French and Chinese too."""

import json
import sys
import types

import sdk_stubs

state = sdk_stubs.install()

import panel_fixture  # noqa: E402

panel_fixture.install()

import companion_fixture as fake  # noqa: E402
import companions  # noqa: E402
from companions import game_pause, open_key, panel_assets, panel_fonts, panel_form, panel_model  # noqa: E402
from companions import panel_team, panel_view, session, settings, team_key  # noqa: E402
from companions import panel_cards  # noqa: E402
from companions.characters.companions import bars, owners, player_paint, team as team_module  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


def notes(event: str) -> list[dict]:
    found = [json.loads(text.removeprefix("[Companions] ")) for text in state["info"]
             if text.startswith("[Companions] {")]
    return [line for line in found if line["event"] == event]


panel_assets.texture = lambda _world, name=panel_assets.AVATAR: object()
panel_fonts.build = lambda _root: {"title": object(), "body": object()}
mod = companions.mod
model = panel_model.Model(mod)
game = fake.Game(state)
watched: list = []
game_pause.watch = lambda: watched.append(1)
player_paint.played_by = lambda _pc: "Vex"
bars.installed = lambda *_args, **_kwargs: False


def window():
    _root, made = panel_view.build_view(object(), model)
    return made, panel_form.PanelForm({name: (lambda item=item: item) for name, item in made.items()}, model)


def enabled(name: str) -> bool:
    return widgets[name].calls.get("SetIsEnabled", (True,))[0] is True


def press(name: str):
    """A click on that button; a greyed one takes none, as the game's CheckBox (decisions.md, line 61)."""
    if enabled(name):
        widgets[name].SetIsChecked(True)
    return form.poll()


def text(name: str) -> str:
    return panel_fixture.text(widgets, name)


def shown(name: str) -> bool:
    return panel_fixture.visible(widgets, name)


def go(page: str) -> None:
    press(f"nav:{page}")


widgets, form = window()
check("three pages: VAULT HUNTERS, ALLIES, SETTINGS", model.pages == ("hunters", "allies", "settings")
      and [text(f"nav:{page}_label") for page in model.pages] == ["VAULT HUNTERS", "ALLIES", "SETTINGS"])
check("no UNDO nor RESTORE", "undo" not in widgets and "restore" not in widgets)
check("the hunters' page: its cards only, its sentence beside the title", "mate:Vex" in widgets
      and text("heading:hunters") == "VAULT HUNTERS" and "weapons only" in text("group:hunters"))
check("a card out of the team: no count, no « − », not even its frame", not shown("mate_times:Vex")
      and not shown("mate_minus_box:Vex"))
check("no team yet: TEAM 0 / 8, said", text("team_count:hunters") == "TEAM 0 / 8"
      and text("team_who:hunters").startswith("No companion yet"))
check("the footer's sentence", text("notice") == "Choose a companion to add it to the team, then LAUNCH THE TEAM.")
press("mate_add:Vex")
press("mate_add:Vex")
check("a card's name adds one more, written at once", settings.team.value == ["Vex", "Vex"]
      and text("mate_times_text:Vex") == "×2" and shown("mate_times:Vex") and shown("mate_minus_box:Vex")
      and text("team_count:hunters") == "TEAM 2 / 8" and text("team_who:hunters") == "VEX ×2")
check("the outfit on the card of the hunter the player plays only", shown("mate_outfit_line:Vex")
      and not shown("mate_outfit_line:Rafa"))
press("mate_outfit:Vex:player")
check("his outfit chosen, written", settings.outfits.value == {"Vex": "player"})
press("mate_minus:Vex")
check("« − » takes one away", settings.team.value == ["Vex"])
settings.team.value = ["Rafa"] * 8
form.refresh_labels(widgets)
press("mate_add:Vex")
check("a ninth refused, said with the team's most", settings.team.value == ["Rafa"] * 8
      and text("notice") == "The team is full: 8 companions at most.")
settings.team.value = []
form.refresh_labels(widgets)
press("team_launch:hunters")
check("no companion: the launch refused, said, the team never asked", not session.team_on()
      and text("notice").startswith("Add at least") and notes("companions_launch_pressed") == [])
go("allies")
check("the allies' page", text("heading:allies") == "ALLIES" and "mate:Crankus" in widgets)
check("Lilith, Lilith Phoenix and Moxxi after the allies, no outfit on their cards (decision 78)",
      [kind.name for kind in panel_cards.PAGES["allies"]][4:] == ["Lilith", "Lilith Phoenix", "Moxxi"]
      and all(f"mate:{name}" in widgets and f"mate_outfit_line:{name}" not in widgets
              for name in ("Lilith", "Lilith Phoenix", "Moxxi")))
press("mate_add:Crankus")
settings.health.value = 7
check("LAUNCH THE TEAM: started with the settings, the window closing without the mods list",
      press("team_launch:allies") == "leave" and session.team_on()
      and notes("team_start")[-1]["tuning"]["Crankus"][0] == 7.0)
settings.health.value = 4

widgets, form = window()
check("reopened while it is on: the cards locked under a line", text("team_locked:allies") == "Stop the team to "
      "change it." and shown("team_locked:allies") and text("team_launch:allies_label") == "STOP THE TEAM")
check("a locked card's buttons greyed", widgets["mate_add:Crankus"].calls["SetIsEnabled"][0] is False)
press("mate_add:Crankus")
check("a locked card takes no click: nothing changed", settings.team.value == ["Crankus"]
      and text("notice") == "Your team follows you. Stop it here to change it.")
go("settings")
check("the settings greyed while the team is on, said", not widgets["setting:health_times"].calls.get(
      "SetIsEnabled", (True,))[0] and shown("settings_locked"))
check("the bars' row left to set while the team runs: they are read at each publish", enabled("setting:companion_bars"))
go("allies")
session.stop_team()
form.poll()
check("the team stopped while the window is open: the page follows", text("team_launch:allies_label") ==
      "LAUNCH THE TEAM" and not shown("team_locked:allies"))
session.start_team(["Crankus"])
form.poll()
check("STOP THE TEAM: stopped, the window kept", press("team_launch:allies") is False and not session.team_on()
      and text("notice").startswith("The team stopped"))

widgets, form = window()
go("settings")
check("the settings' title and its sentence", text("heading:settings") == "TEAM SETTINGS"
      and text("group:settings") == "For all your companions.")
check("the values in words: ×4, 30%, NEVER, +20%, 45 s", [text(f"value:{option.identifier}") for option in
      settings.TEAM] == ["×4", "30%", "NEVER", "+20%", "45 s"])
check("the ends in words", [(text(f"low:{option.identifier}"), text(f"high:{option.identifier}")) for option in
      settings.TEAM] == [("×1", "×20"), ("0%", "100%"), ("NEVER", "120 s"), ("0%", "+50%"), ("10 s", "120 s")])
check("not greyed while the team is off", widgets["setting:health_times"].calls["SetIsEnabled"][0] is True
      and not shown("settings_locked"))
check("OPTIONS under them, the bars' row hidden without their package", text("heading:options") == "OPTIONS"
      and not shown("settings_bars_box"))
check("the footer's sentence", text("notice") == "The team's settings apply to all your companions.")
check("the menu's key: NONE at first; the team's F8", widgets["open_key"].calls["SetNoKeySpecifiedText"][0] ==
      "NONE" and widgets["open_key"].SelectedKey.Key.KeyName == "None"
      and widgets["team_key"].SelectedKey.Key.KeyName == "F8")
press("FR")
check("in French: the values and the words", text("value:shield_refill_s") == "JAMAIS"
      and text("low:shield_refill_s") == "JAMAIS" and text("high:speed_percent") == "+50 %"
      and text("value:shield_percent") == "30 %" and text("heading:settings") == "RÉGLAGES DE L'ÉQUIPE"
      and text("label:back_after_s") == "RETOUR APRÈS LA MORT")
press("EN")
widgets["open_key"].SelectedKey = types.SimpleNamespace(Key=types.SimpleNamespace(KeyName="F11"))
form.poll()
check("a menu key chosen: written, the SDK's keybind given it", open_key.option.value == "F11"
      and open_key.bind.key == "F11")
widgets["team_key"].SelectedKey = types.SimpleNamespace(Key=types.SimpleNamespace(KeyName="F11"))
form.poll()
widgets["team_key"].SelectedKey = types.SimpleNamespace(Key=types.SimpleNamespace(KeyName="F12"))
form.poll()
check("a team key chosen: written, the SDK's keybind given it", team_key.option.value == "F12"
      and team_key.bind.key == "F12")
team_key.option.value = "F8"
team_key.align()
form.refresh_labels(widgets)
widgets["team_key"].SelectedKey = types.SimpleNamespace(Key=types.SimpleNamespace(KeyName="F11"))
form.poll()
check("the other key refused, given back, said", team_key.option.value == "F8"
      and widgets["team_key"].SelectedKey.Key.KeyName == "F8" and text("notice").startswith("That key is already"))
check("the pause looked at by every poll", len(watched) > 10)
check("a key chosen to open the window: a watch closes the window with it too",
      open_key.closer() is not None and open_key.option.value == "F11")
reads = iter([0, 0x8000, 0, 0])
form.closer.api = types.SimpleNamespace(GetAsyncKeyState=lambda _code: next(reads, 0))
form.closer.muted = True
closing = [form.poll() for _ in range(4)]
check("the key chosen to open the window closes it, once up after its press", closing[-1] == "close"
      and closing[:-1] == [False, False, False] and notes("open_key_closes")[-1]["key"] == "F11")
open_key.option.value = None
open_key.align()
widgets, form = window()
check("with no key to open it, no watch closes the window", form.closer is None and open_key.bind.key is None)

bars.installed = lambda *_args, **_kwargs: True
widgets, form = window()
go("settings")
check("the bars' package in the game: their row shown", shown("settings_bars_box"))
bars.installed = lambda *_args, **_kwargs: False

OUTDATED = ("Your It Follows is too old to share the companions, even when switched off: update it, then restart "
            "the game.")
sys.modules["it_follows.companions.team"] = types.ModuleType("it_follows.companions.team")
widgets, form = window()
check("an It Follows too old in the game: the line says to update it, then restart", text("team_locked:hunters")
      == OUTDATED and shown("team_locked:hunters"))
settings.team.value = ["Vex"]
check("LAUNCH THE TEAM greyed, takes no click; the footer says why", not enabled("team_launch:hunters")
      and press("team_launch:hunters") is False and not session.team_on() and text("notice") == OUTDATED)
check("the cards greyed too", not enabled("mate_add:Vex"))
del sys.modules["it_follows.companions.team"]

owners.reset_for_tests()
owners.switched_on(team_module.OWNER)
owners.switched_on("it_follows", first=True)
widgets, form = window()
check("It Follows leading: the line says so", text("team_locked:hunters") == "It Follows controls the companions. "
      "Use its menu." and shown("team_locked:hunters"))
settings.team.value = ["Vex"]
painted: dict = {}
real_paint = panel_cards.b.paint
panel_cards.b.paint = lambda made, name, style: (painted.__setitem__(name, style), real_paint(made, name, style))
form.refresh_labels(widgets)
panel_cards.b.paint = real_paint
check("LAUNCH THE TEAM painted greyed, never yellow and dead", painted.get("team_launch:hunters") == "disabled")
check("LAUNCH THE TEAM greyed, takes no click; the footer says why, no invitation to launch",
      not enabled("team_launch:hunters") and press("team_launch:hunters") is False and not session.team_on()
      and text("notice") == "It Follows controls the companions. Use its menu.")
go("settings")
check("the settings greyed under the same line, the bars' row too: It Follows' own apply",
      not enabled("setting:health_times") and not enabled("setting:companion_bars") and shown("settings_locked")
      and text("settings_locked") == "It Follows controls the companions. Use its menu."
      and text("notice") == "It Follows controls the companions. Use its menu.")
check("the window's key stays: it opens this window", enabled("open_key"))
check("the team's key greyed: it would launch nothing", not enabled("team_key"))
owners.switched_off("it_follows")
form.poll()
go("hunters")
check("It Follows switched off while the window is open: the page follows, LAUNCH THE TEAM back",
      enabled("team_launch:hunters") and not shown("team_locked:hunters") and enabled("mate_add:Vex"))
owners.reset_for_tests()
foreign = types.ModuleType(owners.STATE)
foreign.protocol, foreign.owners = owners.PROTOCOL + 1, {}
sys.modules[owners.STATE] = foreign
widgets, form = window()
MISMATCH = ("It Follows and Companions are at versions that do not work together, so no team starts: update both, "
            "then restart the game.")
check("two versions of the companions' code: said as such, never as It Follows leading",
      text("team_locked:hunters") == MISMATCH and text("notice") == MISMATCH and not enabled("team_launch:hunters"))
owners.reset_for_tests()
widgets, form = window()
sys.modules[owners.STATE] = foreign
check("the two versions met between the paint and the click: the launch refused with the reason as it is now",
      press("team_launch:hunters") is False and not session.team_on() and text("notice") == MISMATCH)
owners.reset_for_tests()

widgets, form = window()
mod.is_enabled = False
form.refresh_labels(widgets)
check("Companions disabled: LAUNCH THE TEAM greyed, the footer says where to enable it",
      not enabled("team_launch:hunters") and text("notice") == "Companions is disabled: enable it at the bottom "
      "left, then launch the team.")
mod.is_enabled = True
form.refresh_labels(widgets)
real_showing = session.main_menu.showing
session.main_menu.showing = lambda _pc: True
press("team_launch:hunters")
check("at the main menu: said", not session.team_on() and text("notice") == "Load a game first, then launch the "
      "team.")
session.main_menu.showing = real_showing
real_start = session.start_team
session.start_team = lambda _names: "unexpected"
press("team_launch:hunters")
session.start_team = real_start
check("an answer of the launch none expected: said as such, never as none chosen", text("notice") ==
      "The team did not start. The reason is in unrealsdk.log.")
real_flush = form.flush
form.flush = lambda _widgets: False
press("team_launch:hunters")
form.flush = real_flush
check("the choices being saved: said, nothing started", not session.team_on()
      and text("notice") == "Your choices are being saved: launch the team again.")
widgets, form = window()
go("settings")
press("FR")
check("the menu's key NONE in French", widgets["open_key"].calls["SetNoKeySpecifiedText"][0] == "AUCUNE")
press("ZH")
check("and in Chinese", widgets["open_key"].calls["SetNoKeySpecifiedText"][0] == "无")
press("EN")
settings.team.value = []

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
