"""Skip the console's extra Press page only for this mod's controls button."""

from types import MethodType

from . import report

MAX_STACK = 32
MAX_CHOICE_LENGTH = 3
MARKER = "_apex_grapple_direct_controls"


def attach_page(mod, button):
    try:
        from console_mod_menu import screens
        from console_mod_menu.screens.mod import ModScreen
    except ImportError:
        report.error_once("controls:menu", "Direct controls access is unavailable; use the Press button.")
        return
    if not 0 < len(screens.screen_stack) <= MAX_STACK:
        return
    page = screens.screen_stack[-1]
    if not isinstance(page, ModScreen) or page.mod is not mod or getattr(page, MARKER, False):
        return
    original = page.handle_option_input

    def handle(current, line):
        # Keep the existing page on the stack, so Close returns directly to the mod settings.
        if type(line) is str and 0 < len(line) <= MAX_CHOICE_LENGTH and line.isascii() and line.isdigit():
            index = int(line) - 1
            if 0 <= index < len(current.drawn_options) and current.drawn_options[index] is button:
                button.on_press(button)
                return True
        return original(line)

    page.handle_option_input = MethodType(handle, page)
    setattr(page, MARKER, True)


def install(mod, button):
    if getattr(mod, MARKER, False):
        return
    original = mod.iter_display_options

    def display():
        attach_page(mod, button)
        try:
            from . import panel_entry
            panel_entry.open_page(mod)
        except (ImportError, AttributeError):
            report.error_once("panel:menu", "Custom menu unavailable. Console settings remain available.")
        yield from original()

    # Per-instance adapters: neither the SDK class nor another mod's page is modified.
    mod.iter_display_options = display
    setattr(mod, MARKER, True)
