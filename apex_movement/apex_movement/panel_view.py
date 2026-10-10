"""Apex Movement in Grapple's approved frame, with a scrolling movement list."""

from . import panel_buttons as b, panel_fonts as fonts, panel_header as h, panel_shortcut as sc
from . import panel_modal as modal, panel_window_size as size
from . import panel_options as o, panel_pages as p
from . import panel_text as tx, panel_theme as t, panel_widgets as w, report


def _sidebar(owner, widgets, template):
    # The side padding lies inside the scrolling list, as in the mockup's nav: a ScrollBox cuts whatever leaves it,
    # and the slanted page buttons lean past their box (corners cut, Kevin's screenshot of 2026-10-06).
    panel = w.border(owner, t.COLOR_SIDEBAR, w.pad(t.SPACE_5, 0))
    column = w.new("VerticalBox", panel)
    panel.SetContent(column)
    # No SETTINGS caption over the pages (Kevin, 2026-10-10): it took room for nothing, beside the OPTIONS page.
    scroll = w.new("ScrollBox", column)
    w.cosmetic("nav_scrollbar", lambda: p._scrollbar(scroll, template))
    nav = w.new("VerticalBox", scroll)
    scroll.AddChild(nav).SetPadding(w.pad(0, t.SPACE_4))
    for page in t.PAGES:
        button = b.button(nav, widgets, f"nav:{page}", "nav", template, "nav_off")
        w.column(nav, button, padding=w.pad(0, 0, t.SPACE_2))
        # An Options tab's page is opened from the gear: collapsed rather than left out, its button stays in the
        # tree for the code that reads every page's (Kevin, 2026-10-06).
        if page in o.TABS:
            button.SetVisibility(w.enum("ESlateVisibility", "Collapsed"))
    w.column(column, scroll, fill=True)
    widgets["meta"] = tx.text(column, "", "meta", wrap=True)
    w.column(column, widgets["meta"], padding=w.pad(t.SPACE_5, t.SPACE_4 + t.SPACE_2, t.SPACE_3))
    w.column(column, b.button(column, widgets, "enabled", "master", template, "on"), halign="Left",
             padding=w.pad(0, t.SPACE_4))
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
    layers, _ = w.shadowed(root, frame, size.SHADOW)
    root.SetContent(w.sized(root, layers, size.WIDTH + size.SHADOW, size.HEIGHT + size.SHADOW))
    # Pop-ups (panel_popup.py) lie in a layer over the whole window: a page or its scrolling never cuts one.
    over = w.new("Overlay", body)
    body.SetContent(over)
    stack = w.new("VerticalBox", over)
    w.layer(over, stack)
    widgets["popups"] = w.new("Overlay", over)
    widgets["popups"].SetVisibility(w.enum("ESlateVisibility", "SelfHitTestInvisible"))
    w.layer(over, widgets["popups"])
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
        # A shortcut sits on its switch's row: the walk key on the auto sprint's page (Kevin, 2026-09-25).
        sc.rows(p.card(body, widgets, key), group.children, widgets, template)
        switcher.AddChild(page)
    if "commands" in model.pages:
        from . import panel_camera_commands as commands
        switcher.AddChild(commands.page(switcher, model, widgets, template, o.commands_frame(widgets, template)))
    if "language" in model.pages:
        switcher.AddChild(o.language_page(switcher, widgets, template))
    if "dynamic_camera" in model.pages:
        switcher.AddChild(o.dynamic_page(switcher, model, widgets, template))
    for key in o.CARD_PAGES:
        if key in model.pages:
            switcher.AddChild(o.card_page(switcher, model, widgets, template, key))
    switcher.AddChild(o.options_page(switcher, model, widgets, template))
    w.row(middle, switcher, fill=True)
    w.column(stack, w.line(stack, t.COLOR_INK, height=t.STROKE_THICK))
    w.column(stack, _footer(stack, widgets, template))
    return avatar


def build_view(pc, model, _return_to_menu=True):
    t.use(model.theme)  # every colour below, and every later repaint, reads this theme
    size.use(model.window_size, pc)  # the drawing's size, read below, by the header and the layer
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
    widgets["focus"] = widgets["options" if model.page in o.TABS else f"nav:{model.page}"]
    report.note(f"settings window: fonts={'+'.join(sorted(loaded)) or 'engine'}, "
                f"avatar={'shown' if avatar else 'hidden'}")
    return modal.held(pc, root), widgets

