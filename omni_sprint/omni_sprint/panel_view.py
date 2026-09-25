"""Omni Sprint in Grapple's approved frame: its camera page, the shortcut beside its switch."""

import unrealsdk

from . import panel_buttons as b, panel_fonts as fonts, panel_header as h
from . import panel_pages as p, panel_shortcut as sc, panel_text as tx, panel_theme as t, panel_widgets as w, report


def _sidebar(owner, widgets, template):
    panel = w.border(owner, t.COLOR_SIDEBAR, w.pad(t.SPACE_5, t.SPACE_4))
    column = w.new("VerticalBox", panel)
    panel.SetContent(column)
    widgets["settings_caption"] = tx.text(column, "", "caption")
    w.column(column, widgets["settings_caption"], padding=w.pad(0, t.SPACE_2, t.SPACE_3))
    scroll = w.new("ScrollBox", column)
    w.cosmetic("nav_scrollbar", lambda: p._scrollbar(scroll, template))
    nav = w.new("VerticalBox", scroll)
    scroll.AddChild(nav)
    for page in t.PAGES:
        w.column(nav, b.button(nav, widgets, f"nav:{page}", "nav", template, "nav_off"),
                 padding=w.pad(0, 0, t.SPACE_2))
    w.column(column, scroll, fill=True)
    widgets["meta"] = tx.text(column, "", "meta", wrap=True)
    w.column(column, widgets["meta"], padding=w.pad(t.SPACE_5, t.SPACE_2, t.SPACE_3))
    w.column(column, b.button(column, widgets, "enabled", "master", template, "on"), halign="Left")
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
    for group, key in zip(model.groups, model.pages):
        page, body = p.scrolling_body(switcher, template)
        # No camera option is shown while another mod drives the camera: its card keeps the sentence.
        shown = [option for option in group.children if option.identifier in model.options]
        sc.rows(p.card(body, widgets, key), shown, widgets, template)
        switcher.AddChild(page)
    w.row(middle, switcher, fill=True)
    w.column(stack, w.line(stack, t.COLOR_INK, height=t.STROKE_THICK))
    w.column(stack, _footer(stack, widgets, template))
    return avatar


def _held(pc, content):
    holder = w.new("UserWidget", pc)
    tree = w.new("WidgetTree", holder)
    holder.WidgetTree = tree
    tree.RootWidget = content
    return holder


def build_view(pc, model, _return_to_menu=True):
    root = w.new("ScaleBox", pc)
    root.SetStretch(w.enum("EStretch", "ScaleToFit"))
    template = w.new("InputKeySelector", root).WidgetStyle.Normal
    loaded = fonts.build(root)
    tx.use(loaded)
    try:
        widgets = {}
        avatar = _window(root, pc, model, widgets, template)
    finally:
        tx.use({})
    widgets["focus"] = widgets[f"nav:{model.page}"]
    report.note(f"settings window: fonts={'+'.join(sorted(loaded)) or 'engine'}, "
                f"avatar={'shown' if avatar else 'hidden'}")
    return _held(pc, root), widgets


def viewport_slot():
    width = (t.WINDOW_WIDTH + t.SHADOW_XL) / t.STAGE_WIDTH
    height = (t.WINDOW_HEIGHT + t.SHADOW_XL) / t.STAGE_HEIGHT
    anchors = unrealsdk.make_struct("Anchors", Minimum=w.vector((1 - width) / 2, (1 - height) / 2),
                                    Maximum=w.vector((1 + width) / 2, (1 + height) / 2))
    return unrealsdk.make_struct("GameViewportWidgetSlot", ZOrder=t.ORDER, bAutoRemoveOnWorldRemoved=True,
                                 Alignment=w.vector(0.0, 0.0), Anchors=anchors, Offsets=w.pad(0))
