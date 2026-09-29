"""The mockup's kinds of text: font, size, colour, letter spacing and ink outline, one entry per kind."""

from . import panel_fonts as fonts, panel_theme as t, panel_widgets as w

# Movement's hero role lives here because Grapple is the generated menus' visual authority.
# kind: (family, CSS weight, size in px, colour, letter spacing in px, ink outline and shadow)
ROLES = {
    "logo": ("title", None, t.TEXT_LOGO, t.COLOR_GOLD, t.TRACKING_MD, True),
    "hero": ("title", None, t.TEXT_HERO, t.COLOR_GOLD, t.TRACKING_MD, True),
    "plate": ("title", None, t.TEXT_LG, t.COLOR_INK, t.TRACKING_MD, False),
    "nav": ("title", None, t.TEXT_LG, t.COLOR_TEXT, t.TRACKING_SM, False),
    "value": ("title", None, t.TEXT_LG, t.COLOR_GOLD, t.TRACKING_MD, False),
    "button": ("body", t.WEIGHT_BOLD, t.TEXT_MD, t.COLOR_INK, t.TRACKING_LG, False),
    "small_button": ("body", t.WEIGHT_BOLD, t.TEXT_XS, t.COLOR_INK, t.TRACKING_MD, False),
    "tag": ("body", t.WEIGHT_BOLD, t.TEXT_XS, t.COLOR_GOLD, t.TRACKING_LG, False),
    "caption": ("body", t.WEIGHT_BOLD, t.TEXT_2XS, t.COLOR_TEXT_DIM, t.TRACKING_XL, False),
    "meta": ("body", t.WEIGHT_MEDIUM, t.TEXT_XS, t.COLOR_TEXT_DIM, t.TRACKING_MD, False),
    "label": ("body", t.WEIGHT_MEDIUM, t.TEXT_MD, t.COLOR_TEXT, t.TRACKING_SM, False),
    "body": ("body", t.WEIGHT_REGULAR, t.TEXT_MD, t.COLOR_TEXT, 0, False),
    "gold": ("body", t.WEIGHT_MEDIUM, t.TEXT_MD, t.COLOR_GOLD, 0, False),
    "status": ("body", t.WEIGHT_MEDIUM, t.TEXT_MD, t.COLOR_SPARK, 0, False),
    "desc": ("body", t.WEIGHT_REGULAR, t.TEXT_SM, t.COLOR_TEXT_DIM, 0, False),
    "hint": ("body", t.WEIGHT_REGULAR, t.TEXT_XS, t.COLOR_TEXT_DIM, 0, False),
    "ends": ("body", t.WEIGHT_MEDIUM, t.TEXT_2XS, t.COLOR_TEXT_DIM, 0, False),
}
# The line heights the mockup's CSS gives Anton; Barlow keeps its own, as in the browser.
LEADING = {"logo": t.LEADING_NONE, "hero": t.LEADING_TIGHT, "plate": t.LEADING_SNUG,
           "nav": t.LEADING_SNUG, "value": t.LEADING_SNUG}
_loaded = {}  # family -> font object, only while one window is being built


def trim(role):
    """Pixels to take off a box's top and bottom padding so it keeps the mockup's height around this text.

    CSS centres the letters in a shorter line; Unreal keeps the font's full line. Taking half the difference off
    each side gives the same box and the same letter position.
    """
    if role not in LEADING:
        return 0.0
    family, size = ROLES[role][0], ROLES[role][2]
    return (t.FONT_LINE_HEIGHT[family] - LEADING[role]) * size / 2


def inset(padding, role):
    return max(0.0, padding - trim(role))


def use(loaded):
    _loaded.clear()
    _loaded.update(loaded)


def configure(font, role):
    """Fills a font description in place; used by text blocks and by the key selectors' own text style."""
    family, weight, size, _tint, tracking, _inked = ROLES[role]
    try:
        font.Size = t.points(size)
    except TypeError:
        font.Size = round(t.points(size))  # Engines before 5.1 size fonts in whole points.
    if family in _loaded:
        font.FontObject = _loaded[family]
        font.TypefaceFontName = fonts.face(family, weight)
    if tracking:
        # Unreal counts letter spacing in thousandths of the font size.
        w.cosmetic("letter_spacing", lambda: setattr(font, "LetterSpacing", round(tracking / size * 1000)))
    return font


def _ink(widget, font):
    # CSS draws the 7 px stroke centred on the letter edge and behind the fill: half of it shows.
    font.OutlineSettings.OutlineSize = round(t.TEXT_STROKE / 2)
    font.OutlineSettings.OutlineColor = w.linear(t.COLOR_INK)
    font.OutlineSettings.bApplyOutlineToDropShadows = True
    widget.SetShadowOffset(w.vector(t.SHADOW_MD, t.SHADOW_MD))
    widget.SetShadowColorAndOpacity(w.linear(t.COLOR_INK))


def text(owner, value, role, wrap=False, center=False):
    # No drop shadow except on inked titles: a one-point shadow on every text blurred the letters (2026-09-21).
    widget = w.new("TextBlock", owner)
    widget.SetText(value)
    font = configure(widget.Font, role)
    if ROLES[role][5]:
        w.cosmetic("text_outline", lambda: _ink(widget, font))
    widget.SetFont(font)
    widget.SetColorAndOpacity(w.slate(ROLES[role][3]))
    widget.SetAutoWrapText(wrap)
    if center:
        w.cosmetic("justify", lambda: widget.SetJustification(w.enum("ETextJustify", "Center")))
    return widget
