# Generated: the window Kevin's mods share, taken from Hunter Change's plain window, under Co-op Duel's
# names. Its comments may speak of other mods. Never edited by hand: docs/duel/outils/menu_window.py
# writes this file.
"""Connect Co-op Duel's authoritative options to the shared menu frame."""

import unrealsdk

from .panel_model import Model
from .panel_form import PanelForm
from . import panel_view


class PanelBindings:
    def __init__(self):
        from . import mod
        self.mod = mod

    def ready(self):
        return True  # The menu remains open while its gameplay switch is off.

    def prepare(self):
        return True


def build(pc, bindings, return_to_menu, model=None):
    # A theme change draws the window again around the same model: its undo, page and transactions carry over.
    model = model or Model(bindings.mod)
    root, widgets = panel_view.build_view(pc, model, return_to_menu)
    weak = unrealsdk.unreal.WeakPointer
    return root, PanelForm({name: weak(widget) for name, widget in widgets.items()}, model)
