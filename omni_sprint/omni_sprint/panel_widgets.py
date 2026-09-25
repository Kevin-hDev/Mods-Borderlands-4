"""UMG layout primitives for the settings window: boxes, ink outlines and hard shadows, sized from the theme."""

import unrealsdk as sdk

from . import panel_theme as t, report

# Reflection mismatches raise these; anything else is a real fault and propagates.
STYLE_ERRORS = (AttributeError, TypeError, ValueError, KeyError, RuntimeError)


def cosmetic(key, action):
    """Runs one styling step not yet seen working in BL4; a failure costs its look, never the window."""
    try:
        action()
        return True
    except STYLE_ERRORS as error:
        report.error_once(f"panel:style:{key}", f"Settings window style '{key}' unavailable ({type(error).__name__}).")
        return False


def new(kind, owner):
    return sdk.construct_object(kind, owner)


def enum(name, member):
    return getattr(sdk.find_enum(name), member)


def linear(hex_color, alpha=1.0):
    red, green, blue, opacity = t.rgba(hex_color, alpha)
    return sdk.make_struct("LinearColor", R=red, G=green, B=blue, A=opacity)


def slate(hex_color, alpha=1.0):
    return sdk.make_struct("SlateColor", SpecifiedColor=linear(hex_color, alpha))


def vector(x, y):
    return sdk.make_struct("Vector2D", X=float(x), Y=float(y))


def pad(*values):
    """CSS shorthand order (top, right, bottom, left), so each call reads like the mockup's menu.css."""
    top, right, bottom, left = {1: lambda a: (a, a, a, a), 2: lambda a, b: (a, b, a, b),
                                3: lambda a, b, c: (a, b, c, b), 4: lambda a, b, c, d: (a, b, c, d)}[len(values)](*values)
    return sdk.make_struct("Margin", Left=float(left), Top=float(top), Right=float(right), Bottom=float(bottom))


def border(owner, hex_color=None, padding=0, alpha=1.0):
    widget = new("Border", owner)
    widget.SetBrushColor(linear(hex_color or t.COLOR_INK, alpha if hex_color else 0.0))
    widget.SetPadding(padding if not isinstance(padding, (int, float)) else pad(padding))
    return widget


def framed(owner, fill, stroke, padding=0, frame=t.COLOR_INK):
    """An ink outline around a flat box: two nested borders, the only outline proven in BL4 so far."""
    outer = border(owner, frame, stroke)
    inner = border(outer, fill, padding)
    outer.SetContent(inner)
    return outer, inner


def layer(overlay, child, padding=None, halign="Fill", valign="Fill"):
    # An overlay slot sits top-left at its content's smallest size unless told to fill: in 0.15.0 that shrank the
    # sliders to a few pixels and the shadows to nothing (Kevin's screenshot, 2026-09-21 22:14).
    return place(overlay.AddChildToOverlay(child), padding=padding, halign=halign, valign=valign)


def shadowed(owner, child, offset, hex_color=t.COLOR_INK):
    """The mockup's hard shadow: an ink copy of the box, offset down and right behind it."""
    layers = new("Overlay", owner)
    shade = border(layers, hex_color)
    layer(layers, shade, pad(offset, 0, 0, offset))
    layer(layers, child, pad(0, offset, offset, 0))
    return layers, shade


def sized(owner, child, width=None, height=None):
    box = new("SizeBox", owner)
    if width is not None:
        box.SetWidthOverride(float(width))
    if height is not None:
        box.SetHeightOverride(float(height))
    box.SetContent(child)
    return box


def place(slot, padding=None, fill=False, halign=None, valign=None):
    if padding is not None:
        slot.SetPadding(padding)
    if fill:
        slot.SetSize(sdk.make_struct("SlateChildSize", Value=1.0, SizeRule=enum("ESlateSizeRule", "Fill")))
    if halign is not None:
        slot.SetHorizontalAlignment(enum("EHorizontalAlignment", f"HAlign_{halign}"))
    if valign is not None:
        slot.SetVerticalAlignment(enum("EVerticalAlignment", f"VAlign_{valign}"))
    return slot


def row(box, child, **options):
    return place(box.AddChildToHorizontalBox(child), **options)


def column(box, child, **options):
    return place(box.AddChildToVerticalBox(child), **options)


def line(owner, hex_color, width=None, height=None):
    return sized(owner, border(owner, hex_color), width, height)


def slant(widget, degrees=t.SLANT):
    widget.SetRenderShear(vector(degrees, 0.0))
    return widget


def paint_brush(brush, tint, alpha=1.0, outline=None, size=None):
    brush.DrawAs = enum("ESlateBrushDrawType", "Image")
    brush.TintColor = slate(tint, alpha)
    if size is not None:
        brush.ImageSize.X, brush.ImageSize.Y = float(size[0]), float(size[1])
    if outline is not None:
        # A square RoundedBox is the only brush that carries its own ink outline (slider thumb, scrollbar).
        brush.DrawAs = enum("ESlateBrushDrawType", "RoundedBox")
        brush.OutlineSettings.Width = float(outline)
        brush.OutlineSettings.Color = slate(t.COLOR_INK)
        radii = brush.OutlineSettings.CornerRadii
        radii.X = radii.Y = radii.Z = radii.W = 0.0
        brush.OutlineSettings.RoundingType = enum("ESlateBrushRoundingType", "FixedRadius")
    return brush


def round_shape(widget):
    """Draws a square Border as a disc: a RoundedBox brush whose corner radius is half its height."""
    brush = widget.Background
    brush.DrawAs = enum("ESlateBrushDrawType", "RoundedBox")
    brush.OutlineSettings.Width = 0.0
    brush.OutlineSettings.RoundingType = enum("ESlateBrushRoundingType", "HalfHeightRadius")
    widget.SetBrush(brush)


def style_brush(style, field, template, tint, **options):
    """Copies a proven solid brush into a style field, then recolours it; see panel_view for the template."""
    setattr(style, field, template)
    return paint_brush(getattr(style, field), tint, **options)
