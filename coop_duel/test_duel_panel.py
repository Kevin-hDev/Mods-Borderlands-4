"""Co-op Duel's window: built whole in the plain frame under the mod's name, its pages DUEL, TEAMS and OPTIONS, no UNDO nor RESTORE;
how a duel goes and START DUEL while no duel goes on; START DUEL with the mod off refused in the footer; a refused start
said with its cause, the window kept, nothing changed; a started duel closing the window without the mods list, the
score and STOP DUEL shown at the next opening, START hidden; the score followed while the window is open; STOP DUEL
ending the duel and bringing START back; the texts in French; every text the window asks for in both languages.
OPTIONS: the two keys' fields showing F9 and N; a key chosen written and given to its keybind; the other shortcut's
key refused, the field showing its own again; Escape kept while a field waits for a key; the left button refused
without a word; the open key's field refusing N; a failed save said, the field showing its key again; the footer
cleared by a save after a refusal; a refused start not shown on OPTIONS; F9 pressed then released closing the window,
never the press that opened it, never while a field waits for a key."""

import sys
from types import SimpleNamespace

import sdk_stubs

state = sdk_stubs.install()

import panel_fixture  # noqa: E402

panel_fixture.install()

import game_fixture  # noqa: E402

game = game_fixture.install(state)
panel_fixture.Widget.RemoveFromParent = lambda self: setattr(self, "on_screen", False)

import coop_duel  # noqa: E402
from coop_duel import control_escape  # noqa: E402
from coop_duel import duel, keys, panel_assets, panel_en, panel_fonts, panel_form, panel_fr  # noqa: E402
from coop_duel import panel_model, panel_preferences, panel_theme as theme, panel_view  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


panel_assets.texture = lambda _world, name=panel_assets.AVATAR: object()


class Keyboard:
    """Windows' key reader as the closing watch reads it: each read takes the next state, then the key is up."""

    def __init__(self) -> None:
        self.states: list[int] = []

    def GetAsyncKeyState(self, _code: int) -> int:
        return self.states.pop(0) if self.states else 0


keyboard = Keyboard()
# Never the real keyboard: the window's watches read this one.
control_escape.user32 = lambda: keyboard
panel_fonts.build = lambda _root: {"title": object(), "body": object()}
text, visible = panel_fixture.text, panel_fixture.visible


def opened(language: str = "EN"):
    panel_preferences.language.value = language
    model = panel_model.Model(coop_duel.mod)
    _root, widgets = panel_view.build_view(SimpleNamespace(), model)
    form = panel_form.PanelForm({name: (lambda widget=widget: widget) for name, widget in widgets.items()}, model)
    return form, widgets


def click(form, widgets, name: str):
    widgets[name].SetIsChecked(True)
    return form.poll()


form, widgets = opened()
check("built whole in the plain frame, under the mod's name", theme.BRAND == "CO-OP DUEL"
      and tuple(form.model.pages) == ("duel", "teams", "options") and len(widgets["pages"].children) == 3)
check("no UNDO nor RESTORE in the footer", "undo" not in widgets and "restore" not in widgets)
check("how a duel goes, and START DUEL while no duel goes on", text(widgets, "duel_how") == panel_en.TEXT["duel_how"]
      and text(widgets, "duel_start_label") == "START DUEL" and visible(widgets, "duel_start_box")
      and not visible(widgets, "duel_live"))
check("the footer says how to start", text(widgets, "notice") == panel_en.TEXT["ready_duel"])

coop_duel.mod.disable()
check("START DUEL with the mod off: refused in the footer", click(form, widgets, "duel_start") is False
      and text(widgets, "notice") == panel_en.TEXT["start_off"] and duel.live() is None)
coop_duel.mod.enable()

host = game_fixture.Character("OakCharacter_1", "Kevin", local=True)
guest = game_fixture.Character("OakCharacter_2", "Venus")
game.seat(host)
check("a refused start said with its cause, the window kept", click(form, widgets, "duel_start") is False
      and text(widgets, "notice") == panel_en.TEXT["start_no_guest"] and duel.live() is None)

game.seat(host, guest)
check("a started duel closes the window without the mods list", click(form, widgets, "duel_start") == "leave"
      and duel.live() is not None)

form, widgets = opened()
check("at the next opening: the score and STOP DUEL, START hidden", visible(widgets, "duel_live")
      and not visible(widgets, "duel_start_box") and text(widgets, "duel_score") == "Kevin  0 - 0  Venus"
      and text(widgets, "duel_stop_label") == "STOP DUEL" and text(widgets, "notice") == panel_en.TEXT["ready_on"])
duel._live["duel"].score.won(1)
form.poll()
check("the score followed while the window is open", text(widgets, "duel_score") == "Kevin  1 - 0  Venus")
check("STOP DUEL ends the duel and brings START back", click(form, widgets, "duel_stop") is False
      and duel.live() is None and visible(widgets, "duel_start_box") and not visible(widgets, "duel_live")
      and game.teams.GetTeam(guest).name == "Team_Player")

form, widgets = opened("FR")
check("the texts in French", text(widgets, "duel_start_label") == "LANCER LE DUEL"
      and text(widgets, "heading:duel") == "DUEL" and text(widgets, "notice") == panel_fr.TEXT["ready_duel"])

asked = {"options", "ready_options", "open_key_label", "open_key_hint", "duel_key_label", "duel_key_hint",
         "press_key", "key_taken", "banner_round", "banner_refused", "duel", "duel_how", "start", "stop", "host",
         "banner_start", "banner_over", "banner_draw", "team_name", "player_fallback", "ready_duel",
         *(f"stop_{why}" for why in duel.SAID), "teams", "teams_each", "teams_vs", "teams_one", "ready_teams",
         "teams_allies", "teams_alone", "teams_locked", "teams_not_host",
         "ready_on", "start_off", "start_refused", *(f"start_{refusal}" for refusal in duel.REFUSALS)}
check("every text the window asks for, in both languages", asked <= panel_en.TEXT.keys()
      and asked <= panel_fr.TEXT.keys())
check("the French differs from the English where it is words", all(
    panel_fr.TEXT[key] != panel_en.TEXT[key] for key in asked - {"duel", "banner_start", "banner_refused", "options"}))



def chosen(widgets: dict, name: str, key: str) -> None:
    widgets[name].SelectedKey = SimpleNamespace(Key=SimpleNamespace(KeyName=key))


def field(widgets: dict, name: str) -> str:
    return widgets[name].calls["SetSelectedKey"][0].Key.KeyName


form, widgets = opened()
check("the two keys' fields showing F9 and N", field(widgets, "open_key") == "F9" and field(widgets, "duel_key") == "N"
      and text(widgets, "duel_key_label") == "START OR STOP THE DUEL")
chosen(widgets, "duel_key", "K")
form.poll()
for _step in range(20):
    form.poll()
check("a key chosen written and given to its keybind", keys.DUEL.option.value == "K" and keys.DUEL.bind.key == "K")
chosen(widgets, "duel_key", "F9")
form.poll()
check("the other shortcut's key refused, the field showing its own again", keys.DUEL.key() == "K"
      and field(widgets, "duel_key") == "K" and text(widgets, "notice") == panel_en.TEXT["key_taken"])
widgets["open_key"].selecting = True
check("Escape kept while a field waits for a key", form.selecting())
widgets["open_key"].selecting = False

chosen(widgets, "duel_key", "G")
for _step in range(20):
    form.poll()
# The window stays on DUEL: its own sentence comes back once the refusal is gone.
check("the footer cleared by a save after a refusal", keys.DUEL.key() == "G"
      and text(widgets, "notice") == panel_en.TEXT["ready_duel"])
chosen(widgets, "duel_key", "LeftMouseButton")
form.poll()
check("the left button refused without a word", keys.DUEL.key() == "G" and field(widgets, "duel_key") == "G"
      and text(widgets, "notice") == panel_en.TEXT["ready_duel"])
chosen(widgets, "open_key", "G")
form.poll()
check("the open key's field refusing the duel's key", keys.OPEN.key() == "F9" and field(widgets, "open_key") == "F9")
saves = form.model.save
form.model.save = lambda _changes: False
chosen(widgets, "open_key", "F8")
form.poll()
check("a failed save said, the field showing its key again", keys.OPEN.key() == "F9"
      and field(widgets, "open_key") == "F9" and text(widgets, "notice") == panel_en.TEXT[form.failure_notice()])
form.model.save = saves

form, widgets = opened()
game.seat(host)
click(form, widgets, "duel_start")
widgets["nav:options"].SetIsChecked(True)
form.poll()
check("a refused start not shown on OPTIONS", text(widgets, "notice") == panel_en.TEXT["ready_options"])

DOWN, PRESSED = control_escape.DOWN, control_escape.PRESSED
form, widgets = opened()
keyboard.states = [DOWN, DOWN, 0]
results = [form.poll() for _ in range(3)]
check("the press that opened the window never closes it", "close" not in results)
keyboard.states = [DOWN | PRESSED, 0, 0]
check("F9 pressed then released closes the window", "close" in [form.poll() for _ in range(3)])
form, widgets = opened()
keyboard.states = [0]
form.poll()
widgets["duel_key"].selecting = True
keyboard.states = [DOWN | PRESSED, 0, 0]
check("F9 never closes it while a field waits for a key", "close" not in [form.poll() for _ in range(3)])
widgets["duel_key"].selecting = False

print(f"RESULTAT: {'OK' if not fails else f'{len(fails)} ECHEC(S)'}")
sys.exit(1 if fails else 0)
