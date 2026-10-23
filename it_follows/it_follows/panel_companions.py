"""The COMPANIONS page (decision 50 of docs/renforts/README.md, sketch A of docs/renforts/esquisses_menu, chosen by
Kevin, 22 October 2026; what it holds: spec-compagnons.md, « Le menu »). On the card's title line, two tabs, VAULT
HUNTERS and ALLIES; under it the team, « TEAM 5 / 8 » and who is in it, the line saying the hunters fight with their
weapons only (spec-compagnons.md, « La description du mod »), and the tab's companions in a grid of two columns, a
card each. A card: the companion's name, a button that adds one more to the team (Kevin: « Un clic sur une carte
sélectionne le compagnon et l'ajoute à l'équipe »), its count « ×2 » and a « − » that takes one away, its frame gold
while it is in the team; under the name, its shield on or off and its speed bonus, OFF, +20 % or +30 %, for every one
of it in the team; on the card of the hunter the player plays only, his outfit, BASE or YOUR COLOURS
(spec-compagnons.md, « Deux boutons de tenue »: the player's colours exist for that hunter alone,
companions/player_paint.py). Under the scrolling cards, never scrolled away: the bars' row, shown only while their
package is in the game's Paks (companions/bars.py), and one button that launches the team, then stops it.

While the team is on, every card is locked under a line saying to stop it first: the team runs with the choices it
started with (companions/team.py). Each card's picture, on its left, is panel_companion_pictures.py's. The clicks are
read by panel_companions_poll.py.
"""

from typing import Any

from . import panel_buttons as b, panel_companion_pictures as pictures, panel_i18n as i18n, panel_pages as p
from . import panel_text as tx, panel_theme as t, panel_widgets as w, session
from mods_base import get_pc

from .companions import bars, bars_names, choices, kinds, player_paint

TABS = {"hunters": kinds.HUNTERS, "allies": kinds.ALLIES}
SPEEDS = tuple(choices.SPEEDS)
OUTFITS = choices.OUTFITS
HUNTERS = tuple(kind.name for kind in kinds.HUNTERS)
# The words beside a card's buttons, wide enough for BOUCLIER and VITESSE.
LABEL_WIDTH = 96
# The window's language as the game's files of texts name it, for the allies' names (bars_names.py).
CULTURES = {"EN": None, "FR": "fr", "ZH": "zh-Hans"}
_names: dict = {}  # language -> {companion: name shown}; three at most


def buttons(name: str) -> list[str]:
    """A card's buttons: add one, take one away, its shield, each of its speeds, a hunter's outfits."""
    return [f"mate_add:{name}", f"mate_minus:{name}", f"mate_shield:{name}",
            *(f"mate_speed:{name}:{speed}" for speed in SPEEDS),
            *(f"mate_outfit:{name}:{outfit}" for outfit in (OUTFITS if name in HUNTERS else ()))]


def _visible(widget: Any, shown: bool) -> None:
    widget.SetVisibility(w.enum("ESlateVisibility", "SelfHitTestInvisible" if shown else "Collapsed"))


def names(language: str) -> dict:
    """Each companion's name as the window shows it in that language: the hunters' own, the allies' as the game's
    texts name them, English when that language has no culture of the game's."""
    if language not in _names:
        culture = CULTURES.get(language)
        _names[language] = (bars_names.shown(culture)[0] if culture is not None
                            else {kind.name: kind.name for kind in kinds.ALL})
    return _names[language]


def opened(form: Any) -> str:
    """The tab open, the window's model's, so that a window drawn again shows it still; VAULT HUNTERS at first."""
    tab = getattr(form.model, "companions_tab", None)
    return tab if tab in TABS else "hunters"


def _setting(owner: Any, widgets: dict, name: str, part: str, buttons: list) -> None:
    widgets[f"mate_{part}_line:{name}"] = line = w.new("HorizontalBox", owner)
    widgets[f"mate_{part}_word:{name}"] = word = tx.text(line, "", "caption")
    w.row(line, w.sized(line, word, width=LABEL_WIDTH), valign="Center")
    for index, button in enumerate(buttons):
        w.row(line, button, padding=w.pad(0, 0, 0, t.SPACE_2 if index else 0), valign="Center")
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
    w.row(top, b.button(top, widgets, f"mate_minus:{name}", "lang", template, "lang_off"),
          padding=w.pad(0, 0, 0, t.SPACE_3), valign="Center")
    w.column(rows, top)
    _setting(rows, widgets, name, "shield", [b.button(rows, widgets, f"mate_shield:{name}", "switch", template, "on")])
    _setting(rows, widgets, name, "speed", [b.button(rows, widgets, f"mate_speed:{name}:{speed}", "lang", template,
                                                     "lang_off") for speed in SPEEDS])
    if name in HUNTERS:
        _setting(rows, widgets, name, "outfit", [b.button(rows, widgets, f"mate_outfit:{name}:{outfit}", "lang",
                                                          template, "lang_off") for outfit in OUTFITS])
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
    line = widgets[f"heading_line:{key}"]
    for tab in TABS:
        w.row(line, b.button(line, widgets, f"companions_tab:{tab}", "tab", template, "secondary"),
              padding=w.pad(0, 0, 0, t.SPACE_3), valign="Center")
    team = w.new("HorizontalBox", rows)
    widgets["companions_count"] = tx.text(team, "", "subtitle")
    w.row(team, widgets["companions_count"], valign="Center")
    widgets["companions_who"] = tx.text(team, "", "desc", wrap=True)
    w.row(team, widgets["companions_who"], padding=w.pad(0, 0, 0, t.SPACE_4), fill=True, valign="Center")
    w.column(rows, team, padding=w.pad(t.SPACE_3, 0, 0))
    for name, role in (("companions_lead", "hint"), ("companions_locked", "warning")):
        widgets[name] = tx.text(rows, "", role, wrap=True)
        w.column(rows, widgets[name], padding=w.pad(t.SPACE_2, 0))
    for tab, members in TABS.items():
        widgets[f"companions_grid:{tab}"] = grid = _grid(rows, widgets, members, template)
        w.column(rows, grid, padding=w.pad(t.SPACE_2, 0, 0))
    bottom = w.new("VerticalBox", whole)
    widgets["companions_bars_box"] = box = w.new("VerticalBox", bottom)
    p.setting_rows(box, group.children, widgets, template, expose_rows=True)
    w.column(bottom, box)
    w.column(bottom, b.button(bottom, widgets, "companions_launch", "launch", template, "primary"),
             padding=w.pad(t.SPACE_3, 0, 0))
    w.column(whole, bottom, padding=w.pad(0, t.SPACE_8, t.SPACE_4))
    return whole


def reset(form: Any) -> None:
    """A new window: whether the bars' package is installed, and the hunter the player plays, read once for it; no
    picture in its cards yet."""
    form.companions_loaded = None
    form.companions_bars_offered = bars.installed()
    form.companions_played = player_paint.played_by(get_pc())


def _who(team: list[str], shown: dict, language: str) -> str:
    counted = {name: team.count(name) for name in team}
    if not counted:
        return i18n.text("companions_none", language)
    return " · ".join(shown[name].upper() + (f" ×{count}" if count > 1 else "") for name, count in counted.items())


def _paint_outfit(widgets: dict, name: str, pick: Any, played: str | None, language: str) -> None:
    _visible(widgets[f"mate_outfit_line:{name}"], name == played)
    widgets[f"mate_outfit_word:{name}"].SetText(i18n.text("companions_outfit", language))
    for outfit in OUTFITS:
        widgets[f"mate_outfit:{name}:{outfit}_label"].SetText(i18n.text(f"companions_outfit:{outfit}", language))
        b.paint(widgets, f"mate_outfit:{name}:{outfit}", "lang_on" if outfit == pick.outfit else "lang_off")


def _paint_card(widgets: dict, name: str, shown: dict, count: int, locked: bool, language: str,
                played: str | None) -> None:
    pick = choices.choice(name)
    widgets[f"mate:{name}"].SetBrushColor(w.linear(t.COLOR_GOLD if count else t.COLOR_INK))
    widgets[f"mate_add:{name}_label"].SetText(shown[name].upper())
    widgets[f"mate_add:{name}_label"].SetColorAndOpacity(w.slate(t.COLOR_GOLD_TEXT if count else t.COLOR_TEXT))
    widgets[f"mate_times:{name}"].SetBrushColor(w.linear(t.COLOR_GOLD))
    widgets[f"mate_times_text:{name}"].SetText(f"×{count}")
    _visible(widgets[f"mate_times:{name}"], count > 0)
    _visible(widgets[f"mate_minus:{name}"], count > 0)
    widgets[f"mate_minus:{name}_label"].SetText("−")
    widgets[f"mate_shield_word:{name}"].SetText(i18n.text("companions_shield", language))
    widgets[f"mate_speed_word:{name}"].SetText(i18n.text("companions_speed", language))
    widgets[f"mate_shield:{name}_label"].SetText(i18n.text("on" if pick.shielded else "off", language))
    b.paint(widgets, f"mate_shield:{name}", "on" if pick.shielded else "off")
    for speed in SPEEDS:
        widgets[f"mate_speed:{name}:{speed}_label"].SetText(i18n.text(f"companions_speed:{speed}", language))
        b.paint(widgets, f"mate_speed:{name}:{speed}", "lang_on" if speed == pick.speed else "lang_off")
    if name in HUNTERS:
        _paint_outfit(widgets, name, pick, played, language)
    for button in buttons(name):
        widgets[button].SetIsEnabled(not locked)


def paint(form: Any, widgets: dict, language: str) -> None:
    on, tab, team = session.team_on(), opened(form), choices.names()
    form.companions_on = on
    shown = names(language)
    for one in TABS:
        widgets[f"companions_tab:{one}_label"].SetText(i18n.text(f"companions_{one}", language))
        b.paint(widgets, f"companions_tab:{one}", "stop" if one == tab else "secondary")
        _visible(widgets[f"companions_grid:{one}"], one == tab)
    pictures.load(form, widgets, tab, TABS[tab])
    for kind in kinds.ALL:
        _paint_card(widgets, kind.name, shown, team.count(kind.name), on, language,
                    getattr(form, "companions_played", None))
    widgets["companions_count"].SetText(i18n.text("companions_team", language).format(
        count=len(team), most=choices.MOST))
    widgets["companions_who"].SetText(_who(team, shown, language))
    widgets["companions_lead"].SetText(i18n.text("companions_lead", language))
    widgets["companions_locked"].SetText(i18n.text("companions_locked", language))
    _visible(widgets["companions_locked"], on)
    _visible(widgets["companions_bars_box"], getattr(form, "companions_bars_offered", False))
    widgets["companions_launch_label"].SetText(i18n.text("companions_stop" if on else "companions_launch", language))
    b.paint(widgets, "companions_launch", "stop" if on else "primary")


def changed(form: Any) -> bool:
    """Whether the team began or ended since the page was painted."""
    return getattr(form, "companions_on", None) != session.team_on()
