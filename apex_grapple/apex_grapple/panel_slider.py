"""The mockup's value controls: thick ink-rimmed bar filled in gold, slanted handle, bounds and value box.

Unreal's slider has no filled part: a progress bar under it draws the gold fill, and the slider's own bar is
made invisible so only its handle shows (mockup menu.css, .slider).
"""

from . import panel_i18n as i18n, panel_text as tx, panel_theme as t, panel_widgets as w

_BARS = ("NormalBarImage", "HoveredBarImage", "DisabledBarImage")
_THUMBS = (("NormalThumbImage", t.COLOR_GOLD), ("HoveredThumbImage", t.COLOR_GOLD_HI),
           ("DisabledThumbImage", t.COLOR_TEXT_DIM))


def _track_style(bar, template):
    style = bar.WidgetStyle
    w.style_brush(style, "BackgroundImage", template, t.COLOR_TRACK)
    w.style_brush(style, "FillImage", template, t.COLOR_GOLD)
    w.style_brush(style, "MarqueeImage", template, t.COLOR_GOLD)


def _handle_style(knob, template):
    style = knob.WidgetStyle
    for field in _BARS:
        w.style_brush(style, field, template, t.COLOR_INK, alpha=0.0)
    for field, tint in _THUMBS:
        w.style_brush(style, field, template, tint, outline=t.STROKE,
                      size=(t.SLIDER_THUMB_WIDTH, t.SLIDER_THUMB_HEIGHT))
    style.BarThickness = float(t.SLIDER_TRACK)


def slider(owner, widgets, option, template):
    key = option.identifier
    stack = w.new("Overlay", owner)
    rim = w.border(stack, t.COLOR_INK, t.STROKE)
    bar = w.new("ProgressBar", rim)
    rim.SetContent(bar)
    w.cosmetic("track", lambda: _track_style(bar, template))
    inset = (t.SLIDER_HEIGHT - t.SLIDER_TRACK) / 2
    # The handle travels between its own half-widths, so the fill starts and ends there too.
    w.layer(stack, rim, w.pad(inset, t.SLIDER_THUMB_WIDTH / 2))
    knob = w.new("Slider", stack)
    knob.SetMinValue(float(option.min_value))
    knob.SetMaxValue(float(option.max_value))
    knob.SetStepSize(float(option.step))
    knob.SetValue(float(option.value))
    w.cosmetic("handle", lambda: _handle_style(knob, template))
    w.slant(knob)
    w.layer(stack, knob)
    ends = w.new("HorizontalBox", owner)
    w.row(ends, tx.text(ends, i18n.number(option, option.min_value), "ends"))
    w.row(ends, w.new("Spacer", ends), fill=True)
    w.row(ends, tx.text(ends, i18n.number(option, option.max_value), "ends"))
    control = w.new("VerticalBox", owner)
    w.column(control, w.sized(control, stack, height=t.SLIDER_HEIGHT))
    w.column(control, ends, padding=w.pad(0, t.SLIDER_THUMB_WIDTH / 2))
    widgets[f"setting:{key}"], widgets[f"fill:{key}"] = knob, bar
    return control


def value_box(owner, widgets, key):
    box = w.border(owner, t.COLOR_INK, w.pad(tx.inset(t.SPACE_1, "value"), 0))
    number = tx.text(box, "", "value", center=True)
    box.SetContent(number)
    w.slant(box)
    widgets[f"value:{key}"] = number
    return w.sized(owner, box, width=t.ROW_VALUE_WIDTH)


def show(widgets, option, value):
    widgets[f"value:{option.identifier}"].SetText(i18n.number(option, value))
    span = option.max_value - option.min_value
    fraction = (value - option.min_value) / span if span else 0.0
    widgets[f"fill:{option.identifier}"].SetPercent(min(1.0, max(0.0, fraction)))
