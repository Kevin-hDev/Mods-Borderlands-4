"""It Follows' window as built and polled, every module of it as it is but the session's start, replaced by a run as the
window sees one: the welcome over the window at the first opening, remembered as seen, in two pages, the two modes and
the Horde then the normal mode, holding every click until LET'S GO, and open again for a player who saw its first
edition; the pages HORDE MODE, NORMAL MODE, HISTORY and OPTIONS, no UNDO nor RESTORE; the Horde's page's caution, rows
and START, no row for the killed coming back, the Buff's help without figures, the levels named Level 1 to Level 5, a
choice clicked and written; START refused without a game or with the mod off, said in the footer,
the window kept; START with Kevin's settings, the bar in the window's language, closing the window without the mods
list; the window reopened during the run: the run's card, its level, counts and limit, STOP, the rows locked, the
RUNNING tag, the footer's pause sentence, START and the caution away; STOP: the run stopped, its result over the
window, HISTORY taking it to the history, the run on top; the NORMAL MODE page (decision 80): its sentence, its levels
and the chosen one's help, the allied enemies off, START without a game turning it on, written, the window kept and
waiting, reopened with its card, STOP and its rows locked, its tag on; the Horde's START then replaced by a line, and
refused if read; STOP writing it off; during a Horde run its START replaced by a line, refused if read; START in a game
closing the window; a run that stopped by itself shown at the next opening;
Escape closing the result alone; the words in French; the OPTIONS page's look at the bar, a key chosen and written, a
key refused given back; the key that opens the window closing it; the « ? » beside START and beside STOP opening the
help on how a run goes, in the window's language, closed alone by a click beside it, its CLOSE button or Escape;
the pause looked at by every poll, whatever shows over the window. The Hardcore (decision 89): its card under the
normal mode's, never locked, its progress hidden while it is off; switched on while the mode is on, its progress
shown and the tag at the top; paused, said by the tag; its « ? » opening its help; in French."""

import sys
import time
from types import SimpleNamespace

import sdk_stubs

state = sdk_stubs.install()

import panel_fixture  # noqa: E402

panel_fixture.install()

import it_follows  # noqa: E402
from it_follows import ending, game_pause, kept, open_key, options, panel_assets, panel_fonts, panel_form  # noqa: E402
from it_follows import panel_model  # noqa: E402
from it_follows import panel_preferences as prefs, panel_view, session, texts, welcome  # noqa: E402
from it_follows.normal import options as normal_options  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


panel_assets.texture = lambda _world, name=panel_assets.AVATAR: object()
panel_fonts.build = lambda _root: {"title": object(), "body": object()}
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


class FakeRun:
    """A run as the window sees it (session.live, ending.ended): its level, limit, clock and counts."""

    def __init__(self, settings: object) -> None:
        self.settings, self.ended = settings, []
        self.level = SimpleNamespace(target=settings.level)
        self.clock, self.stats = SimpleNamespace(played=61.9), SimpleNamespace(kills=7, deaths=2)

    def end(self, reason: str) -> None:
        self.ended.append(reason)


started: list = []
real_start = session.start


def start(settings: object) -> str:
    started.append(settings)
    session._state["run"], session._state["began"] = FakeRun(settings), int(time.time()) - 60
    return "started"


watched: list = []
game_pause.watch = lambda: watched.append(True)

try:
    widgets, form = window()
    form.poll()
    check("the pause looked at by every poll, the welcome over the window too", watched)
    check("the welcome over the window at the first opening, remembered as seen at once, its edition 3",
          form.popup == "welcome" and shown("popup:welcome") and welcome.seen.value == welcome.EDITION == 3
          and text("heading:welcome") == "WELCOME TO IT FOLLOWS")
    check("its first page: the two modes, independent, the Horde and its two inspirations, NEXT",
          shown("welcome_page:0") and not shown("welcome_page:1")
          and text("welcome_lead:0").startswith("It Follows holds two modes, independent of each other.")
          and text("welcome_box_title:0:0") == "THE FILM IT FOLLOWS"
          and "Black Ops Zombies".upper() in text("welcome_box_title:0:1")
          and shown("welcome_next_box") and not shown("welcome_go_box") and text("welcome_next_label") == "NEXT")
    check("its caution says what the PC will carry (decisions 54 and 60)",
          text("welcome_caution").startswith("Dozens of enemies, up to over a hundred"))
    check("while it shows, START is not read", press("run_start") is False and not started and form.popup == "welcome")
    widgets["run_start"].SetIsChecked(False)
    check("NEXT turns to the normal mode's page: its levels, still evolving, LET'S GO",
          press("welcome_next") is False and form.popup == "welcome" and shown("welcome_page:1")
          and not shown("welcome_page:0") and text("welcome_lead:1").startswith("The normal mode: play your game")
          and "like three levels of NG+" in text("welcome_lead:1")
          and text("welcome_box_title:1:0") == "THREE LEVELS" and text("welcome_box_title:1:1") == "STILL EVOLVING"
          and "keep evolving" in text("welcome_box_text:1:1") and shown("welcome_go_box")
          and not shown("welcome_next_box") and text("welcome_go_label") == "LET'S GO")
    check("LET'S GO closes it", press("welcome_go") is False and form.popup is None and not shown("popup:welcome"))
    widgets, form = window()
    check("seen once, it does not open again", form.popup is None)
    welcome.seen.value = 1
    widgets, form = window()
    check("seen in its first edition, without the normal mode: it opens again, on its first page",
          form.popup == "welcome" and shown("welcome_page:0") and welcome.seen.value == 3)
    press("welcome_next")
    press("welcome_go")

    check("four pages, HORDE MODE, NORMAL MODE, HISTORY and OPTIONS; no UNDO nor RESTORE",
          [text(f"nav:{key}_label") for key in ("run", "normal", "history", "options")]
          == ["HORDE MODE [BETA]", "NORMAL MODE", "HISTORY", "OPTIONS"]
          and "undo" not in widgets and "restore" not in widgets)
    check("the Horde's page: its title, its caution, START, no run card, no lock, no RUNNING tag, nothing blocked",
          text("heading:run") == "RUN SETTINGS" and shown("run_caution") and shown("run_start_box")
          and not shown("run_live_box") and not shown("run_locked") and not shown("nav_running_tag")
          and not shown("run_blocked") and text("run_start_label") == "START")
    check("no row for the killed coming back; the Buff's help without figures",
          "setting:respawn" not in widgets
          and text("description:buff") == "Buff: the enemies have more health and you take more damage. Buff+: even "
                                          "more.")
    check("the levels named Level 1 to Level 5, never their number",
          [text(f"setting:level:{key}_label") for key in ("25", "40", "60", "80", "100")]
          == ["LEVEL 1", "LEVEL 2", "LEVEL 3", "LEVEL 4", "LEVEL 5"])
    check("the « ? » beside START opens the help on how a run goes", text("run_help_label") == "?"
          and press("run_help") is False and form.popup == "help_run" and shown("popup:help_run")
          and text("heading:popup_help_run") == "HOW A RUN GOES"
          and text("help:help_run").startswith("A run starts quietly: the enemies nearby start chasing you.")
          and "go and find them" in text("help:help_run")
          and "travel across the map" in text("help:help_run"))
    check("while it shows, START is not read", press("run_start") is False and not started
          and form.popup == "help_run")
    widgets["run_start"].SetIsChecked(False)
    check("a click beside it closes the help alone, the window kept", press("popup:help_run:beside") is False
          and form.popup is None and not shown("popup:help_run"))
    press("run_help")
    check("its CLOSE button closes it", press("popup:help_run:close") is False and form.popup is None)
    press("run_help")
    check("Escape closes the help alone", form.escape() is False and form.popup is None)
    check("decision 99: Manage far enemies greyed and locked before any run, the other rows free",
          widgets["setting:manage_far"].calls["SetIsEnabled"] == (False,)
          and widgets["row:manage_far"].calls["SetRenderOpacity"] != (1.0,)
          and widgets["setting:level"].calls["SetIsEnabled"] == (True,)
          and "Manage far" not in text("run_caution_text"))
    check("the footer says START closes the menu", text("notice") == "Ready: press START, the menu closes and the run "
                                                                     "begins.")
    press("setting:level:60")
    check("a level clicked is written", form.flush(widgets) and options.level.value == "60")

    check("START without a game: refused, said, the window kept", press("run_start") is False
          and not session.running() and text("notice") == "No run here: load a game first.")
    mod.is_enabled = False
    check("START with the mod off: said, nothing started", press("run_start") is False and not session.running()
          and text("notice") == "It Follows is off: switch it on, then press START.")
    mod.is_enabled = True
    session.start = start
    check("START with Kevin's settings, the bar in the window's language, closes the window without the mods list",
          press("run_start") == "leave" and started[-1].level == 60 and started[-1].language == "EN")

    widgets, form = window()
    check("reopened during the run: the run's card, its level, counts and limit, STOP",
          shown("run_live_box") and text("heading:run_live") == "RUN IN PROGRESS · LEVEL 3"
          and text("live:kills") == "7" and text("live:deaths") == "2" and text("live:time") == "01:01"
          and text("live:limit") == "" and text("run_stop_label") == "STOP")
    check("the run's rows locked, START and the caution away, the RUNNING tag on, the footer saying the pause",
          widgets["setting:level"].calls["SetIsEnabled"] == (False,) and not shown("run_start_box")
          and not shown("run_caution") and shown("run_locked") and shown("nav_running_tag")
          and text("nav_running") == "RUNNING" and text("notice") == "The game is paused while this menu is open.")
    session._state["run"].stats.kills = 9
    form.poll()
    check("the counts painted again as they change", text("live:kills") == "9")
    check("during the run, the « ? » beside STOP opens the same help", text("live_help_label") == "?"
          and press("live_help") is False and form.popup == "help_run")
    form.escape()

    check("STOP: the run stopped", press("run_stop") is False and not session.running()
          and session._state["run"] is None)
    form.poll()
    check("its result over the window: title, sentence, counts", form.popup == "result" and shown("popup:result")
          and text("heading:result") == "RUN STOPPED"
          and text("result_sentence") == "You held 01:01 at level 3. The enemies stop coming."
          and text("result:kills") == "9" and text("result:time") == "01:01")
    check("the run on top of the history", kept.runs()[0].kills == 9 and kept.runs()[0].end == "stopped"
          and ending.waiting() is None)
    check("HISTORY closes it on the HISTORY page", press("result_history") is False and form.popup is None
          and model.pages[form.page] == "history")
    check("the history's line: level, limit, time held, counts, end; the next line hidden, no empty sentence",
          shown("history_line:0") and text("history:0:level") == "LEVEL 3" and text("history:0:limit") == "UNLIMITED"
          and text("history:0:held") == "01:01" and text("history:0:kills") == "9" and text("history:0:end") == "STOP"
          and text("history:0:when").startswith("TODAY ") and not shown("history_line:1")
          and not shown("history_empty") and text("notice") == "The last 20 runs, kept from one game launch to the "
                                                                "next.")

    session.start = real_start
    press("nav:normal")
    check("the NORMAL MODE page: its title, its sentence, its levels, START; no card, no lock, nothing blocked",
          text("nav:normal_label") == "NORMAL MODE" and text("heading:normal") == "NORMAL MODE"
          and text("group:normal") == "A first overhaul of the game's enemies, still evolving."
          and [text(f"setting:normal_level:{name}_label") for name in ("Bandit", "Senior", "Predator")]
          == ["BANDIT", "SENIOR", "PREDATOR"] and shown("normal_start_box") and not shown("normal_live_box")
          and not shown("normal_locked") and not shown("normal_blocked") and not shown("nav_normal_running_tag")
          and text("notice") == "Ready: press START, the menu closes and the normal mode begins.")
    check("the level's help is the chosen level's sentence, the allied enemies off",
          text("description:normal_level") == "More enemies, a little faster and tougher. They dodge faster and "
                                              "chase you farther. A shield for those without one, if you want."
          and text("label:normal_allies") == "ALLIED ENEMIES" and text("setting:normal_allies_label") == "OFF")
    check("at Bandit the shields' row shown, on (decision 112)", shown("row:normal_shields")
          and shown("description:normal_shields") and text("label:normal_shields") == "SHIELDS"
          and text("setting:normal_shields_label") == "ON")
    check("at Bandit the enemies' speed row hidden (decision 121)", not shown("row:normal_speed")
          and not shown("description:normal_speed"))
    press("setting:normal_level:Senior")
    form.poll()
    check("another level clicked: written, its sentence shown", form.flush(widgets)
          and normal_options.level.value == "Senior"
          and text("description:normal_level") == "Even more enemies, faster and tougher. Quicker dodges, longer "
                                                  "chases. A shield for every enemy without one.")
    check("at Senior the shields' row hidden: always given", not shown("row:normal_shields")
          and not shown("description:normal_shields"))
    check("at Senior the enemies' speed row shown, its two choices, its help (decision 121)",
          shown("row:normal_speed") and shown("description:normal_speed")
          and text("label:normal_speed") == "ENEMY SPEED"
          and [text(f"setting:normal_speed:{name}_label") for name in ("Increased", "Reduced")]
          == ["INCREASED", "REDUCED"]
          and text("description:normal_speed")
          == "Reduced: at Senior and Predator, the enemies run, dodge and strike slower.")
    press("setting:normal_speed:Reduced")
    form.poll()
    check("REDUCED clicked: written, the level read slower", form.flush(widgets)
          and normal_options.speed.value == "Reduced" and normal_options.read().reduced is True)
    press("setting:normal_speed:Increased")
    form.poll()
    check("INCREASED clicked back: written", form.flush(widgets) and normal_options.speed.value == "Increased")
    check("START without a game: the mode on and written so, the window kept, saying it waits for a game",
          press("normal_start") is False and session.normal_on() and normal_options.on.value is True
          and text("notice") == "The normal mode is on: it starts as soon as you are on foot in a loaded game.")
    widgets, form = window()
    press("nav:normal")
    check("reopened: the mode's card, its level, waiting, STOP; its rows locked; its tag on, the Horde's off",
          shown("normal_live_box") and text("heading:normal_live") == "NORMAL MODE ON · SENIOR"
          and text("normal_live_text") == "It starts as soon as you are on foot in a loaded game."
          and text("normal_stop_label") == "STOP" and not shown("normal_start_box") and shown("normal_locked")
          and widgets["setting:normal_level"].calls["SetIsEnabled"] == (False,)
          and shown("nav_normal_running_tag") and not shown("nav_running_tag"))
    press("nav:run")
    check("the Horde's page while the normal mode is on: START and the caution replaced by a line, the footer saying "
          "the pause, not to press START (trial 20)",
          shown("run_blocked") and not shown("run_start_box") and not shown("run_caution")
          and text("run_blocked") == "The normal mode is on: stop it on its page to start a run."
          and text("notice") == "The game is paused while this menu is open.")
    check("START of the Horde read all the same: refused, said in the footer", press("run_start") is False
          and not session.running() and text("notice") == "Stop the normal mode first, then press START.")
    press("nav:normal")
    check("the Hardcore's card under it, never locked, its progress hidden while it is off, no tag at the top",
          text("heading:hardcore") == "HARDCORE"
          and text("group:hardcore") == "A difficulty that rises slowly, all game long."
          and text("label:normal_hardcore") == "HARDCORE" and text("setting:normal_hardcore_label") == "OFF"
          and "SetIsEnabled" not in widgets["setting:normal_hardcore"].calls and text("hardcore_help_label") == "?"
          and not shown("hardcore_progress_box") and not shown("hardcore_badge_box"))
    press("setting:normal_hardcore")
    form.poll()
    check("switched on while the mode is on: written, its progress shown, the tag at the top at 0 %",
          form.flush(widgets) and normal_options.hardcore.value is True and shown("hardcore_progress_box")
          and shown("hardcore_badge_box") and text("hardcore_badge") == "HARDCORE 0%"
          and text("label:normal_hardcore_progress") == "PROGRESS"
          and text("setting:normal_hardcore_progress_label") == "ON")
    press("setting:normal_hardcore_progress")
    form.poll()
    check("its progress paused: said by the tag", form.flush(widgets) and normal_options.progress.value is False
          and text("hardcore_badge") == "HARDCORE 0% · PAUSED")
    check("its « ? » opens the Hardcore's help", press("hardcore_help") is False and form.popup == "help_hardcore"
          and shown("popup:help_hardcore") and text("heading:popup_help_hardcore") == "THE HARDCORE MODE"
          and text("help:help_hardcore").startswith("In Borderlands 4, the enemies' level follows your hunter's")
          and "1% stronger every 100 enemies killed" in text("help:help_hardcore"))
    check("closed alone by Escape", form.escape() is False and form.popup is None)
    check("STOP: written off, the mode off, START back", press("normal_stop") is False
          and normal_options.on.value is False and not session.normal_on() and shown("normal_start_box")
          and not shown("normal_live_box") and not shown("nav_normal_running_tag"))
    session._state["run"] = FakeRun(options.read())
    form.poll()
    check("during a Horde run, the normal page says to stop it, START away, the footer saying the pause",
          shown("normal_blocked") and not shown("normal_start_box")
          and text("normal_blocked") == "A Horde run is going: stop it to turn the normal mode on."
          and text("notice") == "The game is paused while this menu is open.")
    check("START of the normal mode read all the same: refused, nothing written",
          press("normal_start") is False and not session.normal_on() and normal_options.on.value is False
          and text("notice") == "Stop the Horde run first, then press START.")
    session._state["run"] = None
    state["pc"] = SimpleNamespace(OakCharacter=SimpleNamespace(freed=False))
    form.poll()
    check("START in a game: the mode plays, the window closes without the mods list",
          press("normal_start") == "leave" and session.normal_live() == session.NormalLive("Senior", True))
    widgets, form = window()
    press("nav:normal")
    check("reopened while it plays: its sentence",
          text("normal_live_text") == "The enemies are stronger while you play. STOP gives them back as the game made "
                                      "them.")
    press("normal_stop")
    state["pc"] = None

    ending._waiting["run"] = kept.runs()[0]._replace(end="interrupted")
    widgets, form = window()
    check("a run that stopped by itself shown at the next opening, saying why",
          form.popup == "result" and text("heading:result") == "RUN STOPPED BY ITSELF"
          and "unrealsdk.log" in text("result_sentence"))
    check("Escape closes the result alone", form.escape() is False and form.popup is None)

    check("French chosen", press("FR") is False and model.language == "FR")
    check("the words in French: the history, the end, the date",
          text("heading:history") == "20 DERNIERS RUNS" and text("history_head:when") == "QUAND"
          and text("history:0:level") == "NIVEAU 3" and text("history:0:limit") == "ILLIMITÉE"
          and text("history:0:when").startswith("AUJOURD'HUI ") and text("nav:history_label") == "HISTORIQUE")
    press("nav:run")
    press("run_help")
    check("the help in French", text("heading:popup_help_run") == "COMMENT SE DÉROULE UN RUN"
          and text("help:help_run").startswith("Un run démarre tranquillement : les ennemis aux alentours "
                                               "commencent à te poursuivre.")
          and "va les chercher" in text("help:help_run")
          and "déplace-toi à travers la carte" in text("help:help_run"))
    form.escape()
    check("the Horde's page in French", text("heading:run") == "RÉGLAGES DU RUN"
          and text("nav:run_label") == "MODE HORDE [BETA]"
          and text("setting:level:25_label") == "NIVEAU 1" and text("setting:speed:Normal_label") == "NORMALE"
          and text("description:buff") == "BUFF : les ennemis ont plus de vie et tu reçois plus de dégâts. BUFF+ : "
                                          "encore plus."
          and text("notice") == "Prêt : appuie sur START, le menu se ferme et le run commence.")
    press("nav:normal")
    check("the normal page in French", text("nav:normal_label") == "MODE NORMAL"
          and text("heading:normal") == "MODE NORMAL" and text("label:normal_allies") == "ENNEMIS ALLIÉS"
          and text("description:normal_level") == "Encore plus d'ennemis, plus rapides et plus résistants. Des "
                                                  "esquives plus vives, des poursuites plus longues. Un bouclier pour "
                                                  "chaque ennemi qui n'en a pas."
          and text("label:normal_shields") == "BOUCLIERS"
          and text("label:normal_speed") == "VITESSE DES ENNEMIS"
          and [text(f"setting:normal_speed:{name}_label") for name in ("Increased", "Reduced")]
          == ["AUGMENTÉE", "RÉDUITE"]
          and text("notice") == "Prêt : appuie sur START, le menu se ferme et le mode normal commence.")
    check("the Hardcore in French", text("heading:hardcore") == "HARDCORE"
          and text("label:normal_hardcore_progress") == "PROGRESSION"
          and text("hardcore_badge") == "HARDCORE 0 % · EN PAUSE"
          and press("hardcore_help") is False and text("heading:popup_help_hardcore") == "LE MODE HARDCORE"
          and "1 % tous les 100 ennemis tués" in text("help:help_hardcore"))
    form.escape()
    press("EN")
    press("nav:run")

    press("nav:options")
    check("the OPTIONS page: the bar shown, its look at the size chosen, the key F5",
          text("heading:options") == "OPTIONS" and text("bar_look") == "KILLS 152   DEATHS 1   HORDE 64   HARDCORE 1%   12:47"
          and widgets["bar_look"].Font.Size == 19.0 and widgets["open_key"].SelectedKey.Key.KeyName == "F5")
    press("setting:bar_size:Large")
    check("a size clicked: the look at that size", widgets["bar_look"].Font.Size == 24.0)
    widgets["open_key"].SetSelectedKey(SimpleNamespace(Key=SimpleNamespace(KeyName="F6")))
    form.poll()
    check("a key chosen is written, the SDK's key given it",
          open_key.option.value == "F6" and open_key.bind.key == "F6")
    widgets["open_key"].SetSelectedKey(SimpleNamespace(Key=SimpleNamespace(KeyName="LeftMouseButton")))
    form.poll()
    check("a key refused: the chosen one shown again", open_key.option.value == "F6"
          and widgets["open_key"].SelectedKey.Key.KeyName == "F6")
    widgets["open_key"].selecting = True
    check("the key's field waiting for a key: Escape cancels the wait alone", form.selecting())
    widgets["open_key"].selecting = False

    reads = iter([0, 0x8000, 0, 0])
    form.closer.api = SimpleNamespace(GetAsyncKeyState=lambda _code: next(reads, 0))
    form.closer.muted = True
    closing = [form.poll() for _ in range(4)]
    check("the key that opens the window closes it, once up after its press", closing[-1] == "close"
          and closing[:-1] == [False, False, False])
    check("the language and the page kept for the next opening", prefs.language.value == "EN")
except Exception as error:
    import traceback

    traceback.print_exc()
    fails.append(f"exception {type(error).__name__}: {error}")
    print(f"ECHEC | exception {type(error).__name__}: {error}")

print("RESULTAT:", "TOUS LES TESTS PASSENT" if not fails else f"{len(fails)} ECHEC(S)")
sys.exit(1 if fails else 0)
