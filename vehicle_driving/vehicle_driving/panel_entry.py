"""Open the full panel on this mod's page once; return to the original list on Close."""

MARKER = "_vehicle_driving_panel_opened"
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
    previous = control_window._active
    control_window.start(return_to_menu=True)
    session = control_window._active
    if session is None or session is previous or not getattr(session.form, "keep_when_disabled", False):
        return  # Keep the console settings available if native construction fails.

    def back_to_list():
        if not 0 < len(stack) <= MAX_STACK:
            raise RuntimeError("Menu context changed")
        if stack[-1] is page:
            if len(stack) < 2 or stack[-2] is not parent:
                raise RuntimeError("Menu context changed")
            screens.pop_screen()
        elif stack[-1] is not parent or any(screen is page for screen in stack):
            raise RuntimeError("Menu context changed")
        # If drawing failed after the pop, retry only while this parent still owns the menu.
        parent.draw()

    session.handoff.redraw = back_to_list
