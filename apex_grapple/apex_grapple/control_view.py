"""Binding panel presentation; persistence is delegated to the running mod."""

import unrealsdk

WIDTH, HEIGHT, ORDER = 960.0, 680.0, 10000
PADDING, GAP = 32.0, 12.0
HEADING_SIZE, BODY_SIZE, BUTTON_SIZE = 34, 22, 28
BUTTON_HEIGHT = 68.0
TOGGLE_BUTTON = 1
BACKGROUND = (0.012, 0.019, 0.028, 1.0)
FOREGROUND = (0.95, 0.97, 1.0, 1.0)
ACCENT = (0.25, 0.8, 1.0, 1.0)
ACTION_NORMAL = (0.035, 0.09, 0.15, 1.0)
ACTION_HOVER = (0.07, 0.19, 0.28, 1.0)
TITLE = "APEX GRAPPLE  /  CONTROLS"
INSTRUCTION = "Select a key slot, then press your key or button.\nComplete choices are saved automatically."
BUTTON = "CHOOSE A KEY"
LISTENING = "PRESS YOUR KEY NOW"
FOOTER = "Esc cancels key capture. Close returns to the game."
FOOTER_MENU = "Esc cancels key capture. Close returns to the mod menu."
READY = "Choose a key. It will be saved immediately."
TWO = "Two keys held together"
RESET, CLOSE = "RESET CONTROLS", "CLOSE"
SECOND = "2. CHOOSE SECOND KEY"


def color(values):
    return unrealsdk.make_struct("LinearColor", R=values[0], G=values[1], B=values[2], A=values[3])


def margin(amount):
    return unrealsdk.make_struct("Margin", Left=amount, Top=amount, Right=amount, Bottom=amount)


def text(owner, content, size, tint):
    widget = unrealsdk.construct_object("TextBlock", owner)
    widget.SetText(content)
    font = widget.Font
    font.Size = size
    widget.SetFont(font)
    widget.SetColorAndOpacity(unrealsdk.make_struct("SlateColor", SpecifiedColor=color(tint)))
    widget.SetAutoWrapText(True)
    return widget


def append(box, widget):
    slot = box.AddChildToVerticalBox(widget)
    slot.SetPadding(unrealsdk.make_struct("Margin", Bottom=GAP))


def selector_row(box, label):
    frame = unrealsdk.construct_object("SizeBox", box)
    frame.SetHeightOverride(BUTTON_HEIGHT)
    selector = unrealsdk.construct_object("InputKeySelector", frame)
    selector.TextStyle.Font.Size = BUTTON_SIZE
    selector.SetAllowGamepadKeys(True)
    selector.SetAllowModifierKeys(False)
    selector.SetNoKeySpecifiedText(label)
    selector.SetKeySelectionText(LISTENING)
    selector.SetEscapeKeys([unrealsdk.make_struct("Key", KeyName="Escape")])
    selector.SetCursor(unrealsdk.find_enum("EMouseCursor").Default)
    frame.SetContent(selector)
    append(box, frame)
    return selector


def action_button(owner, label, template):
    # Latched native button state: a short click cannot be missed between two polls.
    button = unrealsdk.construct_object("CheckBox", owner)
    button.WidgetStyle.CheckBoxType = TOGGLE_BUTTON
    for field, brush, tint in (("UncheckedImage", template.Normal, ACTION_NORMAL),
                               ("UncheckedHoveredImage", template.Hovered, ACTION_HOVER),
                               ("UncheckedPressedImage", template.Pressed, ACTION_HOVER),
                               ("CheckedImage", template.Pressed, ACTION_HOVER),
                               ("CheckedHoveredImage", template.Hovered, ACTION_HOVER),
                               ("CheckedPressedImage", template.Pressed, ACTION_HOVER)):
        setattr(button.WidgetStyle, field, brush)
        getattr(button.WidgetStyle, field).TintColor = unrealsdk.make_struct("SlateColor", SpecifiedColor=color(tint))
    button.SetContent(text(button, label, BODY_SIZE, FOREGROUND))
    button.SetIsChecked(False)
    return button


def build_view(pc, summary, return_to_menu=False):
    root = unrealsdk.construct_object("Border", pc)
    root.SetPadding(margin(PADDING))
    root.SetBrushColor(color(BACKGROUND))
    root.SetCursor(unrealsdk.find_enum("EMouseCursor").Default)
    box = unrealsdk.construct_object("VerticalBox", root)
    root.SetContent(box)
    append(box, text(box, TITLE, HEADING_SIZE, ACCENT))
    append(box, text(box, INSTRUCTION, BODY_SIZE, FOREGROUND))
    current = text(box, summary, BODY_SIZE, FOREGROUND)
    append(box, current)
    two = unrealsdk.construct_object("CheckBox", box)
    two.SetContent(text(two, TWO, BODY_SIZE, FOREGROUND))
    append(box, two)
    first = selector_row(box, BUTTON)
    second = selector_row(box, SECOND)
    second.SetIsEnabled(False)
    status = text(box, READY, BODY_SIZE, ACCENT)
    append(box, status)
    actions = unrealsdk.construct_object("HorizontalBox", box)
    reset = action_button(actions, RESET, first.WidgetStyle)
    close = action_button(actions, CLOSE, first.WidgetStyle)
    actions.AddChildToHorizontalBox(reset).SetPadding(margin(GAP))
    actions.AddChildToHorizontalBox(close).SetPadding(margin(GAP))
    append(box, actions)
    append(box, text(box, FOOTER_MENU if return_to_menu else FOOTER, BODY_SIZE, FOREGROUND))
    return root, {"first": first, "second": second, "two": two, "close": close,
                  "reset": reset, "status": status, "current": current}


def viewport_slot():
    centre = unrealsdk.make_struct("Vector2D", X=0.5, Y=0.5)
    return unrealsdk.make_struct("GameViewportWidgetSlot", Alignment=centre,
        Anchors=unrealsdk.make_struct("Anchors", Minimum=centre, Maximum=centre),
        Offsets=unrealsdk.make_struct("Margin", Left=0.0, Top=0.0, Right=WIDTH, Bottom=HEIGHT),
        ZOrder=ORDER, bAutoRemoveOnWorldRemoved=True)
