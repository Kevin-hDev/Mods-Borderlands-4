"""The VAULT HUNTERS and ALLIES pages (sketch A1 of esquisses_mod_companions, decision 68 of docs/renforts), one page
each in the side column. Under the title, the team, « TEAM 5 / 8 » and who is in it, then the page's companions in a
grid of two columns, a card each: its picture on the left (panel_companion_pictures.py), its name, a button that adds
one more to the team, its count « ×2 » and a « − » that takes one away, its frame gold while it is in the team; on
the card of the hunter the player plays only, his outfit, BASE or YOUR COLOURS (spec-compagnons.md, « Deux boutons de
tenue »: the player's colours exist for that hunter alone, companions/player_paint.py). No setting on a card (decision
68): the team's are on the SETTINGS page. Under the scrolling cards, never scrolled away, one button that launches the
team, then stops it.

While the team is on, every card is locked under a line saying to stop it first: the team runs with the choices it
started with. While no team of Companions may start (session.blocked: It Follows leads the team, no mod can be
known to lead, or an It Follows too old to share it is in the game), the cards are locked too, the line says why
and LAUNCH THE TEAM is greyed, as it is while Companions is disabled: a button shown that does nothing is none
(review of 23 October 2026). The clicks are read by panel_cards_poll.py.
"""

from typing import Any

from mods_base import get_pc

from . import panel_buttons as b, panel_companion_pictures as pictures, panel_i18n as i18n
from . import panel_pages as p, panel_text as tx, panel_theme as t, panel_widgets as w, session
from . import team_choices as choices
from .characters.companions import bars_names, kinds, player_paint

# Lilith, Lilith Phoenix and Moxxi after the allies (decision 78 of docs/renforts/README.md): allies of the story.
PAGES = {"hunters": kinds.HUNTERS, "allies": kinds.ALLIES + kinds.GUESTS}
HUNTERS = tuple(kind.name for kind in kinds.HUNTERS)
OUTFITS = choices.OUTFITS


def buttons(name: str) -> list[str]:
    """A card's buttons: add one, take one away, a hunter's outfits."""
    return [f"mate_add:{name}", f"mate_minus:{name}",
            *(f"mate_outfit:{name}:{outfit}" for outfit in (OUTFITS if name in HUNTERS else ()))]


def _visible(widget: Any, shown: bool) -> None:
    widget.SetVisibility(w.enum("ESlateVisibility", "SelfHitTestInvisible" if shown else "Collapsed"))


def _outfits(owner: Any, widgets: dict, name: str, template: Any) -> None:
    widgets[f"mate_outfit_line:{name}"] = line = w.new("HorizontalBox", owner)
    widgets[f"mate_outfit_word:{name}"] = word = tx.text(line, "", "caption")
    w.row(line, w.sized(line, word, width=t.CARD_LABEL_WIDTH), valign="Center")
    for index, outfit in enumerate(OUTFITS):
        w.row(line, b.button(line, widgets, f"mate_outfit:{name}:{outfit}", "lang", template, "lang_off"),
              padding=w.pad(0, 0, 0, t.SPACE_2 if index else 0), valign="Center")
    w.column(owner, line, padding=w.pad(t.SPACE_2, 0, 0))


def _card(owner: Any, widgets: dict, name: str, template: Any) -> Any:
    frame, inner = w.framed(owner, t.COLOR_WINDOW, t.STROKE, w.pad(t.SPACE_3, t.SPACE_4))
    widgets[f"mate:{name}"] = frame
    whole = w.new("HorizontalBox", inner)
    inner.SetContent(whole)
    w.row(whole, pictures.frame(whole, widgets, name), padding=w.pad(0, t.SPACE_4, 0, 0), valign="Top")
    rows = w.new("VerticalBox", whole)
    w.row(whole, rows, fill=True)
    top = w.new("HorizontalBox", rows)
    w.row(top, b.button(top, widgets, f"mate_add:{name}", "nav", template, "nav_off"), fill=True, valign="Center")
    widgets[f"mate_times:{name}"] = tag = w.border(top, t.COLOR_GOLD, w.pad(0, t.SPACE_2))
    widgets[f"mate_times_text:{name}"] = count = tx.text(tag, "", "plate")
    tag.SetContent(count)
    w.row(top, w.slant(tag), padding=w.pad(0, 0, 0, t.SPACE_3), valign="Center")
    # The whole button kept, its frame and shadow with it: hidden out of the team, no empty frame is left.
    widgets[f"mate_minus_box:{name}"] = minus = b.button(top, widgets, f"mate_minus:{name}", "lang", template,
                                                         "lang_off")
    w.row(top, minus, padding=w.pad(0, 0, 0, t.SPACE_3), valign="Center")
    w.column(rows, top)
    if name in HUNTERS:
        _outfits(rows, widgets, name, template)
    return frame


def _grid(owner: Any, widgets: dict, members: tuple, template: Any) -> Any:
    box = w.new("VerticalBox", owner)
    for first in range(0, len(members), 2):
        line = w.new("HorizontalBox", box)
        for index, kind in enumerate(members[first:first + 2]):
            w.row(line, _card(line, widgets, kind.name, template), fill=True,
                  padding=w.pad(0, 0, 0, t.SPACE_4 if index else 0))
        w.column(box, line, padding=w.pad(0, 0, t.SPACE_4))
    return box


def page(owner: Any, group: Any, key: str, widgets: dict, template: Any) -> Any:
    whole = w.new("VerticalBox", owner)
    scroll, body = p.scrolling_body(whole, template)
    w.column(whole, scroll, fill=True)
    rows = p.card(body, widgets, key)
    team = w.new("HorizontalBox", rows)
    widgets[f"team_count:{key}"] = tx.text(team, "", "subtitle")
    w.row(team, widgets[f"team_count:{key}"], valign="Center")
    widgets[f"team_who:{key}"] = tx.text(team, "", "desc", wrap=True)
    w.row(team, widgets[f"team_who:{key}"], padding=w.pad(0, 0, 0, t.SPACE_4), fill=True, valign="Center")
    w.column(rows, team, padding=w.pad(t.SPACE_3, 0, 0))
    widgets[f"team_locked:{key}"] = tx.text(rows, "", "warning", wrap=True)
    w.column(rows, widgets[f"team_locked:{key}"], padding=w.pad(t.SPACE_2, 0))
    w.column(rows, _grid(rows, widgets, PAGES[key], template), padding=w.pad(t.SPACE_2, 0, 0))
    w.column(whole, b.button(whole, widgets, f"team_launch:{key}", "launch", template, "primary"),
             padding=w.pad(t.SPACE_3, t.SPACE_8, t.SPACE_4))
    return whole


def reset(form: Any) -> None:
    """A new window: the hunter the player plays, read once for it; no picture in its cards yet."""
    form.companions_loaded = None
    form.cards_played = player_paint.played_by(get_pc())


def _who(team: list[str], shown: dict, language: str) -> str:
    counted = {name: team.count(name) for name in team}
    if not counted:
        return i18n.text("team_none", language)
    return " · ".join(shown[name].upper() + (f" ×{count}" if count > 1 else "") for name, count in counted.items())


def _paint_card(widgets: dict, name: str, shown: dict, count: int, locked: bool, language: str,
                played: str | None) -> None:
    widgets[f"mate:{name}"].SetBrushColor(w.linear(t.COLOR_GOLD if count else t.COLOR_INK))
    widgets[f"mate_add:{name}_label"].SetText(shown[name].upper())
    widgets[f"mate_add:{name}_label"].SetColorAndOpacity(w.slate(t.COLOR_GOLD_TEXT if count else t.COLOR_TEXT))
    widgets[f"mate_times:{name}"].SetBrushColor(w.linear(t.COLOR_GOLD))
    widgets[f"mate_times_text:{name}"].SetText(f"×{count}")
    _visible(widgets[f"mate_times:{name}"], count > 0)
    _visible(widgets[f"mate_minus_box:{name}"], count > 0)
    widgets[f"mate_minus:{name}_label"].SetText("−")
    if name in HUNTERS:
        _visible(widgets[f"mate_outfit_line:{name}"], name == played)
        widgets[f"mate_outfit_word:{name}"].SetText(i18n.text("outfit", language))
        chosen = choices.outfit(name)
        for outfit in OUTFITS:
            widgets[f"mate_outfit:{name}:{outfit}_label"].SetText(i18n.text(f"outfit:{outfit}", language))
            b.paint(widgets, f"mate_outfit:{name}:{outfit}", "lang_on" if outfit == chosen else "lang_off")
    for button in buttons(name):
        widgets[button].SetIsEnabled(not locked)


def _state(form: Any) -> tuple:
    """What the pages show of the team: on, why none may start, Companions enabled."""
    return session.team_on(), session.blocked(), form.model.mod.is_enabled


def paint(form: Any, widgets: dict, language: str) -> None:
    on, why, enabled = form.cards_state = _state(form)
    team = choices.names()
    launchable = on or (why is None and enabled)
    shown = bars_names.in_window(language)
    page_key = form.model.pages[form.page]
    if page_key in PAGES:
        pictures.load(form, widgets, page_key, PAGES[page_key])
    for kind in kinds.ALL:
        _paint_card(widgets, kind.name, shown, team.count(kind.name), on or why is not None, language,
                    getattr(form, "cards_played", None))
    for key in PAGES:
        widgets[f"team_count:{key}"].SetText(i18n.text("team_count", language).format(count=len(team),
                                                                                      most=choices.MOST))
        widgets[f"team_who:{key}"].SetText(_who(team, shown, language))
        widgets[f"team_locked:{key}"].SetText(i18n.text("cards_locked" if on else why or "cards_locked", language))
        _visible(widgets[f"team_locked:{key}"], on or why is not None)
        widgets[f"team_launch:{key}_label"].SetText(i18n.text("team_stop" if on else "team_launch", language))
        widgets[f"team_launch:{key}"].SetIsEnabled(launchable)
        b.paint(widgets, f"team_launch:{key}", "stop" if on else "primary" if launchable else "disabled")


def changed(form: Any) -> bool:
    """Whether the team began or ended, another mod came to lead it or left, or Companions was enabled or disabled,
    since the pages were painted."""
    return getattr(form, "cards_state", None) != _state(form)
