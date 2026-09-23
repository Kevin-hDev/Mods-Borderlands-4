"""Show the custom window when this mod's SDK settings page is selected."""

from . import report

MARKER = "_vehicle_driving_panel_display_installed"


def install(mod):
    if getattr(mod, MARKER, False):
        return
    original = getattr(mod, "iter_display_options", None)
    if not callable(original):
        return

    def display():
        try:
            from . import panel_entry
            panel_entry.open_page(mod)
        except Exception:
            report.error_once("panel:menu", "Custom menu unavailable. Console settings remain available.")
        yield from original()

    mod.iter_display_options = display
    setattr(mod, MARKER, True)
