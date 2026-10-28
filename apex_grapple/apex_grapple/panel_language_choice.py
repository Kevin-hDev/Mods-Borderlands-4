"""The language buttons: a click saves the language and writes the window's texts in it.

One implementation for every window, Grapple's and Movement's alike. Japanese and the other languages draw from
different fallback faces, chosen when a window is built (panel_fonts.py): a change between the two draws the window
again, as a theme change does (control_window_redraw.py).
"""

from . import panel_fonts as fonts
from .panel_preferences import LANGUAGES


def choose(form, widgets, prefix=""):
    """Whether a language button was pressed; prefix: what its widget's name has before the code, "language:" on an
    Options page. During a key capture, which a new window would drop, the texts change and the faces wait for the
    next opening."""
    for language in LANGUAGES:
        if form.take(widgets[prefix + language]):
            before = form.model.language
            if form.flush(widgets) and form.model.change_language(language):
                form.refresh_labels(widgets)
                if fonts.script(language) != fonts.script(before) and not form.selecting():
                    # Saved already: if the new window cannot be drawn, the old one says so, in the new language.
                    form.redraw, form.redraw_notice = True, "saved"
            else:
                form.report(widgets, "failed")
            return True
    return False
