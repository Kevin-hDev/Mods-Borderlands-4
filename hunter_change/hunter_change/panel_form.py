"""Poll Movement's menu controls and save validated option changes."""

import time

from . import panel_hunters as hunter_page, panel_i18n as i18n, panel_labels as labels, panel_switch, panel_theme as t, switch_page, wardrobe


class PanelForm:
    keep_when_disabled = True

    def __init__(self, widgets, model):
        self.widgets, self.model = widgets, model
        self.page = model.pages.index(model.page)
        self.notice = "ready"
        self.pending, self.shown = {}, {}
        self.changed_at = 0
        self.focus = widgets["focus"]
        self.command_form = self.command_catalogue = None
        if model.command_actions is not None:
            from .camera_control_form import Form
            from .panel_glyphs import Catalogue
            self.command_form = Form(widgets, model)
            self.command_catalogue = Catalogue()
        self.hunter_state = wardrobe.status()
        self.switch_page = switch_page.SwitchPage()
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
            else:
                widget.SetValue(float(option.value))
        self.refresh_labels(widgets)

    def refresh_labels(self, widgets):
        labels.apply(self, widgets)
        for key, option in self.model.options.items():
            labels.value(widgets, option, self.shown[key], self.model.language)
        if self.command_form is not None:
            from . import panel_camera_commands
            panel_camera_commands.refresh(self, widgets, self.command_catalogue)

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
        if self.model.transaction.pending:
            return False
        if not self.pending:
            return True
        success = self.model.write(self.pending)
        self.notice = "saved" if success else "ready" if success is None else "failed"
        self.sync(widgets)
        return success is True

    def close_ready(self):
        return self.model.cancel_transaction()

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

    def poll(self):
        widgets, now = self.resolve(), time.perf_counter_ns()
        outcome = self.model.advance()
        if outcome is not None:
            self.notice = outcome
            self.sync(widgets)
        self.read_changes(widgets, now)
        worn = hunter_page.taken(self.take, widgets)
        if worn is not None:
            self.notice = "saved" if wardrobe.wear(worn) else "failed"
            self.hunter_state = wardrobe.status()
            self.refresh_labels(widgets)
            return False
        # The page follows the game while it is open: a game loaded or left, the mod turned on or off.
        state = wardrobe.status()
        if state != self.hunter_state:
            self.hunter_state = state
            self.refresh_labels(widgets)
        switched = panel_switch.poll(self, widgets)
        if switched:
            return switched if switched == panel_switch.LEAVE else False
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
            if self.command_form is not None and self.take(widgets[f"icons:{family}"]):
                if self.model.change_controller_icons(family):
                    self.refresh_labels(widgets)
                else:
                    self.report(widgets, "failed")
                return False
        for index, key in enumerate(self.model.pages):
            if self.take(widgets[f"nav:{key}"]):
                if self.flush(widgets) and self.model.change_page(key):
                    self.page = index
                    widgets["pages"].SetActiveWidgetIndex(index)
                    self.refresh_labels(widgets)
                else:
                    self.report(widgets, "failed")
                return False
        for name in ("enabled",):
            if self.take(widgets[name]):
                if not self.flush(widgets):
                    return False
                success = (self.model.toggle_enabled if name == "enabled"
                           else getattr(self.model, name))()
                self.notice = ({"restore": "restored", "undo": "undone",
                                "enabled": "saved"}[name] if success else
                               "ready" if success is None else "failed")
                self.sync(widgets)
                return False
        if self.pending and now - self.changed_at >= t.SAVE_DELAY_NS:
            self.flush(widgets)
        if (self.command_form is not None and not self.model.transaction.pending
                and self.model.pages[self.page] == "commands"):
            self.command_form.poll()
            if self.command_form.changed:
                self.refresh_labels(widgets)
        return False

    def selecting(self):
        return False
