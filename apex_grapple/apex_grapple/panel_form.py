"""Full menu interactions, with bounded drafts and one shared key-capture form."""

import time

from .control_form import Form
from .control_bindings import RESERVED
from . import panel_i18n as i18n, panel_labels as labels, panel_theme as t, panel_theme_choice
from . import panel_choices, panel_key_display
from .menu import ACTIVE_WHEN, DEPENDS_ON
from . import panel_size_choice
from . import panel_popup, panel_updates
from .panel_preferences import LANGUAGES


class PanelForm(Form):
    keep_when_disabled = True
    # The open pop-up's key (panel_popup.py), or None; the update notes on show and the page open (panel_updates.py).
    popup = None
    update_notes = ()
    update_page = 0

    def __init__(self, widgets, bindings, model):
        super().__init__(widgets, bindings)
        self.model, self.page, self.notice = model, t.PAGES.index(model.page), "ready"
        self.pending, self.shown = {}, {}
        self.changed_at = 0
        self.redraw = False  # set by a theme change; the window's session then draws it again
        self.focus = widgets["focus"]
        self.key_display = panel_key_display.Display()
        self.sync(self.resolve())
        panel_updates.open_if_due(self, self.resolve())

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
                widget.SetValue(float(option.value))
        self.refresh_dependency(widgets)
        self.refresh_labels(widgets)

    def met(self, needs):
        return all(any(self.shown[switch] is True for switch in switches) for switches in needs)

    def active(self, name):
        """Whether row `name` changes something with the values the window shows, saved or not: one switch of each
        of its menu.DEPENDS_ON tuples on, and its menu.ACTIVE_WHEN test passed."""
        test = ACTIVE_WHEN.get(name)
        return self.met(DEPENDS_ON.get(name, ())) and (test is None or bool(test(self.shown)))

    def refresh_dependency(self, widgets):
        """A row that changes nothing greys and stays still (Kevin, 2026-09-26 and -29, Apex Heirloom's sketches;
        docs/mokup/menu_mods/decisions.md), and wakes at the click that makes it count."""
        for name in {**DEPENDS_ON, **ACTIVE_WHEN}:
            self.grey(widgets, f"setting:{name}", (f"row:{name}", f"description:{name}"), self.active(name))

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

    def escape(self):
        """Escape closes an open pop-up alone; otherwise the window, as the Close button does, saving what is still
        pending (control_escape)."""
        if self.popup is not None:
            panel_popup.hide(self, self.resolve())
            return False
        return self.flush(self.resolve())

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

    def show_result(self, widgets, result):
        success, message = result
        key = "controls_saved" if success else "invalid_keys"
        if message == "Default grapple controls restored.":
            key = "controls_reset"
            self.sync(widgets)  # The reset also put back the hold rows shown above the keys.
        elif message == "Could not save. Previous controls kept.":
            key = "failed"
        elif message == RESERVED:
            key = "reserved_key"
        widgets["status"].SetText(i18n.text(key, self.model.language))
        widgets["current"].SetText(labels.controls_summary(self.bindings, self.model.language))
        self.key_display.summary(self, widgets)

    def poll(self):
        widgets, now = self.resolve(), time.perf_counter_ns()
        # An open pop-up alone takes the clicks: nothing behind it changes meanwhile.
        if panel_updates.poll(self, widgets):
            return False
        self.read_changes(widgets, now)
        if self.take(widgets["close"]):
            return self.flush(widgets)
        if self.take(widgets["theme"]):
            panel_theme_choice.choose(self, widgets)
            return False
        if self.take(widgets["window_size"]):
            panel_size_choice.choose(self, widgets)
            return False
        for language in LANGUAGES:
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
                               else self.model.toggle_notice if name == "enabled" else "failed")
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
