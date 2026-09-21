"""Open the full panel on this mod's page once; return to the original list on Close."""

MARKER = "_apex_grapple_panel_opened"
MAX_STACK = 32


def open_page(mod):
    from console_mod_menu import screens
    from console_mod_menu.screens.mod import ModScreen
    from . import control_window
    stack = screens.screen_stack
    if not 1 < len(stack) <= MAX_STACK:
        return
    page, parent = stack[-1], stack[-2]
    if not isinstance(page, ModScreen) or page.mod is not mod or getattr(page, MARKER, False):
        return
    setattr(page, MARKER, True)
    control_window.start(return_to_menu=True, full_menu=True)
    session = control_window._active
    if session is None or not getattr(session.form, "keep_when_disabled", False):
        return  # Keep the console settings available if native construction fails.

    def back_to_list():
        if len(stack) < 2 or stack[-1] is not page or stack[-2] is not parent:
            raise RuntimeError("Menu context changed")
        screens.pop_screen()
        parent.draw()

    session.handoff.redraw = back_to_list
