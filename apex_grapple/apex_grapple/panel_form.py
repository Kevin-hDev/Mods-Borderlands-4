"""Full menu interactions, with bounded drafts and one shared key-capture form."""

import time

from .control_form import Form
from .control_bindings import RESERVED
from . import panel_i18n as i18n, panel_labels as labels, panel_theme as t
from . import panel_key_display


class PanelForm(Form):
    keep_when_disabled = True

    def __init__(self, widgets, bindings, model):
        super().__init__(widgets, bindings)
        self.model, self.page, self.notice = model, t.PAGES.index(model.page), "ready"
        self.pending, self.shown = {}, {}
        self.changed_at = 0
        self.focus = widgets["focus"]
        self.key_display = panel_key_display.Display()
        self.sync(self.resolve())

    def sync(self, widgets):
        self.pending.clear()
        widgets["pages"].SetActiveWidgetIndex(self.page)
        for key, option in self.model.options.items():
            self.shown[key] = option.value
            widget = widgets[f"setting:{key}"]
            if type(option.default_value) is bool:
                widget.SetIsChecked(False)
            else:
                widget.SetValue(float(option.value))
        self.refresh_labels(widgets)

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

    @staticmethod
    def take(widget):
        if not widget.IsChecked():
            return False
        widget.SetIsChecked(False)
        return True

    def show_result(self, widgets, result):
        success, message = result
        key = "controls_saved" if success else "invalid_keys"
        if message == "Default grapple controls restored.":
            key = "controls_reset"
        elif message == "Could not save. Previous controls kept.":
            key = "failed"
        elif message == RESERVED:
            key = "reserved_key"
        widgets["status"].SetText(i18n.text(key, self.model.language))
        widgets["current"].SetText(labels.controls_summary(self.bindings, self.model.language))
        self.key_display.summary(self, widgets)

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
                self.notice = {"restore": "restored", "undo": "undone", "enabled": "saved"}[name] if success else "failed"
                if success and name in ("restore", "undo"):
                    self.two = False
                    widgets["two"].SetIsChecked(False)
                    widgets["second"].SetIsEnabled(False)
                    self.clear(widgets)
                self.sync(widgets)
                return False
        if self.pending and now - self.changed_at >= t.SAVE_DELAY_NS:
            self.flush(widgets)
        if self.page == t.PAGES.index("controls"):
            previous = self.two
            super().poll()
            if self.two != previous:
                self.refresh_labels(widgets)
            self.key_display.update(self, widgets)
        return False

    def selecting(self):
        return self.page == t.PAGES.index("controls") and super().selecting()
