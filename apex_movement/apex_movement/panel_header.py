"""The window's top: hazard band, avatar, title, author tag, Options gear and Close."""

import math

from . import panel_assets as assets, panel_buttons as b, panel_text as tx, panel_theme as t, panel_widgets as w


def hazard(owner):
    stripes = w.new("HorizontalBox", owner)
    # The mockup's bands are 18 px wide across a 45° line, so each covers 18 × √2 px of the window's width.
    count = round((t.WINDOW_WIDTH - 2 * t.STROKE_THICK) / (t.HAZARD_STRIPE * math.sqrt(2)))
    for index in range(count):
        band = w.border(stripes, t.COLOR_INK if index % 2 else t.COLOR_GOLD)
        w.slant(band, t.HAZARD_ANGLE)
        w.row(stripes, band, fill=True)
    w.cosmetic("hazard_clip", lambda: stripes.SetClipping(w.enum("EWidgetClipping", "ClipToBounds")))
    return w.sized(owner, stripes, height=t.HAZARD_HEIGHT)


def _round(ring):
    brush = ring.Background
    brush.DrawAs = w.enum("ESlateBrushDrawType", "RoundedBox")
    brush.OutlineSettings.RoundingType = w.enum("ESlateBrushRoundingType", "HalfHeightRadius")
    ring.SetBrush(brush)


def _avatar(owner, world):
    """The round picture, or None: the window then shows no empty ring (Kevin's rule: working or invisible)."""
    texture = assets.texture(world)
    if texture is None:
        return None
    image = w.new("Image", owner)
    if not w.cosmetic("avatar_image", lambda: image.SetBrushFromTexture(texture, False)):
        return None
    inner = t.AVATAR_SIZE - 4 * t.STROKE
    gold = w.border(owner, t.COLOR_GOLD, t.STROKE)
    gold.SetContent(w.sized(owner, image, inner, inner))
    ink = w.border(owner, t.COLOR_INK, t.STROKE)
    ink.SetContent(gold)
    layers, shade = w.shadowed(owner, ink, t.SHADOW_MD)
    for ring in (gold, ink, shade):
        w.cosmetic("avatar_round", lambda ring=ring: _round(ring))
    return layers


def header(owner, world, widgets, template):
    """Returns the header and whether the avatar could be shown."""
    stack = w.new("Overlay", owner)
    w.layer(stack, w.border(stack, t.COLOR_HEADER))
    sparks = w.new("CanvasPanel", stack)
    for left, top, side, colour, alpha in t.SPARKS:
        slot = sparks.AddChildToCanvas(w.border(sparks, colour, alpha=alpha))
        slot.SetPosition(w.vector(left, top))
        slot.SetSize(w.vector(side, side))
    w.layer(stack, sparks)
    line = w.new("HorizontalBox", stack)
    avatar = _avatar(line, world)
    if avatar is not None:
        w.row(line, avatar, padding=w.pad(0, t.SPACE_5, 0, 0), valign="Center")
    title = tx.text(line, t.BRAND, "logo")
    title.SetRenderTransformAngle(float(t.TILT_LOGO))
    w.row(line, title, padding=w.pad(0, t.SPACE_5, 0, 0), valign="Center")
    tag = w.border(line, t.COLOR_INK, w.pad(t.SPACE_1, t.SPACE_3))
    widgets["tag"] = tx.text(tag, "", "tag")
    tag.SetContent(widgets["tag"])
    w.row(line, w.slant(tag), valign="Center")
    w.row(line, w.new("Spacer", line), fill=True)
    w.row(line, b.gear(line, widgets, template), padding=w.pad(0, 0, 0, t.SPACE_2), valign="Center")
    w.row(line, b.button(line, widgets, "close", "action", template, "secondary"),
          padding=w.pad(0, 0, 0, t.SPACE_5), valign="Center")
    w.layer(stack, line, w.pad(0, t.SPACE_7), valign="Center")
    return w.sized(owner, stack, height=t.HEADER_HEIGHT), avatar is not None
