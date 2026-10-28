"""The TEAMS page (Kevin, 17 October 2026, docs/duel/spec-equipes.md, model A): EACH FOR THEMSELVES, lit while every
player is alone in his team, a click putting them so (Kevin, after trial 3: unlit at all times, it showed neither what
it does nor whether it is on); the line that sums up arranged teams, then a row a player, his name, HOST by the host's,
and the buttons 1 2 3 4, his team's lit. The rows follow the game as it goes, read from roster.py at each poll: four
are built, a game holding four players, the unused ones hidden. A click is read against the rows as they were shown,
so that it never goes to a player who took the row of one just gone. While a duel goes on the teams are kept, as the
duel holds them: each row keeps only his team's button (Kevin, 17 October 2026, choice A: the others, looking as
always, seemed clickable while a click did nothing), the footer saying to stop the duel first. In a guest's game no
row is shown: that game's host arranges its teams, and the seats of the last game hosted wait for the next."""

from typing import Any

from . import duel, panel_buttons as b, panel_i18n as i18n, panel_pages as p, panel_text as tx
from . import panel_theme as t, panel_widgets as w, report, roster, teams
from .panel_duel import visible

ROWS = roster.MAX_SEATS


def _pick(index: int, team: int) -> str:
    return f"teams_pick:{index}:{team}"


def page(owner: Any, group: Any, key: str, widgets: dict, template: Any) -> Any:
    scroll, body = p.scrolling_body(owner, template)
    rows = p.card(body, widgets, key)
    w.column(rows, b.button(rows, widgets, "teams_each", "action", template, "secondary"), halign="Left")
    widgets["teams_summary"] = tx.text(rows, "", "value")
    w.column(rows, widgets["teams_summary"], padding=w.pad(t.SPACE_4, 0, t.SPACE_2))
    for index in range(ROWS):
        line = w.new("HorizontalBox", rows)
        widgets[f"teams_name:{index}"] = tx.text(line, "", "label")
        w.row(line, widgets[f"teams_name:{index}"], fill=True, valign="Center")
        widgets[f"teams_host:{index}"] = tx.text(line, "", "tag")
        w.row(line, widgets[f"teams_host:{index}"], padding=w.pad(0, t.SPACE_3), valign="Center")
        for team in roster.TEAMS:
            name = _pick(index, team)
            widgets[f"{name}_box"] = b.button(line, widgets, name, "lang", template, "lang_off")
            w.row(line, widgets[f"{name}_box"], padding=w.pad(0, 0, 0, t.SPACE_2), valign="Center")
        widgets[f"teams_row:{index}"] = line
        w.column(rows, line, padding=w.pad(t.SPACE_2, 0))
    return scroll


def shown() -> list[roster.Seat]:
    """The seats the page shows: none in a guest's game."""
    return [] if roster.ROSTER.where == roster.GUEST else roster.ROSTER.seats[:ROWS]


def each_alone() -> bool:
    """Every player shown alone in his team, two players at least."""
    groups = roster.ROSTER.groups().values()
    return len(shown()) >= 2 and all(len(seats) == 1 for seats in groups)


def summary(language: str) -> str:
    """Arranged teams in a few words: ONE TEAM ONLY, or each team's size joined by VS. Nothing when every player is
    alone, which the lit EACH FOR THEMSELVES says, or when the host is alone."""
    if len(shown()) < 2 or each_alone():
        return ""
    sizes = [len(seats) for seats in roster.ROSTER.groups().values()]
    if len(sizes) == 1:
        return i18n.text("teams_one", language)
    return f" {i18n.text('teams_vs', language)} ".join(str(size) for size in sizes)


def paint(form: Any, widgets: dict, language: str) -> None:
    locked = duel.live() is not None
    seats = shown()
    widgets["heading:teams"].SetText(i18n.text("teams", language))
    widgets["group:teams"].SetText("")
    widgets["teams_each_label"].SetText(i18n.text("teams_each", language))
    b.paint(widgets, "teams_each", "on" if each_alone() else "disabled" if locked or len(seats) < 2 else "secondary")
    widgets["teams_summary"].SetText(summary(language))
    for index in range(ROWS):
        seat = seats[index] if index < len(seats) else None
        visible(widgets[f"teams_row:{index}"], seat is not None)
        if seat is None:
            continue
        fallback = i18n.text("player_fallback", language).format(number=seat.number)
        widgets[f"teams_name:{index}"].SetText(seat.name or fallback)
        widgets[f"teams_host:{index}"].SetText(i18n.text("host", language).upper() if seat.host else "")
        for team in roster.TEAMS:
            name = _pick(index, team)
            widgets[f"{name}_label"].SetText(str(team))
            b.paint(widgets, name, "lang_on" if seat.team == team else "lang_off")
            visible(widgets[f"{name}_box"], seat.team == team or not locked)


def notice(language: str) -> str:
    """The footer's sentence on this page."""
    if roster.ROSTER.where == roster.GUEST:
        return i18n.text("teams_not_host", language)
    if duel.live() is not None:
        return i18n.text("teams_locked", language)
    if len(roster.ROSTER.seats) < 2:
        return i18n.text("teams_alone", language)
    if len(roster.ROSTER.groups()) >= teams.ALLIES_FROM:
        return i18n.text("teams_allies", language)
    return i18n.text("ready_teams", language)


def _signature() -> tuple:
    return roster.ROSTER.where, tuple((seat.number, seat.team, seat.host, seat.name) for seat in roster.ROSTER.seats)


def poll(form: Any, widgets: dict) -> bool:
    """The page's clicks taken, every row's, hidden ones too, so that none waits for the next player on its row; the
    players read again; then each click applied to the player of its row as shown, if still there: a team chosen, or
    every player alone; forgotten while a duel goes on and in a guest's game. Whether a click was taken: players
    coming or going only repaint the page, the window's own clicks of the same poll (a page, CLOSE) still to be
    read."""
    seats = shown()
    each = form.take(widgets["teams_each"])
    picks = [(index, team) for index in range(ROWS) for team in roster.TEAMS if form.take(widgets[_pick(index, team)])]
    before = _signature()
    roster.refresh()
    free = duel.live() is None and roster.ROSTER.where != roster.GUEST
    changed = False
    if each and free:
        roster.ROSTER.each_alone()
        changed = True
        report.note("teams each alone", players=len(roster.ROSTER.seats))
    for index, team in picks:
        seat = seats[index] if index < len(seats) else None
        if seat is None or not free or not any(seat is kept for kept in roster.ROSTER.seats):
            continue
        if roster.ROSTER.set_team(seat.number, team):
            changed = True
            report.note("team chosen", player=report.player(seat.number), team=team)
    # A start refused with every player in one team: said on DUEL of the teams since changed, it would be false.
    if changed and form.notice == "start_one_team":
        form.notice = "ready"
    if changed or _signature() != before:
        form.refresh_labels(widgets)
    return each or bool(picks)
