"""The TEAMS page (docs/duel/spec-equipes.md, model A): between DUEL and OPTIONS; alone, the host's row only and the
footer saying to invite a friend; HOST by the host's name; the rows following the game, each player alone in his team
at first, his team's button lit; the summary; a click putting a player in a team, written in the log by number; one
team only said; EACH FOR THEMSELVES lit while every player is alone, unlit once teams are arranged, a click lighting
it again; three teams or more, the footer saying enemies may side with a team; a start refused with every player in
one team no longer said once the teams change; a click on the row of a player leaving at that read going to nobody,
nor waiting on the hidden row; during a duel the teams kept, each row keeping only his team's button, a click forgotten
and the footer saying to stop it, every button back once it is over; the
page in French; a guest's game showing no row, a click forgotten, the footer saying only the host arranges the
teams; the names never in the log."""

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
from coop_duel import control_escape, duel, panel_assets, panel_en, panel_fonts, panel_form, panel_fr  # noqa: E402
from coop_duel import panel_model, panel_preferences, panel_theme as t, panel_view, panel_widgets as w  # noqa: E402
from coop_duel import roster  # noqa: E402

fails: list[str] = []


def check(label: str, condition: bool) -> None:
    print(("OK   " if condition else "ECHEC") + " | " + label)
    if not condition:
        fails.append(label)


class Keyboard:
    def GetAsyncKeyState(self, _code: int) -> int:
        return 0


control_escape.user32 = lambda: Keyboard()
panel_assets.texture = lambda _world, name=panel_assets.AVATAR: object()
panel_fonts.build = lambda _root: {"title": object(), "body": object()}
text, visible = panel_fixture.text, panel_fixture.visible


def opened(language: str = "EN"):
    panel_preferences.language.value = language
    model = panel_model.Model(coop_duel.mod)
    _root, widgets = panel_view.build_view(SimpleNamespace(), model)
    form = panel_form.PanelForm({name: (lambda widget=widget: widget) for name, widget in widgets.items()}, model)
    widgets["nav:teams"].SetIsChecked(True)
    form.poll()
    return form, widgets


def click(form, widgets, name: str):
    widgets[name].SetIsChecked(True)
    return form.poll()


def lit(widgets, name: str) -> bool:
    return widgets[f"{name}_fill"].calls["SetBrushColor"][0] == w.linear(t.colour("COLOR_GOLD"))


def lines(event: str) -> list[dict]:
    return [line for line in game_fixture.duel_lines(state) if line["event"] == event]


Character = game_fixture.Character
host = Character("OakCharacter_1", "Kevin", local=True)
venus, raph = Character("OakCharacter_2", "Venus"), Character("OakCharacter_3", "Raph")
roster.ROSTER.seats.clear()
game.seat(host)
form, widgets = opened()
check("the page between DUEL and OPTIONS", tuple(form.model.pages) == ("duel", "teams", "options")
      and text(widgets, "heading:teams") == "TEAMS")
check("alone: the host's row only, no summary, the footer says to invite a friend", visible(widgets, "teams_row:0")
      and not visible(widgets, "teams_row:1") and text(widgets, "teams_summary") == ""
      and text(widgets, "notice") == panel_en.TEXT["teams_alone"])
check("HOST by the host's name, EACH FOR THEMSELVES greyed with nobody to arrange", text(widgets, "teams_name:0")
      == "Kevin" and text(widgets, "teams_host:0") == "HOST" and not lit(widgets, "teams_each"))
game.seat(host, venus, raph)
click(form, widgets, "nav:options")
check("players coming do not swallow a click on another page", form.model.pages[form.page] == "options")
click(form, widgets, "nav:teams")
check("the rows follow the game, each player alone in his team, his button lit", visible(widgets, "teams_row:2")
      and not visible(widgets, "teams_row:3") and text(widgets, "teams_name:1") == "Venus"
      and lit(widgets, "teams_pick:1:2") and not lit(widgets, "teams_pick:1:1") and text(widgets, "teams_host:1") == "")
check("each for themselves: the button lit, no summary; three teams, the footer says enemies may side with a team",
      lit(widgets, "teams_each") and text(widgets, "teams_summary") == ""
      and text(widgets, "notice") == panel_en.TEXT["teams_allies"])
click(form, widgets, "teams_pick:2:1")
check("a click puts a player in a team, written by number", roster.ROSTER.seats[2].team == 1
      and lit(widgets, "teams_pick:2:1") and text(widgets, "teams_summary") == "2 VS 1"
      and not lit(widgets, "teams_each") and lines("team chosen")[-1]["player"] == "J3"
      and lines("team chosen")[-1]["team"] == 1)
check("two teams: the footer says how", text(widgets, "notice") == panel_en.TEXT["ready_teams"])
click(form, widgets, "teams_pick:1:1")
check("one team only said", text(widgets, "teams_summary") == "ONE TEAM ONLY")
coop_duel.mod.enable()
click(form, widgets, "nav:duel")
click(form, widgets, "duel_start")
check("a start refused with every player in one team, said on DUEL",
      text(widgets, "notice") == panel_en.TEXT["start_one_team"])
click(form, widgets, "nav:teams")
click(form, widgets, "teams_each")
check("EACH FOR THEMSELVES puts every player alone again, lit", [seat.team for seat in roster.ROSTER.seats] == [
    1, 2, 3] and lit(widgets, "teams_each") and text(widgets, "teams_summary") == "")
click(form, widgets, "nav:duel")
check("the teams changed, the refusal no longer said on DUEL", text(widgets, "notice") == panel_en.TEXT["ready_duel"])
click(form, widgets, "nav:teams")
chosen = len(lines("team chosen"))
widgets["teams_pick:1:1"].SetIsChecked(True)
game.seat(host, raph)
form.poll()
check("a click on the row of a player leaving at that read goes to nobody, not to the one now on his row", [
    (seat.number, seat.team) for seat in roster.ROSTER.seats] == [(1, 1), (3, 3)]
      and len(lines("team chosen")) == chosen)
widgets["teams_pick:2:1"].SetIsChecked(True)
form.poll()
game.seat(host, venus, raph)
form.poll()
check("a hidden row's button holds no click for the next player on it", not widgets["teams_pick:2:1"].IsChecked()
      and len(lines("team chosen")) == chosen and [seat.team for seat in roster.ROSTER.seats] == [1, 2, 3])
duel.start("EN")
form, widgets = opened()
click(form, widgets, "teams_pick:1:1")
check("during a duel the teams are kept: a click forgotten, the footer says to stop it first",
      roster.ROSTER.seats[1].team == 2 and lit(widgets, "teams_pick:1:2") and not lit(widgets, "teams_pick:1:1")
      and text(widgets, "notice") == panel_en.TEXT["teams_locked"])
check("during a duel each row keeps only his team's button", visible(widgets, "teams_pick:1:2_box") and not any(
    visible(widgets, f"teams_pick:{row}:{number}_box") for row, team in ((0, 1), (1, 2), (2, 3))
    for number in (1, 2, 3, 4) if number != team))
duel.stop("stopped")
form.poll()
check("the duel over, every button back in the window still open", all(
    visible(widgets, f"teams_pick:{row}:{number}_box") for row in range(3) for number in (1, 2, 3, 4)))
form, widgets = opened("FR")
click(form, widgets, "teams_pick:2:1")
check("the page in French", text(widgets, "heading:teams") == "ÉQUIPES" and text(widgets, "teams_host:0") == "HÔTE"
      and text(widgets, "teams_each_label") == "CHACUN POUR SOI" and text(widgets, "teams_summary") == "2 CONTRE 1")
game.seat(Character("OakCharacter_9", "Them", role=game_fixture.PROXY), venus)
form.poll()
check("in a guest's game, the footer says only the host arranges the teams",
      text(widgets, "notice") == panel_fr.TEXT["teams_not_host"])
check("in a guest's game, no row of the last game hosted, no summary, EACH FOR THEMSELVES unlit",
      not any(visible(widgets, f"teams_row:{index}") for index in range(4)) and text(widgets, "teams_summary") == ""
      and not lit(widgets, "teams_each"))
kept = [seat.team for seat in roster.ROSTER.seats]
click(form, widgets, "teams_pick:1:3")
click(form, widgets, "teams_each")
check("in a guest's game, a click forgotten, the seats kept for the next game hosted",
      [seat.team for seat in roster.ROSTER.seats] == kept)
logged = "\n".join(state["logs"])
check("the names never in the log", not any(name in logged for name in ("Kevin", "Venus", "Raph")))

print(f"RESULTAT: {'OK' if not fails else f'{len(fails)} ECHEC(S)'}")
sys.exit(1 if fails else 0)
