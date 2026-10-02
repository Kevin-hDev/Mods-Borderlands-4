# Generated: the settings window Kevin's mods share, taken from Apex Heirloom's and put under this mod's names.
# Its comments may speak of that mod. Never edited by hand: the window's generator writes this file.
"""Full menu interactions, with bounded drafts; the COMMANDS page's own form captures the keys."""

import time

from .command_form import Form
from .panel_glyphs import Catalogue
from . import panel_i18n as i18n, panel_labels as labels, panel_theme as t
from . import panel_choices, panel_rows, slider_values
from .menu import COMMANDS_DEPEND_ON, DEPENDS_ON


class PanelForm:
    keep_when_disabled = True

    def __init__(self, widgets, model):
        self.widgets = widgets
        self.model, self.page, self.notice = model, t.PAGES.index(model.page), "ready"
        self.pending, self.shown = {}, {}
        self.changed_at = 0
        self.focus = widgets["focus"]
        self.command_form, self.command_catalogue = Form(widgets, model), Catalogue()
        self.sync(self.resolve())

    def resolve(self):
        widgets = {name: reference() for name, reference in self.widgets.items()}
        if any(widget is None for widget in widgets.values()):
            raise ValueError("Window widget unavailable")
        return widgets

    def sync(self, widgets):
        self.pending.clear()
        widgets["pages"].SetActiveWidgetIndex(self.page)
        for key, option in self.model.options.items():
            self.shown[key] = option.value
            widget = widgets[f"setting:{key}"]
            if type(option.default_value) is bool:
                widget.SetIsChecked(False)
            elif panel_choices.is_choice(option):
                panel_choices.release(widgets, option)
            else:
                self.shown[key] = slider_values.bounded(option)
                widget.SetValue(self.shown[key])
        self.refresh_dependency(widgets)
        self.refresh_labels(widgets)

    def met(self, needs):
        return all(any(self.shown[switch] is True for switch in switches) for switches in needs)

    def refresh_dependency(self, widgets):
        for name, needs in DEPENDS_ON.items():
            active = self.met(needs) and panel_rows.active(name, self.shown)
            self.grey(widgets, f"setting:{name}", (f"row:{name}", f"description:{name}"), active)
        panel_rows.show(widgets, self.shown)
        for command, needs in COMMANDS_DEPEND_ON.items():
            active = self.met(needs)
            self.grey(widgets, f"card:command_{command}", (f"card:command_{command}",), active)
            self.command_form.block(widgets, command, not active)

    @staticmethod
    def grey(widgets, control, faded, active):
        widgets[control].SetIsEnabled(active)
        # The whole row fades, label and value included, as the mockup's .row.muted does.
        for name in faded:
            widgets[name].SetRenderOpacity(1.0 if active else t.OPACITY_DISABLED)

    def refresh_labels(self, widgets):
        labels.apply(self, widgets)
        for key, option in self.model.options.items():
            labels.value(widgets, option, self.shown[key], self.model.language)

    def report(self, widgets, key):
        self.notice = key
        widgets["notice"].SetText(i18n.text(key, self.model.language))

    def flush(self, widgets):
        if not self.pending:
            return True
        success = self.model.write(self.pending)
        self.notice = "saved" if success else "failed"
        self.sync(widgets)
        return success

    def read_changes(self, widgets, now):
        for key, option in self.model.options.items():
            widget = widgets[f"setting:{key}"]
            if type(option.default_value) is bool:
                if not self.take(widget):
                    continue
                value = not self.shown[key]
            elif panel_choices.is_choice(option):
                value = panel_choices.taken(self.take, widgets, option, self.shown[key])
                if value is None or value == self.shown[key]:
                    continue
            else:
                raw = widget.GetValue()
                if abs(raw - self.shown[key]) < max(1e-6, option.step * 0.01):
                    continue  # Native sliders return float32, not exact Python decimals.
                try:
                    value = self.model.normalize(option, raw)
                except (TypeError, ValueError, OverflowError):
                    self.notice = "failed"
                    self.sync(widgets)
                    return
                if value == self.shown[key]:
                    continue
            self.shown[key] = value
            if value == option.value:
                self.pending.pop(key, None)
            else:
                self.pending[key] = value
            self.changed_at = now
            labels.value(widgets, option, value, self.model.language)
        self.refresh_dependency(widgets)

    @staticmethod
    def take(widget):
        if not widget.IsChecked():
            return False
        widget.SetIsChecked(False)
        return True

    def poll(self):
        widgets, now = self.resolve(), time.perf_counter_ns()
        self.read_changes(widgets, now)
        if self.take(widgets["close"]):
            return self.flush(widgets)
        for language in ("EN", "FR"):
            if self.take(widgets[language]):
                if self.flush(widgets) and self.model.change_language(language):
                    self.refresh_labels(widgets)
                else:
                    self.report(widgets, "failed")
                return False
        for family in ("PS5", "XSX"):
            if self.take(widgets[f"icons:{family}"]):
                if self.model.change_controller_icons(family):
                    self.refresh_labels(widgets)
                else:
                    self.report(widgets, "failed")
                return False
        for index, key in enumerate(t.PAGES):
            if self.take(widgets[f"nav:{key}"]):
                if self.flush(widgets) and self.model.change_page(key):
                    self.page = index
                    widgets["pages"].SetActiveWidgetIndex(index)
                    self.refresh_labels(widgets)
                else:
                    self.report(widgets, "failed")
                return False
        for name in ("restore", "undo", "enabled"):
            if self.take(widgets[name]):
                if not self.flush(widgets):
                    return False
                operation = self.model.toggle_enabled if name == "enabled" else getattr(self.model, name)
                success = operation()
                self.notice = ({"restore": "restored", "undo": "undone", "enabled": "saved"}[name] if success
                               else "failed")
                self.sync(widgets)
                return False
        if self.pending and now - self.changed_at >= t.SAVE_DELAY_NS:
            self.flush(widgets)
        if self.page == t.PAGES.index("controls"):
            self.command_form.poll()
            if self.command_form.changed:
                self.refresh_labels(widgets)
        return False

    def selecting(self):
        return self.page == t.PAGES.index("controls") and self.command_form.selecting()
