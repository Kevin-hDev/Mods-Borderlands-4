"""The APPEARANCE page of sketch B2 (Kevin's choice, 2026-09-28): above the cards, the sentence saying a look applies
at once, in the heirloom's orange frame (panel_notice.py); one card per hunter in three columns, each with Kevin's
picture of the hunter, its name and its class in the class's colour; in the card's top right corner, YOUR HUNTER on the
hunter played and CHOSEN on the look worn when it is another hunter's, the worn card framed in gold; under them, a
sentence naming both, and on another hunter's look the rows of its body and head skins (panel_skins.py, sketch C1).
Outside a game there is no card and no frame, only a sentence asking to load one: a card that could change nothing
would read as broken. With the mod off, the cards and skins stay in view but greyed and still, the orange frame saying
to turn it on (Kevin's choice A, 2026-10-08): a click had dressed the character with the mod off.

A card is clicked like the window's buttons: a latched CheckBox, read once per poll (panel_buttons.py). A picture that
does not load leaves the card without it, never an empty frame (panel_picture.py of the heirloom does the same).

The frame above the cards, the grid of six cards, the sentence under them and the painting of one card are the HUNTER
page's too (panel_switch.py), from here only: each page names its cards under its own prefix, so that a click on one
page is never read by the other.
"""

from typing import Any

from . import hunters, menu, panel_assets as assets, panel_buttons as b, panel_hunters_theme as ht
from . import panel_i18n as i18n, panel_notice, panel_pages as p, panel_skins, panel_text as tx, panel_theme as t
from . import panel_widgets as w, wardrobe

APPLIES, OFF = "applies", "look_off"
# The two tags of sketch B2: (part, fill, outline, letters), as theme colour names read when the card is drawn.
TAGS = (("own", "COLOR_INK", "COLOR_SPARK", "COLOR_SPARK"), ("chosen", "COLOR_GOLD", "COLOR_GOLD", "COLOR_INK"))


def _picture(owner: Any, widgets: dict, name: str, code: str, world: Any) -> Any:
    file, width, height = menu.PICTURES[code]
    texture = assets.texture(world, file) if world is not None else None
    if texture is None:
        return None
    image = w.new("Image", owner)
    if not w.cosmetic(f"picture:{code}", lambda: image.SetBrushFromTexture(texture, False)):
        return None
    widgets[f"{name}_picture"] = image
    return w.sized(owner, image, width, height)


def _tags(owner: Any, widgets: dict, name: str) -> Any:
    """The card's tags, top right as B2 has them: laid over the card, they never push its name or class aside."""
    tags = w.new("HorizontalBox", owner)
    for part, *names in TAGS:
        fill, outline, letters = (t.colour(name) for name in names)
        frame, inner = w.framed(tags, fill, t.STROKE_THIN, w.pad(0, t.SPACE_2), frame=outline)
        widgets[f"{name}_{part}"] = tx.text(inner, "", "tag")
        widgets[f"{name}_{part}"].SetColorAndOpacity(w.slate(letters))
        inner.SetContent(widgets[f"{name}_{part}"])
        widgets[f"{name}_{part}_tag"] = w.slant(frame)
        w.row(tags, frame)
    widgets[f"{name}_tags"] = tags
    return tags


def _card(owner: Any, widgets: dict, name: str, hunter: hunters.Hunter, template: Any, world: Any) -> Any:
    frame, fill = w.framed(owner, t.COLOR_INK, t.STROKE)
    check = w.new("CheckBox", fill)
    check.WidgetStyle.CheckBoxType = b.TOGGLE_BUTTON
    for field, veil in b._STATES:
        tint, alpha = veil or (t.COLOR_INK, 0.0)
        w.style_brush(check.WidgetStyle, field, template, tint, alpha=alpha)
    w.cosmetic("hunter_card_padding", lambda: setattr(check.WidgetStyle, "Padding", w.pad(t.SPACE_2)))
    face = w.new("Overlay", check)
    line = w.new("HorizontalBox", face)
    picture = _picture(line, widgets, name, hunter.code, world)
    if picture is not None:
        w.row(line, picture, valign="Center")
    texts = w.new("VerticalBox", line)
    for part, role in (("name", "nav"), ("class", "label")):
        widgets[f"{name}_{part}"] = tx.text(texts, "", role)
        w.column(texts, widgets[f"{name}_{part}"], padding=w.pad(0, 0, t.SPACE_1))
    w.row(line, texts, fill=True, padding=w.pad(0, 0, 0, t.SPACE_4), valign="Center")
    w.layer(face, line)
    # B2 sets the tags 12 px from the card's top and 16 px from its right; the card's own padding gives the rest.
    w.layer(face, _tags(face, widgets, name), w.pad(t.SPACE_3 - t.SPACE_2, t.SPACE_4 - t.SPACE_2, 0, 0),
            halign="Right", valign="Top")
    check.SetContent(face)
    check.SetIsChecked(False)
    fill.SetContent(check)
    layers, shade = w.shadowed(owner, w.sized(owner, frame, height=ht.CARD_HEIGHT), t.SHADOW_MD)
    widgets.update({name: check, f"{name}_frame": frame, f"{name}_shadow": shade})
    return layers


def grid(rows: Any, widgets: dict, template: Any, world: Any, prefix: str) -> Any:
    """The six cards in three columns, added to `rows`; each card named `prefix:code`, so that the APPEARANCE and
    HUNTER pages each have their own."""
    cards = w.new("VerticalBox", rows)
    line = None
    for index, hunter in enumerate(hunters.HUNTERS):
        column = index % ht.COLUMNS
        if column == 0:
            line = w.new("HorizontalBox", cards)
            w.column(cards, line, padding=w.pad(0, 0, t.SPACE_4))
        gap = t.SPACE_4 if column < ht.COLUMNS - 1 else 0
        card = _card(line, widgets, f"{prefix}:{hunter.code}", hunter, template, world)
        w.row(line, card, fill=True, padding=w.pad(0, gap, 0, 0))
    w.column(rows, cards)
    return cards


def notice_block(rows: Any, widgets: dict, key: str) -> Any:
    """The page's sentence above the cards, in the heirloom's orange frame (panel_notice.py), added to `rows`."""
    block = w.new("VerticalBox", rows)
    panel_notice.notice(block, widgets, key)
    w.column(rows, block, padding=w.pad(0, 0, t.SPACE_5))
    return block


def sentence(rows: Any, widgets: dict, name: str) -> Any:
    """The page's sentence under the cards, added to `rows` and kept as `name`."""
    widgets[name] = tx.text(rows, "", "desc", wrap=True)
    w.column(rows, widgets[name], padding=w.pad(t.SPACE_2, 0, t.SPACE_3))
    return widgets[name]


def page(owner: Any, key: str, widgets: dict, template: Any, world: Any) -> Any:
    scroll, body = p.scrolling_body(owner, template)
    rows = p.card(body, widgets, key)
    widgets["hunter_applies"] = notice_block(rows, widgets, APPLIES)
    widgets["hunter_grid"] = grid(rows, widgets, template, world, "hunter")
    sentence(rows, widgets, "hunter_state")
    panel_skins.rows(rows, widgets, template)
    return scroll


def taken(take: Any, widgets: dict, prefix: str = "hunter") -> str | None:
    """The code of the first card of `prefix` clicked since the last poll, if any. Every other card clicked meanwhile
    is dropped: at the title screen, a second card clicked during the first change's pause would change the game
    again at once."""
    clicked = [hunter.code for hunter in hunters.HUNTERS if take(widgets[f"{prefix}:{hunter.code}"])]
    return clicked[0] if clicked else None


def show(widget: Any, shown: bool) -> None:
    widget.SetVisibility(w.enum("ESlateVisibility", "Visible" if shown else "Collapsed"))


def paint_notice(widgets: dict, key: str, language: str, text: str | None = None) -> None:
    """The text `text`, or else `key`'s, in the frame made for `key`, in capitals as sketch B2 wrote it."""
    widgets[f"notice:{key}"].SetText(i18n.text(text or key, language).upper())


def still(widget: Any, enabled: bool) -> None:
    """A widget greyed and deaf to clicks while the mod is off."""
    widget.SetIsEnabled(enabled)
    widget.SetRenderOpacity(1.0 if enabled else t.OPACITY_DISABLED)


def paint_card(widgets: dict, prefix: str, hunter: hunters.Hunter, language: str, own: bool, chosen: bool,
               framed: bool) -> None:
    """One card of `prefix`: its name, its class in the class's colour, YOUR HUNTER when `own`, CHOSEN when `chosen`,
    and the gold frame and shadow when `framed`."""
    name = f"{prefix}:{hunter.code}"
    widgets[f"{name}_name"].SetText(hunter.name.upper())
    widgets[f"{name}_name"].SetColorAndOpacity(w.slate(ht.CARD_TEXT))
    widgets[f"{name}_class"].SetText(i18n.text(f"class:{hunter.code}", language))
    widgets[f"{name}_class"].SetColorAndOpacity(w.slate(ht.CLASS_COLOURS[hunter.code]))
    widgets[f"{name}_own"].SetText(i18n.text("your_hunter", language))
    show(widgets[f"{name}_own_tag"], own)
    widgets[f"{name}_chosen"].SetText(i18n.text("chosen", language))
    show(widgets[f"{name}_chosen_tag"], chosen)
    widgets[f"{name}_frame"].SetBrushColor(w.linear(t.COLOR_GOLD if framed else t.COLOR_TEXT_DIM))
    widgets[f"{name}_shadow"].SetBrushColor(w.linear(t.COLOR_GOLD_SHADE if framed else t.COLOR_INK))


def paint(widgets: dict, state: wardrobe.Status | None, language: str, enabled: bool = True) -> None:
    """The cards, the sentence and the skin rows for `state`, or None outside a game; greyed and still with the mod
    off."""
    shown = state is not None
    show(widgets["hunter_grid"], shown)
    show(widgets["hunter_applies"], shown)
    paint_notice(widgets, APPLIES, language, APPLIES if enabled else OFF)
    still(widgets["hunter_grid"], enabled)
    still(widgets["skins"], enabled)
    panel_skins.paint(widgets, state, language)
    if not shown:
        widgets["hunter_state"].SetText(i18n.text("no_game", language))
        return
    played, worn = state.played, state.worn.hunter
    for hunter in hunters.HUNTERS:
        worn_here = hunter == worn
        paint_card(widgets, "hunter", hunter, language, own=hunter == played, chosen=worn_here and worn != played,
                   framed=worn_here)
    key = "own_look" if worn == played else "worn_look"
    widgets["hunter_state"].SetText(i18n.text(key, language).format(
        played=played.name, worn=worn.name, own=played.name.upper()))


def poll(form: Any, widgets: dict) -> bool:
    """A card or a skin clicked, worn at once while the mod is on: True, the poll stops there. Otherwise the page
    follows the game while the window is open (a game loaded or left, the mod turned on or off): False."""
    code = taken(form.take, widgets)
    # Both read, so that a skin clicked with a card is dropped, not worn at the next poll; with the mod off, both are.
    skin = panel_skins.taken(form.take, widgets)
    if form.model.mod.is_enabled and (code is not None or skin is not None):
        done = wardrobe.wear(code) if code is not None else wardrobe.wear_skin(*skin)
        form.notice = "saved" if done else "failed"
        form.hunter_state = wardrobe.status()
        form.refresh_labels(widgets)
        return True
    state = wardrobe.status()
    if state != form.hunter_state:
        form.hunter_state = state
        form.refresh_labels(widgets)
    return False
