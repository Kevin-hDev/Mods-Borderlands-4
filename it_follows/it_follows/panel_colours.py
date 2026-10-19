"""The OPTIONS page's colour profile on one line (decision 149; Kevin after trial 119: « tout pourrait tenir sur une
ligne »): the switch, then, while it is on, the three profiles' buttons and PREVIEW on the same line.

PREVIEW hides the window and leaves a small card over the game, in the screen's top right corner, with the three
profiles and BACK, which shows the window again on the OPTIONS page: beside the window on the screen's layer, the
blur gone while it shows, the keyboard kept in the card, never on the hidden window, whose focus watch would give it
back and fail. Escape closes the whole window, card and all; the next opening draws the window anew, the card hidden.

The profile keeps its own row's option (options.colour_profile), which the window's form reads and writes as any row
of choices: only its buttons sit on the switch's line, and its own label and help are never shown. A profile clicked
in the card is written at once, so that the game, paused behind, shows it (colours.chosen).
"""

from typing import Any

from . import options, panel_buttons as b, panel_choices, panel_i18n as i18n, panel_modal as modal
from . import panel_pages as p, panel_text as tx, panel_theme as t, panel_widgets as w, panel_window_size as size
from . import report

PREVIEW, BACK, CARD = "colour_preview", "colour_back", "colour_card"
EXTRAS, CORNER, MENU, BACKDROP = "colour_extras", "colour_corner", "colour_menu", "colour_backdrop"
# Wide enough for the three profiles' buttons in a row, on the 1920 x 1080 stage.
CARD_WIDTH = 560
SHOWN, HIDDEN = "SelfHitTestInvisible", "Collapsed"


def _visible(widget: Any, shown: bool) -> None:
    widget.SetVisibility(w.enum("ESlateVisibility", SHOWN if shown else HIDDEN))


def _card_button(profile: str) -> str:
    return f"colour_card:{profile}"


def merge(owner: Any, widgets: dict, template: Any) -> None:
    """The profiles' buttons and PREVIEW on the switch's line. The profile row's label and help, which the form names
    as every row's, sit on the line collapsed: the window holds its widgets by weak pointers, and the engine's garbage
    collection took the two when left unplaced, the window then closing on its next turn (trial 120's poll_error)."""
    line = widgets[f"row:{options.colours.identifier}"]
    extras = w.new("HorizontalBox", line)
    w.row(extras, panel_choices.buttons(extras, widgets, options.colour_profile, template), valign="Center")
    w.row(extras, b.button(extras, widgets, PREVIEW, "switch", template, "secondary"),
          padding=w.pad(0, 0, 0, t.SPACE_5), valign="Center")
    w.row(line, extras, valign="Center")
    widgets[EXTRAS] = extras
    key = options.colour_profile.identifier
    for name, style in ((f"label:{key}", "label"), (f"description:{key}", "hint")):
        widgets[name] = tx.text(owner, "", style)
        _visible(widgets[name], False)
        w.row(line, widgets[name])


def _through(widget: Any) -> Any:
    """Lets the clicks through to the card, or beside it to the layer that keeps them from the game."""
    widget.SetVisibility(w.enum("ESlateVisibility", "SelfHitTestInvisible"))
    return widget


def build_card(holder: Any, menu: Any, widgets: dict, template: Any) -> None:
    """The card, hidden, on the screen's layer that holds the window, at the window's scale."""
    screen = holder.WidgetTree.RootWidget
    corner = w.new("ScaleBox", screen)
    corner.SetStretch(w.enum("EStretch", "ScaleToFit"))
    _visible(corner, False)
    stage = _through(w.new("Overlay", corner))
    box = _through(w.sized(corner, stage, size.STAGE_WIDTH, size.STAGE_HEIGHT))
    slot = corner.SetContent(box)
    # Past a 16:9 screen, the stage keeps to the top right and the bands go left and below.
    w.cosmetic("colour_corner", lambda: w.place(slot, halign="Right", valign="Top"))
    column = w.new("VerticalBox", stage)
    w.layer(stage, w.sized(stage, column, width=CARD_WIDTH), padding=w.pad(t.SPACE_3, t.SPACE_3, 0, 0),
            halign="Right", valign="Top")
    rows = p.card(column, widgets, CARD)
    line = w.new("HorizontalBox", rows)
    for index, profile in enumerate(options.COLOUR_PROFILES):
        w.row(line, b.button(line, widgets, _card_button(profile), "switch", template, "off"),
              padding=w.pad(0, 0, 0, t.SPACE_2 if index else 0), valign="Center")
    w.column(rows, line, padding=w.pad(t.SPACE_3, 0, 0), halign="Left")
    w.column(rows, w.line(rows, t.COLOR_HOVER, height=t.STROKE_THIN), padding=w.pad(t.SPACE_4, 0, 0))
    w.column(rows, b.button(rows, widgets, BACK, "action", template, "secondary"), halign="Right",
             padding=w.pad(t.SPACE_3, 0, t.SPACE_2))
    modal._span(screen.AddChildToCanvas(corner), 0.0, 0.0)
    widgets[CORNER], widgets[MENU] = corner, menu
    # panel_modal.held lays the blur under the window first.
    w.cosmetic("colour_backdrop", lambda: widgets.__setitem__(BACKDROP, screen.GetChildAt(0)))


def _on(form: Any) -> bool:
    return form.shown.get(options.colours.identifier) is True


def _profile(form: Any) -> str:
    chosen = form.shown.get(options.colour_profile.identifier)
    return chosen if chosen in options.COLOUR_PROFILES else options.DEFAULT_COLOUR_PROFILE


def previewing(form: Any) -> bool:
    return getattr(form, "colour_preview", False) is True


def _blur(widgets: dict, strength: float) -> None:
    backdrop = widgets.get(BACKDROP)
    if backdrop is not None:
        # A clear layer, where the blur was refused, has no strength to set (panel_modal.py).
        w.cosmetic("colour_blur", lambda: backdrop.SetBlurStrength(float(strength)))


def _show_card(form: Any, widgets: dict, shown: bool) -> None:
    form.colour_preview = shown
    widgets[MENU].SetVisibility(w.enum("ESlateVisibility", "Collapsed" if shown else "Visible"))
    _blur(widgets, 0.0 if shown else t.BACKDROP_BLUR)
    _visible(widgets[CORNER], shown)
    (widgets[_card_button(_profile(form))] if shown else widgets["focus"]).SetKeyboardFocus()


def paint(form: Any, widgets: dict, language: str) -> None:
    on, chosen = _on(form), _profile(form)
    _visible(widgets[EXTRAS], on)
    widgets[f"{PREVIEW}_label"].SetText(i18n.text(PREVIEW, language))
    widgets[f"heading:{CARD}"].SetText(i18n.option_text(options.colours, language)[0].upper())
    widgets[f"group:{CARD}"].SetText("")
    for profile in options.COLOUR_PROFILES:
        name = _card_button(profile)
        widgets[f"{name}_label"].SetText(panel_choices.label(profile, language, options.colour_profile))
        b.paint(widgets, name, "on" if profile == chosen else "off")
    widgets[f"{BACK}_label"].SetText(i18n.text(BACK, language))
    form.colour_painted = (on, chosen)


def changed(form: Any) -> bool:
    """Whether the switch or the profile was clicked since the line was painted."""
    return getattr(form, "colour_painted", None) != (_on(form), _profile(form))


def _choose(form: Any, widgets: dict, profile: str) -> None:
    """The profile written at once, as its row's button would after the form's delay."""
    key = options.colour_profile.identifier
    form.shown[key] = profile
    if profile == options.colour_profile.value:
        form.pending.pop(key, None)
    else:
        form.pending[key] = profile
    saved = form.flush(widgets)
    report.note("colour_preview_profile", profile=profile, saved=saved)


def poll(form: Any, widgets: dict) -> bool:
    """PREVIEW, a profile of the card, or BACK clicked: whether one was. While the card shows, the keyboard is kept in
    it, and every one of its buttons read, so that none keeps a click for later."""
    if previewing(form):
        clicked = [profile for profile in options.COLOUR_PROFILES if form.take(widgets[_card_button(profile)])]
        back = form.take(widgets[BACK])
        if clicked:
            _choose(form, widgets, clicked[-1])
        if back:
            _show_card(form, widgets, False)
            report.note("colour_preview", shown=False)
        elif not widgets[CORNER].HasFocusedDescendants():
            widgets[_card_button(_profile(form))].SetKeyboardFocus()
        if clicked or back:
            form.refresh_labels(widgets)
        return bool(clicked or back)
    if not form.take(widgets[PREVIEW]):
        return False
    if _on(form) and form.flush(widgets):
        _show_card(form, widgets, True)
        report.note("colour_preview", shown=True, profile=_profile(form))
    form.refresh_labels(widgets)
    return True
