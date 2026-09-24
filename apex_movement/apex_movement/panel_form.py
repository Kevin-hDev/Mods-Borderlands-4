"""Poll Movement's menu controls and save validated option changes."""

import time

from . import panel_i18n as i18n, panel_labels as labels, panel_shortcut as sc, panel_theme as t


class PanelForm:
    keep_when_disabled = True

    def __init__(self, widgets, model):
        self.widgets, self.model = widgets, model
        saved_page = model.page
        self.options_open = saved_page == "options"
        self.page = 0 if self.options_open else model.pages.index(saved_page)
        self.notice = "ready"
        self.pending, self.shown = {}, {}
        self.changed_at = 0
        self.focus = widgets["focus"]
        self.sync(self.resolve())

    def resolve(self):
        widgets = {name: reference() for name, reference in self.widgets.items()}
        if any(widget is None for widget in widgets.values()):
            raise ValueError("Window widget unavailable")
        return widgets

    def sync(self, widgets):
        self.pending.clear()
        active_page = len(self.model.pages) if self.options_open else self.page
        widgets["pages"].SetActiveWidgetIndex(active_page)
        for key, option in self.model.options.items():
            self.shown[key] = option.value
            widget = widgets[f"setting:{key}"]
            if sc.is_shortcut(option):
                continue  # The labels show its key; its Change button keeps its own word.
            if type(option.default_value) is bool:
                widget.SetIsChecked(False)
            else:
                widget.SetValue(float(option.value))
        self.refresh_dependency(widgets)
        self.refresh_labels(widgets)

    def refresh_dependency(self, widgets):
        if "fov" not in self.model.camera_options:
            return
        active = self.shown["custom_fov"] is True
        widgets["setting:fov"].SetIsEnabled(active)
        # The whole row fades, label and value included, as the mockup's .row.muted does.
        for name in ("row:fov", "description:fov"):
            widgets[name].SetRenderOpacity(1.0 if active else t.OPACITY_DISABLED)

    def refresh_labels(self, widgets):
        labels.apply(self, widgets)
        for key, option in self.model.options.items():
            labels.value(widgets, option, self.shown[key], self.model.language)

    @staticmethod
    def take(widget):
        if not widget.IsChecked():
            return False
        widget.SetIsChecked(False)
        return True

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
            if sc.is_shortcut(option):
                raw = sc.take_key(widget)
                if raw is None:
                    continue
                try:
                    value = self.model.normalize(option, raw)
                except (TypeError, ValueError):
                    self.report(widgets, "failed")
                    continue
                if value == self.shown[key]:
                    continue
            elif type(option.default_value) is bool:
                if not self.take(widget):
                    continue
                value = not self.shown[key]
            else:
                raw = widget.GetValue()
                if abs(raw - self.shown[key]) < max(1e-6, option.step * 0.01):
                    continue
                try:
                    value = self.model.normalize(option, raw)
                except (TypeError, ValueError, OverflowError):
                    self.report(widgets, "failed")
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

    def poll(self):
        widgets, now = self.resolve(), time.perf_counter_ns()
        self.read_changes(widgets, now)
        if self.take(widgets["close"]):
            return self.flush(widgets)
        if self.take(widgets["options"]):
            if self.flush(widgets) and self.model.change_page("options"):
                self.options_open = True
                widgets["pages"].SetActiveWidgetIndex(len(self.model.pages))
                self.refresh_labels(widgets)
            else:
                self.report(widgets, "failed")
            return False
        for language in ("EN", "FR"):
            if self.take(widgets[f"language:{language}"]):
                if self.flush(widgets) and self.model.change_language(language):
                    self.refresh_labels(widgets)
                else:
                    self.report(widgets, "failed")
                return False
        for index, key in enumerate(self.model.pages):
            if self.take(widgets[f"nav:{key}"]):
                if self.flush(widgets) and self.model.change_page(key):
                    self.page = index
                    self.options_open = False
                    widgets["pages"].SetActiveWidgetIndex(index)
                    self.refresh_labels(widgets)
                else:
                    self.report(widgets, "failed")
                return False
        for name in ("restore", "undo", "enabled"):
            if self.take(widgets[name]):
                if not self.flush(widgets):
                    return False
                success = (self.model.toggle_enabled if name == "enabled"
                           else getattr(self.model, name))()
                self.notice = {"restore": "restored", "undo": "undone",
                               "enabled": "saved"}[name] if success else "failed"
                self.sync(widgets)
                return False
        if self.pending and now - self.changed_at >= t.SAVE_DELAY_NS:
            self.flush(widgets)
        return False

    def selecting(self):
        widgets = self.resolve()
        return any(sc.is_shortcut(option) and widgets[f"setting:{key}"].GetIsSelectingKey()
                   for key, option in self.model.options.items())
