"""Connect Apex Movement's authoritative options to the shared menu frame."""

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


def build(pc, bindings, return_to_menu):
    model = Model(bindings.mod)
    root, widgets = panel_view.build_view(pc, model, return_to_menu)
    weak = unrealsdk.unreal.WeakPointer
    return root, PanelForm({name: weak(widget) for name, widget in widgets.items()}, model)
