"""The settings window laid out as Kevin's approved mockup v2, with this mod's four pages in the sidebar."""

import unrealsdk

from . import panel_buttons as b, panel_fonts as fonts, panel_header as h, panel_i18n as i18n, panel_pages as p
from . import panel_text as tx, panel_theme as t, panel_widgets as w, report


def _sidebar(owner, widgets, template):
    panel = w.border(owner, t.COLOR_SIDEBAR, w.pad(t.SPACE_5, t.SPACE_4))
    nav = w.new("VerticalBox", panel)
    panel.SetContent(nav)
    widgets["settings_caption"] = tx.text(nav, "", "caption")
    w.column(nav, widgets["settings_caption"], padding=w.pad(0, t.SPACE_2, t.SPACE_3))
    for page in t.PAGES:
        w.column(nav, b.button(nav, widgets, f"nav:{page}", "nav", template, "nav_off"),
                 padding=w.pad(0, 0, t.SPACE_2))
    widgets["meta"] = tx.text(nav, "", "meta", wrap=True)
    w.column(nav, widgets["meta"], padding=w.pad(t.SPACE_5, t.SPACE_2, t.SPACE_3))
    w.column(nav, b.button(nav, widgets, "enabled", "master", template, "on"), halign="Left")
    return w.sized(owner, panel, width=t.SIDEBAR_WIDTH)


def _footer(owner, widgets, template):
    panel = w.border(owner, t.COLOR_HEADER, w.pad(t.SPACE_3, t.SPACE_7))
    line = w.new("HorizontalBox", panel)
    panel.SetContent(line)
    widgets["notice"] = tx.text(line, "", "desc", wrap=True)
    w.row(line, widgets["notice"], fill=True, valign="Center")
    for name in ("undo", "restore"):
        w.row(line, b.button(line, widgets, name, "action", template, "secondary"),
              padding=w.pad(0, 0, 0, t.SPACE_5), valign="Center")
    return panel


def _window(root, world, model, widgets, template):
    frame, body = w.framed(root, t.COLOR_WINDOW, t.STROKE_THICK)
    frame.SetCursor(w.enum("EMouseCursor", "Default"))
    layers, _ = w.shadowed(root, frame, t.SHADOW_XL)
    root.SetContent(w.sized(root, layers, t.WINDOW_WIDTH + t.SHADOW_XL, t.WINDOW_HEIGHT + t.SHADOW_XL))
    stack = w.new("VerticalBox", body)
    body.SetContent(stack)
    w.column(stack, h.hazard(stack))
    head, avatar = h.header(stack, world, widgets, template)
    w.column(stack, head)
    w.column(stack, w.line(stack, t.COLOR_INK, height=t.STROKE_THICK))
    middle = w.new("HorizontalBox", stack)
    w.column(stack, middle, fill=True)
    w.row(middle, _sidebar(middle, widgets, template))
    w.row(middle, w.line(middle, t.COLOR_INK, width=t.STROKE_THICK))
    switcher = w.new("WidgetSwitcher", middle)
    widgets["pages"] = switcher
    for group, key in zip(model.groups, t.PAGES):
        switcher.AddChild(p.settings_page(switcher, group, key, widgets, template))
    switcher.AddChild(p.controls_page(switcher, widgets, template))
    w.row(middle, switcher, fill=True)
    w.column(stack, w.line(stack, t.COLOR_INK, height=t.STROKE_THICK))
    w.column(stack, _footer(stack, widgets, template))
    return avatar


def _held(pc, content):
    """Wraps the window in a UserWidget, which Slate keeps alive for as long as it is on screen.

    Nothing held the bare ScaleBox: the garbage collector removed the window 35 and 50 s after it opened, twice
    without a click on Close (journal of 2026-09-21, "window_gone"). Matt's BL4 Mods Menu builds its window the same
    way (single source).
    """
    holder = w.new("UserWidget", pc)
    tree = w.new("WidgetTree", holder)
    holder.WidgetTree = tree
    tree.RootWidget = content
    return holder


def build_view(pc, model, _return_to_menu=True):
    root = w.new("ScaleBox", pc)
    root.SetStretch(w.enum("EStretch", "ScaleToFit"))
    # A spare key selector lends its solid button brush to every other style: the one brush proven in BL4.
    template = w.new("InputKeySelector", root).WidgetStyle.Normal
    loaded = fonts.build(root)
    tx.use(loaded)
    try:
        widgets = {name: p.selector(root, i18n.text("listening", model.language), template)
                   for name in ("first", "second")}
        avatar = _window(root, pc, model, widgets, template)
    finally:
        tx.use({})
    widgets["focus"] = widgets[f"nav:{model.page}"]
    # The line to read after an opening: which of the mockup's fonts and picture the game accepted.
    report.note(f"settings window: fonts={'+'.join(sorted(loaded)) or 'engine'}, avatar={'shown' if avatar else 'hidden'}")
    return _held(pc, root), widgets


def viewport_slot():
    # The mockup's window keeps its share of the 1920 × 1080 screen at any resolution; the ScaleBox fits it.
    width = (t.WINDOW_WIDTH + t.SHADOW_XL) / t.STAGE_WIDTH
    height = (t.WINDOW_HEIGHT + t.SHADOW_XL) / t.STAGE_HEIGHT
    anchors = unrealsdk.make_struct("Anchors", Minimum=w.vector((1 - width) / 2, (1 - height) / 2),
                                    Maximum=w.vector((1 + width) / 2, (1 + height) / 2))
    return unrealsdk.make_struct("GameViewportWidgetSlot", ZOrder=t.ORDER, bAutoRemoveOnWorldRemoved=True,
                                 Alignment=w.vector(0.0, 0.0), Anchors=anchors, Offsets=w.pad(0))
