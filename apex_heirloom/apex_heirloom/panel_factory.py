"""Adapt the complete menu to the proven window lifecycle and key-binding service."""

import unrealsdk

from .control_bindings import Bindings
from .panel_model import Model
from .panel_form import PanelForm
from . import panel_view


class PanelBindings(Bindings):
    def ready(self):
        # A disabled mod must remain configurable and re-enableable from its own menu.
        return True

    def prepare(self):
        if not self.mod.is_enabled:
            return True
        return super().prepare()


def build(pc, bindings, return_to_menu):
    model = Model(bindings.mod)
    root, widgets = panel_view.build_view(pc, model, return_to_menu)
    weak = unrealsdk.unreal.WeakPointer
    return root, PanelForm({name: weak(widget) for name, widget in widgets.items()}, bindings, model)
