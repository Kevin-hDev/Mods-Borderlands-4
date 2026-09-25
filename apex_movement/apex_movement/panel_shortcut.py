"""A shortcut's two fields on its switch's row: the bound key, then the button that captures a new one."""

import unrealsdk
from mods_base import KeybindOption

from . import panel_buttons as b, panel_i18n as i18n, panel_pages as p, panel_text as tx, panel_theme as t
from . import panel_widgets as w

# The selectors wear the menu buttons' hover and press veils; their colour comes from the Border behind them.
_VEILS = (("Normal", None), ("Hovered", t.HOVER_OVERLAY), ("Pressed", t.PRESS_OVERLAY), ("Disabled", None))
_MENU_CLICK = "LeftMouseButton"
# A shortcut has no row of its own: its two fields sit right of its switch (Kevin, 2026-09-25).
SHORTCUT_ROWS = {"third_person_key": "third_person", "walk_key": "walk"}


def is_shortcut(option):
    # The SDK's own class: the camera runtime's keyboard-only subclass ships in the full pack alone, and this window
    # also ships in every separate movement file.
    return isinstance(option, KeybindOption)


def _selector(owner, template, role, colour, margin):
    """A native key selector: the only widget that captures a key, and the one that names it as the game does."""
    widget = w.new("InputKeySelector", owner)
    widget.SetAllowGamepadKeys(False)
    widget.SetAllowModifierKeys(False)
    widget.SetEscapeKeys([unrealsdk.make_struct("Key", KeyName="Escape")])
    widget.SetCursor(w.enum("EMouseCursor", "Default"))
    w.cosmetic("key_selector", lambda: _selector_style(widget, template, role, colour, margin))
    # Unreal's button nudges its text down while pressed; the menu's buttons keep theirs still.
    w.cosmetic("key_selector_padding", lambda: _still(widget.WidgetStyle))
    return widget


def _selector_style(widget, template, role, colour, margin):
    for field, veil in _VEILS:
        tint, alpha = veil or (t.COLOR_INK, 0.0)
        w.style_brush(widget.WidgetStyle, field, template, tint, alpha=alpha)
    tx.configure(widget.TextStyle.Font, role)
    widget.TextStyle.ColorAndOpacity = w.slate(colour)
    widget.Margin = margin


def _still(style):
    style.NormalPadding = w.pad(0)
    style.PressedPadding = w.pad(0)


def _key_field(owner, widgets, name, template):
    """The FOV value's ink box (panel_slider.value_box), naming the bound key."""
    box = w.border(owner, t.COLOR_INK)
    fit = w.new("ScaleBox", box)
    # A long name such as "Thumb Mouse Button 2" shrinks to the box instead of pushing the row wider.
    fit.SetStretch(w.enum("EStretch", "ScaleToFit"))
    fit.SetStretchDirection(w.enum("EStretchDirection", "DownOnly"))
    shown = _selector(fit, template, "value", t.COLOR_GOLD, w.pad(0, t.SPACE_3))
    # Display only: never clicked nor reached from the keyboard, so it cannot start a capture of its own.
    shown.SetVisibility(w.enum("ESlateVisibility", "HitTestInvisible"))
    fit.SetContent(shown)
    box.SetContent(fit)
    widgets[f"key:{name}"] = shown
    return w.slant(box)


def _change_button(owner, widgets, name, template):
    """The menu's secondary button, with the switch's frame, shadow and height, around the capturing selector."""
    role, stroke, offset, padding, _centred, _minimum = b.KINDS["switch"]
    fill, frame, text, shadow = b.STYLES["secondary"]
    outer, inner = w.framed(owner, fill, stroke, frame=frame)
    selector = _selector(inner, template, role, text, w.pad(tx.inset(padding[0], role), padding[1]))
    inner.SetContent(selector)
    body = w.new("SizeBox", owner)
    body.SetMinDesiredWidth(float(t.KEY_CHANGE_WIDTH))
    body.SetContent(outer)
    layers, _shade = w.shadowed(owner, body, offset, shadow)
    widgets[f"setting:{name}"] = selector
    return w.slant(layers)


def fields(line, widgets, name, template):
    """Adds both fields to the end of a setting's row, after its switch."""
    offset = b.KINDS["switch"][2]
    # Stretched to the row less the switch's shadow, the key box is as tall as the buttons' faces.
    w.row(line, _key_field(line, widgets, name, template), fill=True, padding=w.pad(0, 0, offset, 0), valign="Fill")
    # A smaller gap than the one after the switch keeps the key and its button together, as with EN and FR.
    w.row(line, _change_button(line, widgets, name, template), padding=w.pad(0, 0, 0, t.SPACE_3), valign="Center")


def rows(card, options, widgets, template):
    """A card's setting rows, registered as row:<name> so a page can grey one, with each shortcut on its switch."""
    options = tuple(options)
    p.setting_rows(card, [option for option in options if not is_shortcut(option)], widgets, template,
                   expose_rows=True)
    for option in options:
        if is_shortcut(option):
            fields(widgets[f"row:{SHORTCUT_ROWS[option.identifier]}"], widgets, option.identifier, template)


def texts(widgets, key, language):
    widgets[f"setting:{key}"].SetNoKeySpecifiedText(i18n.text("change_key", language))
    widgets[f"setting:{key}"].SetKeySelectionText(i18n.text("press_key", language))
    widgets[f"key:{key}"].SetNoKeySpecifiedText(i18n.text("no_key", language))


def show_key(selector, name):
    """With no key, a selector shows its own word: the Change button's label, or the key field's "none"."""
    key = unrealsdk.make_struct("Key", KeyName=name or "None")
    selector.SetSelectedKey(unrealsdk.make_struct("InputChord", Key=key))


def take_key(selector):
    """The key a Change button has just captured, or None; the button then shows its own word again."""
    if selector.GetIsSelectingKey():
        return None
    name = str(selector.SelectedKey.Key.KeyName)
    if name in ("", "None"):
        return None
    show_key(selector, None)
    # A second click on the button arrives as the left button, which key_option refuses as a shortcut: it cancels
    # the wait like Escape, instead of reporting a failed save.
    return None if name == _MENU_CLICK else name
