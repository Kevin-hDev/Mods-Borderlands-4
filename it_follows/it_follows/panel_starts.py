"""The Horde's starting points on the HORDE MODE page (decisions 138 to 141, spec-points-de-depart.md, section 3): the
Starting point row with the place chosen and its « ? »; while the row is on, one tab per place on the card's title
line, each name on two lines (Kevin: « il les faut sur deux ligne comme dans A »); a tab opened shows in the card,
instead of the settings, the place's name and region, its picture and its map's side by side, as wide as each other
(Kevin, sketch A: « A c'est mieux »), CHOOSE, and BACK. The tab opened, clicked again, comes back to the settings too:
the card's title is no button in our windows (plan-points-de-depart.md). The row off, the tabs go and the place chosen
is kept (options.start_place). During a run or a trip the tabs and CHOOSE are locked, as the settings are.

The pictures load each time their tab opens, as the avatar does (panel_assets.texture): fourteen at every opening of
the window would cost for nothing, and a texture kept in Python is no hold on it, the game may free it once its
frame shows another, and drawing it then could crash the game (It Follows' audit, 2026-10-19). One that does not
load is hidden with its caption, never an empty frame (Kevin's rule of 2026-09-21). The tab open is the window's
model's, so that a window drawn again (theme, size) shows it still. A trip that fails while the window is open says
why in its footer at once. The names are the game's English ones in every language (decision 141)."""

from typing import Any

import mods_base

from . import options, panel_assets as assets, panel_buttons as b, panel_en, panel_help as help_
from . import panel_i18n as i18n, panel_text as tx, panel_theme as t, panel_widgets as w
from . import panel_window_size as size, report, session
from . import start_places, start_point

# Each picture as wide as its neighbour, the two side by side across the card: 440 in the smallest window (1400
# wide), half of every width more in a larger one, so that they grow with the window (Kevin, 2026-10-19: « qu'elle
# s'agrandissent avec lui »). The height follows each picture's own proportions (start_places_data.py).
PICTURE_WIDTH = 440
PICTURES = (("place", "place_picture", "place_size"), ("map", "map_picture", "map_size"))
SHOWN, HIDDEN = "SelfHitTestInvisible", "Collapsed"


def _visible(widget: Any, shown: bool) -> None:
    widget.SetVisibility(w.enum("ESlateVisibility", SHOWN if shown else HIDDEN))


def picture_width() -> float:
    """Each picture's width in the window being drawn (panel_window_size.use, set before the pages)."""
    return PICTURE_WIDTH + (size.WIDTH - t.WINDOW_WIDTH) / 2


def _tab(number: int) -> str:
    return f"start_tab:{number}"


def tabs(widgets: dict, template: Any) -> None:
    """The places' tabs on the Horde card's title line, right of the title."""
    line = widgets["heading_line:run"]
    widgets["start_tabs"] = box = w.new("HorizontalBox", line)
    for index, place in enumerate(start_places.PLACES):
        w.row(box, b.button(box, widgets, _tab(place.number), "place_tab", template, "secondary"),
              padding=w.pad(0, 0, 0, t.SPACE_1 if index else 0), valign="Center")
    w.row(line, box, padding=w.pad(0, 0, 0, t.SPACE_3), valign="Center")


def row(widgets: dict, template: Any) -> None:
    """On the Starting point row, after its switch: the place chosen, then its « ? »."""
    line = widgets["row:start_point"]
    widgets["start_place_name"] = tx.text(line, "", "gold")
    w.row(line, widgets["start_place_name"], fill=True, valign="Center")
    w.row(line, help_.button(line, widgets, "start_help", template), padding=w.pad(0, 0, 0, t.SPACE_3),
          valign="Center")


def page(owner: Any, widgets: dict, template: Any) -> Any:
    """A place's page, shown in the card instead of the settings while its tab is open."""
    widgets["start_page_box"] = box = w.new("VerticalBox", owner)
    widgets["start_page_name"] = tx.text(box, "", "subtitle")
    w.column(box, widgets["start_page_name"], padding=w.pad(t.SPACE_4, 0, 0))
    widgets["start_page_region"] = tx.text(box, "", "desc")
    w.column(box, widgets["start_page_region"], padding=w.pad(t.SPACE_1, 0, t.SPACE_3))
    line = w.new("HorizontalBox", box)
    for index, (kind, _name, _size) in enumerate(PICTURES):
        widgets[f"start_picture_column:{kind}"] = column = w.new("VerticalBox", line)
        widgets[f"start_picture:{kind}"] = image = w.new("Image", column)
        widgets[f"start_picture_box:{kind}"] = sized = w.sized(column, image, picture_width(), picture_width() / 2)
        w.column(column, sized)
        widgets[f"start_caption:{kind}"] = tx.text(column, "", "hint")
        w.column(column, widgets[f"start_caption:{kind}"], padding=w.pad(t.SPACE_1, 0, 0))
        w.row(line, column, padding=w.pad(0, 0, 0, t.SPACE_4 if index else 0), valign="Top")
    w.column(box, line)
    buttons = w.new("HorizontalBox", box)
    w.row(buttons, b.button(buttons, widgets, "start_choose", "action", template, "primary"), valign="Center")
    w.row(buttons, b.button(buttons, widgets, "start_back", "action", template, "secondary"),
          padding=w.pad(0, 0, 0, t.SPACE_5), valign="Center")
    w.column(box, buttons, padding=w.pad(t.SPACE_5, 0, t.SPACE_2), halign="Left")
    _visible(box, False)
    return box


def reset(form: Any) -> None:
    """A new window: no picture in its frames yet; the tab open is the model's, none at a first opening."""
    form.start_loaded, form.start_painted = None, None


def opened(form: Any) -> int | None:
    """The place whose tab is open, None for none."""
    return getattr(form.model, "start_open", None)


def _open(form: Any, number: int | None) -> None:
    form.model.start_open = number


def _load(form: Any, widgets: dict, place: Any) -> None:
    """The open place's two pictures in their frames, each as tall as its proportions want; one missing hidden with its
    caption."""
    pc = mods_base.get_pc()
    for kind, name, size in PICTURES:
        texture = assets.texture(pc, getattr(place, name)) if pc is not None else None
        shown = texture is not None and w.cosmetic(f"start_picture:{kind}", lambda texture=texture, kind=kind: (
            widgets[f"start_picture:{kind}"].SetBrushFromTexture(texture, False)))
        width, height = getattr(place, size)
        widgets[f"start_picture_box:{kind}"].SetHeightOverride(float(picture_width() * height / width))
        _visible(widgets[f"start_picture_column:{kind}"], shown)
    form.start_loaded = place.number


def _on(form: Any) -> bool:
    return form.shown.get(options.start_point.identifier) is True


def _locked() -> bool:
    return session.running() or start_point.travelling()


def paint(form: Any, widgets: dict, language: str) -> None:
    on, locked = _on(form), _locked()
    if not on or locked:
        _open(form, None)
    shown, chosen = opened(form), start_places.find(options.start_place.value)
    _visible(widgets["start_tabs"], on)
    for place in start_places.PLACES:
        name = _tab(place.number)
        widgets[f"{name}_label"].SetText(start_places.two_lines(place.name).upper())
        b.paint(widgets, name, "stop" if place.number == shown else "secondary")
        if place.number == chosen.number and place.number != shown:
            widgets[f"{name}_label"].SetColorAndOpacity(w.slate(t.COLOR_GOLD))
        widgets[name].SetIsEnabled(not locked)
    widgets["start_place_name"].SetText(chosen.name.upper() if on else "")
    _visible(widgets["run_settings_box"], shown is None)
    _visible(widgets["start_page_box"], shown is not None)
    form.start_painted = (on, locked)
    if shown is None:
        form.start_loaded = None
        return
    place = start_places.find(shown)
    if form.start_loaded != place.number:
        _load(form, widgets, place)
    widgets["start_page_name"].SetText(place.name.upper())
    widgets["start_page_region"].SetText(place.region.upper())
    for kind, _name, _size in PICTURES:
        widgets[f"start_caption:{kind}"].SetText(i18n.text(f"start_{kind}_caption", language))
    done = place.number == chosen.number
    widgets["start_choose_label"].SetText(i18n.text("start_chosen" if done else "start_choose", language))
    b.paint(widgets, "start_choose", "disabled" if done else "primary")
    widgets["start_choose"].SetIsEnabled(not done)
    widgets["start_back_label"].SetText(i18n.text("start_back", language))


def changed(form: Any) -> bool:
    """Whether the row was switched, or a run or a trip began or ended, since the page was painted."""
    return getattr(form, "start_painted", None) != (_on(form), _locked())


def poll(form: Any, widgets: dict) -> bool:
    """A tab, CHOOSE or BACK clicked, or a trip that failed while the window is open (panel_run._reopen finds it
    open): whether one was. Every button is read, so that none keeps a click for later."""
    trip = start_point.take_outcome()
    if trip is not None:
        form.notice = notice(trip)
        report.note("start_trip_said", outcome=trip)
        form.refresh_labels(widgets)
        return True
    clicked = [place.number for place in start_places.PLACES if form.take(widgets[_tab(place.number)])]
    back, choose = form.take(widgets["start_back"]), form.take(widgets["start_choose"])
    if not (clicked or back or choose) or _locked():
        return bool(clicked or back or choose)
    if clicked:
        _open(form, None if opened(form) == clicked[0] else clicked[0])
        report.note("start_tab", place=clicked[0], opened=opened(form) is not None)
    elif back:
        _open(form, None)
    elif choose and opened(form) is not None:
        value = str(opened(form))
        saved = form.flush(widgets) and form.model.save(((options.start_place, value),))
        form.notice = "saved" if saved else "failed"
        report.note("start_chosen", place=opened(form), saved=saved)
    form.refresh_labels(widgets)
    return True


def notice(outcome: str) -> str:
    """The footer's words for why START, or a trip, did not end in a run: the reason's own, start_<reason> or the
    reason itself when it is already one (start_failed), else the general refusal."""
    key = outcome if outcome.startswith("start_") else f"start_{outcome}"
    return key if key in panel_en.TEXT else "start_refused"
